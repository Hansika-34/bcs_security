import requests
import frappe


API_KEY = "Bcs@1234"


def zabbix_request(method, params, zabbix_server=None):

    # =========================
    # GET MONITORING SETTINGS
    # =========================
    settings = frappe.get_doc(
        "Monitoring Settings",
        zabbix_server
    )

    middleware_url = (
        settings.custom_api_url.rstrip("/")
        + "/zabbix/"
    )

    payload = {
        "api_key": API_KEY,
        "method": method,
        "params": params
    }

    try:

        response = requests.post(
            middleware_url,
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