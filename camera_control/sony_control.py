from urllib.parse import urlparse

import requests
from ssdpy import SSDPClient

from camera_control import CameraControl
import xml.etree.ElementTree as ET


class SonyCameraControl(CameraControl):
    """
    Camera controller for Sony Alpha cameras

    API from https://developer.sony.com/develop/cameras/
    Python implementation based on https://github.com/petabite/libsonyapi
    """
    def __init__(self, cam_url):
        self.cam_url = cam_url

    @classmethod
    def discover(cls):
        client = SSDPClient()
        devices = client.m_search('urn:schemas-sony-com:service:ScalarWebAPI:1')
        urls = []
        for device in devices:
            cam_url = urlparse(device["location"])
            urls.append(cam_url)
        return urls

    def __enter__(self):
        device_xml_request = requests.get(self.cam_url)
        xml_file = str(device_xml_request.content.decode())
        xml = ET.fromstring(xml_file)
        name = xml.find(
            "{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-upnp-org:device-1-0}friendlyName"
        ).text
        api_version = xml.find(
            "{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-sony-com:av}X_ScalarWebAPI_DeviceInfo/{urn:schemas-sony-com:av}X_ScalarWebAPI_Version"
        ).text
        service_list = xml.find(
            "{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-sony-com:av}X_ScalarWebAPI_DeviceInfo/{urn:schemas-sony-com:av}X_ScalarWebAPI_ServiceList"
        )
