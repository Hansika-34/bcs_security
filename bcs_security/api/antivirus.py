import frappe
import subprocess
import time
import re
import json
import requests


def run_ps(target, command, username=None, password=None):
    """
    Run PowerShell command remotely via WinRM.
    target = Hyper-V node (CHYPERV02), not guest VM IP
    """

    if username and password:
        credential_block = f"""
        $pass = ConvertTo-SecureString '{password}' -AsPlainText -Force
        $cred = New-Object System.Management.Automation.PSCredential('{username}', $pass)

        Invoke-Command -ComputerName {target} -Credential $cred -ScriptBlock {{
            {command}
        }}
        """
    else:
        credential_block = f"""
        Invoke-Command -ComputerName {target} -ScriptBlock {{
            {command}
        }}
        """

    result = subprocess.run(
        ["pwsh", "-Command", credential_block],
        capture_output=True,
        text=True,
        timeout=180
    )

    return result.stdout, result.stderr


def wait_for_provisioned(vm_name, max_wait_seconds=600, interval=15):

    attempts = max_wait_seconds // interval

    for _ in range(attempts):

        doc = frappe.get_doc("Virtual Machine", vm_name)

        if doc.custom_provision_status == "Provisioned":
            return True

        if doc.custom_provision_status == "Failed":
            return False

        time.sleep(interval)

    return False


def fetch_vm_ip(doc):
    try:
        url = f"http://103.231.215.171:5078/api/v1/vms/ip/{doc.custom_nodes}/{doc.vm_name}"
        r = requests.get(url, timeout=50)

        if r.status_code != 200:
            return None

        data = r.json()
        ips = json.loads(data) if isinstance(data, str) else data

        for ip in ips:
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                doc.db_set("custom_ip", ip)
                return ip

    except Exception as e:
        frappe.log_error(str(e), "AV Install - IP Fetch Failed")

    return None


def install_av_on_vm(vm_name):

    frappe.logger().info(f"[AV Install] Waiting for VM {vm_name} to be provisioned...")

    provisioned = wait_for_provisioned(vm_name)

    if not provisioned:
        frappe.log_error(
            f"VM {vm_name} did not reach Provisioned state.",
            "AV Install Timeout"
        )
        frappe.db.set_value(
            "Virtual Machine",
            vm_name,
            "custom_antivirus_status",
            "Failed"
        )
        return

    vm = frappe.get_doc("Virtual Machine", vm_name)

    if not vm.custom_enable_antivirus:
        return

    if not vm.custom_antivirus_server:
        frappe.log_error(
            f"No AV server linked on {vm_name}",
            "AV Install Error"
        )
        vm.db_set("custom_antivirus_status","Failed")
        return

    # keep this if you still want to record VM IP
    #if not vm.custom_ip:
      #  fetch_vm_ip(vm)

    try:
        av = frappe.get_doc(
            "Antivirus Server",
            vm.custom_antivirus_server
        )

    except Exception as e:
        frappe.log_error(str(e), "AV Server Fetch Failed")
        vm.db_set("custom_antivirus_status","Failed")
        return

    if not av.installer_url:
        frappe.log_error(
            "Installer URL missing",
            "AV Install Error"
        )
        vm.db_set("custom_antivirus_status","Failed")
        return

    vm.db_set("custom_antivirus_status","Installing")

    username = getattr(av,"winrm_username",None) or None
    password = getattr(av,"winrm_password",None) or None

    # IMPORTANT CHANGE:
    # Use Hyper-V node instead of unreachable guest IP
    hyperv_node = "45.198.60.23"
    install_command = f"""
        $url = "{av.installer_url}"
        $output = "C:\\temp\\av_installer.exe"

        New-Item -ItemType Directory -Force -Path "C:\\temp" | Out-Null

        Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing

        if (-not (Test-Path $output)) {{
            throw "Download failed"
        }}

        $proc = Start-Process `
            -FilePath $output `
            -ArgumentList "/s" `
            -Wait `
            -PassThru

        if ($proc.ExitCode -ne 0) {{
            throw "Installer exited with code $($proc.ExitCode)"
        }}

        Write-Host "Install successful"
    """

    try:

        stdout, stderr = run_ps(
            hyperv_node,
            install_command,
            username=username,
            password=password
        )

        frappe.log_error(
            f"Node: {hyperv_node}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}",
            "AV Install Logs"
        )

        if stderr and "error" in stderr.lower():
            raise Exception(stderr)

        if "failed" in stdout.lower():
            raise Exception(stdout)

        vm.db_set("custom_antivirus_status","Installed")

    except subprocess.TimeoutExpired:

        frappe.log_error(
            f"PowerShell timeout for {vm_name}",
            "AV Install Timeout"
        )

        vm.db_set("custom_antivirus_status","Failed")

    except Exception as e:

        frappe.log_error(
            str(e),
            "AV Install Failed"
        )

        vm.db_set("custom_antivirus_status","Failed")


import frappe
import requests


@frappe.whitelist()
def sync_license(docname):

    # ----------------------------------------
    # GET ANTIVIRUS SERVER DOC
    # ----------------------------------------

    doc = frappe.get_doc(
        "Antivirus Server",
        docname
    )

    # ----------------------------------------
    # VALIDATE API URL
    # ----------------------------------------

    if not doc.custom_api_url:
        frappe.throw(
            "API URL not configured"
        )

    # ----------------------------------------
    # API ENDPOINT
    # ----------------------------------------

    api_url = (
        f"{doc.custom_api_url}"
        "/api/v1/av-license"
    )

    # ----------------------------------------
    # PAYLOAD
    # ----------------------------------------

    payload = {
        "serverIp": doc.server_ip
    }

    # ----------------------------------------
    # CALL API
    # ----------------------------------------

    response = requests.post(
        api_url,
        json=payload,
        timeout=60
    )

    if response.status_code != 200:

        frappe.throw(response.text)

    data = response.json()

    # ----------------------------------------
    # UPDATE LICENSE FIELDS
    # ----------------------------------------

    doc.company_name = data.get(
        "companyName"
    )

    doc.product_name = data.get(
        "productName"
    )

    doc.product_key = data.get(
        "productKey"
    )

    doc.product_type = data.get(
        "productType"
    )

    doc.installation_number = data.get(
        "installationNumber"
    )

    doc.license_valid_till = data.get(
        "licenseValidTill"
    )

    doc.entitled_licenses = data.get(
        "entitledLicenses"
    )

    doc.used_licenses = data.get(
        "usedLicenses"
    )

    doc.remaining_licenses = data.get(
        "remainingLicenses"
    )

    doc.last_sync_time = frappe.utils.now()

    doc.save(ignore_permissions=True)

    return {
        "success": True,
        "message": "License synced successfully"
    }