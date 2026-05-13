import frappe
from datetime import datetime

from bcs_security.api.middleware import (
    zabbix_request
)


@frappe.whitelist()
def get_hosts():

    return frappe.get_all(

        "Monitoring Host",

        fields=[
            "name",
            "zabbix_host_id",
            "custom_zabbix_server",
            "custom_virtual_machine"
        ]
    )


@frappe.whitelist()
def get_metric_data(

    host_id,

    zabbix_server,

    metric_type,

    from_date=None,

    to_date=None
):

    # =========================
    # VALIDATION
    # =========================
    if not host_id or not zabbix_server:

        return {
            "labels": [],
            "values": []
        }

    # =========================
    # KEY MAP
    # =========================
    key_map = {

        "cpu": "system.cpu.util",

        "memory": "vm.memory.util",

        "disk": "vfs.fs.size[C:,pused]",

        "uptime": "system.uptime"
    }

    item_id = None

    # =========================
    # NETWORK METRIC
    # =========================
    if metric_type == "network":

        item_res = zabbix_request(

            "item.get",

            {
                "output": [
                    "itemid",
                    "key_"
                ],

                "hostids": host_id,

                "search": {
                    "key_": "net.if.in"
                },

                "searchWildcardsEnabled": True
            },

            zabbix_server
        )

        if not item_res.get("result"):

            return {
                "labels": [],
                "values": []
            }

        for item in item_res["result"]:

            key = item["key_"]

            if "[" in key and "," not in key:

                item_id = item["itemid"]

                break

    # =========================
    # OTHER METRICS
    # =========================
    else:

        key_name = key_map.get(metric_type)

        item_res = zabbix_request(

            "item.get",

            {
                "output": [
                    "itemid",
                    "key_"
                ],

                "hostids": host_id,

                "filter": {
                    "key_": key_name
                }
            },

            zabbix_server
        )

        if not item_res.get("result"):

            return {
                "labels": [],
                "values": []
            }

        item_id = item_res["result"][0]["itemid"]

    # =========================
    # ITEM CHECK
    # =========================
    if not item_id:

        return {
            "labels": [],
            "values": []
        }

    # =========================
    # TIME RANGE
    # =========================
    if from_date and to_date:

        time_from = int(

            datetime.strptime(
                from_date,
                "%Y-%m-%dT%H:%M"
            ).timestamp()
        )

        time_till = int(

            datetime.strptime(
                to_date,
                "%Y-%m-%dT%H:%M"
            ).timestamp()
        )

    else:

        time_till = int(
            datetime.now().timestamp()
        )

        time_from = time_till - 300

    # =========================
    # HISTORY TYPE
    # =========================
    history_type = 0

    if metric_type == "uptime":

        history_type = 3

    # =========================
    # GET HISTORY
    # =========================
    history_res = zabbix_request(

        "history.get",

        {
            "output": "extend",

            "history": history_type,

            "itemids": item_id,

            "time_from": time_from,

            "time_till": time_till,

            "sortfield": "clock",

            "sortorder": "ASC"
        },

        zabbix_server
    )

    labels = []

    values = []

    # =========================
    # FORMAT RESPONSE
    # =========================
    for row in history_res.get("result", []):

        labels.append(

            datetime.fromtimestamp(
                int(row["clock"])
            ).strftime("%H:%M:%S")
        )

        val = float(row["value"])

        if metric_type == "uptime":

            val = val / 3600

        values.append(val)

    return {

        "labels": labels,

        "values": values
    }