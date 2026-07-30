
import requests

session = requests.Session()

login_url = "https://www.betpawa.cm/api/user/v3/authenticate"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "X-Pawa-Brand": "betpawa-cameroon",
    "X-Pawa-Language": "en"
}

payload = {
    "username": "678392088",
    "password": "1290",
    "rememberMe": False
}

login_response = session.post(login_url, headers=headers, json=payload)

print("LOGIN STATUS:", login_response.status_code)

# Extract token automatically
token = session.cookies.get("x-pawa-token")

print("TOKEN:", token)

