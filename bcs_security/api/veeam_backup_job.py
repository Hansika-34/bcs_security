# -*- coding: utf-8 -*-

import frappe
import requests
import json
import re

TIMEOUT_SHORT = 30
TIMEOUT_LONG  = 300   # 5 min for restore ops


# -----------------------------------------------------------------------------
# Dynamic API URL
# -----------------------------------------------------------------------------
def get_base_url(backup_server):
    doc = frappe.get_doc("Backup Servers", backup_server)
    api_url = doc.custom_api_url
    if not api_url:
        raise Exception(f"No API URL configured for Backup Server: {backup_server}")
    return api_url.rstrip("/") + "/api/v1/veeam"


# -----------------------------------------------------------------------------
# Get Veeam Server IP (from Backup Servers doc)
# -----------------------------------------------------------------------------
def get_veeam_ip(backup_server):
    doc = frappe.get_doc("Backup Servers", backup_server)
    ip = doc.custom_backup_url
    if not ip:
        raise Exception(f"No Backup URL/IP configured for Backup Server: {backup_server}")
    return ip.strip()


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _safe_text(res):
    raw = res.content
    try:
        text = raw.decode("windows-1252")
    except Exception:
        text = raw.decode("latin-1")
    text = text.encode("utf-8", errors="replace").decode("utf-8")
    return text


_WIN1252_FIXUPS = str.maketrans({
    "\u2013": "-", "\u2014": "-",
    "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2026": "...", "\u00a0": " ",
})


def _parse_response(res):
    text = _safe_text(res)
    text = re.sub(r'WARNING:[^\n]*\n?', '', text).strip()
    text = text.translate(_WIN1252_FIXUPS)
    for start_char in ('[', '{'):
        idx = text.find(start_char)
        if idx != -1:
            text = text[idx:]
            break
    if not text:
        return None
    return json.loads(text)


# -----------------------------------------------------------------------------
# Repositories
# -----------------------------------------------------------------------------
@frappe.whitelist()
def get_repositories(backup_server):
    BASE_URL = get_base_url(backup_server)
    veeam_ip = get_veeam_ip(backup_server)
    try:
        res = requests.get(
            f"{BASE_URL}/repositories",
            params={"backupServer": veeam_ip},
            timeout=TIMEOUT_SHORT
        )
        res.raise_for_status()
        data = _parse_response(res)
        if data is None:
            return {"status": "error", "message": "Empty response from server"}
        if isinstance(data, dict):
            data = [data]
        return {"status": "success", "data": data}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Repo Fetch Error")
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# Create Job
# -----------------------------------------------------------------------------
@frappe.whitelist()
def create_job(job_name, vm_name, repository, backup_server, retention_days=7):
    BASE_URL = get_base_url(backup_server)
    veeam_ip = get_veeam_ip(backup_server)
    try:
        try:
            retention_days = int(retention_days)
        except (TypeError, ValueError):
            retention_days = 7
        retention_days = max(1, min(retention_days, 365))

        payload = {
            "name":          job_name,
            "node":          vm_name,
            "storageVolume": repository,
            "retentionDays": retention_days,
            "backupServer":  veeam_ip
        }
        res = requests.post(f"{BASE_URL}/create-job", json=payload, timeout=TIMEOUT_LONG)
        return {
            "status":  "success" if res.status_code == 200 else "error",
            "message": _safe_text(res)
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Job Error")
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# Run Job
# -----------------------------------------------------------------------------
@frappe.whitelist()
def run_job(job_name, backup_server):
    BASE_URL = get_base_url(backup_server)
    veeam_ip = get_veeam_ip(backup_server)
    try:
        res = requests.post(
            f"{BASE_URL}/run-job",
            params={"jobName": job_name, "backupServer": veeam_ip},
            timeout=TIMEOUT_LONG
        )
        return {
            "status":  "success" if res.status_code == 200 else "error",
            "message": _safe_text(res)
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Run Job Error")
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# Job Status
# -----------------------------------------------------------------------------
@frappe.whitelist()
def get_job_status(job_name, backup_server):
    BASE_URL = get_base_url(backup_server)
    veeam_ip = get_veeam_ip(backup_server)
    try:
        res = requests.get(
            f"{BASE_URL}/job-status",
            params={"jobName": job_name, "backupServer": veeam_ip},
            timeout=TIMEOUT_SHORT
        )
        res.raise_for_status()
        return {"status": "success", "data": _parse_response(res)}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Job Status Error")
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# Restore Points
# -----------------------------------------------------------------------------
@frappe.whitelist()
def get_restore_points(vm_name, backup_server):
    BASE_URL = get_base_url(backup_server)
    veeam_ip = get_veeam_ip(backup_server)
    try:
        res = requests.get(
            f"{BASE_URL}/restore-points",
            params={"vmName": vm_name, "backupServer": veeam_ip},
            timeout=TIMEOUT_SHORT
        )
        res.raise_for_status()
        data = _parse_response(res)
        if data is None:
            return {"status": "error", "message": "Empty response from server"}
        if isinstance(data, dict):
            data = [data]
        return {"status": "success", "data": data}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Restore Points Error")
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# Restore Status
# -----------------------------------------------------------------------------
@frappe.whitelist()
def get_restore_status(vm_name, backup_server):
    BASE_URL = get_base_url(backup_server)
    veeam_ip = get_veeam_ip(backup_server)
    try:
        res = requests.get(
            f"{BASE_URL}/restore-status",
            params={"vmName": vm_name, "backupServer": veeam_ip},
            timeout=TIMEOUT_SHORT
        )
        res.raise_for_status()
        return {"status": "success", "data": _parse_response(res)}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Veeam: Restore Status Error")
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# Restore Guest Files  ? KEY FIX: destination_path now passed to API
# -----------------------------------------------------------------------------
@frappe.whitelist()
def restore_guest_files(restore_point_id, selected_paths, destination_path, backup_server):
    BASE_URL = get_base_url(backup_server)
    veeam_ip = get_veeam_ip(backup_server)
    try:
        paths = json.loads(selected_paths) if isinstance(selected_paths, str) else selected_paths
        if not paths:
            return {"status": "error", "message": "No files selected"}

        payload = {
            "restorePointId":  restore_point_id,
            "selectedFiles":   paths,
            "destinationPath": destination_path,   # ? passed to PS script
            "backupServer":    veeam_ip
        }
        res = requests.post(
            f"{BASE_URL}/restore-vm-files",
            json=payload,
            timeout=TIMEOUT_LONG
        )
        if res.status_code == 200:
            try:
                data = _parse_response(res)
            except Exception:
                data = _safe_text(res)

            # Parse per-file results for a clean UI response
            files = []
            if isinstance(data, dict) and "Files" in data:
                for f in (data.get("Files") or []):
                    files.append({
                        "path":    f.get("Path", ""),
                        "status":  f.get("Status", ""),
                        "message": f.get("Message", "")
                    })

            return {
                "status":        "success",
                "overallStatus": data.get("Status", "Unknown") if isinstance(data, dict) else "Unknown",
                "restoredCount": data.get("RestoredCount", 0)  if isinstance(data, dict) else 0,
                "failedCount":   data.get("FailedCount", 0)    if isinstance(data, dict) else 0,
                "files":         files,
                "data":          data
            }

        return {"status": "error", "message": _safe_text(res)}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Veeam: Restore Guest Files Error")
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# Browse Tree
# -----------------------------------------------------------------------------
@frappe.whitelist()
def browse_tree(restore_point_id, backup_server, parent_path=""):
    BASE_URL = get_base_url(backup_server)
    veeam_ip = get_veeam_ip(backup_server)
    try:
        params = {
            "restorePointId": restore_point_id,
            "backupServer":   veeam_ip
        }
        if parent_path:
            params["parentPath"] = parent_path
        res = requests.get(f"{BASE_URL}/browse-tree", params=params, timeout=TIMEOUT_LONG)
        res.raise_for_status()
        data = _parse_response(res)
        if data is None:
            return {"status": "success", "data": []}
        if isinstance(data, dict):
            data = [data]
        return {"status": "success", "data": data}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Veeam: Browse Tree Error")
        return {"status": "error", "message": str(e)}


# -----------------------------------------------------------------------------
# Schedule Job
# -----------------------------------------------------------------------------
@frappe.whitelist()
def schedule_job(job_name, enabled, backup_server,
                 schedule_type="Everyday", run_at_time="22:00", days=""):
    BASE_URL = get_base_url(backup_server)
    veeam_ip = get_veeam_ip(backup_server)
    try:
        days_list = [d.strip() for d in days.split(",") if d.strip()] if days else []
        payload = {
            "jobName":      job_name,
            "enabled":      frappe.utils.cint(enabled) == 1,
            "scheduleType": schedule_type,
            "runAtTime":    run_at_time,
            "days":         days_list,
            "backupServer": veeam_ip
        }
        res = requests.post(f"{BASE_URL}/schedule-job", json=payload, timeout=TIMEOUT_LONG)
        if res.status_code == 200:
            try:
                data = _parse_response(res)
            except Exception:
                data = _safe_text(res)
            return {"status": "success", "data": data}
        return {"status": "error", "message": _safe_text(res)}
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Schedule Job Error")
        return {"status": "error", "message": str(e)}