"""
Fixed Setup Script - Console based OAuth
Browser mein code aayega -> terminal mein paste karo -> Done!
"""

import os
import sys

print("=" * 60)
print("🔐 YouTube Auto-Post Bot — One-Time Setup (Fixed)")
print("=" * 60)

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file load ho gayi")
except:
    print("⚠️  python-dotenv nahi hai, manually env set karo")

# Check credentials files
print("\n📁 Credentials files check ho rahi hain...")
missing = []
if not os.path.exists('credentials/drive_credentials.json'):
    missing.append('credentials/drive_credentials.json')
if not os.path.exists('credentials/youtube_credentials.json'):
    missing.append('credentials/youtube_credentials.json')

if missing:
    print("❌ Yeh files nahi mili:")
    for f in missing:
        print(f"   → {f}")
    sys.exit(1)

print("✅ Credentials files mil gayi!\n")

# ─────────────────────────────────────────────
# DRIVE TOKEN
# ─────────────────────────────────────────────
print("=" * 40)
print("STEP 1: Google Drive Login")
print("=" * 40)

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

drive_creds = None
if os.path.exists('credentials/drive_token.json'):
    drive_creds = Credentials.from_authorized_user_file(
        'credentials/drive_token.json', DRIVE_SCOPES
    )

if not drive_creds or not drive_creds.valid:
    if drive_creds and drive_creds.expired and drive_creds.refresh_token:
        drive_creds.refresh(Request())
        print("✅ Drive token refresh ho gaya!")
    else:
        print("\n🌐 Browser mein Google login hoga...")
        print("📋 Login karo → phir browser band karo → yahan wapas aao\n")

        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials/drive_credentials.json',
            DRIVE_SCOPES
        )

        # run_local_server with specific port
        try:
            drive_creds = flow.run_local_server(
                port=8080,
                prompt='consent',
                authorization_prompt_message='Browser mein login karo: {url}',
                success_message='✅ Login ho gaya! Yeh tab band karo.',
                open_browser=True
            )
        except Exception as e:
            print(f"Browser method failed: {e}")
            print("\n🔄 Manual method try kar raha hoon...")
            # Manual OOB flow
            flow2 = InstalledAppFlow.from_client_secrets_file(
                'credentials/drive_credentials.json',
                DRIVE_SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            auth_url, _ = flow2.authorization_url(prompt='consent')
            print(f"\n👉 Yeh URL browser mein open karo:\n{auth_url}\n")
            code = input("Browser mein jo code mila woh yahan paste karo: ").strip()
            flow2.fetch_token(code=code)
            drive_creds = flow2.credentials

    # Token save karo
    os.makedirs('credentials', exist_ok=True)
    with open('credentials/drive_token.json', 'w') as f:
        f.write(drive_creds.to_json())
    print("✅ Drive token save ho gaya!")

# Drive test
try:
    service = build('drive', 'v3', credentials=drive_creds)
    folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
    if folder_id:
        results = service.files().list(
            q=f"'{folder_id}' in parents and mimeType='video/mp4' and trashed=false",
            pageSize=5,
            fields="files(id, name)"
        ).execute()
        videos = results.get('files', [])
        print(f"✅ Drive connected! Folder mein {len(videos)} MP4 videos mili")
        if videos:
            print(f"   Pehli video: {videos[0]['name']}")
    else:
        print("⚠️  GOOGLE_DRIVE_FOLDER_ID .env mein set nahi hai")
except Exception as e:
    print(f"⚠️  Drive test: {e}")

# ─────────────────────────────────────────────
# YOUTUBE TOKEN
# ─────────────────────────────────────────────
print("\n" + "=" * 40)
print("STEP 2: YouTube Login")
print("=" * 40)

YT_SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

yt_creds = None
if os.path.exists('credentials/youtube_token.json'):
    yt_creds = Credentials.from_authorized_user_file(
        'credentials/youtube_token.json', YT_SCOPES
    )

if not yt_creds or not yt_creds.valid:
    if yt_creds and yt_creds.expired and yt_creds.refresh_token:
        yt_creds.refresh(Request())
        print("✅ YouTube token refresh ho gaya!")
    else:
        print("\n🌐 Browser mein YouTube login hoga...")

        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials/youtube_credentials.json',
            YT_SCOPES
        )

        try:
            yt_creds = flow.run_local_server(
                port=8081,
                prompt='consent',
                authorization_prompt_message='Browser mein login karo: {url}',
                success_message='✅ Login ho gaya! Yeh tab band karo.',
                open_browser=True
            )
        except Exception as e:
            print(f"Browser method failed: {e}")
            print("\n🔄 Manual method try kar raha hoon...")
            flow2 = InstalledAppFlow.from_client_secrets_file(
                'credentials/youtube_credentials.json',
                YT_SCOPES,
                redirect_uri='urn:ietf:wg:oauth:2.0:oob'
            )
            auth_url, _ = flow2.authorization_url(prompt='consent')
            print(f"\n👉 Yeh URL browser mein open karo:\n{auth_url}\n")
            code = input("Browser mein jo code mila woh yahan paste karo: ").strip()
            flow2.fetch_token(code=code)
            yt_creds = flow2.credentials

    os.makedirs('credentials', exist_ok=True)
    with open('credentials/youtube_token.json', 'w') as f:
        f.write(yt_creds.to_json())
    print("✅ YouTube token save ho gaya!")

# YouTube test
try:
    yt_service = build('youtube', 'v3', credentials=yt_creds)
    response = yt_service.channels().list(part='snippet', mine=True).execute()
    if response.get('items'):
        channel = response['items'][0]['snippet']
        print(f"✅ YouTube connected! Channel: {channel['title']}")
    else:
        print("⚠️  YouTube connected but channel nahi mila")
except Exception as e:
    print(f"⚠️  YouTube test: {e}")

# ─────────────────────────────────────────────
# CLOUDINARY TEST
# ─────────────────────────────────────────────
print("\n" + "=" * 40)
print("STEP 3: Cloudinary Test")
print("=" * 40)

try:
    import cloudinary
    import cloudinary.api
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )
    result = cloudinary.api.ping()
    print(f"✅ Cloudinary connected! Status: {result.get('status', 'OK')}")
except Exception as e:
    print(f"❌ Cloudinary error: {e}")
    print("   .env mein CLOUDINARY_* values check karo")

# ─────────────────────────────────────────────
# OPENROUTER TEST
# ─────────────────────────────────────────────
print("\n" + "=" * 40)
print("STEP 4: OpenRouter Test")
print("=" * 40)

try:
    import requests
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY .env mein set nahi hai!")
    else:
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3.1-8b-instruct:free",
                "messages": [{"role": "user", "content": "Say OK only"}],
                "max_tokens": 5
            },
            timeout=20
        )
        if resp.status_code == 200:
            print("✅ OpenRouter connected! Free model working hai")
        else:
            print(f"⚠️  OpenRouter status: {resp.status_code} — {resp.text[:100]}")
except Exception as e:
    print(f"❌ OpenRouter error: {e}")

# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("🎉 Setup Complete!")
print("=" * 60)
print("Ab yeh command chala ke bot start karo:")
print("\n   python main.py\n")