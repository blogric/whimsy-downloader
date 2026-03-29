from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import re
import yt_dlp
import os
import tempfile
import zipfile
from io import BytesIO

app = FastAPI(title="RedNote Downloader")
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
        return {"error": "Koi valid xhslink.com link nahi mila"}

    with tempfile.TemporaryDirectory() as tmpdirname:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best',
            'outtmpl': f'{tmpdirname}/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.xiaohongshu.com/',
            }
        }

        downloaded_files = []
        errors = []

        for url in links:
            try:
                print(f"[+] Trying: {url}")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info:
                        for entry in info.get('requested_downloads', []):
                            fp = entry.get('filepath')
                            if fp and os.path.exists(fp):
                                downloaded_files.append(os.path.basename(fp))
                                print(f"[✓] Downloaded: {os.path.basename(fp)}")
            except Exception as e:
                err = str(e)[:300]
                errors.append(f"{url}: {err}")
                print(f"[-] Failed {url}: {err}")

        if not downloaded_files:
            error_msg = "Koi video download nahi ho saka.\n\n" + "\n".join(errors[:5])
            if "Unable to extract" in error_msg or "generic" in error_msg.lower():
                error_msg += "\n\nNote: RedNote (xhslink) currently has heavy blocking on yt-dlp. Direct download mushkil hai."
            return {"error": error_msg}

        # ZIP banao
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in downloaded_files:
                zf.write(os.path.join(tmpdirname, fname), fname)
        
        zip_buffer.seek(0)
        
        # Fixed way to send BytesIO
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=rednote_videos.zip"
            }
        )
