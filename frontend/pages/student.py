import streamlit as st
import pandas as pd
from services.api import submit_od, get_my_ods

def student_page():
    st.title("🎓 Student OD Request")

    with st.form("od_form"):
        od_date = st.date_input("OD Date")
        duration = st.selectbox("Duration", ["Half Day", "Full Day"])
        reason = st.text_area("Reason")
        submitted = st.form_submit_button("Submit OD")

        if submitted:
            res = submit_od(
                st.session_state.token,
                {
                    "od_date": str(od_date),
                    "duration": duration,
                    "reason": reason
                }
            )
            if res.status_code == 200:
                st.success("OD submitted successfully")
            else:
                st.error(res.text)

    st.divider()
    st.subheader("📄 My OD Requests")

    res = get_my_ods(st.session_state.token)
    if res.status_code == 200:
        df = pd.DataFrame(res.json())
        st.dataframe(df, use_container_width=True)
    else:
        st.error("Unable to fetch OD requests")
