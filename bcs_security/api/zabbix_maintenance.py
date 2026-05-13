import frappe
from bcs_security.api.zabbix import create_maintenance


def after_insert(doc, method=None):

    if not doc.zabbix_host_id:
        frappe.throw("Zabbix Host ID missing")

    try:
        result = create_maintenance(
            doc.zabbix_host_id,
            doc.maintenance_name,
            doc.active_since,
            doc.active_till,
            doc.custom_zabbix_server
        )

        frappe.log_error(str(result), "Maintenance Debug")

        if result.get("result"):

            doc.db_set("zabbix_maintenance_id", result["result"]["maintenanceids"][0])
            doc.db_set("status", "Created")

        else:
            doc.db_set("status", "Failed")
            doc.db_set("message", str(result))

    except Exception:
        frappe.log_error(frappe.get_traceback(), "Maintenance Hook Error")