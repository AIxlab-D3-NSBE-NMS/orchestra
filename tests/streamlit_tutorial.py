import pandas as pd  
import streamlit as st 
import requests
import json


cols = st.columns(3, gap='small')


samaritan = 'http://192.168.10.2'
selected_pc = samaritan
mediamtx_api_port = '9997'
API_BASE = selected_pc + ':' + mediamtx_api_port
mediamtx_url = selected_pc + ':' + mediamtx_api_port
streaming_port = '8889'
TIMEOUT = 3.0    
PATH = 'screen'                      

urls = [selected_pc + ':' + streaming_port + '/screen',
        selected_pc + ':' + streaming_port + '/webcam',
        selected_pc + ':' + streaming_port + '/owl']

# --- Helpers talking to MediaMTX API ---
def get_path_config(name: str) -> dict | None:
    try:
        r = requests.get(f"{API_BASE}/v3/config/paths/get/{name}", timeout=TIMEOUT)
        return r.json() if r.ok else None
    except Exception:
        return None
def get_path_runtime(name: str) -> dict | None:
    try:
        r = requests.get(f"{API_BASE}/v3/paths/get/{name}", timeout=TIMEOUT)
        return r.json() if r.ok else None
    except Exception:
        return None
def patch_record(name: str, enable: bool) -> tuple[int, str]:
    payload = {"record": bool(enable)}
    # When enabling, also ensure good defaults for precise, resilient recording
    # (idempotent; re-sending is harmless)
    if enable:
        payload.update({
            "recordFormat": "fmp4",                         # precise PTS/DTS, resilient
            "recordPath": "/home/labadmin/Desktop/video_test/media/%path/%Y-%m-%d_%H-%M-%S-%f",
            "recordSegmentDuration": "300s"                 # split into 5 min segments
        })
    try:
        r = requests.patch(
            f"{API_BASE}/v3/config/paths/patch/{name}",
            json=payload,
            timeout=TIMEOUT,
        )
        return r.status_code, r.text
    except Exception as e:
        return 599, str(e)
def compute_status(rec_enabled: bool, ready: bool) -> tuple[str, str]:
    """Returns (status_text, color)"""
    if rec_enabled and ready:
        return "ON", "green"
    if rec_enabled and not ready:
        return "ARMED", "gold"
    return "OFF", "crimson"

# --- Fetch current state ---
cfg = get_path_config(PATH) or {}
runtime = get_path_runtime(PATH) or {}
rec_enabled = bool(cfg.get("record", False))
ready = bool(runtime.get("ready", False))
status_text, color = compute_status(rec_enabled, ready)

st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:.75rem;">
        <div style="font-weight:600;">Recording status:</div>
        <span style="display:inline-block;padding:.2rem .6rem;border-radius:999px;
                     background:{color};color:white;min-width:4.5rem;text-align:center;">
            {status_text}
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns([1, 3])

with left:
    desired = st.toggle("Record", value=rec_enabled, help="Toggle recording for this path")

    if desired != rec_enabled:
        code, msg = patch_record(PATH, desired)
        if 200 <= code < 300:
            st.success("Recording setting updated.")
        else:
            st.error(f"Failed to update recording (HTTP {code}).")
        # Refresh state after change
        cfg = get_path_config(PATH) or {}
        runtime = get_path_runtime(PATH) or {}
        rec_enabled = bool(cfg.get("record", False))
        ready = bool(runtime.get("ready", False))
        status_text, color = compute_status(rec_enabled, ready)

with right:
    # Show quick diagnostics from API
    st.subheader("Diagnostics")
    st.json({
        "config.record": rec_enabled,
        "runtime.ready": ready,
        "runtime.tracks": runtime.get("tracks", []),
    })

# Small live badge refresh button
st.button("Refresh status", help="Re-read status from MediaMTX API")

r = {}
df = pd.DataFrame(
    {'Patch': ['webcam', 'owl', 'screen'],
     'payload': "{'name': 'screen', 'source': 'publisher', 'sourceFingerprint': '', \
                 'useAbsoluteTimestamp': True, 'record': False, \
                 'recordPath': './/home/labadmin/Desktop/video_test/media/%path/%Y-%m-%d_%H-%M-%S-%f', \
                 'recordFormat': 'fmp4', \
                 'runOnInit': '/home/labadmin/aixlab/code/orchestra/stream/mediamtx/ffmpeg -fflags +genpts -use_wallclock_as_timestamps 1 -f x11grab -video_size 3840x2400 -thread_queue_size 1024 -framerate 30 -i :0.0 -c:v h264_nvenc -preset p1 -g 30 -pix_fmt yuv420p -f rtsp -rtsp_transport tcp rtsp://localhost:8553/screen', \
                 'runOnInitRestart': True}"
    }
)

for col, url in zip(cols, urls):
    with col:
        st.caption(url.split(":" + streaming_port + "/")[-1])
        st.components.v1.iframe(url, height=150, scrolling=False) 
        st.write(url)

# st.components.v1.iframe('http://192.168.10.2:8889/screen', width=200)
# st.components.v1.iframe('http://192.168.10.2:8889/webcam',width=200)
# st.components.v1.iframe('http://192.168.10.2:8888/owl',width=200)




pressed = st.button('Get MEDIAMTX Configuration')
if pressed:
    r = requests.get(mediamtx_url + '/v3/config/paths/list').json()
    #r = requests.get('http://192.168.10.2:9997/v3/config/global/get').json()
    print(r)

result_display = st.json(r)

btw_screen_config = st.button('Patch screen configuration')
if btw_screen_config:
    requests.post('http://192.168.10.2:9997/v3/config/paths/add/webcam', 
        json=json.load(open('/home/labadmin/aixlab/code/orchestra/tests/webcam.json')))




st.subheader('config patches')
st.data_editor(df)



