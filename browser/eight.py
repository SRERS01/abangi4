from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, urljoin
import json
import os

def authenticated_site_spider(start_url, username, password, max_pages=10):
    start_url = start_url.strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = f"https://{start_url}"

    parsed_start = urlparse(start_url)
    start_hostname = parsed_start.hostname or ""
    start_parts = start_hostname.split('.')
    target_root_domain = ".".join(start_parts[-2:]) if len(start_parts) >= 2 else start_hostname

    print(f"\n🕸️  Initializing Authenticated Spider for: {target_root_domain}")
    print(f"🔐 Configured Target Account Identity: {username}")

    queue = []
    visited_pages = set()
    captured_traffic = []
    ui_routes = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, # Watch the login process execute live
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        # Capture response data payloads
        def handle_response(response):
            try:
                request = response.request
                url = request.url
                if any(x in url for x in ["google", "facebook", "doubleclick", "sentry"]):
                    return

                parsed_url = urlparse(url)
                host = parsed_url.hostname or ""
                parts = host.split('.')
                current_domain = ".".join(parts[-2:]) if len(parts) >= 2 else host

                if current_domain == target_root_domain and request.resource_type in ["xhr", "fetch"]:
                    headers = request.headers
                    auth_header = headers.get("authorization", "None")
                    cookie_header = headers.get("cookie", "None")
                    post_data = request.post_data if request.post_data else "None"

                    try:
                        response_payload = response.json()
                    except Exception:
                        response_payload = "Non-JSON Data"

                    traffic_node = {
                        "url": url,
                        "method": request.method,
                        "status": response.status,
                        "authorization": auth_header,
                        "cookies": cookie_header,
                        "request_body": post_data,
                        "response_json": response_payload
                    }
                    captured_traffic.append(traffic_node)
            except Exception:
                pass

        page.on("response", handle_response)

        try:
            # STEP 1: Direct browser to the specific login path
            login_url = f"https://{start_hostname}/login"
            print(f"🎯 Directing browser to: {login_url}")
            page.goto(login_url, wait_until="load", timeout=25000)
            page.wait_for_timeout(5000)

            # STEP 2: Automated Credentials Input
            print("✏️  Injecting credentials into active input fields...")
            
            # Selectors tailored for phone numbers and passcode configurations
            page.locator("input[type='tel'], input[placeholder*='Phone'], input[type='text']").first.fill(username)
            page.wait_for_timeout(1000)
            page.locator("input[type='password']").first.fill(password)
            page.wait_for_timeout(1000)

            # STEP 3: Click Login Submit Button
            print("🚀 Submitting authentication payload...")
            submit_selectors = ["button[type='submit']", "button:has-text('LOGIN')", ".btn-login", "button"]
            
            clicked = False
            for selector in submit_selectors:
                try:
                    locator = page.locator(selector).first
                    if locator.is_visible():
                        locator.click(force=True, timeout=2000)
                        clicked = True
                        break
                except Exception:
                    continue

            # Pause 6 seconds to let the account load completely
            print("⏳ Allowing session handshake 6 seconds to initialize...")
            page.wait_for_timeout(6000)
            print(f"🛡️  Current Authenticated URL State: {page.url}")

            # STEP 4: Fall back into the multi-page collection queue
            queue.append(page.url)
            ui_routes.add(page.url)

            while queue and len(visited_pages) < max_pages:
                current_url = queue.pop(0)
                parsed_current = urlparse(current_url)
                normalized_url = f"{parsed_current.scheme}://{parsed_current.netloc}{parsed_current.path}"

                if normalized_url in visited_pages:
                    continue

                print(f"🔍 Crawling Area [{len(visited_pages)+1}/{max_pages}]: {normalized_url}")
                visited_pages.add(normalized_url)

                try:
                    page.goto(current_url, wait_until="commit", timeout=15000)
                    page.wait_for_timeout(4000)
                    
                    # Pull fresh elements to keep navigating through sub-tabs
                    elements = page.locator("a, button, [role='button'], [class*='sport']").all()
                    
                    for element in elements[:12]:
                        try:
                            if element.is_visible():
                                href_attr = element.get_attribute("href")
                                if href_attr and not href_attr.startswith(('#', 'javascript:')):
                                    full_url = urljoin(page.url, href_attr)
                                    parsed_found = urlparse(full_url)
                                    
                                    if target_root_domain in (parsed_found.hostname or ""):
                                        ui_routes.add(full_url)
                                        found_normalized = f"{parsed_found.scheme}://{parsed_found.netloc}{parsed_found.path}"
                                        if found_normalized not in visited_pages and found_normalized not in queue:
                                            queue.append(full_url)
                        except Exception:
                            continue

                    page.evaluate("window.scrollBy(0, 400);")
                    page.wait_for_timeout(1500)

                except Exception as e:
                    print(f"⚠️  Navigation skipping exception: {e}")
                    continue

            browser.close()
        except Exception as e:
            print(f"❌ Automation runtime failure: {e}")
            browser.close()
            return

    # --- EXPORT TO DISK ---
    with open("authenticated_traffic.json", "w", encoding="utf-8") as f:
        json.dump(captured_traffic, f, indent=4, ensure_ascii=False)

    print("\n" + "="*90)
    print(f"🏁 RUN COMPLETE. Saved authenticated parameters to: 'authenticated_traffic.json'")
    print("="*90)

# --- Clean Execution Loop Interface ---
print("🚀 Authenticated Multi-Page Traffic Mapping Engine Online.")
print("Type 'exit' to shut down.")

while True:
    target_site = input("\nEnter Target Site Domain (e.g., www.betpawa.cm): ")
    if target_site.strip().lower() == 'exit':
        print("Goodbye!")
        break
    user_num = input("Enter Account Phone Number/Username: ")
    user_pass = input("Enter Account Security Password: ")

    if target_site and user_num and user_pass:
        authenticated_site_spider(target_site, user_num, user_pass, max_pages=10)
        break # Breaks loop after single complete crawl execution
