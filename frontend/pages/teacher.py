import streamlit as st
import pandas as pd
from services.api import get_pending_ods, approve_od, reject_od

def teacher_page():
    st.title("👨‍🏫 Teacher Dashboard")

    res = get_pending_ods(st.session_state.token, "TEACHER")
    if res.status_code != 200:
        st.error("Unable to fetch OD list")
        return

    df = pd.DataFrame(res.json())
    st.dataframe(df, use_container_width=True)

    st.subheader("Approve / Reject")

    od_id = st.number_input("OD ID", step=1)
    remarks = st.text_area("Remarks")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Approve"):
            approve_od(st.session_state.token, "TEACHER", od_id, remarks)
            st.success("Approved")

    with col2:
        if st.button("❌ Reject"):
            reject_od(st.session_state.token, "TEACHER", od_id, remarks)
            st.error("Rejected")
