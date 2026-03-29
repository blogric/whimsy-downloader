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
        return {"error": "Koi valid xhslink.com link nahi mila"}

    with tempfile.TemporaryDirectory() as tmpdirname:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best',
            'outtmpl': f'{tmpdirname}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.xiaohongshu.com/',
            }
        }

        downloaded_files = []
        for url in links:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info:
                        # Downloaded file ka naam nikaalo
                        for entry in info.get('requested_downloads', []):
                            if os.path.exists(entry.get('filepath', '')):
                                downloaded_files.append(os.path.basename(entry['filepath']))
            except Exception as e:
                print(f"Download failed for {url}: {str(e)[:150]}")

        if not downloaded_files:
            return {"error": "Koi bhi video download nahi ho saka. RedNote blocking kar raha hai ya links expired hain."}

        # ZIP file banao
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in downloaded_files:
                filepath = os.path.join(tmpdirname, fname)
                zf.write(filepath, fname)
        
        zip_buffer.seek(0)
        return FileResponse(
            path=zip_buffer,
            media_type="application/zip",
            filename="rednote_videos.zip"
        )
