import re
import sys
import os
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup, Comment
import requests
from colorama import Fore, Style, init

# Initialize color processing
init(autoreset=True)

# High-risk keywords to flag (now evaluated as strict whole-words)
DANGER_KEYWORDS = ["todo", "fixme", "pass", "key", "secret", "admin", "token", "creds", "db", "config"]

# Regex for capturing single line (//) and multi-line (/* */) comments
JS_COMMENT_REGEX = re.compile(r'(?://.*)|(?:/\*(?:[^*]|\*(?!/))*\*/)', re.MULTILINE)

# Request Configuration
HEADERS = {"User-Agent": "Mozilla/5.0 BugBountyScraper/3.0"}
TIMEOUT = 8
MAX_THREADS = 10  
OUTPUT_FILE = "high_risk_comments.txt"

def log_to_file(url, comment_type, content, keywords):
    """Safely appends dangerous findings directly to a text log file."""
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(f"[URL] {url}\n")
        f.write(f"[TYPE] {comment_type} | [KEYWORDS] {', '.join(keywords)}\n")
        f.write(f"[CONTENT] {content}\n")
        f.write("-" * 60 + "\n")

def check_high_risk(comment_text):
    """Checks if a comment contains strict, standalone high-risk keywords using regex boundaries."""
    found_keywords = []
    text_lower = comment_text.lower()
    
    for word in DANGER_KEYWORDS:
        # \b ensures we match "pass" but completely ignore "params" or "bypass"
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            found_keywords.append(word)
            
    return found_keywords

def process_comments(content, url, context_name):
    """Parses text content using regex/BeautifulSoup for comment signatures."""
    findings = 0
    
    # 1. Parse HTML comments if analyzing raw web page source
    if context_name == "HTML":
        soup = BeautifulSoup(content, 'html.parser')
        html_comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in html_comments:
            cleaned = comment.strip()
            risks = check_high_risk(cleaned)
            if risks:
                print(Fore.RED + f"    [!] CRITICAL HTML COMMENT on {url} (Keywords: {risks}): <!-- {cleaned} -->")
                log_to_file(url, "HTML Comment", f"<!-- {cleaned} -->", risks)
                findings += 1

    # 2. Parse JS comments (works for inline script blocks and external raw .js assets)
    matches = JS_COMMENT_REGEX.findall(content)
    for match in matches:
        cleaned = match.strip()
        risks = check_high_risk(cleaned)
        if risks:
            print(Fore.RED + f"    [!] CRITICAL JS COMMENT in {context_name} on {url} (Keywords: {risks}): {cleaned}")
            log_to_file(url, f"JS ({context_name})", cleaned, risks)
            findings += 1
            
    return findings

def scan_target(url):
    """Core target worker engine executed inside the concurrent thread pool."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    
    print(Fore.CYAN + f"[*] Thread started: Scanning target -> {url}")
    total_findings = 0
    
    try:
        # Fetch base web page source code
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        if response.status_code != 200:
            return f"Skipped {url} (Status Code: {response.status_code})"
            
        # Process HTML layouts and inline JS structures
        total_findings += process_comments(response.text, url, "HTML")
        
        # Scrape and follow external script paths discovered in page DOM
        soup = BeautifulSoup(response.text, 'html.parser')
        scripts = soup.find_all('script')
        
        for script in scripts:
            src = script.get('src')
            if src:
                js_url = urljoin(url, src)
                try:
                    # Request the raw external JS code file directly
                    js_resp = requests.get(js_url, headers=HEADERS, timeout=TIMEOUT, verify=False)
                    if js_resp.status_code == 200:
                        total_findings += process_comments(js_resp.text, js_url, "External JS File")
                except requests.exceptions.RequestException:
                    continue # Skip broken external links silently

    except requests.exceptions.RequestException as e:
        return f"Failed to connect to target: {url}"

    if total_findings > 0:
        return Fore.GREEN + f"[+] Finished {url} - Found {total_findings} true positive high-risk comments logged!"
    return f"Finished {url} - No critical comments found."

def main():
    # Disable SSL Warnings for aggressive bug hunting scans
    requests.packages.urllib3.disable_warnings()

    if len(sys.argv) < 2:
        print(Fore.RED + "Usage: python multi_comment_scraper.py <subdomains_list_file.txt>")
        print("Example: python multi_comment_scraper.py targets.txt")
        sys.exit(1)
        
    targets_file = sys.argv[1]
    if not os.path.exists(targets_file):
        print(Fore.RED + f"[-] Error: File '{targets_file}' not found.")
        sys.exit(1)

    with open(targets_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(Fore.MAGENTA + f"[=] Starting Smart Multi-threaded Engine against {len(urls)} targets.")
    print(Fore.MAGENTA + f"[=] Filtering out noise. Outputs stored in: {OUTPUT_FILE}\n")

    # Launch ThreadPool executor pipeline 
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_url = {executor.submit(scan_target, url): url for url in urls}
        for future in as_completed(future_to_url):
            result = future.result()
            if result:
                print(result)

if __name__ == "__main__":
    main()
