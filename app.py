from flask import Flask, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

def extract_video(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, allow_redirects=True)
        final_url = r.url

        html = requests.get(final_url, headers=headers).text
        soup = BeautifulSoup(html, "html.parser")

        video = None

        # try video tag
        tag = soup.find("video")
        if tag and tag.get("src"):
            video = tag.get("src")

        # fallback meta
        if not video:
            meta = soup.find("meta", property="og:video")
            if meta:
                video = meta.get("content")

        return video
    except:
        return None


@app.route("/")
def home():
    return open("index.html").read()


@app.route("/bulk", methods=["POST"])
def bulk():
    data = request.json
    links = data.get("links", [])
    results = []

    for link in links:
        video = extract_video(link)
        results.append({
            "link": link,
            "video": video if video else "Not Found"
        })

    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
