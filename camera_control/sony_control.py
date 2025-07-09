import json
from urllib.parse import urlparse
import datetime as dt

import requests
import logging
from ssdpy import SSDPClient

from camera_control import CameraControl, CameraState
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


def _parse_list(data):
    return data.decode("utf-8").strip().split("\n")

def _parse_dict(data):
    return {it.split("=")[0]: it.split("=")[1] for it in _parse_list(data)[1:]}

class SonyCameraControl(CameraControl):
    """
    Camera controller for Sony Alpha cameras

    API from https://developer.sony.com/develop/cameras/
    Python implementation based on https://github.com/petabite/libsonyapi
    """
    def __init__(self, cam_url):
        self.cam_url = cam_url
        self.name = None

    @classmethod
    def discover(cls, iface="wlan0"):
        client = SSDPClient(iface=iface.encode("utf-8"))
        devices = client.m_search('urn:schemas-sony-com:service:ScalarWebAPI:1')
        urls = []
        for device in devices:
            cam_url = device["location"]
            urls.append(cam_url)
        return urls

        # subprocess.run(["wpa_cli", "-i", "wlan0", "p2p_find", "10"], capture_output=True, check=True)
        # sleep(10)
        # peers = _parse_list(subprocess.run(["wpa_cli", "-i", "wlan0", "p2p_peers"], capture_output=True, check=True).stdout)
        #
        # result = []
        # for peer in peers:
        #     info = _parse_dict(subprocess.run(["wpa_cli", "-i", "wlan0", "p2p_peer", peer], capture_output=True, check=True).stdout)
        #     if info["device_name"] == "ILCE-7M3":
        #         result.append(peer)
        #     print(info["oper_ssid"])
        # return result

    def __enter__(self):
        #status = subprocess.run(["wpa_cli", "-i", "wlan0", "p2p_connect", self.cam_mac, "pbc", "join"], capture_output=True, check=True).stdout
        #if status != "OK\n":
        #    raise IOError(f"Failed to connect to camera on {self.cam_mac}")

        device_xml_request = requests.get(self.cam_url)
        xml_file = str(device_xml_request.content.decode())
        xml = ET.fromstring(xml_file)
        self.name = xml.find(
            "{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-upnp-org:device-1-0}friendlyName"
        ).text
        self.name += " (" + urlparse(self.cam_url).netloc.split(':')[0] + ")"
        self.api_version = xml.find(
            "{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-sony-com:av}X_ScalarWebAPI_DeviceInfo/{urn:schemas-sony-com:av}X_ScalarWebAPI_Version"
        ).text
        service_list = xml.find(
            "{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-sony-com:av}X_ScalarWebAPI_DeviceInfo/{urn:schemas-sony-com:av}X_ScalarWebAPI_ServiceList"
        )
        self.api_service_urls = {}
        for service in service_list:
            service_type = service.find(
                "{urn:schemas-sony-com:av}X_ScalarWebAPI_ServiceType"
            ).text
            action_url = service.find(
                "{urn:schemas-sony-com:av}X_ScalarWebAPI_ActionList_URL"
            ).text
            self.api_service_urls[service_type] = action_url
        return self

    def prepare(self):
        pass

    def get_state(self) -> CameraState:
        result = self._post_request("getEvent", False, version="1.2")["result"]
        camera_status = result[1]["cameraStatus"]
        recording = camera_status in ["MovieWaitRecStart", "MovieRecording", "MovieWaitRecStop", "MovieSaving"]

        recording_time = result[57]["recordingTime"]
        time = dt.timedelta(minutes=30) - dt.timedelta(seconds=recording_time) if recording_time >= 0 else dt.timedelta(minutes=30)
        return CameraState(recording, time)

    def video_record_start(self):
        self._post_request("startMovieRec")

    def video_record_stop(self):
        self._post_request("stopMovieRec")

    def _post_request(self, method, *params, version="1.0"):
        """
        sends post request to url with method and param as json
        """
        url = self.api_service_urls["camera"] + "/camera"
        json_request = {"method": method, "params": params, "id": 1, "version": version}
        request = requests.post(url, json.dumps(json_request))
        response = json.loads(request.content)
        if "error" in list(response.keys()):
            logger.error("Error: ")
            logger.error(response)
        else:
            return response

    def __exit__(self, *args):
        pass
