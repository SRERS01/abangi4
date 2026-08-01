from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import json, sys, os
def run_query(kw):
    if not os.path.exists('webkit_session.json'): return
    with open('webkit_session.json', 'r') as f: tk = json.load(f).get('x-pawa-token')
    r = 'https://betpawa.cm' if 'withdraw' in str(kw).lower() else 'https://betpawa.cm'
    print(f'\n🍏 WebKit Client Active...\n🎯 Target Subdomain Route: {r}')
    dm = {}
    with sync_playwright() as p:
        try:
            b = p.webkit.launch(headless=True)
            ctx = b.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15', bypass_csp=True)
            ctx.add_cookies([{'name': 'x-pawa-token', 'value': tk, 'domain': 'www.betpawa.cm', 'path': '/'}])
            page = ctx.new_page()
            page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});window.chrome=undefined;")
            def sniffer(res):
                try:
                    if '/api/payment/' in res.request.url:
                        dm[urlparse(res.request.url).path] = {'status': res.status, 'json': res.json()}
                except: pass
            page.on('response', sniffer)
            page.goto(r, wait_until='commit', timeout=25000)
            page.wait_for_timeout(8000)
            b.close()
        except Exception as e:
            print(f'❌ Context Error: {e}'); return
    print('\n' + '='*90 + '\n🎯 DISSECTED LIVE TRANSACTION DATA PAYLOAD\n' + '='*90)
    h = 0
    for path, info in dm.items():
        if any(x in path for x in ['limit', 'options', 'pending', 'active']):
            print(f'\n🟢 Node Path: {path} (HTTP {info["status"]})')
            print(json.dumps(info["json"], indent=4, ensure_ascii=False))
            h += 1
    if h == 0: print('⚠️ No payload traffic captured. Re-run harvester.')
    print('='*90 + '\n')
if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'deposit'
    run_query(target)
