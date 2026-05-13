import frappe

from bcs_security.api.zabbix import (
    create_group_maintenance
)


@frappe.whitelist()
def create_group_maintenance_from_ui(docname):

    # =========================
    # GET DOC
    # =========================
    doc = frappe.get_doc(
        "Monitoring Group",
        docname
    )

    # =========================
    # VALIDATIONS
    # =========================
    if not doc.custom_maintenance_name:

        frappe.throw(
            "Maintenance Name Required"
        )

    if not doc.custom_maintenance_start:

        frappe.throw(
            "Maintenance Start Required"
        )

    if not doc.custom_maintenance_end:

        frappe.throw(
            "Maintenance End Required"
        )

    if not doc.monitoring_settings:

        frappe.throw(
            "Monitoring Settings Required"
        )

    # =========================
    # CREATE MAINTENANCE
    # =========================
    result = create_group_maintenance(

        doc.group_id,

        doc.custom_maintenance_name,

        doc.custom_maintenance_start,

        doc.custom_maintenance_end,

        doc.monitoring_settings
    )

    # =========================
    # DEBUG LOG
    # =========================
    frappe.log_error(
        message=str(result),
        title="Group Maintenance"
    )

    # =========================
    # SUCCESS
    # =========================
    if result.get("result"):

        doc.db_set(
            "custom_zabbix_maintenance_id",
            result["result"]["maintenanceids"][0]
        )

        doc.db_set(
            "custom_maintenance_status",
            "Created"
        )

        frappe.db.commit()

        return "Maintenance Created"

    # =========================
    # FAILED
    # =========================
    else:

        doc.db_set(
            "custom_maintenance_status",
            "Failed"
        )

        frappe.db.commit()

        return result