# Whimsy — RedNote Smart Downloader v3 ONLINE

Aapke PC wale tool ka exact online version.

## Features
- Koi bhi text paste karein — links auto-detect
- xhslink.com aur xiaohongshu.com dono support
- Real-time download queue with status
- Direct browser download (MP4)
- Duplicate skip, retry support

---

## Deploy on Railway — Step by Step

### Step 1: GitHub repo banayein
1. github.com pe jayen, login karein
2. "New repository" → naam: `whimsy-downloader`
3. "Private" rakhen (recommended)
4. Yeh files upload karein (structure bilkul same rakhen):
   ```
   whimsy-downloader/
   ├── app.py
   ├── requirements.txt
   ├── Procfile
   ├── railway.toml
   └── static/
       └── index.html
   ```

### Step 2: Railway pe deploy karein
1. railway.app pe jayen → "Start a New Project"
2. "Deploy from GitHub repo" → apna repo select karein
3. Railway automatically build karega (2-3 min)
4. "Settings" → "Networking" → "Generate Domain"
5. Aapko milega: `https://whimsy-downloader-xxx.up.railway.app`

### Step 3: Use karein
- Woh URL kholein — Whimsy ka UI dikhega
- Links ya koi bhi text paste karein
- "Download karein" dabayein
- Har video ke saamne "Download" button aayega

---

## Free Tier
Railway deta hai $5/month free credit — personal use ke liye kaafi hai.
