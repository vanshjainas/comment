import os
import json
from concurrent.futures import ThreadPoolExecutor
from instagrapi import Client

# ========== CONFIG ==========
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.txt")
COMMENTS_FILE = os.path.join(BASE_DIR, "comments.txt")
COOKIE_DIR = os.path.join(BASE_DIR, "cookies")
POST_URL = "https://www.instagram.com/reel/DQrIsphkWsn/?igsh=MXJ6NGwxZWt4eWoyZg=="
TARGET_USERS = ["heartbreak.run", "insta360Active ", "insta360"]

os.makedirs(COOKIE_DIR, exist_ok=True)


# ========== HELPERS ==========
def cookie_file(username: str) -> str:
    return os.path.join(COOKIE_DIR, f"{username}.json")


def load_accounts():
    """Load accounts from accounts.txt (username:password:proxy:status)."""
    accounts = []
    if not os.path.exists(ACCOUNTS_FILE):
        print("❌ accounts.txt not found")
        return accounts

    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) < 2:
                print(f"⚠️ Skipping invalid line: {line}")
                continue
            username, password = parts[0].strip(), parts[1].strip()
            accounts.append((username, password))
    return accounts


def load_comments():
    """Load comments from comments.txt (one per line)."""
    comments = []
    if os.path.exists(COMMENTS_FILE):
        with open(COMMENTS_FILE, "r", encoding="utf-8") as f:
            comments = [c.strip() for c in f if c.strip()]
    return comments


def login_with_retry(username: str, password: str) -> Client | None:
    """
    Try cookie-based session first (load_settings + login),
    else do a fresh login, then persist cookies (dump_settings).
    """
    cl = Client()

    # Optional: set a stable mobile-like device/UA (helps consistency)
    # cl.set_user_agent("Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; OnePlus; 6T; qcom; en_US; 314665256)")

    cpath = cookie_file(username)
    if os.path.exists(cpath):
        try:
            cl.load_settings(cpath)
            # This login call finalizes auth refresh using the loaded settings
            cl.login(username, password)
            print(f"✅ Logged in with cookies: {username}")
            return cl
        except Exception as e:
            print(f"⚠️ Cookie login failed for {username}: {e}")

    # Fresh login fallback
    try:
        cl.login(username, password)
        cl.dump_settings(cpath)
        print(f"🔑 Fresh login success, cookies saved: {username}")
        return cl
    except Exception as e:
        print(f"❌ Fresh login failed for {username}: {e}")
        return None


def do_actions(username: str, password: str, media_pk: int, comment_text: str):
    """
    Perform Like + Save + Comment via private_request endpoints,
    which avoids Pydantic model validation issues.
    """
    print(f"\n🔄 Processing: {username}")
    cl = login_with_retry(username, password)
    if not cl:
        return

    # Like
    # try:
    #     cl.private_request(
    #         f"media/{media_pk}/like/",
    #         {"media_id": str(media_pk), "module_name": "feed_timeline"},
    #     )
    #     print(f"❤️ by {username}")
    # except Exception as e:
    #     print(f"⚠️ Like failed for {username}: {e}")

    # # Save
    # try:
    #     cl.private_request(
    #         f"media/{media_pk}/save/",
    #         {"media_id": str(media_pk)}
    #     )
    #     print(f"💾 by {username}")
    # except Exception as e:
    #     print(f"⚠️ Save failed for {username}: {e}")

    #     # Follow target usernames
    # for target_username in TARGET_USERS:
    #     try:
    #         user_id = cl.user_id_from_username(target_username)
    #         cl.private_request(
    #             f"friendships/create/{user_id}/",
    #             {"user_id": str(user_id)}
    #         )
    #         print(f"👤 {username} followed {target_username}")
    #     except Exception as e:
    #         print(f"⚠️ Follow failed for {username} → {target_username}: {e}")


    # Comment
    if comment_text:
        try:
            for i in range(5):  # can adjust to post multiple comments if desired
                 cl.private_request(
                    f"media/{media_pk}/comment/",
                    {
                    "comment_text": comment_text,
                    "idempotence_token": cl.generate_uuid()
                 },
                 )
                 print(f"💬 by {username}")
        except Exception as e:
            print(f"⚠️ Comment failed for {username}: {e}")
    # Optional: cl.logout()  # generally not necessary


# ========== MAIN ==========
def main():
    accounts = load_accounts()
    if not accounts:
        print("❌ No accounts to process.")
        return

    comments = load_comments()
    print(f"📌 Loaded {len(accounts)} accounts, {len(comments)} comments")

    # Fetch media_pk once using first working account
    media_pk = None
    for u, p in accounts:
        cl = login_with_retry(u, p)
        if not cl:
            continue
        try:
            media_pk = cl.media_pk_from_url(POST_URL)
            print(f"✅ media_pk fetched: {media_pk}")
            break
        except Exception as e:
            print(f"⚠️ Failed to fetch media_pk with {u}: {e}")

    if not media_pk:
        print("❌ Could not fetch media_pk with any account.")
        return

    # Assign comments (cycle if fewer than accounts)
    assigned = []
    for i in range(len(accounts)):
        comment = comments[i % len(comments)] if comments else ""
        assigned.append(comment)

    # Run in parallel (tune workers to manage rate limits)
    with ThreadPoolExecutor(max_workers=5) as executor:
        for (username, password), comment_text in zip(accounts, assigned):
            executor.submit(do_actions, username, password, media_pk, comment_text)


if __name__ == "__main__":
    main()
