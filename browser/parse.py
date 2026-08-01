import json
import csv
import os

if not os.path.exists("deep_api_inspection.json"):
    print("❌ Run 'python3 eleven.py' first to generate data.")
    exit()

with open("deep_api_inspection.json", "r", encoding="utf-8") as f:
    traffic = json.load(f)

print(f"\n📊 Processing {len(traffic)} captured API transactions...")

print("\n🔍 EVALUATING LOGGED HEADERS FOR CUSTOM SESSION TOKENS:")
unique_keys = set()
for node in traffic:
    # FIXED: Added fallback .get() dictionary guard
    headers_dict = node.get("all_headers", {})
    for k in headers_dict.keys():
        if any(x in k.lower() for x in ["auth", "token", "brand", "client", "session", "jwt", "pawa"]):
            unique_keys.add(k)

for key in sorted(unique_keys):
    print(f"  -> {key}")

try:
    with open("traffic_report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["METHOD", "PATH", "STATUS", "URL", "PAYLOAD"])
        for node in traffic:
            body = str(node.get("request_body", "None"))
            short_body = body[:60] + "..." if len(body) > 60 else body
            writer.writerow([node.get("method", "GET"), node.get("path", "/"), node.get("status", 200), node.get("url", ""), short_body])
    print(f"\n💾 Spreadsheet generated successfully: 'traffic_report.csv'")
except Exception as e:
    print(f"❌ CSV generation error: {e}")
