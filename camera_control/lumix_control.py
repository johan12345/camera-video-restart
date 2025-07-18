from urllib.parse import urlparse

import requests as r
from ssdpy import SSDPClient

from . import CameraControl, CameraState
import xml.etree.ElementTree as ET
import datetime as dt
import logging

logger = logging.getLogger(__name__)


class LumixCameraControl(CameraControl):
    """
    Camera controller for Panasonic Lumix cameras

    API discovered here: https://www.personal-view.com/talks/discussion/6703/control-your-gh3-from-a-web-browser-now-with-video-/p1
    Python implementation based on https://github.com/palmdalian/python_lumix_control
    """

    def __init__(self, cam_ip):
        self.cam_ip = cam_ip
        self.baseurl = "http://" + self.cam_ip + "/cam.cgi"
        self.name = f"Panasonic ({self.cam_ip})"

    @classmethod
    def discover(cls, iface=None):
        client = SSDPClient(iface=iface.encode("utf-8"))
        devices = client.m_search('urn:schemas-upnp-org:service:ContentDirectory:1')
        ips = []
        for device in devices:
            if "Panasonic-UPnP" in device["server"]:
                ip, port = urlparse(device["location"]).netloc.split(':')
                ips.append(ip)
        return ips

    def __enter__(self):
        resp = r.get(self.baseurl, params={"mode": "camcmd", "value": "recmode"})
        self._check_response(resp)
        return self

    def __exit__(self, *args):
        pass

    def prepare(self):
        try:
            # set Cinelike D profile
            self.set_color_mode('cinelike_d')
        except:
            pass

    def get_state(self):
        cam_state = ET.fromstring(self._get_state().text).find('state')
        remaining = dt.timedelta(seconds=int(cam_state.find('video_remaincapacity').text))

        rec_elem = cam_state.find('rec')
        if rec_elem is not None:
            # G81
            rec = rec_elem.text == 'on'
        else:
            # GH3
            rec = None

        return CameraState(rec, remaining)

    def start_stream(self, upd_port):
        resp = r.get(self.baseurl, params={"mode": "startstream", "value": str(upd_port)})
        self._check_response(resp)

    def stop_stream(self):
        resp = r.get(self.baseurl, params={"mode": "stopstream"})
        self._check_response(resp)

    def _get_info(self, setting):
        params = {"mode": "getinfo", "type": setting}
        resp = r.get(self.baseurl, params=params)
        return resp

    def _get_lens_info(self):
        # ?, max_fstop, min_fstop, max_shutter, min_shutter, ?, ?, max_zoom, min_zoom, ?, ?, ?
        resp = self._get_info("lens")
        return resp

    def _get_setting(self, setting):
        params = {"mode": "getsetting", "type": setting}
        resp = r.get(self.baseurl, params=params)
        return resp

    def _set_setting(self, settings):
        params = {"mode": "setsetting"}
        params.update(settings)
        resp = r.get(self.baseurl, params=params)
        self._check_response(resp)
        return resp

    def get_focus_mode(self):
        resp = self._get_setting("focusmode")
        return resp

    def get_focus_mag(self):
        resp = self._get_setting("mf_asst_mag")
        return resp

    def get_mf_asst_setting(self):
        resp = self._get_setting("mf_asst")
        return resp

    def set_iso(self, iso):
        if iso == "auto":
            iso = "50"
        self._set_setting({"type": "iso", "value": iso})

    def set_focal(self, focal):
        # 256 between full stops. The rest are third stops.
        # See http://c710720.r20.cf2.rackcdn.com/wp-content/uploads/2011/08/ISO-Shutter-Speeds-Fstops-Copyright-2009-2011-photographyuncapped.gif
        fstop = {
            "1": "0/256",
            "1.1": "85/256",
            "1.2": "171/256",
            "1.4": "256/256",
            "1.6": "341/256",
            "1.8": "427/256",
            "2": "512/256",
            "2.2": "597/256",
            "2.4": "640/256",
            "2.8": "768/256",
            "3.2": "853/256",
            "3.5": "939/256",
            "4": "1024/256",
            "4.5": "1110/256",
            "5": "1195/256",
            "5.6": "1280/256",
            "6.3": "1364/256",
            "7.1": "1451/256",
            "8": "1536/256",
            "9": "1621/256",
            "10": "1707/256",
            "11": "1792/256",
            "13": "1877/256",
            "14": "1963/256",
            "16": "2048/256",
            "18": "2133/256",
            "20": "2219/256",
            "22": "2304/256"
        }
        self._set_setting({"type": "focal", "value": fstop[focal]})

    def set_shutter(self, shutter):
        # 256 between full stops. 1 second is the pos/neg boundary
        # See http://c710720.r20.cf2.rackcdn.com/wp-content/uploads/2011/08/ISO-Shutter-Speeds-Fstops-Copyright-2009-2011-photographyuncapped.gif
        shutter_speed = {
            "4000": "3072/256",
            "3200": "2987/256",
            "2500": "2902/256",
            "2000": "2816/256",
            "1600": "2731/256",
            "1300": "2646/256",
            "1000": "2560/256",
            "800": "2475/256",
            "640": "2390/256",
            "500": "2304/256",
            "400": "2219/256",
            "320": "2134/256",
            "250": "2048/256",
            "200": "1963/256",
            "160": "1878/256",
            "125": "1792/256",
            "100": "1707/256",
            "80": "1622/256",
            "60": "1536/256",
            "50": "1451/256",
            "40": "1366/256",
            "30": "1280/256",
            "25": "1195/256",
            "20": "1110/256",
            "15": "1024/256",
            "13": "939/256",
            "10": "854/256",
            "8": "768/256",
            "6": "683/256",
            "5": "598/256",
            "4": "512/256",
            "3.2": "427/256",
            "2.5": "342/256",
            "2": "256/256",
            "1.6": "171/256",
            "1.3": "86/256",
            "1": "0/256",
            "1.3s": "-85/256",
            "1.6s": "-170/256",
            "2s": "-256/256",
            "2.5s": "-341/256",
            "3.2s": "-426/256",
            "4s": "-512/256",
            "5s": "-682/256",
            "6s": "-768/256",
            "8s": "-853/256",
            "10s": "-938/256",
            "13s": "-1024/256",
            "15s": "-1109/256",
            "20s": "-1194/256",
            "25s": "-1280/256",
            "30s": "-1365/256",
            "40s": "-1450/256",
            "50s": "-1536/256",
            "60s": "16384/256",
            "B": "256/256"
        }
        self._set_setting({"type": "shtrspeed", "value": shutter_speed[shutter]})

    def set_video_quality(self, quality="mp4ed_30p_100mbps_4k"):
        # mp4_24p_100mbps_4k / mp4_30p_100mbps_4k
        self._set_setting({"type": "videoquality", "value": quality})

    def set_color_mode(self, colormode='cinelike_d'):
        self._set_setting({
            'type': 'colormode',
            'value': colormode
        })

    def focus_control(self, direction="tele", speed="normal"):
        # tele or wide for direction, normal or fast for speed
        params = {"mode": "camctrl", "type": "focus", "value": direction + "-" + speed}
        resp = r.get(self.baseurl, params=params)
        return resp

    def rack_focus(self, start_point="current", end_point="0", speed="normal"):
        # tele or wide for direction, normal or fast for speed

        # Check where we are with a fine step
        resp = self.focus_control("tele", "normal").text
        current_position = int(resp.split(',')[1])

        if end_point == "current":
            end_point = current_position + 13

        # First get to the starting point if necessary
        if start_point == "current":
            start_point = current_position + 13
        elif int(start_point) < current_position:
            while current_position - int(start_point) > 13:
                resp = self.focus_control("tele", "fast").text
                current_position = int(resp.split(',')[1])
        else:
            while int(start_point) - current_position > 13:
                resp = self.focus_control("wide", "fast").text
                current_position = int(resp.split(',')[1])

        # At the start, now let's get to the end point
        start_point = int(start_point)

        threshold = 13
        if speed == "fast":
            threshold = 70

        if start_point > int(end_point):
            while current_position - int(end_point) > threshold:
                resp = self.focus_control("tele", speed).text
                current_position = int(resp.split(',')[1])
                if current_position - int(end_point) <= threshold:
                    # Fine focus for the last bit
                    threshold = 13
                    speed = "normal"
        else:
            while int(end_point) - current_position > threshold:
                resp = self.focus_control("wide", speed).text
                current_position = int(resp.split(',')[1])
                if int(end_point) - current_position <= threshold:
                    threshold = 13
                    speed = "normal"

    def capture_photo(self):
        params = {"mode": "camcmd", "value": "capture"}
        resp = r.get(self.baseurl, params=params)
        return resp

    def video_record_start(self):
        params = {"mode": "camcmd", "value": "video_recstart"}
        resp = r.get(self.baseurl, params=params)
        return resp

    def video_record_stop(self):
        params = {"mode": "camcmd", "value": "video_recstop"}
        resp = r.get(self.baseurl, params=params)
        return resp

    def _get_state(self):
        params = {"mode": "getstate"}
        resp = r.get(self.baseurl, params=params)
        return resp

    def _check_response(self, resp):
        if "<result>ok</result" not in resp.text:
            raise IOError(resp.text)
