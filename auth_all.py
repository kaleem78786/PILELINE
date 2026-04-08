import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

os.environ['DISPLAY'] = ':1'

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

CLIENT_SECRETS = [
    ("client_secret.json", "token1.json"),
    ("client_secret2.json", "token2.json"),
    ("client_secret3.json", "token3.json"),
    ("client_secret4.json", "token4.json"),
]

def authenticate(client_secret_file, token_file):
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        if creds and creds.valid:
            print(f"  Already authenticated! Token: {token_file}")
            return

    print(f"  Browser khulay ga — Google account se login karo...")
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")

    with open(token_file, "w") as f:
        f.write(creds.to_json())
    print(f"  Token saved: {token_file}")

def main():
    for i, (secret, token) in enumerate(CLIENT_SECRETS, 1):
        print(f"\n{'='*50}")
        print(f"[{i}/4] Authenticating: {secret}")
        print(f"{'='*50}")
        authenticate(secret, token)

    print(f"\n{'='*50}")
    print("Sab done! Tokens saved:")
    for _, token in CLIENT_SECRETS:
        status = "EXISTS" if os.path.exists(token) else "MISSING"
        print(f"  {token} — {status}")

if __name__ == "__main__":
    main()
