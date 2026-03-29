from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import re
import yt_dlp
import os
import tempfile
from io import BytesIO

app = FastAPI(title="RedNote Pro")
templates = Jinja2Templates(directory="templates")

def extract_rednote_links(text: str):
    url_pattern = r'https?://[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    return list(dict.fromkeys([u.strip() for u in urls if 'xhslink.com' in u.lower()]))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Single Video Download
@app.post("/download_single")
async def download_single(url: str = Form(...)):
    if not url or 'xhslink.com' not in url.lower():
        return {"error": "Invalid xhslink"}

    with tempfile.TemporaryDirectory() as tmp:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best',
            'outtmpl': f'{tmp}/%(title)s.%(ext)s',
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

                    def file_iterator():
                        with open(filepath, "rb") as f:
                            yield from f

                    return StreamingResponse(
                        file_iterator(),
                        media_type="video/mp4",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
                    )
        except Exception as e:
            return {"error": str(e)[:150]}

    return {"error": "Download failed"}
