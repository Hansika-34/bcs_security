import frappe

from bcs_security.api.zabbix import (
    create_maintenance
)


def after_insert(doc, method=None):

    # =========================
    # VALIDATION
    # =========================
    if not doc.zabbix_host_id:

        frappe.throw(
            "Zabbix Host ID missing"
        )

    if not doc.custom_zabbix_server:

        frappe.throw(
            "Monitoring Settings missing"
        )

    try:

        # =========================
        # CREATE MAINTENANCE
        # =========================
        result = create_maintenance(

            doc.zabbix_host_id,

            doc.maintenance_name,

            doc.active_since,

            doc.active_till,

            doc.custom_zabbix_server
        )

        # =========================
        # DEBUG LOG
        # =========================
        frappe.log_error(
            message=str(result),
            title="Maintenance Debug"
        )

        # =========================
        # SUCCESS
        # =========================
        if result.get("result"):

            doc.db_set(
                "zabbix_maintenance_id",
                result["result"]["maintenanceids"][0]
            )

            doc.db_set(
                "status",
                "Created"
            )

            frappe.db.commit()

        # =========================
        # FAILED
        # =========================
        else:

            doc.db_set(
                "status",
                "Failed"
            )

            doc.db_set(
                "message",
                str(result)
            )

            frappe.db.commit()

    except Exception:

        frappe.log_error(
            frappe.get_traceback(),
            "Maintenance Hook Error"
        )