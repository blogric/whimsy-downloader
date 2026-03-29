from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.templating import Jinja2Templates
import re
import yt_dlp
import os
import tempfile
import zipfile
from io import BytesIO

app = FastAPI(title="RedNote Pro Downloader")
templates = Jinja2Templates(directory="templates")

def extract_rednote_links(text: str):
    url_pattern = r'https?://[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    rednote_urls = [u.strip() for u in urls if 'xhslink.com' in u.lower()]
    return list(dict.fromkeys(rednote_urls))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ====================== SINGLE VIDEO DOWNLOAD ======================
@app.post("/download_single")
async def download_single(url: str = Form(...)):
    if not url or 'xhslink.com' not in url.lower():
        return {"error": "Invalid RedNote link"}

    with tempfile.TemporaryDirectory() as tmpdirname:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best',
            'outtmpl': f'{tmpdirname}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.xiaohongshu.com/',
            }
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info and info.get('requested_downloads'):
                    filepath = info['requested_downloads'][0]['filepath']
                    filename = os.path.basename(filepath) or "rednote_video.mp4"

                    def iter_file():
                        with open(filepath, 'rb') as f:
                            yield from f

                    return StreamingResponse(
                        iter_file(),
                        media_type="video/mp4",
                        headers={"Content-Disposition": f"attachment; filename={filename}"}
                    )
        except Exception as e:
            return {"error": str(e)[:200]}

    return {"error": "Download failed"}

# ====================== DOWNLOAD ALL AS ZIP ======================
@app.post("/download")
async def download_videos(text: str = Form(...)):
    links = extract_rednote_links(text)
    if not links:
        return {"error": "Koi valid link nahi mila"}

    with tempfile.TemporaryDirectory() as tmpdirname:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best',
            'outtmpl': f'{tmpdirname}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': True,
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
                    ydl.extract_info(url, download=True)
                    for f in os.listdir(tmpdirname):
                        if f.endswith('.mp4') and f not in downloaded_files:
                            downloaded_files.append(f)
                            break
            except:
                pass

        if not downloaded_files:
            return {"error": "Koi video download nahi ho saka"}

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
