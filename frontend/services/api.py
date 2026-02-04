import requests

API_BASE = "http://127.0.0.1:8000"

def auth_header(token):
    return {"Authorization": f"Bearer {token}"}

# -------- STUDENT --------
def submit_od(token, data):
    return requests.post(
        f"{API_URL}/od/student",
        json=data,
        headers=auth_header(token)
    )

def get_my_ods(token):
    return requests.get(
        f"{API_BASE}/od/my",
        headers=auth_header(token)
    )

# -------- TEACHER / HOD / DEAN --------
def get_pending_ods(token, role):
    return requests.get(
        f"{API_BASE}/{role.lower()}/pending",
        headers=auth_header(token)
    )

def approve_od(token, role, od_id, remarks=""):
    return requests.post(
        f"{API_BASE}/{role.lower()}/approve",
        json={"od_id": od_id, "remarks": remarks},
        headers=auth_header(token)
    )

def reject_od(token, role, od_id, remarks):
    return requests.post(
        f"{API_BASE}/{role.lower()}/reject",
        json={"od_id": od_id, "remarks": remarks},
        headers=auth_header(token)
    )
