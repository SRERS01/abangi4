from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, urljoin
import json
import sys

def master_spider(start_url, username, password, max_pages=15):
    start_url = start_url.strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = f"https://{start_url}"

    parsed_start = urlparse(start_url)
    start_hostname = parsed_start.hostname or ""
    start_parts = start_hostname.split('.')
    target_root_domain = ".".join(start_parts[-2:]) if len(start_parts) >= 2 else start_hostname

    print(f"\n🕸️  Initializing Master Spider for: {target_root_domain}")
    queue, visited_pages, captured_traffic = [], set(), []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
        context = browser.new_context(viewport={"width": 1280, "height": 850}, user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        def handle_response(response):
            try:
                request = response.request
                url = request.url
                if any(x in url for x in ["google", "facebook", "doubleclick", "sentry"]): return
                parsed_url = urlparse(url)
                host = parsed_url.hostname or ""
                current_domain = ".".join(host.split('.')[-2:]) if len(host.split('.')) >= 2 else host

                if current_domain == target_root_domain and request.resource_type in ["xhr", "fetch"]:
                    try: payload = response.json()
                    except: payload = "Non-JSON Data"
                    captured_traffic.append({
                        "url": url, "path": parsed_url.path, "method": request.method,
                        "status": response.status, "all_headers": dict(request.headers),
                        "request_body": request.post_data if request.post_data else "None", "response_json": payload
                    })
            except: pass

        page.on("response", handle_response)

        try:
            print(f"🎯 Routing to: https://{start_hostname}/login")
            page.goto(f"https://{start_hostname}/login", wait_until="load", timeout=25000)
            page.wait_for_timeout(4000)

            print("✏️  Injecting credentials...")
            page.locator("input[type='tel'], input[placeholder*='Phone'], input[type='text']").first.fill(username)
            page.locator("input[type='password']").first.fill(password)
            
            print("🚀 Submitting authentication...")
            for selector in ["button[type='submit']", "button:has-text('LOGIN')", ".btn-login", "button"]:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click(force=True)
                    break

            page.wait_for_timeout(6000)

            print("👤 Opening Sidebar & clicking Withdraw...")
            for selector in ["text='Menu'", "text='Account'", "[class*='balance']"]:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click(force=True)
                    page.wait_for_timeout(2000)
                    break

            for selector in ["text='Withdraw'", "text='Withdrawal'", "a[href*='withdraw']"]:
                if page.locator(selector).first.is_visible():
                    page.locator(selector).first.click(force=True)
                    page.wait_for_timeout(4000)
                    break

            queue.append(page.url)
            while queue and len(visited_pages) < max_pages:
                current_url = queue.pop(0)
                norm_url = f"{urlparse(current_url).scheme}://{urlparse(current_url).netloc}{urlparse(current_url).path}"
                if norm_url in visited_pages: continue
                
                print(f"🔍 Mapping Layout Node [{len(visited_pages)+1}/{max_pages}]: {norm_url}")
                visited_pages.add(norm_url)
                
                page.goto(current_url, wait_until="commit", timeout=15000)
                page.wait_for_timeout(3000)
                
                for el in page.locator("a, button, [role='button']").all()[:15]:
                    href = el.get_attribute("href")
                    if href and not href.startswith(('#', 'javascript:')):
                        full_url = urljoin(page.url, href)
                        if target_root_domain in (urlparse(full_url).hostname or ""):
                            f_norm = f"{urlparse(full_url).scheme}://{urlparse(full_url).netloc}{urlparse(full_url).path}"
                            if f_norm not in visited_pages and f_norm not in queue: queue.append(full_url)
                page.evaluate("window.scrollBy(0, 400);")
            browser.close()
        except Exception as e:
            print(f"❌ Automation Error: {e}"); browser.close(); return

    with open("deep_api_inspection.json", "w", encoding="utf-8") as f:
        json.dump(captured_traffic, f, indent=4, ensure_ascii=False)
    print(f"💾 Raw Traffic dumped to 'deep_api_inspection.json'")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 eleven.py <domain> <user> <pass>")
    else:
        master_spider(sys.argv[1], sys.argv[2], sys.argv[3])
