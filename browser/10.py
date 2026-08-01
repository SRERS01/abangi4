import json
import os
from urllib.parse import urlparse

def analyze_captured_session(json_file):
    if not os.path.exists(json_file):
        print(f"❌ Error: Target log repository '{json_file}' not found.")
        print("Please ensure you run 'nine.py' or your previous crawler script first.")
        return

    print(f"📖 Loading and decoding traffic log matrix: '{json_file}'...")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            traffic_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON log stream: {e}")
        return

    print(f"✅ Successfully compiled {len(traffic_data)} network transactions.")
    print("\n" + "="*90)
    print("📋 ACTIVE AUTHENTICATION / SESSION COOKIE INVENTORY")
    print("="*90)

    # Stage 1: Isolate active session tracking cookies
    discovered_cookies = set()
    for node in traffic_data:
        cookie_string = node.get("cookies", "None")
        if cookie_string and cookie_string != "None":
            # Split individual keys to map structural variables cleanly
            individual_cookies = [c.strip() for c in cookie_string.split(";")]
            for cookie in individual_cookies:
                # We target common framework cookies (Session tokens, JWT targets, device identifiers)
                if any(x in cookie.lower() for x in ["session", "token", "jwt", "auth", "uid", "sid"]):
                    discovered_cookies.add(cookie)

    if discovered_cookies:
        for idx, cookie_node in enumerate(sorted(discovered_cookies)):
            # Mask trailing characters to keep data profile safe inside logs
            if "=" in cookie_node:
                key, val = cookie_node.split("=", 1)
                masked_val = val[:12] + "..." if len(val) > 12 else val
                print(f"  [Cookie {idx+1}] {key} = {masked_val}")
            else:
                print(f"  [Cookie {idx+1}] {cookie_node}")
    else:
        print("  ⚠️ No framework session state cookies flagged in request headers.")

    print("\n" + "="*90)
    print("🎯 ISOLATED WITHDRAWAL / PAYMENT GATEWAY DATA OBJECTS")
    print("="*90)

    # Stage 2: Extract specific response metrics for the withdrawal pipelines
    withdrawal_hits = 0
    for node in traffic_data:
        url = node.get("url", "")
        # Focus strictly on payment nodes discovered via your previous scan metrics
        if "withdrawal" in url.lower() or "payment" in url.lower():
            withdrawal_hits += 1
            parsed_url = urlparse(url)
            print(f"\n⚡ Target [{withdrawal_hits}]: {node.get('method')} -> {parsed_url.path}")
            print(f"   📊 Server Return Status: {node.get('status')}")
            
            # Print Outbound parameters (if data values were submitted)
            req_body = node.get("request_body", "None")
            if req_body and req_body != "None":
                print(f"   📤 Request Parameters sent: {req_body}")

            # Decode dynamic JSON payload return structures
            response_json = node.get("response_json")
            print("   📥 Server Data Payload Content:")
            if isinstance(response_json, dict) or isinstance(response_json, list):
                # Format long JSON blocks so they look visually organized
                formatted_json = json.dumps(response_json, indent=6, ensure_ascii=False)
                # Cap displaying long arrays to avoid text overflow crashes
                if len(formatted_json) > 800:
                    print(formatted_json[:800] + "\n      ... [Output Truncated for Layout Safety] ...")
                else:
                    print(formatted_json)
            else:
                print(f"      {response_json}")

    if withdrawal_hits == 0:
        print("  ⚠️ No matching financial metadata blocks isolated in backend responses.")
    
    print("\n" + "="*90)
    print("🏁 INVENTORY DATA COMPRESSED SYSTEM WRAP.")
    print("="*90)

# Run the analyzer module against your captured output file node
analyze_captured_session("authenticated_traffic.json")
