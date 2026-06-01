import os
from operator import index
import requests
import streamlit as st

STREAMING_PORT = 8888
API_PORT = 9997

# fixed list of candidate IPs
host_machines = ['192.168.10.2',
                 '192.168.10.3',
                 '192.168.10.4',
                 '192.168.10.5',
                 'fakehost_low_load']
paths = ['owl', 'screen', 'webcam']

vid_height = 198

# set payload directory:
payload_dir = '/home/labadmin/aixlab/code/orchestra/maestro/payloads'
global_cfg = os.path.join(payload_dir, 'globalconfig.json')
owl_cfg = os.path.join(payload_dir, 'owl.json')
screen_cfg = os.path.join(payload_dir, 'screen.json')
webcam_cfg = os.path.join(payload_dir, 'webcam.json')

rec_status_colors = {False: ':white_circle:', True: ':red_circle:'}


def update_record_status(path_idx, new_value, host):
    """Update recording status via API"""
    path = paths[path_idx]
    try:
        outcome = requests.patch(f'http://{host}:{API_PORT}/v3/config/paths/patch/{path}',
                                 json={'record': new_value})
        return outcome.status_code == 200
    except Exception as e:
        st.error(f"Error updating {path}: {e}")
        return False


def get_current_status(path, host):
    """Get current recording status from API"""
    try:
        rec_state = requests.get(f'http://{host}:{API_PORT}/v3/config/paths/get/{path}').json()['record']
        return rec_state
    except Exception as e:
        st.warning(f"Could not fetch status for {path}: {e}")
        return False


left, right = st.columns([1, 4])
with left:
    host = st.radio('Select host', host_machines, index=2)

with right:
    configcol, displaycol = st.columns([1, 2])
    with configcol:
        # OWL
        current_owl_status = get_current_status('owl', host)
        rec_btn_owl = st.toggle('record owl', value=current_owl_status, key='owl_toggle')
        status_placeholder_owl = st.empty()
        status_placeholder_owl.markdown(rec_status_colors[current_owl_status])

        if rec_btn_owl != current_owl_status:
            if update_record_status(0, rec_btn_owl, host):
                status_placeholder_owl.markdown(rec_status_colors[rec_btn_owl])

        st.segmented_control('owl_config', ['STANDBY', 'STREAM'],
                             selection_mode='single', default='STANDBY', label_visibility='hidden')
        st.divider()

        # SCREEN
        current_screen_status = get_current_status('screen', host)
        rec_btn_screen = st.toggle('record screen', value=current_screen_status, key='screen_toggle')
        status_placeholder_screen = st.empty()
        status_placeholder_screen.markdown(rec_status_colors[current_screen_status])

        if rec_btn_screen != current_screen_status:
            if update_record_status(1, rec_btn_screen, host):
                status_placeholder_screen.markdown(rec_status_colors[rec_btn_screen])

        st.segmented_control('screen_config', ['STANDBY', 'STREAM'],
                             selection_mode='single', default='STANDBY', label_visibility='hidden')
        st.divider()

        # WEBCAM
        current_webcam_status = get_current_status('webcam', host)
        rec_btn_webcam = st.toggle('record webcam', value=current_webcam_status, key='webcam_toggle')
        status_placeholder_webcam = st.empty()
        status_placeholder_webcam.markdown(rec_status_colors[current_webcam_status])

        if rec_btn_webcam != current_webcam_status:
            if update_record_status(2, rec_btn_webcam, host):
                status_placeholder_webcam.markdown(rec_status_colors[rec_btn_webcam])

        st.segmented_control('webcam_config', ['STANDBY', 'STREAM'],
                             selection_mode='single', default='STANDBY', label_visibility='hidden')

    with displaycol:
        st.components.v1.iframe(f'http://{host}:{STREAMING_PORT}/{paths[0]}', height=vid_height, scrolling=False)
        st.components.v1.iframe(f'http://{host}:{STREAMING_PORT}/{paths[1]}', height=vid_height, scrolling=False)
        st.components.v1.iframe(f'http://{host}:{STREAMING_PORT}/{paths[2]}', height=vid_height, scrolling=False)