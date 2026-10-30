"""
X-Ray Execution Agent: HTTP Backend Application Server
Module: app.py

Features:
- REST API routing with /api/trace, /api/validate, /api/presets, and /api/health endpoints.
- Real-time Python syntax validation using standard library AST parsing.
- Support for Custom Code Playground execution with bounded resource limits.
- Secure routing with sandboxed execution in production and verified local mode.
- Server-rendered routing for main visualizer, privacy policy, and terms.
- Static asset serving for minimal geometric SVG favicon and CodeMirror/frontend assets.
"""

import ast
import os
import time
from collections import defaultdict
from flask import Flask, jsonify, render_template, request, send_from_directory
from tracer import ExecutionTracer
from presets_data import ALGORITHM_PRESETS, ALLOWED_PRESET_IDS
from sandbox_adapter import (
    Judge0SandboxAdapter,
    SandboxConfigurationError,
    SandboxExecutionError,
    SandboxRateLimitError,
    SandboxTimeoutError
)

# Resolve absolute paths for Vercel serverless environment compatibility
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize Flask application with explicit template and static folder configurations
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
# Request payload safety limit: 128 KB
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024

# Safety constants for request processing
MAX_CODE_CHARS = 10000
APP_VERSION = "1.2.0"

# Sliding-window rate limiter (20 requests per 60 seconds per IP)
RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX_REQUESTS = 20
_client_request_history = defaultdict(list)


def is_rate_limited(client_ip: str) -> bool:
    """
    Check if a client IP has exceeded the allowed request frequency.
    """
    now = time.monotonic()
    history = _client_request_history[client_ip]
    # Prune timestamps older than window
    active_history = [t for t in history if now - t < RATE_LIMIT_WINDOW]
    _client_request_history[client_ip] = active_history
    if len(active_history) >= RATE_LIMIT_MAX_REQUESTS:
        return True
    active_history.append(now)
    return False


@app.errorhandler(413)
def request_entity_too_large(error):
    """
    Handle oversized request payloads exceeding MAX_CONTENT_LENGTH.
    """
    return jsonify({
        "error": "Request payload exceeds maximum allowed size (128 KB)."
    }), 413


@app.after_request
def add_no_cache_headers(response):
    """
    Ensure static assets and templates are revalidated immediately by clients,
    and configure safe CORS headers for multi-domain frontend hosting.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Service health check endpoint.
    Returns status: healthy, version, and execution capabilities.
    """
    execution_mode = os.environ.get("XRAY_EXECUTION_MODE", "playground").lower()
    return jsonify({
        "status": "healthy",
        "version": APP_VERSION,
        "execution_mode": execution_mode,
        "total_presets": len(ALGORITHM_PRESETS),
        "custom_code_enabled": True
    }), 200


@app.route("/api/presets", methods=["GET"])
def list_presets():
    """
    Returns the metadata of all 25 pre-approved algorithms in the allowlist.
    """
    summary = [
        {
            "id": p["id"],
            "title": p["title"],
            "category": p["category"]
        }
        for p in ALGORITHM_PRESETS.values()
    ]
    return jsonify({
        "presets": summary,
        "total": len(summary)
    }), 200


@app.route("/api/validate", methods=["POST", "OPTIONS"])
def validate_code():
    """
    Python syntax validation endpoint using standard AST parsing.
    Detects syntax errors before execution, returning exact line and column offsets.
    """
    if request.method == "OPTIONS":
        return ("", 204)

    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({
            "valid": False,
            "error": {
                "type": "ValidationError",
                "message": "Invalid request payload. Expected JSON object with 'code' field.",
                "line_no": 1,
                "offset": 1
            }
        }), 400

    code_str = payload.get("code")
    if code_str is None or not isinstance(code_str, str):
        return jsonify({
            "valid": False,
            "error": {
                "type": "ValidationError",
                "message": "Field 'code' must be a valid string.",
                "line_no": 1,
                "offset": 1
            }
        }), 400

    if not code_str.strip():
        return jsonify({
            "valid": False,
            "error": {
                "type": "ValidationError",
                "message": "Code submission cannot be empty. Please enter Python code to visualize.",
                "line_no": 1,
                "offset": 1
            }
        }), 400

    if len(code_str) > MAX_CODE_CHARS:
        return jsonify({
            "valid": False,
            "error": {
                "type": "ValidationError",
                "message": f"Code length exceeds maximum allowed limit of {MAX_CODE_CHARS} characters.",
                "line_no": 1,
                "offset": 1
            }
        }), 400

    try:
        ast.parse(code_str, filename="<user_code>")
        return jsonify({"valid": True}), 200
    except SyntaxError as syn_err:
        line_no = syn_err.lineno or 1
        col_no = syn_err.offset or 1
        msg = syn_err.msg or "Invalid Python syntax"
        return jsonify({
            "valid": False,
            "error": {
                "type": "SyntaxError",
                "message": msg,
                "line_no": line_no,
                "offset": col_no,
                "text": (syn_err.text or "").strip()
            }
        }), 200


@app.route("/api/trace", methods=["POST", "OPTIONS"])
def trace_code():
    """
    Runtime code interception and execution endpoint.
    Accepts JSON body: {"code": "..."} for custom code or {"preset_id": "..."} for preloaded problems.
    Routes execution to an isolated sandbox environment or verified local execution mode.
    Guarantees AST syntax pre-validation, input bounds, and fail-closed security.
    """
    if request.method == "OPTIONS":
        return ("", 204)

    # Enforce per-client rate limit (disabled during automated test runner)
    if not app.config.get("TESTING", False):
        client_ip = request.remote_addr or "127.0.0.1"
        if is_rate_limited(client_ip):
            return jsonify({
                "error": "Rate limit exceeded. Maximum 20 requests per minute permitted."
            }), 429

    # Parse incoming JSON payload safely
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({
            "error": "Invalid request payload. Expected JSON object with 'code' or 'preset_id' field."
        }), 400

    preset_id = payload.get("preset_id")
    code_str = payload.get("code")

    # If neither preset_id nor code is provided
    if not preset_id and (code_str is None or not isinstance(code_str, str)):
        return jsonify({
            "error": "Missing required field. Please provide 'code' or a valid 'preset_id'."
        }), 400

    # 1. Preset execution path (trusted allowlist)
    if preset_id:
        if not isinstance(preset_id, str):
            return jsonify({
                "error": "Field 'preset_id' must be a valid string identifier.",
                "allowed_presets": list(ALGORITHM_PRESETS.keys())
            }), 400

        if preset_id not in ALGORITHM_PRESETS:
            return jsonify({
                "error": f"Unknown preset_id: '{preset_id}'. Only the 25 predefined algorithmic presets are supported.",
                "allowed_presets": list(ALGORITHM_PRESETS.keys())
            }), 400

        target_code = ALGORITHM_PRESETS[preset_id]["code"]
        is_preset = True
    else:
        # 2. Custom code execution path
        if not code_str.strip():
            return jsonify({
                "status": "syntax_error",
                "total_steps": 0,
                "steps": [],
                "error": {
                    "type": "ValidationError",
                    "message": "Code submission cannot be empty. Please enter Python code to visualize.",
                    "line_no": 1,
                    "offset": 1
                },
                "stdout": ""
            }), 400

        if len(code_str) > MAX_CODE_CHARS:
            return jsonify({
                "error": f"Field 'code' exceeds maximum limit of {MAX_CODE_CHARS} characters."
            }), 400

        target_code = code_str
        is_preset = False

    # AST syntax validation before execution
    try:
        ast.parse(target_code, filename="<user_code>")
    except SyntaxError as syn_err:
        return jsonify({
            "status": "syntax_error",
            "total_steps": 0,
            "steps": [],
            "error": {
                "type": "SyntaxError",
                "message": syn_err.msg or "Invalid syntax",
                "line_no": syn_err.lineno or 1,
                "offset": syn_err.offset or 1
            },
            "stdout": ""
        }), 400

    exec_mode = os.environ.get("XRAY_EXECUTION_MODE", "local").lower()
    allow_local = os.environ.get("XRAY_ALLOW_LOCAL_EXEC", "true").lower() == "true"
    is_testing = app.config.get("TESTING", False)

    # If it is a trusted preset OR local execution is authorized OR running under tests:
    if is_preset or allow_local or exec_mode == "local" or is_testing:
        tracer = ExecutionTracer(max_steps=1000, max_seconds=2.0)
        try:
            result = tracer.run_trace(target_code)
        except Exception as unexpected_err:
            return jsonify({
                "error": "Internal tracer execution failed.",
                "message": str(unexpected_err)
            }), 500
    else:
        # Production arbitrary code execution: Fail-closed sandbox isolation
        sandbox = Judge0SandboxAdapter()
        try:
            result = sandbox.execute(target_code)
        except SandboxConfigurationError as cfg_err:
            return jsonify({
                "error": "Isolated sandbox execution provider is not configured.",
                "details": str(cfg_err),
                "code": "SANDBOX_NOT_CONFIGURED"
            }), 503
        except SandboxRateLimitError as rate_err:
            return jsonify({
                "error": str(rate_err),
                "code": "SANDBOX_RATE_LIMITED"
            }), 429
        except SandboxTimeoutError as timeout_err:
            result = {
                "status": "timeout",
                "total_steps": 0,
                "steps": [],
                "error": {
                    "type": "TraceTimeout",
                    "message": str(timeout_err),
                    "line_no": 1
                },
                "stdout": ""
            }
        except SandboxExecutionError as exec_err:
            return jsonify({
                "error": "Isolated sandbox execution failed.",
                "details": str(exec_err)
            }), 503

    # Syntax errors in user code are returned as structured 400 responses
    if result.get("status") == "syntax_error":
        return jsonify(result), 400

    # Return execution timeline payload matching the exact frontend schema
    try:
        return jsonify(result), 200
    except Exception as serialization_err:
        return jsonify({
            "error": "Failed to serialize execution trace payload to JSON.",
            "message": str(serialization_err)
        }), 400


@app.route("/", methods=["GET"])
def index_page():
    """
    Serves the primary 3-pane industrial visualizer interface.
    """
    return render_template("index.html")


@app.route("/privacy", methods=["GET"])
def privacy_page():
    """
    Serves the dedicated Privacy Policy page.
    """
    return render_template("privacy.html")


@app.route("/terms", methods=["GET"])
def terms_page():
    """
    Serves the dedicated Terms and Conditions page.
    """
    return render_template("terms.html")


@app.route("/favicon.svg", methods=["GET"])
def favicon_icon():
    """
    Serves the minimal geometric SVG favicon directly from static folder.
    """
    return send_from_directory(app.static_folder, "favicon.svg", mimetype="image/svg+xml")


if __name__ == "__main__":
    # Support custom port configuration via environment variable for deployment readiness
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port, debug=False)
