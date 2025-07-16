from fastapi import FastAPI
from enum import Enum

app = FastAPI(title="Acquisition Agent")

class AcquisitionState(str, Enum):
    STANDBY     = "standby"
    STREAMING   = "streaming"
    RUNNING     = "running"

state = {"status": AcquisitionState.STANDBY}

@app.post("/start")
def start_acquisition():
    if state["status"] == AcquisitionState.RUNNING:
        return {"message": "Acquisition is already running."}
    state["status"] = AcquisitionState.RUNNING
    print("Acquisition started.")
    return {"message": "Acquisition started."}

@app.post("/stop")
def stop_acquisition():
    if state["status"] == AcquisitionState.STANDBY:
        return {"message": "Acquisition is already stopped."}
    state["status"] = AcquisitionState.STANDBY
    print("Acquisition stopped.")
    return {"message": "Acquisition stopped."}

@app.get("/status")
def get_status():
    return {"status": state["status"]}


#
# uvicorn agent:app --port 8001
# uvicorn agent:app --port 8002
