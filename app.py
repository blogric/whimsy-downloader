from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os
import re

app = Flask(__name__)

# 🔥 Start Playwright once (performance + stability)
playwright = sync_playwright().start()

browser = playwright.chromium.launch(
    headless=True,
    args=[
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu"
    ]
)

def get_video(url):
    try:
        page = browser.new_page()
        page.goto(url, timeout=60000)

        # wait for page load
        page.wait_for_timeout(5000)

        # 🔍 Try video tag
        video = page.query_selector("video")
        if video:
            src = video.get_attribute("src")
            page.close()
            if src:
                return src

        # 🔁 Fallback: search in HTML
        content = page.content()
        page.close()

        match = re.search(r'\"url\":\"(https:.*?\\.mp4)\"', content)
        if match:
            return match.group(1)

        return None

    except Exception as e:
        try:
            page.close()
        except:
            pass
        return None


@app.route("/")
def home():
    try:
        return open("index.html").read()
    except:
        return "<h2>Frontend not found</h2>"


@app.route("/bulk", methods=["POST"])
def bulk():
    data = request.json
    links = data.get("links", [])

    results = []

    for link in links:
        video = get_video(link)
        results.append({
            "link": link,
            "video": video if video else "Failed"
        })

    return jsonify(results)


# 🔥 Railway compatible PORT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
