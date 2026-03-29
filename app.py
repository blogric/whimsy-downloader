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
    rednote_urls = [u.strip() for u in urls if 'xhslink.com' in u.lower()]
    return list(dict.fromkeys(rednote_urls))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/download")
async def download_videos(text: str = Form(...)):
    links = extract_rednote_links(text)
    if not links:
        return {"error": "Koi valid xhslink nahi mila"}

    with tempfile.TemporaryDirectory() as tmpdirname:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best',
            'outtmpl': f'{tmpdirname}/%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'merge_output_format': 'mp4',
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
                'Referer': 'https://www.xiaohongshu.com/',
            }
        }

        downloaded = []
        for url in links:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info and 'requested_downloads' in info:
                        for d in info['requested_downloads']:
                            if os.path.exists(d['filepath']):
                                downloaded.append(os.path.basename(d['filepath']))
            except Exception as e:
                print(f"Failed {url}: {str(e)[:100]}")

        if not downloaded:
            return {"error": "Koi video download nahi ho saka. RedNote currently blocks many direct downloads."}

        # Create ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in downloaded:
                fpath = os.path.join(tmpdirname, fname)
                zf.write(fpath, fname)
        
        zip_buffer.seek(0)
        return FileResponse(
            path=zip_buffer,
            media_type="application/zip",
            filename="rednote_videos.zip"
        )
