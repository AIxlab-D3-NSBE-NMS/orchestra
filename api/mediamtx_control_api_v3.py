from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import os

app = FastAPI()

# Load configuration from a JSON file
CONFIG_FILE = "config.json"

# Default configuration
default_config = {
    "record_base_path": "/home/labadmin/aixlab/data"
}

# Load or create config file
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = default_config
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# MediaMTX v3 Control API endpoints
GET_CONFIG_URL = "http://localhost:9997/v3/config/global/get"
SET_CONFIG_URL = "http://localhost:9997/v3/config/global/set"

class RecordControlRequest(BaseModel):
    path: str

@app.post("/record/start")
def start_recording(req: RecordControlRequest):
    try:
        current_config = requests.get(GET_CONFIG_URL).json()
        current_config.setdefault("paths", {}).setdefault(req.path, {})["record"] = True
        current_config["paths"][req.path]["recordPath"] = os.path.join(
            config["record_base_path"],
            f"{req.path}/%Y-%m-%d_%H-%M-%S-%f"
        )
        response = requests.post(SET_CONFIG_URL, json=current_config)
        response.raise_for_status()
        return {"message": f"Recording started for path '{req.path}'."}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/record/stop")
def stop_recording(req: RecordControlRequest):
    try:
        current_config = requests.get(GET_CONFIG_URL).json()
        current_config.setdefault("paths", {}).setdefault(req.path, {})["record"] = False
        response = requests.post(SET_CONFIG_URL, json=current_config)
        response.raise_for_status()
        return {"message": f"Recording stopped for path '{req.path}'."}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/record/status/{path}")
def get_recording_status(path: str):
    try:
        current_config = requests.get(GET_CONFIG_URL).json()
        path_config = current_config.get("paths", {}).get(path)
        if path_config is None:
            raise HTTPException(status_code=404, detail=f"Path '{path}' not found.")
        return {
            "path": path,
            "recording": path_config.get("record", False),
            "recordPath": path_config.get("recordPath", "not set")
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

