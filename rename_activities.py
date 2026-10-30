"""Bulk-rename activities listed in renames.csv (columns: activity_number,new_name).

activity_number is the position in your history, oldest first: 1 = first activity you ever recorded.
"""
import csv
from pathlib import Path

API = "https://www.strava.com/api/v3"
RENAMES_FILE = Path("renames.csv")


def load_renames():
    with RENAMES_FILE.open(newline="") as f:
        rows = [(i, r["activity_number"].strip(), r["new_name"].strip())
                for i, r in enumerate(csv.DictReader(f), start=2)]
    bad = [i for i, num, name in rows if not num.isdigit() or int(num) < 1 or not name]
    if bad:
        raise ValueError(f"Missing/invalid activity_number or new_name on line(s) {bad} of {RENAMES_FILE}")
    return [(int(num), name) for _, num, name in rows]


def fetch_all(session):
    acts, page = [], 1
    while batch := session.get(f"{API}/athlete/activities", params={"per_page": 200, "page": page}).json():
        acts += batch
        page += 1
    return sorted(acts, key=lambda a: a["start_date"])


def run(session, assume_yes=False):
    print(f"This reads {RENAMES_FILE} (activity_number,new_name); activity_number counts from your first activity.")
    if input(f"Have you updated {RENAMES_FILE} with the activities you want renamed? [y/N] ").lower() != "y":
        return print("Update the file and try again.")
    try:
        renames = load_renames()
    except (OSError, ValueError, KeyError) as e:
        return print(f"Error: {e}")

    acts = fetch_all(session)
    print(f"You have {len(acts)} activities on Strava.")
    too_big = [n for n, _ in renames if n > len(acts)]
    if too_big:
        return print(f"activity_number {too_big} exceeds your activity count. Nothing renamed.")

    plan = []
    for n, new in renames:
        a = acts[n - 1]
        if a["name"] != new:
            plan.append((a["id"], new))
            print(f"#{n} {a['start_date_local'][:16]}  {a['name']!r} -> {new!r}")
    if not plan:
        return print("Nothing to rename.")
    if not assume_yes and input(f"\nRename {len(plan)} activities? [y/N] ").lower() != "y":
        return print("Aborted.")
    for aid, new in plan:
        session.put(f"{API}/activities/{aid}", data={"name": new}).raise_for_status()
        print("renamed", new)
