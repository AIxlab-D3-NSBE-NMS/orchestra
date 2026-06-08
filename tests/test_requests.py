"""
Probe and patch MediaMTX API path configuration for manual testing.

Inputs:
    Hard-coded MediaMTX API URLs and local JSON output/input file paths.

Expected output:
    Writes path configuration JSON files and patches the owl path from disk.
"""

import requests
import json
import sys

if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
    print(__doc__.strip())
    raise SystemExit(0)
# url = 'http://192.168.10.2:9997/v3/config/global/get'
url = 'http://192.168.10.2:9997/v3/config/paths/list'

response = requests.get(url, verify=False)

streaming_config = '/home/labadmin/code/orchestra/tests/streaming_config.json'
json.dump(response.json(), open(streaming_config, "w"), indent=2)

json.dump(requests.get('http://192.168.10.2:9997/v3/config/paths/get/owl').json(), 
    open('/home/labadmin/code/orchestra/tests/owl.json', "w"), indent=2)

json.dump(requests.get('http://192.168.10.2:9997/v3/config/paths/get/webcam').json(),
open('/home/labadmin/code/orchestra/tests/webcam.json', "w"), indent=2)

json.dump(requests.get('http://192.168.10.2:9997/v3/config/paths/get/screen').json(),
    open('/home/labadmin/code/orchestra/tests/screen.json', "w"), indent=2)

requests.patch('http://192.168.10.2:9997/v3/config/paths/patch/owl', 
               json.load(open('/home/labadmin/code/orchestra/tests/owl.json')))