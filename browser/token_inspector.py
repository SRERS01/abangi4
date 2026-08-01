from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json
import sys

def harvest_and_test_live_navigation(start_url, username, password):
    start_url = start_url.strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = f"https://{start_url}"

    parsed_start = urlparse(start_url)
    start_hostname = parsed_start.hostname or ""

    print(f"\n⚡ Step 1: Initializing Live Browser context to authenticate account...")
    
    full_token_value = None
    user_agent_string = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    
    # Local dictionary to capture the true, live 200 OK server responses
    live_captured_responses = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
        context = browser.new_context(viewport={"width": 1280, "height": 850}, user_agent=user_agent_string)
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        # Live Response Sniffer Loop - captures the true background network traffic during page loads
        def response_sniffer(response):
            try:
                url = response.request.url
                if "/api/payment/" in url:
                    # Parse the path descriptor name cleanly
                    path_key = urlsplit_path = urlparse(url).path
                    try:
                        payload = response.json()
                        live_captured_responses[path_key] = {
                            "status": response.status,
                            "url": url,
                            "data": payload
                        }
                    except:
                        pass
            except:
                pass

        page.on("response", response_sniffer)

        try:
            # Login authentication lifecycle pass
            login_url = f"https://{start_hostname}/login"
            page.goto(login_url, wait_until="load", timeout=25000)
            page.wait_for_timeout(4000)

            print("✏️  Injecting credentials into active DOM elements...")
            page.locator("input[type='tel'], input[placeholder*='Phone'], input[type='text']").first.fill(username)
            page.locator("input[type='password']").first.fill(password)
            page.wait_for_timeout(1000)

            print("🚀 Dispatching login button submission events...")
            submit_selectors = ["button[type='submit']", "button:has-text('LOGIN')", ".btn-login", "button"]
            for selector in submit_selectors:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click(force=True)
                    break

            print("⏳ Allowing session handshake 7 seconds to compile storage objects...")
            page.wait_for_timeout(7000)

            # Retrieve cookie details
            live_cookies = context.cookies()
            for cookie in live_cookies:
                if cookie.get('name') == 'x-pawa-token':
                    full_token_value = cookie.get('value')
                    break

            print("\n" + "="*90)
            print("🔬 UNTRUNCATED SESSION TOKEN DISCOVERY STATUS")
            print("="*90)
            if full_token_value:
                print("🎉 Token harvested with absolute integrity!")
                print(f"🔑 Full Token: {full_token_value}")
            else:
                print("❌ Critical Error: Could not locate an active 'x-pawa-token'.")
            print("="*90)

            # --- STEP 2: LIVE PAGE NAVIGATION SWEEP ---
            print("\n⚡ Step 2: Querying backend payment gateways natively using viewport navigation...")
            
            # Target human routing paths on the site to trigger backend API pipelines naturally
            ui_navigation_targets = [
                f"https://{start_hostname}/withdraw",
                f"https://{start_hostname}/deposit"
            ]

            for target_path in ui_navigation_targets:
                print(f"📡 Navigating viewport container directly to: {target_path}")
                # Use standard page.goto inside the valid browser timeline context
                page.goto(target_path, wait_until="load", timeout=20000)
                page.wait_for_timeout(5000)  # Allow the application engine time to fetch limits and options

            browser.close()
        except Exception as e:
            print(f"❌ Playwright Automation Error: {e}")
            browser.close()
            return

    print("\n" + "="*90)
    print("🎯 DISSECTED LIVE PAYMENT METRICS REPORT SUMMARY")
    print("="*90)

    if live_captured_responses:
        # Print out the clean, authorized 200 OK responses captured during navigation
        for path, info in live_captured_responses.items():
            print(f"\n🟢 Captured Path: {path} (HTTP {info['status']})")
            print(json.dumps(info['data'], indent=4, ensure_ascii=False))
            
        with open("token_endpoint_results.json", "w", encoding="utf-8") as output_file:
            json.dump(live_captured_responses, output_file, indent=4, ensure_ascii=False)
        print("\n💾 Complete live payload records dumped cleanly to: 'token_endpoint_results.json'")
    else:
        print("⚠️  No payment endpoint traffic captured during navigation sweeps. Verify account constraints.")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 token_inspector.py <domain> <username> <password>")
    else:
        harvest_and_test_live_navigation(sys.argv[1], sys.argv[2], sys.argv[3])
