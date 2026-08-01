from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json
import os

def capture_deep_api_traffic(start_url):
    start_url = start_url.strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = f"https://{start_url}"

    parsed_start = urlparse(start_url)
    start_hostname = parsed_start.hostname or ""
    start_parts = start_hostname.split('.')
    target_root_domain = ".".join(start_parts[-2:]) if len(start_parts) >= 2 else start_hostname

    print(f"\n🕸️  Initializing Deep API Inspector for: {target_root_domain}")
    print("⏳ Running browser... Intercepting live request/response data frames.")

    captured_traffic = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, # Keep open so single page apps execute payloads normally
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        # Callback function triggered whenever a background network response resolves
        def handle_response(response):
            try:
                request = response.request
                url = request.url
                
                # Skip tracking networks to focus purely on core app engineering
                if any(x in url for x in ["google", "facebook", "doubleclick", "sentry"]):
                    return

                parsed_url = urlparse(url)
                host = parsed_url.hostname or ""
                parts = host.split('.')
                current_domain = ".".join(parts[-2:]) if len(parts) >= 2 else host

                # Target background APIs (xhr/fetch) belonging to the site
                if current_domain == target_root_domain and request.resource_type in ["xhr", "fetch"]:
                    
                    # 1. Capture Request Header Parameters (Tokens, Auth, Cookies)
                    headers = request.headers
                    auth_header = headers.get("authorization", "None Present")
                    cookie_header = headers.get("cookie", "None Present")
                    
                    # 2. Capture Outbound Post/Put Data (if available)
                    post_data = request.post_data if request.post_data else "No Outbound Body"

                    # 3. Safely attempt to parse inbound JSON Server Responses
                    try:
                        response_payload = response.json()
                    except Exception:
                        response_payload = "Non-JSON Data or Binary Stream"

                    # Structure the data node object
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
                    
                    # Live notification in terminal when an endpoint is dissected
                    print(f"   📥 [Intercepted] {request.method} -> {parsed_url.path[:40]}")
                    if auth_header != "None Present":
                        print(f"      🔑 Auth Token Spotted: {auth_header[:30]}...")

            except Exception:
                pass # Gracefully handle aborted or dropped packets

        # Register the response listener
        page.on("response", handle_response)

        try:
            print(f"🎯 Landing on: {start_url}")
            page.goto(start_url, wait_until="load", timeout=25000)
            
            print("⏳ Monitoring operations... Allowing dynamic framework pipelines to sync.")
            page.wait_for_timeout(5000)
            
            # Simulate real human scrolling interaction to force content API calls
            page.evaluate("window.scrollBy(0, 600);")
            page.wait_for_timeout(4000)
            
            # Locate structural navigation nodes and execute a quick sequence to trigger login/sports pipelines
            broad_selectors = "a, button, [role='button'], [class*='btn']"
            elements = page.locator(broad_selectors).all()
            
            print(f"🖱️  Executing fast automated click matrix against {min(len(elements), 8)} layout elements...")
            for element in elements[:8]:
                try:
                    if element.is_visible():
                        element.click(force=True, timeout=1500)
                        page.wait_for_timeout(1500)
                except Exception:
                    continue

            browser.close()
        except Exception as e:
            print(f"❌ Automation Error: {e}")
            browser.close()
            return

    # --- SAVE FULL ARCHIVE TO DISK ---
    output_filename = "deep_api_inspection.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(captured_traffic, f, indent=4, ensure_ascii=False)

    print("\n" + "="*90)
    print(f"🏁 INSPECTION COMPLETE. Captured {len(captured_traffic)} complete HTTP request/response sequences.")
    print(f"💾 Comprehensive traffic data dumped to: '{output_filename}'")
    print("="*90)

# --- Execution Entry Prompt ---
print("🚀 Live HTTP Header & JSON Payload Inspector Ready.")
print("Type 'exit' to shut down.")

while True:
    user_input = input("\nEnter starting site domain (e.g., www.betpawa.cm): ")
    if user_input.strip().lower() == 'exit':
        print("Goodbye!")
        break
    if not user_input.strip():
        print("⚠️ Input cannot be empty.")
        continue
        
    capture_deep_api_traffic(user_input)
