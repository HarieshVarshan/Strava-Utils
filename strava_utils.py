"""Interactive menu for personal Strava utilities.

Setup: pip install requests python-dotenv; cp .env.example .env and fill it in
  python strava_utils.py
"""
import json, os, time
from pathlib import Path
import requests
from dotenv import load_dotenv

import rename_activities

load_dotenv()

TOKEN_FILE = Path(".strava_tokens.json")
TOKEN_URL = "https://www.strava.com/oauth/token"


def token_request(**data):
    r = requests.post(TOKEN_URL, data={"client_id": os.environ["STRAVA_CLIENT_ID"],
                                       "client_secret": os.environ["STRAVA_CLIENT_SECRET"], **data})
    r.raise_for_status()
    t = r.json()
    TOKEN_FILE.write_text(json.dumps({k: t[k] for k in ("access_token", "refresh_token", "expires_at")}))
    return t["access_token"]


def authorize():
    print("Open and authorize:\nhttps://www.strava.com/oauth/authorize?client_id=%s&response_type=code"
          "&redirect_uri=http://localhost&approval_prompt=force&scope=read,activity:read_all,activity:write"
          % os.environ["STRAVA_CLIENT_ID"])
    code = input("\nPaste the code=... value from the redirected URL: ").strip()
    try:
        token_request(code=code, grant_type="authorization_code")
    except requests.HTTPError as e:
        return print(f"Authorization failed ({e.response.status_code}). The code is single-use and expires quickly; try again.")
    print("Authorized.")


def session():
    """Return an authorized session, or None if authorization was declined/failed."""
    if not TOKEN_FILE.exists():
        authorize()
        if not TOKEN_FILE.exists():
            return None
    t = json.loads(TOKEN_FILE.read_text())
    if t["expires_at"] > time.time() + 60:
        token = t["access_token"]
    else:
        try:
            token = token_request(grant_type="refresh_token", refresh_token=t["refresh_token"])
        except requests.HTTPError as e:
            print(f"Saved Strava login no longer works ({e.response.status_code}); access may have been revoked.")
            if input("Re-authorize now? [y/N] ").lower() != "y":
                return None
            TOKEN_FILE.unlink()
            return session()
    s = requests.Session()
    s.headers["Authorization"] = "Bearer " + token
    return s


# label -> action(session)
MENU = {
    "Bulk rename activities": rename_activities.run,
}


def main():
    options = list(MENU.items())
    while True:
        print("\nStrava Utils")
        for i, (label, _) in enumerate(options, 1):
            print(f"  {i}. {label}")
        print("  q. Quit")
        choice = input("> ").strip().lower()
        if choice == "q":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            if sess := session():
                options[int(choice) - 1][1](sess)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
