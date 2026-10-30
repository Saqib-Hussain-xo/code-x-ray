"""
X-Ray Execution Agent: Test Suite for HTTP Backend Server (Custom Code Playground Architecture)
Module: test_app.py

Validates API endpoints, health check metadata, preset execution, custom code execution,
real-time AST syntax validation, rate limiting, and template serving.
"""

import json
import os
import unittest
from app import app, _client_request_history
from presets_data import ALGORITHM_PRESETS


class TestAppServer(unittest.TestCase):
    """
    Integration tests for Flask HTTP application routes and API responses.
    """

    def setUp(self):
        app.config["TESTING"] = True
        _client_request_history.clear()
        self.client = app.test_client()

    def tearDown(self):
        _client_request_history.clear()

    def test_health_check_endpoint(self):
        """
        Verify GET /api/health returns 200 OK with expected JSON structure and custom code capability.
        """
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("version"), "1.2.0")
        self.assertEqual(data.get("total_presets"), 25)
        self.assertTrue(data.get("custom_code_enabled"))

    def test_list_presets_endpoint(self):
        """
        Verify GET /api/presets returns the metadata summary of all 25 allowlisted presets.
        """
        response = self.client.get("/api/presets")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("total"), 25)
        self.assertEqual(len(data.get("presets")), 25)
        preset_ids = [p["id"] for p in data["presets"]]
        self.assertIn("two_pointer_palindrome", preset_ids)
        self.assertIn("binary_search", preset_ids)
        self.assertIn("bubble_sort", preset_ids)

    def test_validate_endpoint_valid_python(self):
        """
        Verify POST /api/validate with valid Python code returns 200 and valid: true.
        """
        code = "def add(a, b):\n    return a + b\nres = add(2, 3)\n"
        response = self.client.post(
            "/api/validate",
            data=json.dumps({"code": code}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get("valid"))

    def test_validate_endpoint_syntax_error(self):
        """
        Verify POST /api/validate with syntax error returns valid: false with line and column.
        """
        code = "def bad_func(\n    x = 1\n"
        response = self.client.post(
            "/api/validate",
            data=json.dumps({"code": code}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data.get("valid"))
        self.assertIn("error", data)
        self.assertEqual(data["error"]["type"], "SyntaxError")
        self.assertGreaterEqual(data["error"]["line_no"], 1)
        self.assertGreaterEqual(data["error"]["offset"], 1)

    def test_validate_endpoint_empty_code(self):
        """
        Verify POST /api/validate with empty code returns 400 with ValidationError.
        """
        response = self.client.post(
            "/api/validate",
            data=json.dumps({"code": "   "}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertFalse(data.get("valid"))
        self.assertEqual(data["error"]["type"], "ValidationError")

    def test_trace_custom_code_execution(self):
        """
        Verify POST /api/trace with custom code executes and returns populated trace timeline.
        """
        custom_code = (
            "nums = [3, 1, 2]\n"
            "nums.sort()\n"
            "print('Sorted:', nums)\n"
        )
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"code": custom_code}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("status"), "completed")
        self.assertIsInstance(data.get("steps"), list)
        self.assertGreater(len(data["steps"]), 0)
        self.assertIn("nums", data["steps"][-1]["locals_snapshot"])
        self.assertIn("Sorted:", data["stdout"])

    def test_trace_custom_code_syntax_error_returns_400(self):
        """
        Verify POST /api/trace with syntax error in custom code returns 400 Bad Request.
        """
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"code": "def incomplete(\n"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data.get("status"), "syntax_error")
        self.assertIn("error", data)
        self.assertEqual(data["error"]["type"], "SyntaxError")

    def test_trace_custom_code_empty_returns_400(self):
        """
        Verify POST /api/trace with empty code returns 400 Bad Request.
        """
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"code": "   \n\t"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertEqual(data.get("status"), "syntax_error")

    def test_trace_valid_preset(self):
        """
        Verify POST /api/trace with a valid preset_id returns 200 OK and populated steps array.
        """
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"preset_id": "two_pointer_palindrome"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("status"), "completed")
        self.assertIsInstance(data.get("steps"), list)
        self.assertGreater(len(data["steps"]), 0)
        self.assertIn("left", data["steps"][-1]["locals_snapshot"])

    def test_trace_all_25_presets(self):
        """
        Verify that every single preset in the allowlist executes cleanly to completion.
        """
        for preset_id in ALGORITHM_PRESETS:
            response = self.client.post(
                "/api/trace",
                data=json.dumps({"preset_id": preset_id}),
                content_type="application/json"
            )
            self.assertEqual(response.status_code, 200, f"Preset '{preset_id}' returned {response.status_code}")
            data = response.get_json()
            self.assertEqual(data.get("status"), "completed", f"Preset '{preset_id}' failed: {data.get('error')}")
            self.assertGreater(data.get("total_steps", 0), 0)

    def test_trace_unknown_preset_id_rejected(self):
        """
        Verify that submitting an unrecognized preset_id returns 400 Bad Request.
        """
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"preset_id": "unknown_algorithm_123"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("allowed_presets", data)

    def test_trace_missing_both_fields_returns_400(self):
        """
        Verify POST /api/trace with neither code nor preset_id returns 400 Bad Request.
        """
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"wrong_field": "pass"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_trace_oversized_payload_returns_413(self):
        """
        Verify POST /api/trace with payload exceeding MAX_CONTENT_LENGTH (128 KB) returns 413.
        """
        oversized_data = json.dumps({"code": "x = 1\n", "padding": "A" * (130 * 1024)})
        response = self.client.post(
            "/api/trace",
            data=oversized_data,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 413)
        data = response.get_json()
        self.assertIn("error", data)

    def test_template_routes(self):
        """
        Verify all three HTML template routes (/, /privacy, /terms) return 200 OK.
        """
        # 1. Main visualizer index route
        index_res = self.client.get("/")
        self.assertEqual(index_res.status_code, 200)
        self.assertIn(b"X-Ray // Runtime Inspector", index_res.data)

        # 2. Privacy Policy route
        privacy_res = self.client.get("/privacy")
        self.assertEqual(privacy_res.status_code, 200)
        self.assertIn(b"Privacy Policy", privacy_res.data)

        # 3. Terms and Conditions route
        terms_res = self.client.get("/terms")
        self.assertEqual(terms_res.status_code, 200)
        self.assertIn(b"Terms and Conditions", terms_res.data)

    def test_favicon_route(self):
        """
        Verify GET /favicon.svg returns 200 OK with SVG mimetype.
        """
        response = self.client.get("/favicon.svg")
        self.assertEqual(response.status_code, 200)
        self.assertIn("image/svg+xml", response.content_type)
        self.assertIn(b"<svg", response.data)

    def test_rate_limiter_blocks_excessive_requests(self):
        """
        Verify that exceeding the client rate limit returns 429 Too Many Requests.
        """
        app.config["TESTING"] = False
        try:
            # Execute 20 allowable requests
            for _ in range(20):
                res = self.client.post(
                    "/api/trace",
                    data=json.dumps({"preset_id": "bubble_sort"}),
                    content_type="application/json"
                )
                self.assertIn(res.status_code, [200, 400])

            # 21st request should be rate limited
            blocked_res = self.client.post(
                "/api/trace",
                data=json.dumps({"preset_id": "bubble_sort"}),
                content_type="application/json"
            )
            self.assertEqual(blocked_res.status_code, 429)
            data = blocked_res.get_json()
            self.assertIn("Rate limit", data.get("error"))
        finally:
            app.config["TESTING"] = True


if __name__ == "__main__":
    unittest.main()
