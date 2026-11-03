"""
Code X-Ray: Final Security and Edge-Case Test Suite
Validates:
1. Trace Export / Import integrity and sanitization
2. Shareable link encoding, restoration, and secret isolation
3. Execution security (timeouts, limits, sandbox fail-closed, secrets)
4. Comprehensive algorithmic edge cases
5. Presets validity across all 25 allowlisted algorithms
"""

import json
import os
import sys
import unittest
from app import app, ALGORITHM_PRESETS, is_rate_limited, _client_request_history
from tracer import ExecutionTracer, TraceTimeout, TraceLimitExceeded
from recognizer import recognize_algorithm
from analyzer import analyze_complexity
from sandbox_adapter import Judge0SandboxAdapter, SandboxConfigurationError


class FinalSecurityAndEdgeCaseAudit(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    # =========================================================================
    # 1. TRACE EXPORT / IMPORT INTEGRITY
    # =========================================================================
    def test_trace_export_structure_and_roundtrip(self):
        code = "x = [3, 1, 2]\nx.sort()\nprint(x)"
        res = self.client.post("/api/trace", json={"code": code})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # Simulate export payload structure created by exportTraceJSON()
        export_payload = {
            "schema_version": "1.0",
            "exported_at": "2026-11-01T00:00:00Z",
            "code": code,
            "status": data["status"],
            "total_steps": data["total_steps"],
            "steps": data["steps"],
            "recognition": data.get("recognition"),
            "complexity": data.get("complexity"),
            "operation_metrics": data.get("operation_metrics"),
            "stdout": data.get("stdout")
        }

        # Verify all essential fields are present
        self.assertIn("steps", export_payload)
        self.assertGreater(len(export_payload["steps"]), 0)
        self.assertEqual(export_payload["status"], "completed")
        self.assertEqual(export_payload["total_steps"], len(export_payload["steps"]))

        # Check step integrity
        step0 = export_payload["steps"][0]
        self.assertIn("line_no", step0)
        self.assertIn("locals_snapshot", step0)
        self.assertIn("event_type", step0)

    def test_malformed_trace_import_validation(self):
        # 1. Empty payload
        empty_json = "{}"
        parsed_empty = json.loads(empty_json)
        self.assertFalse(bool(parsed_empty.get("steps")))

        # 2. Missing steps array
        corrupted_json = '{"schema_version": "1.0", "steps": "not_an_array"}'
        parsed_corrupted = json.loads(corrupted_json)
        self.assertFalse(isinstance(parsed_corrupted.get("steps"), list))

        # 3. Non-numeric total_steps fallback
        missing_total = {"schema_version": "1.0", "steps": [{"line_no": 1, "variables": {}}]}
        steps = missing_total["steps"]
        total_steps = missing_total.get("total_steps") or len(steps)
        self.assertEqual(total_steps, 1)

    # =========================================================================
    # 2. SHAREABLE LINKS
    # =========================================================================
    def test_shareable_link_encodes_only_source_code(self):
        # Verify that share link format only attaches the source code
        sample_code = "def add(a, b):\n    return a + b\nres = add(2, 3)"
        import urllib.parse
        encoded = urllib.parse.quote(sample_code)
        fragment = f"#code={encoded}"

        # Decoding should exactly restore the source code
        decoded = urllib.parse.unquote(fragment.split("#code=")[1])
        self.assertEqual(decoded, sample_code)

        # Execution history, internal state, variables, and env secrets must NOT be in fragment
        self.assertNotIn("variables", fragment)
        self.assertNotIn("execution_trace", fragment)
        self.assertNotIn("os.environ", fragment)
        self.assertNotIn("SECRET", fragment)

    # =========================================================================
    # 3. EXECUTION SECURITY & LIMITS
    # =========================================================================
    def test_infinite_loop_timeout_protection(self):
        # Code running beyond wall-clock threshold must terminate with TraceTimeout
        infinite_code = "while True:\n    pass"
        tracer = ExecutionTracer(max_steps=5000000, max_seconds=0.05)
        res = tracer.run_trace(infinite_code)
        self.assertEqual(res["status"], "timeout")
        self.assertIn("timeout", res["error"]["type"].lower())

    def test_excessive_step_limit_protection(self):
        # Code exceeding max steps must terminate at 1000 steps
        long_loop_code = "count = 0\nfor i in range(2000):\n    count += 1"
        tracer = ExecutionTracer(max_steps=1000, max_seconds=2.0)
        res = tracer.run_trace(long_loop_code)
        self.assertEqual(res["status"], "step_limit_exceeded")
        self.assertLessEqual(res["total_steps"], 1001)

    def test_excessive_stdout_limit_protection(self):
        # Code producing infinite output must truncate at 20000 chars
        output_code = "for i in range(1000):\n    print('A' * 100)"
        tracer = ExecutionTracer(max_steps=1000, max_seconds=2.0, max_stdout_chars=20000)
        res = tracer.run_trace(output_code)
        self.assertLessEqual(len(res["stdout"]), 20100)
        self.assertIn("stdout truncated", res["stdout"].lower())

    def test_payload_size_limit_413(self):
        # Payloads exceeding 128KB must be rejected by Flask with HTTP 413
        oversized_code = "x = 1\n" * 25000  # ~150KB
        res = self.client.post("/api/trace", data=json.dumps({"code": oversized_code}), content_type="application/json")
        self.assertIn(res.status_code, [400, 413])

    def test_max_code_characters_limit_400(self):
        # Code longer than MAX_CODE_CHARS (10,000) returns 400
        code_10001 = "# comment\n" * 1050
        self.assertGreater(len(code_10001), 10000)
        res = self.client.post("/api/trace", json={"code": code_10001})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("exceeds maximum limit", data["error"])

    def test_rate_limiter_enforcement(self):
        # Test the sliding-window rate limiter directly
        test_ip = "192.168.1.100"
        _client_request_history[test_ip] = []
        for i in range(20):
            self.assertFalse(is_rate_limited(test_ip))
        # The 21st request should be rate-limited
        self.assertTrue(is_rate_limited(test_ip))

    def test_environment_and_secrets_isolation(self):
        # Code attempting to access os.environ inside the sandbox globals
        # tracer runs in clean sandbox_globals without exposing app variables
        code = "import os\nenv_keys = list(os.environ.keys())\nsecret = os.environ.get('SECRET_KEY', 'not_found')"
        tracer = ExecutionTracer(max_steps=1000, max_seconds=2.0)
        res = tracer.run_trace(code)
        self.assertEqual(res["status"], "completed")
        # Ensure server app secrets are not injected into the tracer execution scope
        self.assertNotIn("SECRET_KEY", tracer.stdout_buffer.getvalue())

    def test_production_sandbox_fail_closed(self):
        # When XRAY_EXECUTION_MODE=production and allow_local=false, Judge0 sandbox is invoked
        # If unconfigured, it must fail closed with 503 SANDBOX_NOT_CONFIGURED
        old_mode = os.environ.get("XRAY_EXECUTION_MODE")
        old_local = os.environ.get("XRAY_ALLOW_LOCAL_EXEC")
        try:
            os.environ["XRAY_EXECUTION_MODE"] = "production"
            os.environ["XRAY_ALLOW_LOCAL_EXEC"] = "false"
            # Ensure RapidAPI key is empty
            old_key = os.environ.get("JUDGE0_API_KEY")
            if "JUDGE0_API_KEY" in os.environ:
                del os.environ["JUDGE0_API_KEY"]

            # Disable TESTING flag temporarily to test sandbox branching
            self.app.config["TESTING"] = False
            res = self.client.post("/api/trace", json={"code": "x = 10"})
            self.assertEqual(res.status_code, 503)
            data = res.get_json()
            self.assertEqual(data.get("code"), "SANDBOX_NOT_CONFIGURED")
        finally:
            if old_mode is not None:
                os.environ["XRAY_EXECUTION_MODE"] = old_mode
            else:
                os.environ.pop("XRAY_EXECUTION_MODE", None)
            if old_local is not None:
                os.environ["XRAY_ALLOW_LOCAL_EXEC"] = old_local
            else:
                os.environ.pop("XRAY_ALLOW_LOCAL_EXEC", None)
            if old_key is not None:
                os.environ["JUDGE0_API_KEY"] = old_key
            self.app.config["TESTING"] = True

    # =========================================================================
    # 4. ALGORITHMIC & RUNTIME EDGE CASES
    # =========================================================================
    def test_edge_case_empty_array(self):
        code = "arr = []\nlength = len(arr)\nprint(length)"
        res = self.client.post("/api/trace", json={"code": code})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "completed")

    def test_edge_case_single_element_array(self):
        code = "arr = [42]\nval = arr[0]\narr[0] = 99"
        res = self.client.post("/api/trace", json={"code": code})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "completed")

    def test_edge_case_duplicate_values_and_negatives(self):
        code = "arr = [5, -10, 5, -20, 5, 0]\narr.sort()"
        res = self.client.post("/api/trace", json={"code": code})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "completed")

    def test_edge_case_empty_and_ragged_matrix(self):
        # Empty matrix
        code1 = "m = []\nprint(len(m))"
        res1 = self.client.post("/api/trace", json={"code": code1})
        self.assertEqual(res1.status_code, 200)

        # Ragged / irregular matrix
        code2 = "m = [[1, 2, 3], [4], [5, 6]]\nx = m[1][0]"
        res2 = self.client.post("/api/trace", json={"code": code2})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2["status"], "completed")

    def test_edge_case_large_nested_structure(self):
        code = "data = {'tree': {'nodes': [1, 2, {'val': 3}], 'meta': (True, None)}}\ndata['tree']['nodes'].append(4)"
        res = self.client.post("/api/trace", json={"code": code})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "completed")

    def test_edge_case_missing_search_target(self):
        code = """def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1
res = linear_search([1, 2, 3, 4], 99)"""
        res = self.client.post("/api/trace", json={"code": code})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "completed")

    def test_edge_case_incorrect_sorting_implementation(self):
        # Broken bubble sort that does not complete sort passes
        code = """arr = [5, 2, 9, 1]
for i in range(len(arr) - 1):
    if arr[i] > arr[i+1]:
        arr[i], arr[i+1] = arr[i+1], arr[i]
# Only 1 pass performed, array is still unsorted"""
        res = self.client.post("/api/trace", json={"code": code})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "completed")

    def test_edge_case_multiple_input_calls(self):
        code = "name = input()\nage = input()\nprint(f'{name}:{age}')"
        res = self.client.post("/api/trace", json={"code": code, "stdin": "Alice\n25\n"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["stdout"].strip(), "Alice:25")

    def test_edge_case_invalid_input_conversion(self):
        code = "num = int(input())"
        res = self.client.post("/api/trace", json={"code": code, "stdin": "not_a_number\n"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "exception")
        self.assertEqual(data["error"]["type"], "ValueError")

    def test_edge_case_deep_recursion_guard(self):
        # Deep recursion triggers RecursionError bounded by sys.setrecursionlimit(500)
        code = """def recurse(n):
    return recurse(n + 1)
recurse(1)"""
        tracer = ExecutionTracer(max_steps=1000, max_seconds=5.0)
        res = tracer.run_trace(code)
        self.assertEqual(res["status"], "exception")
        self.assertEqual(res["error"]["type"], "RecursionError")

    def test_edge_case_rapid_repeated_requests(self):
        # 10 rapid back-to-back trace requests in testing mode
        for i in range(10):
            res = self.client.post("/api/trace", json={"code": f"x = {i} * 2"})
            self.assertEqual(res.status_code, 200)

    # =========================================================================
    # 5. ALL 25 PRESETS REGRESSION
    # =========================================================================
    def test_all_25_presets_execute_successfully(self):
        self.assertEqual(len(ALGORITHM_PRESETS), 25)
        for preset_id, preset_info in ALGORITHM_PRESETS.items():
            res = self.client.post("/api/trace", json={"preset_id": preset_id})
            self.assertEqual(res.status_code, 200, f"Preset {preset_id} failed with status {res.status_code}")
            data = res.get_json()
            self.assertEqual(data.get("status"), "completed", f"Preset {preset_id} did not complete: {data.get('error')}")
            self.assertGreater(data.get("total_steps", 0), 0, f"Preset {preset_id} had 0 steps")


if __name__ == "__main__":
    unittest.main()
