import frappe

from bcs_security.api.middleware import (
    zabbix_request
)


@frappe.whitelist()
def sync_zabbix_groups(
    monitoring_settings=None
):

    # =========================
    # VALIDATION
    # =========================
    if not monitoring_settings:

        frappe.throw(
            "Monitoring Settings Required"
        )

    # =========================
    # GET GROUPS
    # =========================
    response = zabbix_request(

        "hostgroup.get",

        {
            "output": [
                "groupid",
                "name"
            ]
        },

        monitoring_settings
    )

    # =========================
    # DEBUG LOG
    # =========================
    frappe.log_error(
        message=str(response),
        title="GROUP RESPONSE"
    )

    # =========================
    # INSERT GROUPS
    # =========================
    for group in response.get("result", []):

        existing = frappe.db.exists(

            "Monitoring Group",

            {
                "group_id": group["groupid"],

                "monitoring_settings": monitoring_settings
            }
        )

        if not existing:

            doc = frappe.get_doc({

                "doctype": "Monitoring Group",

                "group_name": group["name"],

                "group_id": group["groupid"],

                "monitoring_settings": monitoring_settings
            })

            doc.insert(
                ignore_permissions=True
            )

    frappe.db.commit()

    return "Groups Synced Successfully"