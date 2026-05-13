import frappe

from bcs_security.api.middleware import zabbix_request


@frappe.whitelist()
def sync_zabbix_groups():

    response = zabbix_request(
        "hostgroup.get",
        {
            "output": ["groupid", "name"]
        }
    )

    # SAFE LOG
    frappe.log_error(
        message=str(response),
        title="GROUP RESPONSE"
    )

    for group in response.get("result", []):

        existing = frappe.db.exists(
            "Monitoring Group",
            {
                "group_id": group["groupid"]
            }
        )

        if not existing:

            doc = frappe.get_doc({
                "doctype": "Monitoring Group",
                "group_name": group["name"],
                "group_id": group["groupid"]
            })

            doc.insert(
                ignore_permissions=True
            )

    frappe.db.commit()

    return "Groups Synced Successfully"