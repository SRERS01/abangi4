from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json, sys, os
def master_harvest_flow(domain_arg, username, password):
    host = str(domain_arg).strip().replace('https://', '').replace('http://', '').split('/')[0]
    if not host.startswith('www.'): host = f'www.{host}'
    print(f'\n⚡ Step 1: Deploying WebKit Client for: {host}')
    ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15'
    captured_payloads = {}
    with sync_playwright() as p:
        try:
            b = p.webkit.launch(headless=True)
            ctx = b.new_context(viewport={'width':1280,'height':850}, user_agent=ua, bypass_csp=True)
            page = ctx.new_page()
            page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});window.chrome=undefined;")
            def sniffer(res):
                try:
                    url = res.request.url
                    if '/api/payment/' in url:
                        captured_payloads[urlparse(url).path] = {'status': res.status, 'json': res.json()}
                except: pass
            page.on('response', sniffer)
            login_url = f'https://{host}/login'
            print(f'🎯 Navigating directly to login frame: {login_url}')
            page.goto(login_url, wait_until='commit', timeout=25000)
            page.wait_for_timeout(4000)
            print('✏️  Injecting credentials into login forms...')
            page.locator("input[type='tel'], input[placeholder*='Phone'], input[type='text']").first.fill(username)
            page.locator("input[type='password']").first.fill(password)
            page.wait_for_timeout(1000)
            print('🚀 Executing authentication state submission...')
            for s in ["button[type='submit']", "button:has-text('LOGIN')", ".btn-login", "button"]:
                if page.locator(s).first.is_visible():
                    page.locator(s).first.click(force=True)
                    break
            print('⏳ Waiting 7 seconds for session authorization tokens to map...')
            page.wait_for_timeout(7000)
            print('\n⚡ Step 2: Triggering Sequenced Internal Workspace Sweep...')
            target_routes = [f'https://{host}/withdraw', f'https://{host}/deposit']
            for target_route in target_routes:
                print(f'   -> Navigating viewport securely to: {target_route}')
                page.goto(target_route, wait_until='commit', timeout=25000)
                page.wait_for_timeout(6000)
            b.close()
        except Exception as e:
            print(f'❌ Context Error: {e}'); browser.close(); return
    print('\n' + '='*90 + '\n🎯 INTEGRATED TRANSACTION DATA PAYLOAD ARCHIVE\n' + '='*90)
    hits = 0
    for path, info in captured_payloads.items():
        if any(x in path for x in ['limit', 'options', 'pending', 'active']):
            print(f'\n🟢 Path: {path} (HTTP {info["status"]})')
            print(json.dumps(info["json"], indent=4, ensure_ascii=False))
            hits += 1
    if hits == 0: print('⚠️  No protected payload data harvested. Verify parameters.')
    print('='*90 + '\n')
if __name__ == '__main__':
    if len(sys.argv) < 4:
        print('Syntax: python3 ultimate_harvester.py <domain> <username> <password>')
    else: master_harvest_flow(sys.argv[1], sys.argv[2], sys.argv[3])
