# 🤖 YouTube Auto-Post Bot
**Google Drive → GPT → Cloudinary → YouTube | ~₹3-4/video**

---

## 📁 Project Structure
```
yt-autopost/
├── main.py                 # Main bot — yahi chalega
├── drive_watcher.py        # Google Drive se videos pick karo
├── metadata_generator.py   # GPT se title/desc/hashtags
├── thumbnail_maker.py      # Cloudinary se thumbnail
├── youtube_uploader.py     # YouTube pe upload
├── queue_manager.py        # Queue system
├── setup.py                # Ek baar chalao tokens ke liye
├── requirements.txt        # Python packages
├── render.yaml             # Render.com config
├── .env.example            # Environment variables template
└── credentials/            # (Khud banao — git mein mat daalo!)
    ├── drive_credentials.json
    └── youtube_credentials.json
```

---

## 🚀 STEP BY STEP SETUP

### STEP 1 — Google Cloud Console Setup (10-15 min, ek baar)

1. **console.cloud.google.com** pe jaao
2. **New Project** banao → naam kuch bhi
3. **"APIs & Services"** → **"Enable APIs"** pe click karo
4. Dono enable karo:
   - ✅ **Google Drive API**
   - ✅ **YouTube Data API v3**
5. **"Credentials"** → **"Create Credentials"** → **"OAuth 2.0 Client ID"**
6. Application type: **"Desktop app"** select karo
7. **Download JSON** karo → rename karke:
   - `drive_credentials.json`
   - `youtube_credentials.json`  
   *(same file dono jagah copy kar sakte ho)*
8. Dono files `credentials/` folder mein daalo
9. **"OAuth consent screen"** mein apna email **"Test users"** mein add karo

---

### STEP 2 — Cloudinary Account (5 min)

1. **cloudinary.com** → Free account banao
2. Dashboard pe jaao → left side mein **Cloud Name** dikhai dega
3. **Settings** → **API Keys** → Copy:
   - Cloud Name
   - API Key  
   - API Secret

---

### STEP 3 — OpenAI API Key (2 min)

1. **platform.openai.com** pe jaao
2. **API Keys** → **"Create new secret key"**
3. Copy karo — sirf ek baar dikhega!
4. Thoda credit add karo ($5 = 1000+ videos ke liye enough)

---

### STEP 4 — Local Machine Pe Pehli Baar Run Karo

```bash
# Project folder mein jaao
cd yt-autopost

# Python packages install karo
pip install -r requirements.txt

# .env file banao
cp .env.example .env

# .env file kholo aur apni values daalo
notepad .env   # Windows
# ya
nano .env      # Mac/Linux

# Setup script chalao (browser mein Google login hoga)
python setup.py
```

**Browser mein 2 baar login hoga:**
- Pehli baar: Drive access ke liye
- Doosri baar: YouTube access ke liye

Tokens `credentials/` mein save ho jayenge.

---

### STEP 5 — Local Test Karo

```bash
# Drive folder mein ek test MP4 daalo pehle
# Phir:
python main.py
```

Console mein kuch aisa dikhega:
```
2024-01-15 10:30:00 | INFO | 🤖 YouTube Auto-Post Bot START
2024-01-15 10:30:01 | INFO | 🔍 Drive mein naye videos dhundh raha hoon...
2024-01-15 10:30:02 | INFO | 🆕 3 nayi videos mili
2024-01-15 10:30:02 | INFO | 🎬 Processing: hulk_fight.mp4
2024-01-15 10:30:05 | INFO | ✅ Title: 🔥 Hulk Ka Sabse Dangerous Fight Scene!
2024-01-15 10:30:08 | INFO | ✅ Thumbnail ready
2024-01-15 10:30:45 | INFO | 🎉 Upload complete! YouTube ID: xXxXxXxXx
```

---

### STEP 6 — Render.com Pe Deploy Karo (Free, 24/7)

1. **render.com** pe free account banao
2. **GitHub pe code daalo:**
   ```bash
   git init
   git add .
   # ⚠️ credentials/ folder mat daalo GitHub pe!
   echo "credentials/" >> .gitignore
   echo ".env" >> .gitignore
   git commit -m "Initial commit"
   # GitHub pe new repo banao aur push karo
   ```
3. Render mein: **"New"** → **"Background Worker"**
4. GitHub repo connect karo
5. **Environment Variables** section mein sab values daalo (.env.example dekho)
6. **Credentials upload** karo:
   - Render mein Shell access jaao
   - `mkdir credentials` karo
   - Files manually paste karo (ya Render Disk use karo)
7. **Deploy** karo → ✅ 24/7 chal raha hai!

---

## ⚙️ Configuration

`.env` mein yeh settings tune kar sakte ho:

| Variable | Default | Matlab |
|---|---|---|
| `UPLOAD_INTERVAL_HOURS` | 3 | Har 3 ghante mein ek video |
| `DRIVE_CHECK_MINUTES` | 15 | Har 15 min Drive check |
| `YT_CATEGORY` | entertainment | YouTube category |
| `YT_PRIVACY` | public | public/private/unlisted |

---

## 💰 Cost

| Service | Cost |
|---|---|
| Render.com Worker | **FREE** (750 hrs/month) |
| Google APIs | **FREE** |
| Cloudinary | **FREE** (25 credits/month) |
| OpenAI GPT-4o mini | **~₹0.40/video** |
| **30 videos/month** | **~₹12 total** |

---

## ❓ Common Issues

**"credentials file nahi mila"**
→ Google Cloud Console se OAuth JSON download karo, `credentials/` mein daalo

**"400 Bad Request Drive"**  
→ Drive folder mein sirf MP4 files honi chahiye, shortcuts nahi

**"YouTube quota exceeded"**  
→ Free tier mein din mein 6 uploads limit hai. `UPLOAD_INTERVAL_HOURS=4` kar do

**"Cloudinary thumbnail nahi bani"**  
→ Cloudinary Dashboard mein "unsigned preset" enable karo
