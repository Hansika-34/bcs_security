import frappe

from bcs_security.api.zabbix import create_group_maintenance


@frappe.whitelist()
def create_group_maintenance_from_ui(docname):

    doc = frappe.get_doc(
        "Monitoring Group",
        docname
    )

    if not doc.custom_maintenance_name:
        frappe.throw("Maintenance Name Required")

    if not doc.custom_maintenance_start:
        frappe.throw("Maintenance Start Required")

    if not doc.custom_maintenance_end:
        frappe.throw("Maintenance End Required")

    result = create_group_maintenance(
        doc.group_id,
        doc.custom_maintenance_name,
        doc.custom_maintenance_start,
        doc.custom_maintenance_end
    )

    frappe.log_error(
        message=str(result),
        title="Group Maintenance"
    )

    if result.get("result"):

        doc.db_set(
            "custom_zabbix_maintenance_id",
            result["result"]["maintenanceids"][0]
        )

        doc.db_set(
            "custom_maintenance_status",
            "Created"
        )

        return "Maintenance Created"

    else:

        doc.db_set(
            "custom_maintenance_status",
            "Failed"
        )

        return result