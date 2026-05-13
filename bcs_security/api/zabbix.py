import frappe
from datetime import datetime
import pytz

from bcs_security.api.middleware import zabbix_request


# =========================
# CREATE HOST
# =========================
def create_zabbix_host(hostname, ip, os_type, zabbix_server=None):

    settings = frappe.get_doc("Monitoring Settings", zabbix_server)

    template_id = (
        settings.windows_template_id
        if os_type == "windows"
        else settings.linux_template_id
    )

    params = {
        "host": hostname,
        "interfaces": [
            {
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": ip,
                "dns": "",
                "port": "10050"
            }
        ],
        "groups": [{"groupid": "6"}]
    }

    if template_id:
        params["templates"] = [
            {"templateid": str(template_id)}
        ]

    result = zabbix_request(
        "host.create",
        params
    )

    return result


# =========================
# ENABLE / DISABLE HOST
# =========================
def update_zabbix_host_status(host_id, zabbix_server=None, enable=True):

    params = {
        "hostid": str(host_id),
        "status": 0 if enable else 1
    }

    result = zabbix_request(
        "host.update",
        params
    )

    return result


# =========================
# CREATE MAINTENANCE
# =========================
def create_maintenance(
    host_id,
    name,
    active_since,
    active_till,
    custom_zabbix_server=None
):

    ist = pytz.timezone("Asia/Kolkata")
    utc = pytz.utc

    start_dt = ist.localize(
        datetime.strptime(
            str(active_since),
            "%Y-%m-%d %H:%M:%S"
        )
    ).astimezone(utc)

    end_dt = ist.localize(
        datetime.strptime(
            str(active_till),
            "%Y-%m-%d %H:%M:%S"
        )
    ).astimezone(utc)

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    params = {
        "name": name or f"Maintenance-{host_id}",
        "active_since": start_ts,
        "active_till": end_ts,
        "hosts": [
            {"hostid": str(host_id)}
        ],
        "timeperiods": [
            {
                "timeperiod_type": 0,
                "start_date": start_ts,
                "period": end_ts - start_ts
            }
        ]
    }

    result = zabbix_request(
        "maintenance.create",
        params
    )

    frappe.log_error(
        str(result),
        "Zabbix Maintenance API"
    )

    return result


import frappe
from datetime import datetime
import pytz

from bcs_security.api.middleware import zabbix_request


# =========================
# CREATE HOST
# =========================
def create_zabbix_host(hostname, ip, os_type, zabbix_server=None):

    settings = frappe.get_doc("Monitoring Settings", zabbix_server)

    template_id = (
        settings.windows_template_id
        if os_type == "windows"
        else settings.linux_template_id
    )

    params = {
        "host": hostname,
        "interfaces": [
            {
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": ip,
                "dns": "",
                "port": "10050"
            }
        ],
        "groups": [{"groupid": "6"}]
    }

    if template_id:
        params["templates"] = [
            {"templateid": str(template_id)}
        ]

    result = zabbix_request(
        "host.create",
        params
    )

    return result


# =========================
# ENABLE / DISABLE HOST
# =========================
def update_zabbix_host_status(host_id, zabbix_server=None, enable=True):

    params = {
        "hostid": str(host_id),
        "status": 0 if enable else 1
    }

    result = zabbix_request(
        "host.update",
        params
    )

    return result


# =========================
# CREATE MAINTENANCE
# =========================
def create_maintenance(
    host_id,
    name,
    active_since,
    active_till,
    custom_zabbix_server=None
):

    ist = pytz.timezone("Asia/Kolkata")
    utc = pytz.utc

    start_dt = ist.localize(
        datetime.strptime(
            str(active_since),
            "%Y-%m-%d %H:%M:%S"
        )
    ).astimezone(utc)

    end_dt = ist.localize(
        datetime.strptime(
            str(active_till),
            "%Y-%m-%d %H:%M:%S"
        )
    ).astimezone(utc)

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    params = {
        "name": name or f"Maintenance-{host_id}",
        "active_since": start_ts,
        "active_till": end_ts,
        "hosts": [
            {"hostid": str(host_id)}
        ],
        "timeperiods": [
            {
                "timeperiod_type": 0,
                "start_date": start_ts,
                "period": end_ts - start_ts
            }
        ]
    }

    result = zabbix_request(
        "maintenance.create",
        params
    )

    frappe.log_error(
        str(result),
        "Zabbix Maintenance API"
    )

    return result


# =========================
# CREATE GROUP MAINTENANCE
# =========================
def create_group_maintenance(
    group_id,
    name,
    active_since,
    active_till,
    custom_zabbix_server=None
):

    ist = pytz.timezone("Asia/Kolkata")
    utc = pytz.utc

    start_dt = ist.localize(
        datetime.strptime(
            str(active_since),
            "%Y-%m-%d %H:%M:%S"
        )
    ).astimezone(utc)

    end_dt = ist.localize(
        datetime.strptime(
            str(active_till),
            "%Y-%m-%d %H:%M:%S"
        )
    ).astimezone(utc)

    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    params = {
        "name": name or f"Group-Maintenance-{group_id}",

        "active_since": start_ts,

        "active_till": end_ts,

        "groups": [
            {
                "groupid": str(group_id)
            }
        ],

        "timeperiods": [
            {
                "timeperiod_type": 0,
                "start_date": start_ts,
                "period": end_ts - start_ts
            }
        ]
    }

    result = zabbix_request(
        "maintenance.create",
        params
    )

    frappe.log_error(
        message=str(result),
        title="Group Maintenance API"
    )

    return result