from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import os

def deep_shadow_network_crawler(start_url):
    start_url = start_url.strip()
    if not start_url.startswith(('http://', 'https://')):
        start_url = f"https://{start_url}"

    parsed_start = urlparse(start_url)
    start_hostname = parsed_start.hostname or ""
    start_parts = start_hostname.split('.')
    target_root_domain = ".".join(start_parts[-2:]) if len(start_parts) >= 2 else start_hostname

    print(f"\n🕸️  Initializing Deep Shadow-DOM Spider for: {target_root_domain}")
    print("⏳ Running browser... Pulling elements natively from document memory context.")

    ui_routes = set()
    api_endpoints = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, # Keep window open so scripts calculate view layouts correctly
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

        # Global Request Sniffer
        def log_request(request):
            url = request.url
            if any(x in url for x in ["google", "facebook", "doubleclick", "sentry"]):
                return

            parsed_url = urlparse(url)
            host = parsed_url.hostname or ""
            parts = host.split('.')
            current_domain = ".".join(parts[-2:]) if len(parts) >= 2 else host

            if current_domain == target_root_domain:
                if request.resource_type in ["document", "stylesheet", "script"]:
                    if not any(url.endswith(ext) for ext in [".js", ".css", ".png", ".jpg", ".svg", ".ico"]):
                        ui_routes.add(url)
                else:
                    api_endpoints.add(url)

        page.on("request", log_request)

        try:
            # Step 1: Open the landing page
            print(f"🎯 Accessing base host URL: {start_url}")
            page.goto(start_url, wait_until="commit", timeout=25000)
            
            print("⏳ Monitoring client framework migration...")
            page.wait_for_load_state("load")
            page.wait_for_timeout(6000) # Give application router time to fully map state
            
            final_url = page.url
            print(f"📍 Landed securely on: {final_url}")
            ui_routes.add(final_url)

            # Step 2: Inject Deep JavaScript query function to breach all Shadow DOM trees
            # This loops through all document nodes and extracts selectors even if hidden inside shadow-roots
            print("🔬 Injecting recursive Shadow-DOM locator script into page context...")
            js_query_script = """
            () => {
                const foundElements = [];
                const selector = "a, button, [role='button'], [class*='btn'], [class*='menu-item'], [class*='sport']";
                
                function findShadowElements(root) {
                    if (!root) return;
                    
                    // Match elements matching our criteria in current boundary
                    const items = root.querySelectorAll(selector);
                    items.forEach(el => {
                        // Gather key attributes to verify visibility and capture meta data
                        if (el.getBoundingClientRect().width > 0) {
                            foundElements.push({
                                text: el.innerText ? el.innerText.trim() : "",
                                tag: el.tagName.toLowerCase(),
                                className: el.className || ""
                            });
                        }
                    });
                    
                    // Recursively check all nested child components for shadow roots
                    const allNodes = root.querySelectorAll('*');
                    allNodes.forEach(node => {
                        if (node.shadowRoot) {
                            findShadowElements(node.shadowRoot);
                        }
                    });
                }
                
                findShadowElements(document);
                return foundElements;
            }
            """
            
            # Execute script inside browser memory
            extracted_nodes = page.evaluate(js_query_script)
            print(f"🖱️  Breached encapsulation layout! Discovered {len(extracted_nodes)} hidden nodes inside Shadow DOM context.")

            # Step 3: Loop through and simulate native structural clicks using text hooks
            clicked_count = 0
            for node in extracted_nodes[:15]:
                try:
                    text_query = node['text'].replace('\n', ' ').strip()
                    if not text_query or len(text_query) < 2:
                        continue
                    
                    print(f"      -> Click Action Executed: [{text_query[:25]}]")
                    
                    # Use Playwright's smart shadow-aware text selector to find and click the component natively
                    page.locator(f"text='{text_query}'").first.click(force=True, timeout=2000)
                    page.wait_for_timeout(2000)
                    
                    ui_routes.add(page.url)
                    clicked_count += 1
                except Exception:
                    continue

            # Step 4: Run a scrolling pass to trigger lazy chunks
            print("📜 Performing step-down viewport sweep...")
            for _ in range(4):
                page.evaluate("window.scrollBy(0, 500);")
                page.wait_for_timeout(1500)

            browser.close()
        except Exception as e:
            print(f"❌ Automation Error: {e}")
            browser.close()
            return

    # --- WRITE DATA OUT ---
    with open("ui_paths.txt", "w") as f:
        for item in sorted(ui_routes):
            f.write(f"{item}\n")
            
    with open("api_endpoints.txt", "w") as f:
        for item in sorted(api_endpoints):
            f.write(f"{item}\n")

    print("\n" + "="*90)
    print(f"💾 Logs successfully dumped to disk!")
    print(f" -> Check 'ui_paths.txt' for all navigated browser paths.")
    print(f" -> Check 'api_endpoints.txt' for all intercepted API data streams.")
    print("="*90)
    print(f"📦 Unique UI Routes/Paths Captured: {len(ui_routes)}")
    print(f"⚡ Unique API Endpoints Sniffed: {len(api_endpoints)}")

# --- Interactive Prompter Loop ---
print("🚀 Custom Element Network Asset Spider Engine Active.")
print("Type 'exit' to shut down.")

while True:
    user_input = input("\nEnter starting site domain (e.g., www.betpawa.cm): ")
    if user_input.strip().lower() == 'exit':
        print("Goodbye!")
        break
    if not user_input.strip():
        print("⚠️ Input cannot be empty.")
        continue
        
    deep_shadow_network_crawler(user_input)
