import typer
from typing import Optional
from rich.console import Console
import requests
import maestro.maestro_utils as maestro_utils
import json

app = typer.Typer()
console = Console()

@app.command()
def isonline(ip_addr: str):
    if maestro_utils.is_mediamtx_running(ip_addr):
        console.print(f"mediaMTX is UP and running on {ip_addr}")
    else:
        console.print(f"{ip_addr} DOWN")


@app.command()
def peek(ip_addr: str):
    console.print("Peeking into IP address", ip_addr, "...")
    # You'd also need to implement actual calls to the mediaMTX API here.

@app.command()
def recording_status(ipaddress: str):
    console.print("Checking recording status for IP address", ipaddress, "...")
    # And again, actual API calls would be needed here.

@app.command()
def recording_start(ipaddress: str):
    console.print("Starting recording for IP address", ipaddress, "...")
    # Here you'd actually call the mediaMTX API to start recording.

@app.command()
def recording_stop(ipaddress: str):
    console.print("Stopping recording for IP address", ipaddress, "...")
    # And here you would make actual calls to stop recording on the mediaMTX API.

if __name__ == '__main__':
    app()
