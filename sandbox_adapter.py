"""
X-Ray Execution Agent: Isolated Sandbox Execution Adapter
Module: sandbox_adapter.py

Handles isolated, sandboxed execution of user-submitted Python code via remote
containerized execution environments (e.g., Judge0 CE or custom isolate runtimes).
Guarantees that untrusted code never executes in the web application process.
"""

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional


class SandboxExecutionError(Exception):
    """Base exception for sandbox execution errors."""
    pass


class SandboxConfigurationError(SandboxExecutionError):
    """Raised when sandbox provider credentials or URLs are missing."""
    pass


class SandboxTimeoutError(SandboxExecutionError):
    """Raised when sandbox execution exceeds wall-clock or network timeout."""
    pass


class SandboxRateLimitError(SandboxExecutionError):
    """Raised when the sandbox provider responds with 429 Too Many Requests."""
    pass


def get_tracer_source() -> str:
    """
    Read the clean source code of tracer.py to embed in the sandbox runner.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    tracer_path = os.path.join(current_dir, "tracer.py")
    with open(tracer_path, "r", encoding="utf-8") as f:
        return f.read()


def build_sandbox_runner_script(user_code: str) -> str:
    """
    Generate a self-contained Python script to execute inside the sandbox.
    Embeds the deterministic tracer and outputs delimited JSON results to stdout.
    """
    tracer_code = get_tracer_source()
    encoded_user_code = base64.b64encode(user_code.encode("utf-8")).decode("ascii")

    runner_template = f'''# Auto-generated X-Ray Sandbox Runner
import base64
import json
import sys

# Embed Tracer Engine Source Directly
{tracer_code}

# Decode and execute user script under tracer
USER_CODE_PAYLOAD = "{encoded_user_code}"
raw_code = base64.b64decode(USER_CODE_PAYLOAD).decode("utf-8")

tracer_instance = ExecutionTracer(max_steps=1000, max_seconds=2.0)
trace_output = tracer_instance.run_trace(raw_code)

# Emit delimited JSON payload for adapter extraction
print("\\n__XRAY_TRACE_START__")
print(json.dumps(trace_output))
print("__XRAY_TRACE_END__")
'''
    return runner_template


class Judge0SandboxAdapter:
    """
    Adapter for executing untrusted code inside Judge0 CE sandboxes.
    Communicates via REST API over HTTPS with base64-encoded payloads.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_host: Optional[str] = None,
        language_id: Optional[int] = None
    ):
        self.api_url = (api_url or os.environ.get("JUDGE0_API_URL") or "https://judge0-ce.p.rapidapi.com").rstrip("/")
        self.api_key = api_key or os.environ.get("JUDGE0_API_KEY")
        self.api_host = api_host or os.environ.get("JUDGE0_API_HOST") or "judge0-ce.p.rapidapi.com"
        self.language_id = language_id or int(os.environ.get("JUDGE0_LANGUAGE_ID", "71"))

    def is_configured(self) -> bool:
        """
        Verify that required provider credentials are present.
        """
        # If targeting official RapidAPI endpoint, an API key is required
        if "rapidapi.com" in self.api_url:
            return bool(self.api_key)
        return bool(self.api_url)

    def execute(self, user_code: str, timeout: float = 12.0) -> Dict[str, Any]:
        """
        Execute user code inside the Judge0 sandbox and extract trace results.
        """
        if not self.is_configured():
            raise SandboxConfigurationError(
                "Judge0 sandbox is not configured. Set JUDGE0_API_KEY (and optionally JUDGE0_API_URL)."
            )

        runner_script = build_sandbox_runner_script(user_code)
        b64_source = base64.b64encode(runner_script.encode("utf-8")).decode("ascii")

        submission_payload = {
            "language_id": self.language_id,
            "source_code": b64_source,
            "stdin": "",
            "cpu_time_limit": 3.0,
            "wall_time_limit": 5.0,
            "memory_limit": 128000,
            "max_file_size": 1024
        }

        endpoint = f"{self.api_url}/submissions?base64_encoded=true&wait=true"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "X-Ray-Execution-Agent/1.0"
        }
        if self.api_key:
            headers["X-RapidAPI-Key"] = self.api_key
            headers["X-RapidAPI-Host"] = self.api_host

        req = urllib.request.Request(
            endpoint,
            data=json.dumps(submission_payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw_response = resp.read().decode("utf-8")
                response_data = json.loads(raw_response)
        except urllib.error.HTTPError as http_err:
            if http_err.code == 429:
                raise SandboxRateLimitError("Sandbox provider rate limit exceeded. Please retry shortly.")
            error_body = ""
            try:
                error_body = http_err.read().decode("utf-8")
            except Exception:
                pass
            raise SandboxExecutionError(f"Sandbox provider HTTP error {http_err.code}: {error_body}")
        except urllib.error.URLError as url_err:
            raise SandboxTimeoutError(f"Network error connecting to sandbox provider: {url_err.reason}")
        except Exception as e:
            raise SandboxExecutionError(f"Unexpected error communicating with sandbox: {str(e)}")

        return self._parse_judge0_response(response_data)

    def _parse_judge0_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract X-Ray trace results from Judge0 execution output.
        """
        status_info = response_data.get("status", {})
        status_id = status_info.get("id")

        # Status 5: Time Limit Exceeded
        if status_id == 5:
            return {
                "status": "timeout",
                "total_steps": 0,
                "steps": [],
                "error": {
                    "type": "TraceTimeout",
                    "message": "Execution timed out inside the sandbox container.",
                    "line_no": 1
                },
                "stdout": ""
            }

        # Status 6: Compilation Error
        if status_id == 6:
            compile_output = response_data.get("compile_output") or ""
            if compile_output:
                try:
                    compile_output = base64.b64decode(compile_output).decode("utf-8", errors="replace")
                except Exception:
                    pass
            return {
                "status": "syntax_error",
                "total_steps": 0,
                "steps": [],
                "error": {
                    "type": "SyntaxError",
                    "message": compile_output.strip() or "Syntax error in user script.",
                    "line_no": 1
                },
                "stdout": ""
            }

        # Base64 decode stdout from Judge0
        raw_b64_stdout = response_data.get("stdout") or ""
        decoded_stdout = ""
        if raw_b64_stdout:
            try:
                decoded_stdout = base64.b64decode(raw_b64_stdout).decode("utf-8", errors="replace")
            except Exception:
                decoded_stdout = raw_b64_stdout

        # Search for delimited X-Ray JSON payload
        pattern = r"__XRAY_TRACE_START__\s*([\s\S]*?)\s*__XRAY_TRACE_END__"
        match = re.search(pattern, decoded_stdout)
        if match:
            json_blob = match.group(1).strip()
            try:
                trace_payload = json.loads(json_blob)
                return trace_payload
            except json.JSONDecodeError as decode_err:
                raise SandboxExecutionError(f"Failed to parse trace JSON from sandbox stdout: {str(decode_err)}")

        # If delimiter not found, check stderr
        raw_b64_stderr = response_data.get("stderr") or ""
        decoded_stderr = ""
        if raw_b64_stderr:
            try:
                decoded_stderr = base64.b64decode(raw_b64_stderr).decode("utf-8", errors="replace")
            except Exception:
                decoded_stderr = raw_b64_stderr

        description = status_info.get("description", "Unknown error")
        raise SandboxExecutionError(
            f"Sandbox execution failed ({description}). stderr: {decoded_stderr.strip()}"
        )
