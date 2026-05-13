import frappe
import requests

API_VERSION = "1.1-rev2"


def get_settings():
    """Fetch Veeam Settings from ERPNext"""
    return frappe.get_single("Veeam Settings")


def get_token():
    """Authenticate with Veeam REST API and return access token"""
    settings = get_settings()

    url = f"{settings.server_url}:{settings.api_port}/api/oauth2/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "x-api-version": API_VERSION
    }

    # Veeam REST API requires credentials in the POST body, NOT as Basic Auth header.
    # The username must be plain (no domain prefix) unless your Veeam server
    # is domain-joined and the account is a domain account.
    # Try plain username first: "BackupUser"
    # If that fails with "Authentication failed", try: "VEEAMTEST\\BackupUser"
    payload = {
        "grant_type": "password",
        "username": settings.username,       # e.g. "BackupUser" or "DOMAIN\\BackupUser"
        "password": settings.get_password("password"),  # use get_password for encrypted field
    }

    response = requests.post(
        url,
        headers=headers,
        data=payload,
        verify=settings.verify_ssl,
        timeout=30
    )

    # Surface the actual error message from Veeam for easier debugging
    if not response.ok:
        try:
            err = response.json()
            frappe.throw(f"Veeam Auth Error [{response.status_code}]: {err.get('message', response.text)}")
        except Exception:
            frappe.throw(f"Veeam Auth Error [{response.status_code}]: {response.text}")

    data = response.json()
    token = data.get("access_token")

    if not token:
        frappe.throw(f"Veeam returned no access_token. Response: {data}")

    return token


def api_get(endpoint):
    """Generic function to call Veeam REST API"""
    settings = get_settings()
    token = get_token()

    url = f"{settings.server_url}:{settings.api_port}{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-api-version": API_VERSION
    }

    response = requests.get(
        url,
        headers=headers,
        verify=settings.verify_ssl,
        timeout=30
    )

    if not response.ok:
        try:
            err = response.json()
            frappe.throw(f"Veeam API Error [{response.status_code}]: {err.get('message', response.text)}")
        except Exception:
            frappe.throw(f"Veeam API Error [{response.status_code}]: {response.text}")

    return response.json()