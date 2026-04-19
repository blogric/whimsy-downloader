# app.py
from flask import Flask, request, jsonify
import os
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow same-origin requests

# Your RapidAPI key MUST be set in Railway Environment Variables
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
if not RAPIDAPI_KEY:
    print("⚠️  WARNING: RAPIDAPI_KEY not set in environment variables!")

@app.route("/")
def home():
    # The full premium HTML is embedded here (see the big HTML block above)
    # For GitHub upload, copy the entire HTML content from the block above into the string below
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return html

@app.route("/api/convert", methods=["POST"])
def convert():
    if not RAPIDAPI_KEY:
        return jsonify({"success": False, "error": "Server configuration error - RAPIDAPI_KEY missing"}), 500
    
    data = request.get_json()
    youtube_url = data.get("url")
    
    if not youtube_url:
        return jsonify({"success": False, "error": "No URL provided"}), 400
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "youtube-mp310.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(
            "https://youtube-mp310.p.rapidapi.com/download/mp3",
            headers=headers,
            params={"url": youtube_url},
            timeout=15
        )
        
        if response.status_code == 200:
            api_data = response.json()
            if "downloadUrl" in api_data:
                return jsonify({
                    "success": True,
                    "downloadUrl": api_data["downloadUrl"]
                })
            else:
                return jsonify({"success": False, "error": "Invalid response from RapidAPI"}), 502
        else:
            return jsonify({
                "success": False,
                "error": f"RapidAPI error {response.status_code}: {response.text[:200]}"
            }), response.status_code
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
