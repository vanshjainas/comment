import os
import pickle
import json
from instagrapi import Client

# --- CONFIG ---
ACCOUNTS_FILE = "accounts.txt"   # your file with username:password:flag:status
COOKIE_DIR = "cookies"           # folder to store cookies

os.makedirs(COOKIE_DIR, exist_ok=True)

def save_session(cl, username):
    """Save Instagram session to both .pkl and .json"""
    settings = cl.get_settings()

    # Save as Pickle
    session_file_pkl = os.path.join(COOKIE_DIR, f"{username}.pkl")
    with open(session_file_pkl, "wb") as f:
        pickle.dump(settings, f)
    print(f"💾 Saved {session_file_pkl}")

    # Save as JSON
    session_file_json = os.path.join(COOKIE_DIR, f"{username}.json")
    with open(session_file_json, "w") as f:
        json.dump(settings, f, indent=2)
    print(f"💾 Saved {session_file_json}")

def load_session(cl, username):
    """Load session if available"""
    session_file_pkl = os.path.join(COOKIE_DIR, f"{username}.pkl")
    if os.path.exists(session_file_pkl):
        with open(session_file_pkl, "rb") as f:
            settings = pickle.load(f)
        cl.set_settings(settings)
        try:
            cl.get_timeline_feed()  # test session
            print(f"✅ Loaded existing session for {username}")
            return True
        except Exception:
            print(f"⚠️ Session expired for {username}")
    return False

def login_account(username, password):
    cl = Client()
    if not load_session(cl, username):
        try:
            cl.login(username, password)
            print(f"🔑 Logged in: {username}")
            save_session(cl, username)
        except Exception as e:
            print(f"❌ Login failed for {username}: {e}")
            return None
    return cl

def main():
    with open(ACCOUNTS_FILE, "r") as f:
        accounts = f.read().splitlines()

    for acc in accounts:
        try:
            username, password, flag, status = acc.split(":")
        except ValueError:
            print(f"⚠️ Skipping invalid line: {acc}")
            continue

        if status.strip() == "login_failed":
            print(f"⏭️ Skipping {username} (login_failed)")
            continue

        login_account(username, password)

if __name__ == "__main__":
    main()
