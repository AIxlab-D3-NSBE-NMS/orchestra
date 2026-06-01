
def get_ip_list_local():
    ip_preppend = '192.168.10.'
    ip_list = [ip_preppend + str(i) for i in range(1, 23)]
    return ip_list

class ExperimentConfig:
    ip_list = get_ip_list_local()
    mediamtx_api_port       = 9997
    streaming_rtsp_port     = 8853
    streaming_webrtc_port   = 8889