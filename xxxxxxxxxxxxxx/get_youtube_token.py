from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]

print("Browser mein YouTube login hoga...")
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials/youtube_credentials.json', SCOPES
)
creds = flow.run_local_server(port=8081, prompt='consent')

with open('credentials/youtube_token.json', 'w') as f:
    f.write(creds.to_json())

print("YouTube token saved!")