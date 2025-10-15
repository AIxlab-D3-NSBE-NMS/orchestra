import os
import subprocess
import ipaddress
import requests

def ping_ip(ip_address, verbose=0):


    # example ping -c 1 192.168.10.1
    # response = os.system(f"ping -c 1 {ip_address}")
    # todo: replace ping with fping for faster execution. fping also supports
    # multiple arrays
    response = subprocess.run(["ping", "-c", "1", ip_address], stdout = subprocess.DEVNULL)

    #and then check the response...
    if verbose:
        if response.returncode == 0:
            print(f"{ip_address} is up!")
        else:
            print(f"{ip_address} is down!")

    return response.returncode

def who_is_online(ip_list, verbose=0):
    online_ips = []
    for ip in ip_list:
        if ping_ip(ip, verbose) == 0:
            online_ips.append(ip)
    return online_ips

def is_mediamtx_running(ip_address, port=9997, timeout=2):
    try:
        r = requests.get(f"http://{ip_address}:{port}/v3/config/global/get", 
                         timeout=timeout)
        return True
    except requests.exceptions.RequestException:
        return False
        return r.ok

def get_active_mediamtx_paths(ip_address, port=9997, timeout=2):
    paths = []
    try:
        r = requests.get(f"http://{ip_address}:{port}/v3/config/paths/list", timeout=timeout)
        number_of_active_paths = len(r.json()['items'])
        
        for ii in range(number_of_active_paths):
            paths.append(r.json()['items'][ii]['name'])
    except requests.exceptions.RequestException:
        print('failed to request')
    return paths

def get_path_config(ip_address, path_name, port=9997, timeout=2):
    try:
        r = requests.get(f"http://{ip_address}:{port}/v3/config/paths/get/{path_name}", timeout=timeout)
        if r.ok:
            return r.json()
        else:
            return None
    except requests.exceptions.RequestException:
        print('failed to request')
        return None

def get_path_record_status(ip_address, path_name, port=9997, timeout=2):
    rec = None
    try:
        rjson = get_path_config(ip_address, path_name, port, timeout)
        if rjson is not None:
            rec = rjson.get('record')
        else:
            print('failed to get path config')
    except requests.exceptions.RequestException:
        print('failed to request')
    return rec
    
def set_path_record_status(ip_address, path_name, enable, port=9997, timeout=2): 
    payload = {"record": bool(enable)}
    r = None
    try:
        r = requests.patch(
            f"http://{ip_address}:{port}/v3/config/paths/patch/{path_name}",
            json=payload,
            timeout=timeout,
        )
    except requests.exceptions.RequestException:
        print('failed to request')
    
    return r

def set_all_paths_record_status(ip_address, enable, port=9997, timeout=2):
    paths = get_active_mediamtx_paths(ip_address, port, timeout)
    responses = {}
    for path in paths:
        responses[path] = set_path_record_status(ip_address, path, enable, port, timeout)

