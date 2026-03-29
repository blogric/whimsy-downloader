from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import yt_dlp
import os
import uuid
import threading
import time
import re
import json

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "/tmp/whimsy_downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Track job status in memory
jobs = {}

def cleanup_file(path, delay=600):
    def _delete():
        time.sleep(delay)
        try:
            if os.path.exists(path):
                os.remove(path)
        except:
            pass
    threading.Thread(target=_delete, daemon=True).start()

def extract_links(text):
    text = re.sub(r'(?<=[^\s])(https?://)', r'\n\1', text)
    clean = []
    pattern = re.compile(r'(https?://(www\.)?(xhslink\.com|xiaohongshu\.com)[a-zA-Z0-9/_\-?.=&%]+)')
    for line in text.splitlines():
        line = line.strip()
        m = pattern.match(line)
        if m:
            url = m.group(1)
            if url not in clean:
                clean.append(url)
    return clean

def download_worker(job_id, links, quality):
    jobs[job_id]['status'] = 'running'
    jobs[job_id]['total'] = len(links)
    jobs[job_id]['done'] = 0
    jobs[job_id]['results'] = []

    fmt_map = {
        'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '720':  'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '480':  'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'worst':'worst[ext=mp4]/worst',
    }
    fmt = fmt_map.get(quality, fmt_map['best'])

    for i, url in enumerate(links):
        file_id = str(uuid.uuid4())
        output_path = os.path.join(DOWNLOAD_DIR, f"{file_id}.mp4")

        jobs[job_id]['current_url'] = url
        jobs[job_id]['current_index'] = i + 1

        ydl_opts = {
            'format': fmt,
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 3,
            'noplaylist': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', f'video_{i+1}') if info else f'video_{i+1}'

            # Find actual output file
            actual_path = output_path
            if not os.path.exists(actual_path):
                for f in os.listdir(DOWNLOAD_DIR):
                    if f.startswith(file_id):
                        actual_path = os.path.join(DOWNLOAD_DIR, f)
                        break

            if os.path.exists(actual_path):
                cleanup_file(actual_path, delay=600)
                safe_title = re.sub(r'[\\/*?:"<>|]', '', title)[:60]
                jobs[job_id]['results'].append({
                    'status': 'success',
                    'url': url,
                    'title': safe_title,
                    'file_id': file_id,
                    'filename': f"{safe_title}.mp4"
                })
            else:
                jobs[job_id]['results'].append({
                    'status': 'error',
                    'url': url,
                    'error': 'File not found after download'
                })

        except Exception as e:
            jobs[job_id]['results'].append({
                'status': 'error',
                'url': url,
                'error': str(e)[:200]
            })

        jobs[job_id]['done'] = i + 1
        if i < len(links) - 1:
            time.sleep(1)

    jobs[job_id]['status'] = 'complete'

@app.route('/')
def index():
    with open(os.path.join(os.path.dirname(__file__), 'static', 'index.html'), 'r') as f:
        return f.read()

@app.route('/api/extract', methods=['POST'])
def api_extract():
    data = request.json
    text = data.get('text', '')
    links = extract_links(text)
    return jsonify({'links': links, 'count': len(links)})

@app.route('/api/start', methods=['POST'])
def api_start():
    data = request.json
    links = data.get('links', [])
    quality = data.get('quality', 'best')

    if not links:
        return jsonify({'error': 'No links provided'}), 400
    if len(links) > 50:
        return jsonify({'error': 'Max 50 links at once'}), 400

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'queued',
        'total': len(links),
        'done': 0,
        'results': [],
        'current_url': '',
        'current_index': 0,
        'created': time.time()
    }

    thread = threading.Thread(target=download_worker, args=(job_id, links, quality), daemon=True)
    thread.start()

    return jsonify({'job_id': job_id})

@app.route('/api/status/<job_id>', methods=['GET'])
def api_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

@app.route('/api/file/<file_id>', methods=['GET'])
def api_file(file_id):
    filename = request.args.get('name', 'video.mp4')
    # Security: only alphanumeric and hyphens in file_id
    if not re.match(r'^[a-f0-9\-]+$', file_id):
        return jsonify({'error': 'Invalid file id'}), 400

    path = None
    for f in os.listdir(DOWNLOAD_DIR):
        if f.startswith(file_id):
            path = os.path.join(DOWNLOAD_DIR, f)
            break

    if not path or not os.path.exists(path):
        return jsonify({'error': 'File not found or expired'}), 404

    return send_file(
        path,
        as_attachment=True,
        download_name=filename,
        mimetype='video/mp4'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
