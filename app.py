from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import re
import yt_dlp
import os
import tempfile
import zipfile
from io import BytesIO

app = FastAPI(title="RedNote Video Downloader")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def extract_rednote_links(text: str):
    # Sab URLs nikaalo
    url_pattern = r'https?://[^\s<>"]+'
    urls = re.findall(url_pattern, text)
    # Sirf RedNote / xhslink wale
    rednote_urls = [u.strip() for u in urls if any(x in u.lower() for x in ['xhslink.com', 'xiaohongshu.com', 'rednote'])]
    return list(dict.fromkeys(rednote_urls))  # duplicates remove

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/extract")
async def extract(text: str = Form(...)):
    links = extract_rednote_links(text)
    return {"links": links}

@app.post("/download")
async def download_videos(links: str = Form(...)):
    url_list = links.split(",")
    if not url_list:
        return {"error": "No links"}

    with tempfile.TemporaryDirectory() as tmpdirname:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': f'{tmpdirname}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'merge_output_format': 'mp4',
        }

        downloaded_files = []
        for url in url_list:
            url = url.strip()
            if not url:
                continue
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                # Downloaded file find karo
                for file in os.listdir(tmpdirname):
                    if file.endswith('.mp4') and file not in downloaded_files:
                        downloaded_files.append(file)
                        break
            except Exception as e:
                print(f"Error downloading {url}: {e}")

        # ZIP banao
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_name in downloaded_files:
                file_path = os.path.join(tmpdirname, file_name)
                zip_file.write(file_path, file_name)
        
        zip_buffer.seek(0)
        return FileResponse(
            path=zip_buffer,
            media_type="application/zip",
            filename="rednote_videos.zip",
            headers={"Content-Disposition": "attachment; filename=rednote_videos.zip"}
        )
