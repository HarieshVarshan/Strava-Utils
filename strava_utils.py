"""Interactive menu for personal Strava utilities.

Setup: pip install requests python-dotenv; cp .env.example .env and fill it in
  python strava_utils.py        # confirms before changing anything
  python strava_utils.py -y     # skip the "Rename N activities?" confirmation
"""
import argparse, json, os, time
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
    token_request(code=code, grant_type="authorization_code")
    print("Authorized.")


def session():
    if not TOKEN_FILE.exists():
        authorize()
    t = json.loads(TOKEN_FILE.read_text())
    token = t["access_token"] if t["expires_at"] > time.time() + 60 else \
        token_request(grant_type="refresh_token", refresh_token=t["refresh_token"])
    s = requests.Session()
    s.headers["Authorization"] = "Bearer " + token
    return s


# label -> action(session, assume_yes)
MENU = {
    "Bulk rename activities": rename_activities.run,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-y", "--yes", action="store_true", help="skip the final rename confirmation (file check is always asked)")
    assume_yes = parser.parse_args().yes
    options = list(MENU.items())
    while True:
        print("\nStrava Utils")
        for i, (label, _) in enumerate(options, 1):
            print(f"  {i}. {label}")
        print("  a. Re-authorize with Strava")
        print("  q. Quit")
        choice = input("> ").strip().lower()
        if choice == "q":
            return
        if choice == "a":
            authorize()
        elif choice.isdigit() and 1 <= int(choice) <= len(options):
            options[int(choice) - 1][1](session(), assume_yes)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
