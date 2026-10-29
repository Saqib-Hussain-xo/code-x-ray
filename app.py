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
from flask import Flask, jsonify, render_template, request, send_from_directory
from tracer import ExecutionTracer

# Initialize Flask application with explicit template and static folder configurations
app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
# Request payload safety limit: 128 KB
app.config["MAX_CONTENT_LENGTH"] = 128 * 1024

# Safety constants for request processing
MAX_CODE_CHARS = 10000
APP_VERSION = "1.0.0"


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
    Ensure static assets and templates are revalidated immediately by clients.
    """
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@app.route("/api/health", methods=["GET"])
def health_check():
    """
    Service health check endpoint.
    Returns status: healthy and current service version.
    """
    return jsonify({
        "status": "healthy",
        "version": APP_VERSION
    }), 200


@app.route("/api/trace", methods=["POST"])
def trace_code():
    """
    Runtime code interception endpoint.
    Accepts JSON body: {"code": "..."}
    Executes Python code inside isolated tracer sandbox and returns step history.
    """
    # Parse incoming JSON payload safely
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return jsonify({
            "error": "Invalid request payload. Expected JSON object with a 'code' field."
        }), 400

    code_str = payload.get("code")
    if code_str is None or not isinstance(code_str, str):
        return jsonify({
            "error": "Field 'code' must be a valid string."
        }), 400

    if len(code_str) > MAX_CODE_CHARS:
        return jsonify({
            "error": f"Field 'code' exceeds maximum limit of {MAX_CODE_CHARS} characters."
        }), 400

    # Instantiate deterministic tracer engine
    tracer = ExecutionTracer(max_steps=1000, max_seconds=2.0)

    try:
        result = tracer.run_trace(code_str)
    except Exception as unexpected_err:
        # Catch unexpected tracer boundary errors
        return jsonify({
            "error": "Internal tracer execution failed.",
            "message": str(unexpected_err)
        }), 500

    # Syntax errors in user code are returned as structured 400 responses
    if result.get("status") == "syntax_error":
        return jsonify(result), 400

    # Return execution timeline payload
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
