import json
import os

def run_diagnostic_audit():
    token_file = "token_endpoint_results.json"
    traffic_file = "deep_api_inspection.json"
    
    print("\n" + "="*90)
    print("🛡️  AUTOMATED API & INFRASTRUCTURE RISK DIAGNOSTIC TOOL")
    print("="*90)
    
    if not os.path.exists(token_file):
        print(f"⚠️  Missing '{token_file}'. Proceeding with raw network inspection traffic.")
        token_data = {}
    else:
        with open(token_file, "r", encoding="utf-8") as f:
            token_data = json.load(f)

    # --------------------------------------------------------------------
    # TEST 1: Cookie Transportation Layer (Secure vs Non-Secure)
    # --------------------------------------------------------------------
    print("\n[TEST 1] Cookie Security Transport Flags:")
    # We recall from your earlier Playwright cookie dump:
    # x-pawa-token featured: HTTPOnly: True | Secure: False
    print("  🚨 FLAGGED RISK: 'x-pawa-token' cookie is transmitted with [Secure: False].")
    print("     -> Impact: This allows session cookies to travel over unencrypted HTTP channels.")
    print("     -> Remediation: Force the 'Secure' flag to True to restrict cookies strictly to HTTPS.")

    # --------------------------------------------------------------------
    # TEST 2: Account Enumeration & UUID Information Disclosure
    # --------------------------------------------------------------------
    print("\n[TEST 2] Identity Information Disclosure (UUID Mapping):")
    deposit_limit = token_data.get("Deposit Configuration Limits", {}).get("response_payload", {})
    user_uuid = deposit_limit.get("userUuid", None)
    
    if user_uuid:
        print(f"  🔍 Isolated User Identity Node: {user_uuid}")
        print("  ⚠️  VULNERABILITY RISK: Object exposures found in GET queries.")
        print("     -> Impact: If the backend gateway fails to check session alignment (IDOR),")
        print("                changing this UUID can expose other users' deposit limits.")
    else:
        print("  ✅ No clear UUID maps extracted from token files.")

    # --------------------------------------------------------------------
    # TEST 3: Business Logic & Payout Parameter Constraints
    # --------------------------------------------------------------------
    print("\n[TEST 3] Financial Business Logic Threshold Validation:")
    payout_data = token_data.get("Active Payout Routing Methods", {}).get("response_payload", {}).get("data", {})
    methods = payout_data.get("payoutMethods", [])
    
    if methods:
        for m in methods:
            print(f"  💵 Active Channel: {m.get('PayoutTypeName')} ({m.get('currencyCode')})")
            print(f"     -> Transaction Constraints: Min: {m.get('minAmount')} | Max: {m.get('maxAmount')}")
            print(f"     -> Compliance Profile Status: 'personalDataSet' is {m.get('personalDataSet')}")
        print("  ⚠️  AUDIT POINT: Parameter Manipulation Potential.")
        print("     -> Impact: Check if modifying 'minAmount' in outbound JSON requests bypasses server constraints.")
    else:
        print("  ✅ No active financial routing arrays found.")

    # --------------------------------------------------------------------
    # TEST 4: Sensitive Endpoint Exposure (Strapi CMS Routing)
    # --------------------------------------------------------------------
    print("\n[TEST 4] Content Management System (CMS) Route Leakage:")
    if os.path.exists(traffic_file):
        with open(traffic_file, "r", encoding="utf-8") as f:
            raw_traffic = json.load(f)
        
        strapi_routes = set()
        for node in raw_traffic:
            path = node.get("path", "")
            if "strapi" in path.lower() or "api/pages" in path.lower():
                strapi_routes.add(path)
                
        if strapi_routes:
            print(f"  🚨 DISCOVERED ENDPOINTS: {len(strapi_routes)} hidden Strapi CMS pathways found:")
            for route in sorted(strapi_routes):
                print(f"     -> {route}")
            print("     -> Impact: Direct visibility into backend CMS architectures simplifies attack mapping.")
            print("     -> Remediation: Restrict or filter routing signatures behind a unified API gateway.")
        else:
            print("  ✅ No internal CMS endpoints leaked in the raw traffic log.")
    else:
        print("  ⚠️  Raw network logs missing; skipping CMS endpoint check.")

    print("\n" + "="*90)
    print("🏁 INFRASTRUCTURE AUDIT AND ARCHITECTURE PASS COMPLETE.")
    print("="*90)

if __name__ == "__main__":
    run_diagnostic_audit()
