# Strava-Utils

Personal command-line utilities for the Strava API.

Run `strava_utils.py` for an interactive menu; each feature is its own module.

## Setup

1. Create an app at https://www.strava.com/settings/api
   - Authorization Callback Domain: `localhost`
   - Don't use "Strava" in the app name (against their guidelines)
2. Install dependencies:
   ```
   pip install requests python-dotenv
   ```
3. Copy `.env.example` to `.env` and fill in the Client ID and Client Secret from your app page:
   ```
   cp .env.example .env
   ```
4. Run:
   ```
   python strava_utils.py
   ```
   On first use it prints an authorization URL. Open it and click **Authorize**. The browser then lands on a `localhost` page that fails to load; that's expected. Copy the value after `code=` from the address bar and paste it into the terminal. Tokens are saved to `.strava_tokens.json` and refreshed automatically.

## Features

### Bulk rename activities

Reads `renames.csv`:

```
activity_number,new_name
138,E138 Plot Twist I Showed Up
139,E139 Chaos But Make It Cardio
```

- `activity_number` is the position in your history, oldest first (1 = your first activity ever).
- `new_name` is the name to set.

The script fetches all your activities, shows `#N date 'old name' -> 'new name'` for each row, and asks for confirmation before renaming. Activities that already have the target name are skipped, so it's safe to re-run.

If you have an extra or missing activity on Strava, every number after it shifts by one. Check the dates and old names in the plan before confirming.

Pass `-y` to skip the final "Rename N activities?" confirmation:

```
python strava_utils.py -y
```

## Adding a feature

Create a module with `run(session, assume_yes=False)` and add one line to `MENU` in `strava_utils.py`. `session` is a `requests.Session` with the auth header already set.

## Files

| File | Purpose |
| --- | --- |
| `strava_utils.py` | Menu, OAuth, token refresh |
| `rename_activities.py` | Bulk rename feature |
| `renames.csv` | Input for bulk rename |
| `.env` | Your Client ID/Secret (gitignored) |
| `.strava_tokens.json` | Saved tokens (gitignored) |
