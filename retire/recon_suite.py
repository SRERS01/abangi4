import re
import sys
import os
import json
import subprocess
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import requests
from colorama import Fore, Style, init

# Initialize terminal colors
init(autoreset=True)

# Configuration Profiles
DANGER_KEYWORDS = ["todo", "fixme", "pass", "key", "secret", "admin", "token", "creds", "db", "config"]
JS_COMMENT_REGEX = re.compile(r'(?://.*)|(?:/\*(?:[^*]|\*(?!/))*\*/)', re.MULTILINE)
HEADERS = {"User-Agent": "Mozilla/5.0 BugBountyScraper/5.0"}
TIMEOUT = 7
MAX_THREADS = 5 # Balance this based on CPU constraints and network bandwidth

# Global Storage for HTML reporting compilation
report_data = []

def run_subfinder(domain):
    """Executes subfinder passively to discover active and historical subdomains."""
    print(Fore.MAGENTA + f"[🚀] Step 1: Gathering subdomains via Subfinder for: {domain}")
    try:
        # Use -silent flag so subfinder prints pure subdomain list strings
        result = subprocess.run(
            ["subfinder", "-d", domain, "-silent"],
            capture_output=True, text=True, check=True
        )
        subdomains = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        print(Fore.GREEN + f"[+] Found {len(subdomains)} subdomains for {domain}.\n")
        return subdomains
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(Fore.RED + "[-] Error: 'subfinder' execution failed. Defaulting to standalone target URL parsing.")
        return [domain]

def check_high_risk_secrets(comment_text):
    """Strict whole-word regex check to eliminate generic false positives."""
    found_keywords = []
    text_lower = comment_text.lower()
    for word in DANGER_KEYWORDS:
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            found_keywords.append(word)
    return found_keywords

def run_retire_js(js_url):
    """Passes unique JavaScript asset URLs to Retire.js for CVE detection analysis."""
    vulns = []
    try:
        result = subprocess.run(
            ["retire", "--jsurl", js_url, "--outputformat", "json"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            data = json.loads(result.stdout)
            for item in data:
                for res in item.get("results", []):
                    component = res.get("component", "Unknown Library")
                    version = res.get("version", "Unknown")
                    for v in res.get("vulnerabilities", []):
                        severity = v.get("severity", "MEDIUM")
                        info = " ".join(v.get("info", []))
                        vulns.append({"component": component, "version": version, "severity": severity, "info": info})
    except Exception:
        pass  # Gracefully skip parsing errors or zero-vulnerability responses
    return vulns

def scan_individual_target(url):
    """Core target analyzer thread worker."""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
        
    print(Fore.CYAN + f"[*] Commencing Deep Scan: {url}")
    target_findings = {"url": url, "vulnerable_libraries": [], "leaked_secrets": []}
    
    try:
        # Resolve target domain validation checks
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        if resp.status_code != 200:
            return None
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        scripts = soup.find_all('script')
        unique_js_assets = set()
        
        for script in scripts:
            src = script.get('src')
            if src:
                unique_js_assets.add(urljoin(url, src))
                
        # Analyze captured assets
        for js_url in unique_js_assets:
            # Check 1: Retire.js CVE Analysis Pipeline
            cve_results = run_retire_js(js_url)
            if cve_results:
                target_findings["vulnerable_libraries"].extend(cve_results)
                print(Fore.RED + f"    [!] CVE Found on {js_url} via Retire.js!")

            # Check 2: Custom Regex Comment Scraper Analysis
            try:
                js_resp = requests.get(js_url, headers=HEADERS, timeout=TIMEOUT, verify=False)
                if js_resp.status_code == 200:
                    comments = JS_COMMENT_REGEX.findall(js_resp.text)
                    for c in comments:
                        cleaned = c.strip()
                        matched_words = check_high_risk_secrets(cleaned)
                        if matched_words:
                            target_findings["leaked_secrets"].append({"asset": js_url, "keywords": matched_words, "content": cleaned})
                            print(Fore.RED + f"    [!] Secret Flagged in {js_url} -> Key terms: {matched_words}")
            except requests.exceptions.RequestException:
                continue

    except requests.exceptions.RequestException:
        return None # Gracefully skip dead web servers

    if target_findings["vulnerable_libraries"] or target_findings["leaked_secrets"]:
        return target_findings
    return None

def generate_html_report(domain):
    """Compiles collected analytical arrays into a clean, modern HTML layout presentation."""
    html_filename = f"recon_report_{domain.replace('.', '_')}.html"
    
    html_content = f"""<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Bug Bounty Recon Dashboard: {domain}</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #cbd5e1; margin: 0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1 {{ color: #f8fafc; border-bottom: 2px solid #334155; padding-bottom: 10px; }}
            .target-card {{ background: #1e293b; border-radius: 8px; padding: 20px; margin-bottom: 20px; border-left: 5px solid #38bdf8; }}
            .target-url {{ font-size: 1.2em; font-weight: bold; color: #38bdf8; word-break: break-all; }}
            .vuln-badge {{ background: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
            .secret-badge {{ background: #f59e0b; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; background: #0f172a; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #334155; }}
            th {{ background: #1e293b; color: #94a3b8; }}
            pre {{ background: #020617; padding: 10px; border-radius: 4px; overflow-x: auto; color: #34d399; font-family: monospace; max-height: 150px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ Attack Surface Recon Summary: {domain}</h1>
            <p>Total Scanned Targets with Findings: {len(report_data)}</p>
    """
    
    for item in report_data:
        html_content += f"""
        <div class="target-card">
            <div class="target-url">🎯 Target Host: {item['url']}</div>
        """
        
        if item["vulnerable_libraries"]:
            html_content += """<h3>⚠️ Outdated Libraries (Retire.js)</h3><table>
            <tr><th>Component</th><th>Version</th><th>Severity</th><th>Advisory Information</th></tr>"""
            for v in item["vulnerable_libraries"]:
                html_content += f"<tr><td>{v['component']}</td><td>{v['version']}</td><td><span class='vuln-badge'>{v['severity']}</span></td><td>{v['info']}</td></tr>"
            html_content += "</table>"
            
        if item["leaked_secrets"]:
            html_content += """<h3>🔑 Sensitive Comment Leaks (Regex Engine)</h3><table>
            <tr><th>Source JavaScript Asset</th><th>Trigger Keywords</th><th>Extracted Code Content</th></tr>"""
            for s in item["leaked_secrets"]:
                html_content += f"<tr><td style='word-break:break-all;'>{s['asset']}</td><td><span class='secret-badge'>{s['keywords']}</span></td><td><pre>{s['content']}</pre></td></tr>"
            html_content += "</table>"
            
        html_content += "</div>"
        
    html_content += """</div></body></html>"""
    
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(Fore.GREEN + f"\n[🎉] Complete! Interactive HTML visual reporting dashboard saved to: {html_filename}")

def main():
    requests.packages.urllib3.disable_warnings()
    if len(sys.argv) < 2:
        print(Fore.RED + "Usage: python recon_suite.py <root_domain.com>")
        sys.exit(1)
        
    root_domain = sys.argv[1]
    
    # Executing passive sub-domain mappings
    discovered_hosts = run_subfinder(root_domain)
    
    print(Fore.MAGENTA + f"[⚙️] Step 2: Spinning up Concurrent ThreadPool Execution Layer...")
    # Multi-threaded concurrent worker loops mapping the resolved targets list
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_target = {executor.submit(scan_individual_target, host): host for host in discovered_hosts}
        for future in as_completed(future_to_target):
            result = future.result()
            if result:
                report_data.append(result)

    # Step 3: Compiling structured database blocks to local HTML interface 
    if report_data:
        generate_html_report(root_domain)
    else:
        print(Fore.YELLOW + "\n[-] Recon completed. No public CVE vulnerabilities or explicit string comment leaks found.")

if __name__ == "__main__":
    main()
