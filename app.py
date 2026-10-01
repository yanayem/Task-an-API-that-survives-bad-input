import os
from flask import Flask, request, jsonify, redirect
from services.link_service import LinkService, ValidationException

app = Flask(__name__)
link_service = LinkService()


@app.route("/api/links", methods=["POST"])
@app.route("/links", methods=["POST"])
def create_link():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({
            "error": "Request body must be a valid JSON object.",
            "field": "body"
        }), 400

    target_url = data.get("url") or data.get("target_url") or data.get("targetUrl")
    if not target_url:
        return jsonify({
            "error": "Missing required field 'url' in request payload.",
            "field": "url"
        }), 400

    try:
        short_link = link_service.create_or_get_short_link(target_url)
        return jsonify(short_link.to_dict(request.host_url)), 201
    except ValidationException as ve:
        return jsonify({"error": ve.message, "field": ve.field}), 400


@app.route("/api/links/<code_val>", methods=["GET"])
@app.route("/stats/<code_val>", methods=["GET"])
def get_stats(code_val):
    short_link = link_service.get_link_stats(code_val)
    if not short_link:
        return jsonify({
            "error": f"Unknown short code: {code_val}",
            "field": "code"
        }), 404

    return jsonify(short_link.to_dict(request.host_url)), 200


@app.route("/<code_val>", methods=["GET"])
@app.route("/r/<code_val>", methods=["GET"])
def redirect_link(code_val):
    if code_val in ("api", "links", "stats", "favicon.ico"):
        return jsonify({
            "error": "Resource not found.",
            "field": "path"
        }), 404

    short_link = link_service.get_and_follow_link(code_val)
    if not short_link:
        return jsonify({
            "error": f"Unknown short code: {code_val}",
            "field": "code"
        }), 404

    # HTTP 302 Found (Temporary Redirect)
    return redirect(short_link.target_url, code=302)


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "URL Shortener Service (Flask/Python)",
        "status": "running"
    }), 200


@app.errorhandler(400)
def handle_400(e):
    return jsonify({"error": "Bad request format or payload.", "field": "request"}), 400


@app.errorhandler(404)
def handle_404(e):
    return jsonify({"error": "Resource not found.", "field": "path"}), 404


@app.errorhandler(405)
def handle_405(e):
    return jsonify({"error": "Method not allowed for this endpoint.", "field": "method"}), 405


@app.errorhandler(Exception)
def handle_global_exception(e):
    # Safety net: Catch unexpected errors and respond with 400 instead of 500
    return jsonify({"error": f"Invalid request: {str(e)}", "field": "request"}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting URL Shortener Flask Server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
