"""
X-Ray Execution Agent: Test Suite for Sandbox Adapter
Module: test_sandbox_adapter.py

Validates Judge0 CE adapter behavior, runner script generation, Base64 payload encoding,
response extraction, status code mapping, and fail-closed error handling.
"""

import base64
import json
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from sandbox_adapter import (
    Judge0SandboxAdapter,
    SandboxConfigurationError,
    SandboxExecutionError,
    SandboxRateLimitError,
    SandboxTimeoutError,
    build_sandbox_runner_script
)


class TestSandboxAdapter(unittest.TestCase):
    """
    Unit tests for remote execution sandbox adapter.
    """

    def setUp(self):
        self.adapter = Judge0SandboxAdapter(
            api_url="https://judge0-ce.p.rapidapi.com",
            api_key="test-api-key-12345",
            api_host="judge0-ce.p.rapidapi.com"
        )

    def test_runner_script_generation(self):
        """
        Verify that the runner script properly embeds the user script and tracer logic.
        """
        user_code = "a = 10\nb = 20\nprint(a + b)"
        runner_script = build_sandbox_runner_script(user_code)

        self.assertIn("ExecutionTracer", runner_script)
        self.assertIn("__XRAY_TRACE_START__", runner_script)
        self.assertIn("__XRAY_TRACE_END__", runner_script)
        # Verify user code is embedded in Base64
        expected_b64 = base64.b64encode(user_code.encode("utf-8")).decode("ascii")
        self.assertIn(expected_b64, runner_script)

    def test_unconfigured_adapter_raises_configuration_error(self):
        """
        Verify that attempting to execute with no API key raises SandboxConfigurationError.
        """
        unconfigured_adapter = Judge0SandboxAdapter(
            api_url="https://judge0-ce.p.rapidapi.com",
            api_key=None
        )
        with self.assertRaises(SandboxConfigurationError):
            unconfigured_adapter.execute("x = 1")

    def test_parse_judge0_successful_response(self):
        """
        Verify parsing of a valid Judge0 response containing delimited trace JSON.
        """
        sample_trace = {
            "status": "completed",
            "total_steps": 1,
            "steps": [
                {
                    "step_index": 0,
                    "line_no": 1,
                    "locals_snapshot": {"val": 42},
                    "types": {"val": "int"},
                    "mutations": ["val"],
                    "sequences": {},
                    "pointers": [],
                    "stdout": "Result: 42\n"
                }
            ],
            "error": None,
            "stdout": "Result: 42\n"
        }

        embedded_output = f"Prelude log\n__XRAY_TRACE_START__\n{json.dumps(sample_trace)}\n__XRAY_TRACE_END__\nPostlude log"
        b64_stdout = base64.b64encode(embedded_output.encode("utf-8")).decode("ascii")

        mock_judge0_payload = {
            "status": {"id": 3, "description": "Accepted"},
            "stdout": b64_stdout,
            "stderr": None,
            "compile_output": None
        }

        result = self.adapter._parse_judge0_response(mock_judge0_payload)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["total_steps"], 1)
        self.assertEqual(result["steps"][0]["locals_snapshot"]["val"], 42)

    def test_parse_judge0_timeout_status_5(self):
        """
        Verify that status id 5 (Time Limit Exceeded) maps cleanly to an X-Ray timeout payload.
        """
        mock_payload = {
            "status": {"id": 5, "description": "Time Limit Exceeded"},
            "stdout": None,
            "stderr": None
        }

        result = self.adapter._parse_judge0_response(mock_payload)
        self.assertEqual(result["status"], "timeout")
        self.assertEqual(result["error"]["type"], "TraceTimeout")

    def test_parse_judge0_syntax_error_status_6(self):
        """
        Verify that status id 6 (Compilation Error) maps cleanly to a syntax_error payload.
        """
        raw_err = "SyntaxError: invalid syntax (line 1)"
        b64_err = base64.b64encode(raw_err.encode("utf-8")).decode("ascii")

        mock_payload = {
            "status": {"id": 6, "description": "Compilation Error"},
            "stdout": None,
            "stderr": None,
            "compile_output": b64_err
        }

        result = self.adapter._parse_judge0_response(mock_payload)
        self.assertEqual(result["status"], "syntax_error")
        self.assertIn("SyntaxError", result["error"]["message"])

    def test_parse_judge0_missing_delimiters_raises_execution_error(self):
        """
        Verify that if the sandbox stdout lacks X-Ray delimiters, SandboxExecutionError is raised.
        """
        mock_payload = {
            "status": {"id": 11, "description": "Runtime Error (NZEC)"},
            "stdout": base64.b64encode(b"Traceback (most recent call last):\nFatal error").decode("ascii"),
            "stderr": base64.b64encode(b"Out of memory").decode("ascii")
        }

        with self.assertRaises(SandboxExecutionError) as ctx:
            self.adapter._parse_judge0_response(mock_payload)
        self.assertIn("Sandbox execution failed", str(ctx.exception))

    @patch("urllib.request.urlopen")
    def test_execute_handles_http_429_rate_limit(self, mock_urlopen):
        """
        Verify that HTTP 429 from provider raises SandboxRateLimitError.
        """
        http_err = urllib.error.HTTPError(
            url="https://judge0-ce.p.rapidapi.com",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=None
        )
        mock_urlopen.side_effect = http_err

        with self.assertRaises(SandboxRateLimitError):
            self.adapter.execute("a = 1")


if __name__ == "__main__":
    unittest.main()
