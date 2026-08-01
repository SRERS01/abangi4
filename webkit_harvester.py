from playwright.sync_api import sync_playwright
import json
import sys

def webkit_session_harvest(start_url, username, password):
    start_url = start_url.strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = f"https://{start_url}"

    print(f"\n🍏 Initializing Authenticated WebKit (Safari) Harvester...")
    
    full_token_value = None
    user_agent_string = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15"

    with sync_playwright() as p:
        try:
            # 1. Launch WebKit engine instance natively
            browser = p.webkit.launch(headless=False)
            context = browser.new_context(
                viewport={"width": 1280, "height": 850},
                user_agent=user_agent_string,
                bypass_csp=True
            )
            page = context.new_page()

            # 2. Inject structural polyfills to ensure Javascript stays active on Linux
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = undefined;
                if (!window.Intl || !window.Intl.Locale) {
                    window.Intl = window.Intl || {};
                    window.Intl.Locale = class {
                        constructor(tag) { this.baseName = tag; this.language = tag.split('-'); }
                    };
                }
            """)

            # STEP A: Direct page tree layout straight to login
            login_url = f"{start_url.rstrip('/')}/login"
            print(f"🎯 Directing WebKit container to: {login_url}")
            page.goto(login_url, wait_until="commit", timeout=25000)
            page.wait_for_timeout(5000)

            # STEP B: Fill credentials into the dynamic inputs layout
            print("✏️  Injecting target parameters into login inputs...")
            page.locator("input[type='tel'], input[placeholder*='Phone'], input[type='text']").first.fill(username)
            page.locator("input[type='password']").first.fill(password)
            page.wait_for_timeout(1000)

            # STEP C: Fire automated authentication submissions
            print("🚀 Submitting authentication state request...")
            submit_selectors = ["button[type='submit']", "button:has-text('LOGIN')", ".btn-login", "button"]
            for selector in submit_selectors:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click(force=True)
                    break

            print("⏳ Allowing session handshake 7 seconds to settle framework variables...")
            page.wait_for_timeout(7000)

            # STEP D: Trigger the hidden sidebar menu drawer to expose authenticated routes
            print("👤 Opening target dashboard sidebar/balance overlay panels...")
            menu_selectors = ["text='Menu'", "text='Account'", "[class*='balance']", "[class*='profile']"]
            for selector in menu_selectors:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click(force=True)
                    page.wait_for_timeout(3000)
                    break

            # STEP E: Rip out untruncated WebKit cookies data
            live_cookies = context.cookies()
            for cookie in live_cookies:
                if cookie.get('name') == 'x-pawa-token':
                    full_token_value = cookie.get('value')
                    break

            browser.close()
        except Exception as e:
            print(f"❌ WebKit Automation Error: {e}")
            if 'browser' in locals():
                browser.close()
            return

    print("\n" + "="*90)
    print("🔬 SAFARI/WEBKIT UNTRUNCATED DISCOVERY SUMMARY")
    print("="*90)
    if full_token_value:
        print("🎉 Target authenticated session harvested with absolute structural integrity!")
        print(f"🔑 Key Name:  x-pawa-token")
        print(f"🔒 Full Value: {full_token_value}")
        
        # Save credentials node out to file for pipeline portability
        session_export = {"x-pawa-token": full_token_value, "engine": "webkit_safari"}
        with open("webkit_session.json", "w") as f:
            json.dump(session_export, f, indent=4)
        print("💾 Session token written natively to: 'webkit_session.json'")
    else:
        print("❌ Critical Error: Could not capture authenticated session cookie. Check user identity metrics.")
    print("="*90 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("\n🚀 WebKit Live Account Session Harvester Ready.")
        print("Usage: python3 webkit_harvester.py <canonical_domain_url> <username> <password>")
        print("Example: python3 webkit_harvester.py https://betpawa.cm 652223518 9012\n")
    else:
        webkit_session_harvest(sys.argv[1], sys.argv[2], sys.argv[3])
