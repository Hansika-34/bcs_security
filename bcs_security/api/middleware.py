import requests
import frappe

MIDDLEWARE_URL = "http://103.231.215.171:8000/zabbix/"
API_KEY = "Bcs@1234"


def zabbix_request(method, params):

    payload = {
        "api_key": API_KEY,
        "method": method,
        "params": params
    }

    try:

        response = requests.post(
            MIDDLEWARE_URL,
            json=payload,
            timeout=30
        )

        return response.json()

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "Middleware API Error"
        )

        return {
            "error": "Middleware API Failed"
        }