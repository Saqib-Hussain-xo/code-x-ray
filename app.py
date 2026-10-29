"""
X-Ray Execution Agent: HTTP Backend Application Server
Module: app.py

Features:
- REST API routing with /api/trace and /api/health endpoints.
- Error handling with structured 400 responses for syntax and malformed inputs.
- Server-rendered routing for main visualizer, privacy policy, and terms.
- Static asset serving for minimal geometric SVG favicon and frontend assets.
- Clean environment-configurable host and port binding for custom domain readiness.
"""

import os
import time
from collections import defaultdict
from flask import Flask, jsonify, render_template, request, send_from_directory
from tracer import ExecutionTracer
from presets_data import ALGORITHM_PRESETS, ALLOWED_PRESET_IDS

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

# Application metadata
APP_VERSION = "1.0.0"

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
    Returns status: healthy, version, and preset execution capability.
    """
    return jsonify({
        "status": "healthy",
        "version": APP_VERSION,
        "execution_mode": "preset_only",
        "total_presets": len(ALGORITHM_PRESETS)
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


@app.route("/api/trace", methods=["POST", "OPTIONS"])
def trace_code():
    """
    Runtime code interception endpoint.
    Accepts JSON body: {"preset_id": "..."}
    Strictly restricted to the 25 pre-approved algorithm presets.
    Arbitrary user-submitted Python code is rejected for security.
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
            "error": "Invalid request payload. Expected JSON object with a 'preset_id' field."
        }), 400

    # Explicit rejection of arbitrary code submissions
    if "code" in payload and "preset_id" not in payload:
        return jsonify({
            "error": "Arbitrary code execution is disabled in this demo. Please provide a valid 'preset_id' from the 25 supported presets.",
            "code": "ARBITRARY_CODE_EXECUTION_DISABLED",
            "allowed_presets": list(ALGORITHM_PRESETS.keys())
        }), 400

    preset_id = payload.get("preset_id")
    if not preset_id or not isinstance(preset_id, str):
        return jsonify({
            "error": "Field 'preset_id' must be a valid string identifier.",
            "allowed_presets": list(ALGORITHM_PRESETS.keys())
        }), 400

    if preset_id not in ALGORITHM_PRESETS:
        return jsonify({
            "error": f"Unknown preset_id: '{preset_id}'. Only the 25 predefined algorithmic presets are supported.",
            "allowed_presets": list(ALGORITHM_PRESETS.keys())
        }), 400

    # Retrieve vetted, trusted Python code from backend allowlist
    trusted_code = ALGORITHM_PRESETS[preset_id]["code"]

    # Execute line-by-line deterministic tracer engine directly
    tracer = ExecutionTracer(max_steps=1000, max_seconds=2.0)

    try:
        result = tracer.run_trace(trusted_code)
    except Exception as unexpected_err:
        return jsonify({
            "error": "Internal tracer execution failed.",
            "message": str(unexpected_err)
        }), 500

    # Syntax errors in vetted code should not occur, but return 400 defensively
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
