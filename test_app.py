"""
X-Ray Execution Agent: Test Suite for HTTP Backend Server
Module: test_app.py

Validates all API endpoints, HTTP status codes, payload validations,
template serving, and static asset delivery using Flask's test client.
"""

import json
import unittest
from app import app


class TestAppServer(unittest.TestCase):
    """
    Integration tests for Flask HTTP application routes and API responses.
    """

    def setUp(self):
        # Configure app in testing mode and create isolated test client
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_health_check_endpoint(self):
        """
        Requirement 1:
        Verify GET /api/health returns 200 OK with expected JSON structure.
        """
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("version"), "1.0.0")

    def test_trace_valid_while_loop(self):
        """
        Requirement 2:
        Verify POST /api/trace with a valid while loop returns 200 OK and populated steps array.
        """
        code_snippet = """
arr = [1, 2, 3]
i = 0
total = 0
while i < len(arr):
    total += arr[i]
    i += 1
"""
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"code": code_snippet}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("status"), "completed")
        self.assertIsInstance(data.get("steps"), list)
        self.assertGreater(len(data["steps"]), 0)

        # Verify final step recorded the accumulated total
        last_step = data["steps"][-1]
        self.assertEqual(last_step["locals_snapshot"].get("total"), 6)

    def test_trace_infinite_loop_kill_switch_propagation(self):
        """
        Requirement 3:
        Verify POST /api/trace with counter = 0\\nwhile True: counter += 1 returns 200 OK,
        and JSON payload confirms status: 'step_limit_exceeded'.
        """
        infinite_loop_code = "counter = 0\nwhile True:\n    counter += 1"
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"code": infinite_loop_code}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("status"), "step_limit_exceeded")
        self.assertIsNotNone(data.get("error"))
        self.assertEqual(data["error"].get("type"), "TraceLimitExceeded")
        self.assertEqual(data.get("total_steps"), 1000)

    def test_trace_syntax_error_returns_400(self):
        """
        Requirement 4:
        Verify POST /api/trace with raw garbage text (invalid syntax) returns 400 Bad Request.
        """
        garbage_code = "def invalid_syntax(: {{"
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"code": garbage_code}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

        data = response.get_json()
        self.assertIsNotNone(data)
        self.assertEqual(data.get("status"), "syntax_error")
        self.assertEqual(data["error"].get("type"), "SyntaxError")

    def test_trace_invalid_json_payload_returns_400(self):
        """
        Verify POST /api/trace with missing code field returns 400 Bad Request.
        """
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"wrong_key": "pass"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_trace_code_length_exceeded_returns_400(self):
        """
        Verify POST /api/trace with code exceeding 10,000 characters returns 400 Bad Request.
        """
        large_code = "# harmless comment\n" * 600  # > 10,000 chars
        response = self.client.post(
            "/api/trace",
            data=json.dumps({"code": large_code}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)
        self.assertIn("maximum limit", data["error"])

    def test_trace_oversized_payload_returns_413(self):
        """
        Verify POST /api/trace with payload exceeding MAX_CONTENT_LENGTH (128 KB) returns 413.
        """
        oversized_data = json.dumps({"code": "x = 1", "padding": "A" * (130 * 1024)})
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
        Requirement 5:
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


if __name__ == "__main__":
    unittest.main()
