
import requests
import time

session = requests.Session()

url = "https://www.betpawa.cm/api/user/v3/password/request-otp"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "X-Pawa-Brand": "betpawa-cameroon",
    "X-Pawa-Language": "en"
}

payload = {
    "phoneNumber": "678392088",  # your test number
    "resetMethodName": "SMS"
}

print("=== START RATE LIMIT TEST ===")

for i in range(15):
    response = session.post(url, headers=headers, json=payload)

    try:
        data = response.json()
        limit = data.get("limit", {})
        allowed = limit.get("allowed")
        attempts_left = limit.get("attemptsLeft")
    except:
        allowed = "N/A"
        attempts_left = "N/A"

    print(f"\nAttempt {i+1}")
    print("Status Code:", response.status_code)
    print("Allowed:", allowed)
    print("Attempts Left:", attempts_left)
    print("Response Snippet:", response.text[:120])

    # 🔴 IMPORTANT: mark when limit is exceeded
    if allowed is False:
        print(">>> LIMIT EXCEEDED HERE <<<")

    time.sleep(2)  # keep it safe (no spam)

print("\n=== TEST COMPLETE ===")

