import streamlit as st
import requests

API = "http://127.0.0.1:8000"

def run():
    st.title("FinNews Assistant")
    msg = st.text_input("Ask something about the news:")
    if st.button("Send") and msg:
        r = requests.post(f"{API}/chat", json={"user_id":"demo","message":msg}, timeout=30)
        st.write(r.json().get("reply","<no reply>"))

if __name__ == "__main__":
    run()
