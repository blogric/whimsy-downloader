from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import re
import yt_dlp
import os
import tempfile
import zipfile
from io import BytesIO

app = FastAPI(title="RedNote Direct Downloader")
templates = Jinja2Templates(directory="templates")

def extract_rednote_links(text: str):
    url_pattern = r'https?://[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    # Sirf xhslink.com wale links
    rednote_urls = [u.strip() for u in urls if 'xhslink.com' in u.lower()]
    return list(dict.fromkeys(rednote_urls))  # unique links

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download")
async def download_videos(text: str = Form(...)):
    links = extract_rednote_links(text)
    if not links:
        return {"error": "Koi valid xhslink.com link nahi mila. Sirf http://xhslink.com wale links paste karo."}

    with tempfile.TemporaryDirectory() as tmpdirname:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best',
            'outtmpl': f'{tmpdirname}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': False,           # logging on kar diya
            'no_warnings': False,
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'Referer': 'https://www.xiaohongshu.com/',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }
        }

        downloaded_files = []
        errors = []

        for url in links:
            try:
                print(f"Downloading: {url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info:
                        for entry in info.get('requested_downloads', []):
                            filepath = entry.get('filepath')
                            if filepath and os.path.exists(filepath):
                                downloaded_files.append(os.path.basename(filepath))
                                print(f"Success: {os.path.basename(filepath)}")
            except Exception as e:
                err_msg = str(e)[:200]
                errors.append(f"{url}: {err_msg}")
                print(f"Failed {url}: {err_msg}")

        if not downloaded_files:
            error_text = "Koi video download nahi ho saka.\n\n" + "\n".join(errors[:3])
            if "Unable to extract" in error_text or "generic" in error_text.lower():
                error_text += "\n\nRedNote (xhslink) currently blocks yt-dlp. Manual browser method ya dedicated downloader use karo."
            return {"error": error_text}

        # ZIP banao
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in downloaded_files:
                zf.write(os.path.join(tmpdirname, fname), fname)
        
        zip_buffer.seek(0)
        return FileResponse(
            path=zip_buffer,
            media_type="application/zip",
            filename="rednote_videos.zip"
        )
