import os
import json
import pickle
import time
import argparse
import random
import string

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def load_instagrapi_settings(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Cookie/settings file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb" if ext == ".pkl" else "r") as f:
        if ext == ".pkl":
            data = pickle.load(f)
        else:
            data = json.load(f)
    return data


def random_csrf(n=32):
    return "".join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


def settings_to_browser_cookies(settings):
    auth = settings.get("authorization_data", {}) or {}
    cookies_blob = settings.get("cookies", {}) or {}

    sessionid = auth.get("sessionid") or cookies_blob.get("sessionid")
    ds_user_id = auth.get("ds_user_id") or cookies_blob.get("ds_user_id")
    mid = settings.get("mid") or cookies_blob.get("mid")

    if not sessionid or not ds_user_id:
        raise ValueError("Missing required fields: sessionid and/or ds_user_id.")

    csrftoken = cookies_blob.get("csrftoken") or random_csrf()
    rur = cookies_blob.get("rur") or ""

    base = {"domain": ".instagram.com", "path": "/", "secure": True, "httpOnly": True}

    out = [
        dict(base, name="sessionid", value=sessionid),
        dict(base, name="ds_user_id", value=str(ds_user_id)),
        dict(base, name="csrftoken", value=csrftoken, httpOnly=False),
    ]

    if mid:
        out.append(dict(base, name="mid", value=mid))
    if rur is not None:
        out.append(dict(base, name="rur", value=rur))

    out.append(dict(base, name="ig_nrcb", value="1", httpOnly=False))
    return out


def login_in_chrome(settings_path, headless=False):
    settings = load_instagrapi_settings(settings_path)
    browser_cookies = settings_to_browser_cookies(settings)

    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")

    # ✅ Use webdriver_manager so you never need to download chromedriver manually
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get("https://www.instagram.com/")
    time.sleep(2)

    for ck in browser_cookies:
        try:
            driver.add_cookie(ck)
        except:
            pass

    driver.refresh()
    driver.get("https://www.instagram.com/accounts/edit/")

    try:
        WebDriverWait(driver, 12).until(
            EC.any_of(
                EC.url_contains("/accounts/edit/"),
                EC.presence_of_element_located((By.CSS_SELECTOR, "form input[name='username']")),
            )
        )
    except:
        pass

    cur = driver.current_url
    if "accounts/login" in cur:
        print("❌ Not logged in (cookie expired or checkpoint required).")
    else:
        print("✅ Logged in via cookie, Chrome window is open.")

    # 👇 Keep script alive until user closes Chrome
    print("🔄 Keeping Chrome open. Close the window to exit.")
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("👋 Exiting...")
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cookie", required=True, help="Path to cookie file (.json or .pkl)")
    parser.add_argument("--headless", action="store_true", help="Run Chrome headless")
    args = parser.parse_args()

    login_in_chrome(args.cookie, headless=args.headless)
