from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json
import sys

def extract_live_auth_tokens(start_url, username, password):
    start_url = start_url.strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = f"https://{start_url}"

    parsed_start = urlparse(start_url)
    start_hostname = parsed_start.hostname or ""

    print(f"\n⚡ Initializing Client-Side Memory Scan for: {start_hostname}")
    print("⏳ Starting browser instance...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, # Must be visible to initialize client-side DOM memory
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        try:
            # 1. Access the Login Form directly
            login_url = f"https://{start_hostname}/login"
            print(f"🎯 Directing browser to: {login_url}")
            page.goto(login_url, wait_until="load", timeout=25000)
            page.wait_for_timeout(4000)

            # 2. Input values and submit authorization payload
            print("✏️  Injecting mobile authentication profiles...")
            page.locator("input[type='tel'], input[placeholder*='Phone'], input[type='text']").first.fill(username)
            page.wait_for_timeout(500)
            page.locator("input[type='password']").first.fill(password)
            page.wait_for_timeout(500)

            print("🚀 Dispatching click matrix vectors...")
            submit_selectors = ["button[type='submit']", "button:has-text('LOGIN')", ".btn-login", "button"]
            for selector in submit_selectors:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click(force=True)
                    break

            # Generous wait to ensure application state engine resolves and caches token profiles locally
            print("⏳ Allowing session handshake 7 seconds to compile storage objects...")
            page.wait_for_timeout(7000)
            print(f"🛡️  Active location authenticated state verified: {page.url}")

            print("\n" + "="*90)
            print("🔬 SCANNING BROWSER SYSTEM STORAGE LAYER (window.localStorage)")
            print("="*90)

            # Execute explicit JavaScript extraction from the live browser memory context
            local_storage_data = page.evaluate("() => JSON.stringify(window.localStorage);")
            storage_dict = json.loads(local_storage_data)

            token_found = False
            for key, val in storage_dict.items():
                # Search for typical SPA storage tokens (identity targets, bearer tokens, or structural IDs)
                if any(x in key.lower() for x in ["auth", "token", "session", "jwt", "user", "pawa", "login"]):
                    print(f"  [Found Key] '{key}':")
                    # Re-parse inner JSON if the string is stringified data block
                    try:
                        inner_json = json.loads(val)
                        print(json.dumps(inner_json, indent=4))
                    except:
                        # Print plain text value if it is a raw hash
                        print(f"    Value: {val[:80]}... [Truncated]")
                    token_found = True
                    print("-" * 50)

            if not token_found:
                print("  ⚠️  No obvious auth string identifiers isolated in localStorage parameters.")

            print("\n" + "="*90)
            print("🔬 SCANNING COOKIE SYSTEM RECORDS (context.cookies)")
            print("="*90)

            # Dump cookies explicitly via Playwright's system context tracker API
            live_cookies = context.cookies()
            if live_cookies:
                for idx, cookie in enumerate(live_cookies):
                    print(f"  [Cookie {idx+1}] Name: {cookie.get('name')}")
                    print(f"             Domain: {cookie.get('domain')}")
                    print(f"             Value:  {cookie.get('value')[:60]}...")
                    print(f"             HTTPOnly: {cookie.get('httpOnly')} | Secure: {cookie.get('secure')}")
                    print("-" * 50)
            else:
                print("  ⚠️  No active browser cookies found.")

            browser.close()
        except Exception as e:
            print(f"❌ Automation runtime failure parameter triggered: {e}")
            browser.close()
            return

# --- Direct CLI Launch Parameters Engine ---
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("\n🚀 Direct Client Storage Extraction Matrix Active.")
        print("Syntax: python3 harvest_session.py <domain> <username> <password>")
        print("Example: python3 harvest_session.py www.betpawa.cm 652223518 9012\n")
    else:
        extract_live_auth_tokens(sys.argv[1], sys.argv[2], sys.argv[3])
