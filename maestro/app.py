import pandas as pd  
import streamlit as st 
import streamlit_antd_components as sac
import requests
import json
import utils as mutils
import config as mconfig

st.title("Orchestra Control Panel")

left_panel, display_area = st.columns([1,3], ) # gap='small'

with left_panel:
    st.header("Devices")
    apilive = st.button("↻", use_container_width=True)

    st.divider()

    if apilive:
        st.write("Checking MediaMTX API...")
        devices = []
        for ip in mconfig.get_ip_list_local():
            if mutils.is_mediamtx_running(ip, port=mconfig.ExperimentConfig.mediamtx_api_port):
                devices.append(ip)
                st.write(f"Found {devices}")
    
