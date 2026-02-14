#!/usr/bin/env python3
"""
Oracle Fusion Cloud Deployment Health Check Script
This script performs basic health checks for Fusion managed servers and deployments.
It checks connectivity, authentication, API version, and alerts.
Customize BASE_URL, USERNAME, PASSWORD with your Fusion instance details.
Requires 'requests' library: pip install requests
"""

import requests
import json
import sys
from datetime import datetime

# Configuration - Replace with your actual values
BASE_URL = "https://yourcompany.fa.us2.oraclecloud.com"  # e.g., https://fa-abc-123.fa.us2.oraclecloud.com
USERNAME = "your_username"
PASSWORD = "your_password"
# For OAuth, you'd need to implement token fetch; this uses basic auth for simplicity

def make_request(endpoint, auth_required=True):
    """Helper to make authenticated or unauthenticated request."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    try:
        if auth_required:
            response = requests.get(url, auth=(USERNAME, PASSWORD), headers=headers, timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30)
        return response
    except requests.exceptions.RequestException as e:
        return None, str(e)

def check_connectivity():
    """Check basic connectivity to Fusion base URL."""
    response, error = make_request("/", auth_required=False)
    if error:
        return {"check": "Connectivity", "status": "FAIL", "details": error}
    if response and response.status_code == 200:
        return {"check": "Connectivity", "status": "PASS", "details": "Base URL reachable"}
    return {"check": "Connectivity", "status": "FAIL", "details": f"Status: {response.status_code if response else 'No response'}"}

def check_authentication():
    """Check authentication by attempting to access a protected endpoint (e.g., user profile)."""
    # Use a simple protected endpoint; adjust as needed
    response, error = make_request("/fscmRestApi/resources/11.13.18.05/userProfiles", auth_required=True)
    if error:
        return {"check": "Authentication", "status": "FAIL", "details": error}
    if response and response.status_code == 200:
        return {"check": "Authentication", "status": "PASS", "details": "Auth successful, user profile accessible"}
    return {"check": "Authentication", "status": "FAIL", "details": f"Status: {response.status_code if response else 'No response'}"}

def check_api_version():
    """Check API version availability (indicates server health)."""
    response, error = make_request("/fscmRestApi/resources/version", auth_required=True)
    if error:
        return {"check": "API Version", "status": "FAIL", "details": error}
    if response and response.status_code == 200:
        version = response.text.strip()
        return {"check": "API Version", "status": "PASS", "details": f"Version: {version}"}
    return {"check": "API Version", "status": "FAIL", "details": f"Status: {response.status_code if response else 'No response'}"}

def check_alerts():
    """Check for critical alerts (basic deployment health indicator)."""
    response, error = make_request("/fscmRestApi/resources/latest/alerts?limit=5&orderBy=CreationDate:desc", auth_required=True)
    if error:
        return {"check": "Alerts", "status": "WARN", "details": f"Cannot fetch alerts: {error}"}
    if response and response.status_code == 200:
        alerts = response.json().get("items", [])
        critical = [a for a in alerts if a.get("severity") == "Critical"]
        if critical:
            return {"check": "Alerts", "status": "FAIL", "details": f"{len(critical)} critical alerts found"}
        return {"check": "Alerts", "status": "PASS", "details": "No critical alerts"}
    return {"check": "Alerts", "status": "FAIL", "details": f"Status: {response.status_code if response else 'No response'}"}

def check_deployments():
    """Placeholder for deployment health check. In Fusion Cloud, use specific module endpoints or OCI APIs."""
    # Example: Check a key module like ERP Financials
    response, error = make_request("/fscmRestApi/resources/11.13.18.05/journals", auth_required=True)
    if error:
        return {"check": "Deployments (ERP Example)", "status": "FAIL", "details": error}
    if response and response.status_code == 200:
        return {"check": "Deployments (ERP Example)", "status": "PASS", "details": "Key deployment endpoint accessible"}
    return {"check": "Deployments (ERP Example)", "status": "FAIL", "details": f"Status: {response.status_code if response else 'No response'}"}

def main():
    """Run all health checks and generate report."""
    if not all([BASE_URL, USERNAME, PASSWORD]):
        print("Error: Please update BASE_URL, USERNAME, PASSWORD in the script.")
        sys.exit(1)

    checks = [
        check_connectivity(),
        check_authentication(),
        check_api_version(),
        check_alerts(),
        check_deployments()
    ]

    report = {
        "timestamp": datetime.now().isoformat(),
        "fusion_url": BASE_URL,
        "health_checks": checks,
        "overall_status": "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL" if any(c["status"] == "FAIL" for c in checks) else "WARN"
    }

    # Output to console
    print(json.dumps(report, indent=2))
    
    # Save to file
    with open("fusion_health_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print("Health check report saved to fusion_health_report.json")

if __name__ == "__main__":
    main()