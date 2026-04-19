from flask import Flask, request, jsonify, send_from_directory
import os
import requests
from flask_cors import CORS

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

@app.route("/")
def home():
    return send_from_directory('.', 'index.html')

@app.route("/api/convert", methods=["POST"])
def convert():
    if not RAPIDAPI_KEY:
        return jsonify({"success": False, "error": "RAPIDAPI_KEY is not set in Railway Environment Variables"}), 500

    data = request.get_json(silent=True) or {}
    youtube_url = data.get("url")

    if not youtube_url:
        return jsonify({"success": False, "error": "Please provide a YouTube URL"}), 400

    headers = {
        'x-rapidapi-key': RAPIDAPI_KEY,
        'x-rapidapi-host': "youtube-mp310.p.rapidapi.com"
    }

    try:
        response = requests.get(
            "https://youtube-mp310.p.rapidapi.com/download/mp3",
            headers=headers,
            params={"url": youtube_url},
            timeout=25
        )

        print(f"Status: {response.status_code} | Response preview: {response.text[:400]}")  # For debugging

        if response.status_code == 200:
            result = response.text.strip()

            # Most common case: API returns direct MP3 link as plain text
            if result.startswith("http"):
                return jsonify({
                    "success": True,
                    "downloadUrl": result,
                    "title": "Downloaded Audio"
                })

            # Fallback: try to parse as JSON if the API changed
            try:
                json_data = response.json()
                download_url = (json_data.get("downloadUrl") or 
                               json_data.get("url") or 
                               json_data.get("link") or 
                               result)
                if download_url and str(download_url).startswith("http"):
                    return jsonify({
                        "success": True,
                        "downloadUrl": download_url,
                        "title": json_data.get("title", "YouTube Audio")
                    })
            except:
                pass

            return jsonify({"success": False, "error": "Could not extract download link. Try a different video."}), 502

        else:
            return jsonify({
                "success": False,
                "error": f"API Error {response.status_code}: {response.text[:300]}"
            }), response.status_code

    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
