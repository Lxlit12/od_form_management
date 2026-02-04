import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

def login(username, password):
    res = requests.post(
        f"{API_BASE}/login",
        json={"username": username, "password": password}
    )
    return res

def save_session(token, role):
    st.session_state.token = token
    st.session_state.role = role
    st.session_state.logged_in = True

def logout():
    for key in ["token", "role", "logged_in"]:
        if key in st.session_state:
            del st.session_state[key]
