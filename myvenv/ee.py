
import requests
import time

url = "https://www.betpawa.cm/api/user/v3/password/request-otp"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "X-Pawa-Brand": "betpawa-cameroon",
    "X-Pawa-Language": "en"
}

payload = {
    "phoneNumber": "678392088",
    "resetMethodName": "SMS"
}

session = requests.Session()

print("=== RATE LIMIT BEHAVIOR ANALYSIS ===\n")

responses = []

for i in range(10):
    r = session.post(url, headers=headers, json=payload)

    try:
        data = r.json()
    except:
        data = {}

    limit = data.get("limit", {})
    allowed = limit.get("allowed")
    attempts_left = limit.get("attemptsLeft")

    responses.append((i+1, r.status_code, allowed, attempts_left))

    print(f"Attempt {i+1}")
    print("Status:", r.status_code)
    print("Allowed:", allowed)
    print("Attempts Left:", attempts_left)
    print("-" * 40)

    time.sleep(1)

print("\n=== SUMMARY ===")
for row in responses:
    print(row)
