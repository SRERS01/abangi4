import re
import sys
import os
import subprocess
import json
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests
from colorama import Fore, Style, init

# Initialize color processing
init(autoreset=True)

# High-risk keywords to flag
DANGER_KEYWORDS = ["todo", "fixme", "pass", "key", "secret", "admin", "token", "creds", "db", "config"]
JS_COMMENT_REGEX = re.compile(r'(?://.*)|(?:/\*(?:[^*]|\*(?!/))*\*/)', re.MULTILINE)
HEADERS = {"User-Agent": "Mozilla/5.0 BugBountyScraper/4.0"}

def check_high_risk(comment_text):
    """Checks if a comment contains strict, standalone high-risk keywords."""
    found_keywords = []
    text_lower = comment_text.lower()
    for word in DANGER_KEYWORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            found_keywords.append(word)
    return found_keywords

def run_retire_js(js_url):
    """Executes the local retire command against a specific JS URL."""
    print(Fore.BLUE + f"[*] Running Retire.js on: {js_url}")
    try:
        # Calls the 'retire' binary installed on your Ubuntu system
        result = subprocess.run(
            ["retire", "--jsurl", js_url, "--outputformat", "json"],
            capture_output=True,
            text=True
        )
        
        # Retire.js returns exit code 13 if vulnerabilities are found
        if result.stdout.strip():
            data = json.loads(result.stdout)
            # Parse the JSON results from Retire.js
            for item in data:
                for result_node in item.get("results", []):
                    component = result_node.get("component", "Unknown")
                    version = result_node.get("version", "Unknown")
                    print(Fore.RED + f"    [!] VULNERABLE COMPONENT FOUND: {component} v{version}")
                    for vuln in result_node.get("vulnerabilities", []):
                        severity = vuln.get("severity", "UNKNOWN")
                        info = vuln.get("info", [])
                        print(Fore.RED + f"        - Severity: {severity} | Summary: {info[0] if info else 'No info'}")
        else:
            print(Fore.GREEN + "    [+] Retire.js: No public library CVEs detected.")
            
    except FileNotFoundError:
        print(Fore.RED + "[-] Error: 'retire' command not found. Ensure it is in your PATH.")
    except Exception as e:
        print(Fore.YELLOW + f"    [i] Retire.js parse skipped or completed with zero results.")

def scan_target(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    print(Fore.CYAN + "=" * 60)
    print(Fore.CYAN + f" Starting Combined Recon Scan on: {url}")
    print(Fore.CYAN + "=" * 60 + "\n")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10, verify=False)
        if response.status_code != 200:
            print(Fore.RED + f"[-] Error: Target returned status code {response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"[-] Connection failed: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    scripts = soup.find_all('script')
    
    # Track unique JS files to avoid redundant scanning
    discovered_js_urls = set()

    for script in scripts:
        src = script.get('src')
        if src:
            js_url = urljoin(url, src)
            discovered_js_urls.add(js_url)

    print(Fore.YELLOW + f"[*] Found {len(discovered_js_urls)} unique external JavaScript files.\n")

    # Process each discovered script through both tools
    for js_url in discovered_js_urls:
        print(Fore.WHITE + f"\n--> Analyzing Script Asset: {js_url}")
        print("-" * 50)
        
        # Part 1: Run Retire.js for CVE Check
        run_retire_js(js_url)
        
        # Part 2: Run Custom Comment Scraper for Secret Leaks
        try:
            js_resp = requests.get(js_url, headers=HEADERS, timeout=8, verify=False)
            if js_resp.status_code == 200:
                matches = JS_COMMENT_REGEX.findall(js_resp.text)
                found_comments = False
                for match in matches:
                    cleaned = match.strip()
                    risks = check_high_risk(cleaned)
                    if risks:
                        print(Fore.RED + f"    [!] CUSTOM ALERT (Keywords: {risks}): {cleaned}")
                        found_comments = True
                if not found_comments:
                    print(Fore.GREEN + "    [+] Comment Scraper: No sensitive leaks found.")
        except requests.exceptions.RequestException:
            continue

if __name__ == "__main__":
    requests.packages.urllib3.disable_warnings()
    if len(sys.argv) < 2:
        print(Fore.RED + "Usage: python advanced_js_hunter.py <target_url>")
        sys.exit(1)
        
    scan_target(sys.argv[1])
