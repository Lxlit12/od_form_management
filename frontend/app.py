import streamlit as st
import requests
import pandas as pd

API = "http://127.0.0.1:8000"

st.set_page_config(page_title="OD Management", layout="wide")

# ================= SESSION =================
if "token" not in st.session_state:
    st.session_state.token = None
if "role" not in st.session_state:
    st.session_state.role = None

# ================= LOGIN =================
if st.session_state.token is None:
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = requests.post(
            f"{API}/login",
            json={"username": username, "password": password}
        )
        if res.status_code == 200:
            data = res.json()
            st.session_state.token = data["access_token"]
            st.session_state.role = data["role"]
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ================= LOGOUT =================
st.sidebar.success(f"Logged in as {st.session_state.role}")
if st.sidebar.button("Logout"):
    st.session_state.token = None
    st.session_state.role = None
    st.rerun()

headers = {"Authorization": f"Bearer {st.session_state.token}"}

# ================= STUDENT DASHBOARD =================
if st.session_state.role == "STUDENT":
    st.header("🎓 Student Dashboard")

    with st.form("od_form"):
        od_date = st.date_input("OD Date")
        duration = st.selectbox("Duration", ["Half Day", "Full Day"])
        reason = st.text_area("Reason")
        submit = st.form_submit_button("Submit OD")

        if submit:
            r = requests.post(
                f"{API}/od/request",
                headers=headers,
                json={
                    "od_date": str(od_date),
                    "duration": duration,
                    "reason": reason
                }
            )
            if r.status_code == 200:
                st.success("OD submitted successfully")
            else:
                st.error(r.text)

    st.divider()
    st.subheader("My OD Requests")

    r = requests.get(f"{API}/od/student", headers=headers)
    if r.status_code == 200:
        st.dataframe(pd.DataFrame(r.json()), use_container_width=True)
    else:
        st.error("Unable to fetch OD history")

# ================= TEACHER DASHBOARD =================
elif st.session_state.role == "TEACHER":
    st.header("👨‍🏫 Teacher Dashboard")

    res = requests.get(f"{API}/od/teacher", headers=headers)
    ods = res.json()

    if not ods:
        st.success("No pending OD requests 🎉")
        st.stop()

    for od in ods:
        with st.expander(f"OD #{od['od_id']} | {od['reg_no']}"):
            st.write("📅 Date:", od["od_date"])
            st.write("⏱ Duration:", od["duration"])
            st.write("📝 Reason:", od["reason"])

            remarks = st.text_area("Remarks", key=f"t_{od['od_id']}")

            col1, col2 = st.columns(2)

            if col1.button("✅ Approve", key=f"ta_{od['od_id']}"):
                r = requests.post(
                    f"{API}/teacher/approve",
                    headers=headers,
                    json={"od_id": od["od_id"], "remarks": remarks}
                )
                if r.status_code == 200:
                    st.success("Approved & sent to HOD")
                    st.rerun()
                else:
                    st.error(r.text)

            if col2.button("❌ Reject", key=f"tr_{od['od_id']}"):
                if not remarks.strip():
                    st.warning("Remarks required")
                else:
                    r = requests.post(
                        f"{API}/teacher/reject",
                        headers=headers,
                        json={"od_id": od["od_id"], "remarks": remarks}
                    )
                    if r.status_code == 200:
                        st.error("OD Rejected")
                        st.rerun()
                    else:
                        st.error(r.text)

# ================= HOD DASHBOARD =================
elif st.session_state.role == "HOD":
    st.header("👨‍💼 HOD Dashboard")

    res = requests.get(f"{API}/od/hod", headers=headers)
    ods = res.json()

    if not ods:
        st.success("No pending ODs 🎉")
        st.stop()

    for od in ods:
        with st.expander(f"OD #{od['od_id']} | {od['reg_no']}"):
            st.write("📅 Date:", od["od_date"])
            st.write("⏱ Duration:", od["duration"])
            st.write("📝 Reason:", od["reason"])

            remarks = st.text_area("Remarks", key=f"h_{od['od_id']}")

            col1, col2 = st.columns(2)

            if col1.button("✅ Approve", key=f"ha_{od['od_id']}"):
                requests.post(
                    f"{API}/hod/approve",
                    headers=headers,
                    json={"od_id": od["od_id"], "remarks": remarks}
                )
                st.success("Approved & sent to Dean")
                st.rerun()

            if col2.button("❌ Reject", key=f"hr_{od['od_id']}"):
                requests.post(
                    f"{API}/hod/reject",
                    headers=headers,
                    json={"od_id": od["od_id"], "remarks": remarks}
                )
                st.error("OD Rejected")
                st.rerun()

# ================= DEAN DASHBOARD =================
elif st.session_state.role == "DEAN":
    st.header("🎓 Dean Dashboard")

    res = requests.get(f"{API}/od/dean", headers=headers)
    ods = res.json()

    if not ods:
        st.success("No pending ODs 🎉")
        st.stop()

    for od in ods:
        with st.expander(f"OD #{od['od_id']} | {od['reg_no']}"):
            st.write("📅 Date:", od["od_date"])
            st.write("⏱ Duration:", od["duration"])
            st.write("📝 Reason:", od["reason"])

            remarks = st.text_area("Remarks", key=f"d_{od['od_id']}")

            col1, col2 = st.columns(2)

            if col1.button("✅ Final Approve", key=f"da_{od['od_id']}"):
                requests.post(
                    f"{API}/dean/approve",
                    headers=headers,
                    json={"od_id": od["od_id"], "remarks": remarks}
                )
                st.success("OD Fully Approved")
                st.rerun()

            if col2.button("❌ Reject", key=f"dr_{od['od_id']}"):
                requests.post(
                    f"{API}/dean/reject",
                    headers=headers,
                    json={"od_id": od["od_id"], "remarks": remarks}
                )
                st.error("OD Rejected")
                st.rerun()

# ================= FALLBACK =================
else:
    st.info("No dashboard available for this role")
