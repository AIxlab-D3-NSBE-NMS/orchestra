from fastapi import FastAPI
import httpx

app = FastAPI()

AGENT_ENDPOINTS = [
    "http://localhost:8001",
    "http://localhost:8002",
]

@app.post("/start_all")
async def start_all():
    results = []
    async with httpx.AsyncClient() as client:
        for url in AGENT_ENDPOINTS:
            try:
                response = await client.post(f"{url}/start")
                results.append({url: response.json()})
            except Exception as e:
                results.append({url: f"Error: {str(e)}"})
    return {"start_results": results}

@app.post("/stop_all")
async def stop_all():
    results = []
    async with httpx.AsyncClient() as client:
        for url in AGENT_ENDPOINTS:
            try:
                response = await client.post(f"{url}/stop")
                results.append({url: response.json()})
            except Exception as e:
                results.append({url: f"Error: {str(e)}"})
    return {"stop_results": results}

@app.get("/status_all")
async def status_all():
    results = []
    async with httpx.AsyncClient() as client:
        for url in AGENT_ENDPOINTS:
            try:
                response = await client.get(f"{url}/status")
                results.append({url: response.json()})
            except Exception as e:
                results.append({url: f"Error: {str(e)}"})
    return {"status_results": results}

# uvicorn controller:app --port 8000
