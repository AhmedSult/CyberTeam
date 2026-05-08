"""Streamlit Cloud entrypoint."""

import streamlit as st

from app import main


if __name__ == "__main__":
    st.set_page_config(
        page_title="درع سيبراني",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    main()
