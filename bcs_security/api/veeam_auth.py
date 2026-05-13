import requests
from .veeam_config import VEEAM_URL, USERNAME, PASSWORD


def get_token():
    url = f"{VEEAM_URL}/api/oauth2/token"

    payload = {
        "grant_type": "password",
        "username": USERNAME,
        "password": PASSWORD
    }

    headers = {
        "x-api-version": "1.1-rev2"   # ? IMPORTANT
    }

    response = requests.post(
        url,
        data=payload,
        headers=headers,
        auth=(USERNAME, PASSWORD),
        verify=False,
        timeout=10
    )

    try:
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception:
        return f"ERROR: {response.text}"