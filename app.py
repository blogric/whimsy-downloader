from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import os

app = Flask(__name__)

def get_video(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox","--disable-dev-shm-usage"]
            )
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)

            video = page.query_selector("video")
            if video:
                src = video.get_attribute("src")
                browser.close()
                return src

            content = page.content()
            browser.close()

            import re
            match = re.search(r'\"url\":\"(https:.*?\\.mp4)\"', content)
            if match:
                return match.group(1)

        return None
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
        video = get_video(link)
        results.append({"link": link, "video": video if video else "Failed"})

    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)
