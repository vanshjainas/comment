import os
import pickle
from instagrapi import Client

# --- Read accounts from accounts.txt ---
def load_accounts(file_path):
    accounts = []
    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(":")
            if len(parts) >= 2:
                username = parts[0].strip()
                password = parts[1].strip()
                accounts.append({"username": username, "password": password})
    return accounts

# --- Load accounts ---
ACCOUNTS_FILE = "accounts.txt"
accounts = load_accounts(ACCOUNTS_FILE)

# --- Cookies folder ---
COOKIE_DIR = "cookies"
os.makedirs(COOKIE_DIR, exist_ok=True)

# --- Reel URL to share ---
POST_URL = "https://www.instagram.com/reel/DMDDVQ3zEsP/?igsh=MWlkZWxjM3JseW90Yg=="

# --- Receiver user IDs (creep_sen, man_kind_0001, bca_batch) ---
SHARE_USER_IDS = [62004084526, 58462814975, 61327236292]

# --- Get media ID using the first account ---
first_account = accounts[0]
temp_client = Client()

try:
    temp_client.login(first_account["username"], first_account["password"])
    media_pk = temp_client.media_pk_from_url(POST_URL)
    print(f"📌 Found media PK: {media_pk}")
except Exception as e:
    print("❌ Failed to extract media PK:", e)
    exit()

# --- Main loop for sharing ---
for idx, account in enumerate(accounts):
    username = account["username"]
    password = account["password"]
    cookie_path = os.path.join(COOKIE_DIR, f"{username}.pkl")

    print(f"\n🔄 [{idx + 1}/{len(accounts)}] Processing: {username}")
    cl = Client()

    # --- Load session from cookie or login ---
    if os.path.exists(cookie_path):
        try:
            with open(cookie_path, "rb") as f:
                cl = pickle.load(f)
            cl.get_timeline_feed()
            print("✅ Loaded session from cookie.")
        except Exception:
            print("⚠️ Cookie invalid, logging in again...")
            try:
                cl.login(username, password)
                with open(cookie_path, "wb") as f:
                    pickle.dump(cl, f)
                print("✅ Logged in & session saved.")
            except Exception as e:
                print(f"❌ Login failed for {username}: {e}")
                continue
    else:
        try:
            cl.login(username, password)
            with open(cookie_path, "wb") as f:
                pickle.dump(cl, f)
            print("✅ Logged in & session saved.")
        except Exception as e:
            print(f"❌ Login failed for {username}: {e}")
            continue

    # --- Share media via DM ---
    try:
        for uid in SHARE_USER_IDS:
            cl.direct_send_items(
                user_ids=[[uid]],  # Each user in its own thread
                items=[{
                    "type": "media",
                    "media_id": media_pk
                }],
                text="check this out 🔥"
            )
        print("📤 Shared reel via DM to: creep_sen, man_kind_0001, bca_batch")
    except Exception as e:
        print(f"❌ Error during sharing: {e}")
        continue