
import requests
from bs4 import BeautifulSoup

patterns = [
    "eval(",
    "document.write(",
    "innerHTML",
    "outerHTML",
    "setTimeout(",
    "setInterval(",
    "new Function(",
    "onerror=",
    "onclick="
]

url = input("Enter URL: ").strip()

# Clean input
url = url.replace("Enter URL:", "").strip()

if not url.startswith("http"):
    url = "http://" + url

def scan_content(content, source):
    found = False
    for pattern in patterns:
        if pattern in content:
            found = True
            print(f"[!] Found in {source}: {pattern}")
    return found

try:
    print("\n[+] Fetching main page...\n")
    response = requests.get(url, timeout=10)
    html = response.text

    print("[+] Scanning HTML...\n")
    scan_content(html, "HTML")

    # Parse JS files
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script", src=True)

    print(f"\n[+] Found {len(scripts)} external JS files\n")

    for script in scripts:
        js_url = script["src"]

        # Fix relative URLs
        if js_url.startswith("/"):
            js_url = url.rstrip("/") + js_url
        elif not js_url.startswith("http"):
            continue

        try:
            print(f"[+] Scanning JS: {js_url}")
            js_resp = requests.get(js_url, timeout=10)
            scan_content(js_resp.text, js_url)
        except:
            print(f"[!] Failed to fetch {js_url}")

except Exception as e:
    print("[!] Error:", e)
