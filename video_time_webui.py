#!/usr/bin/python3

import datetime as dt
import os
import threading
import time
import traceback
import re
from typing import Optional

from flask import Flask, request

from camera_control import CameraState
from camera_control.lumix_control import LumixCameraControl
from camera_control.sony_control import SonyCameraControl

camera_types = [LumixCameraControl, SonyCameraControl]


class App:
    def __init__(self, host="0.0.0.0", port=8000):
        self.should_record = False
        self._control_threads = {}
        self._discover_thread = threading.Thread(target=self._discover, daemon=True)
        self._host = host
        self._port = port

        interface_regex = re.compile(r"^(wlan|ap)\d+$")
        self._discover_interfaces = [dev for dev in os.listdir("/sys/class/net/") if interface_regex.match(dev)]
        print(f"discovering on interfaces: {self._discover_interfaces}")

        self._app = Flask(__name__)
        self._app.add_url_rule("/", view_func=self._serve_index)
        self._app.add_url_rule("/get_state", view_func=self._get_state)
        self._app.add_url_rule("/record", view_func=self._record, methods=['POST'])

    def run(self):
        self._discover_thread.start()
        self._app.run(self._host, self._port)

    def _serve_index(self):
        return self._app.send_static_file("webui.html")

    def _get_state(self):
        return {
            "should_record": self.should_record,
            "cameras": {
                self._control_threads[ip].cam_name: {
                    "connected": self._control_threads[ip].connected,
                    "rec": self._control_threads[ip].cam_state.recording if self._control_threads[ip].cam_state is not None else None,
                    "remaining": self._control_threads[ip].cam_state.remaining.total_seconds() if self._control_threads[ip].cam_state is not None and self._control_threads[ip].cam_state.remaining is not None else None,
                } for ip in self._control_threads
            }
        }

    def _record(self):
        data = request.data
        if data == b'true':
            self.should_record = True
        elif data == b'false':
            self.should_record = False
        return ""

    def _discover(self):
        while True:
            for type in camera_types:
                for interface in self._discover_interfaces:
                    try:
                        cam_ips = type.discover(iface=interface)
                        for cam_ip in cam_ips:
                            if cam_ip not in self._control_threads:
                                thread = CameraControlThread(self, cam_ip, type)
                                thread.start()
                                self._control_threads[cam_ip] = thread
                    except:
                        traceback.print_exc()

            time.sleep(10)


class CameraControlThread(threading.Thread):
    def __init__(self, app, ip, type):
        self.ip = ip
        self._control = type(ip)

        self.connected = False
        self.cam_state: Optional[CameraState] = None
        self.cam_name = None
        self._app = app

        super().__init__(name=f"{type.__name__}({ip})", daemon=True)

    def run(self):
        print(f"Camera control starting for {self.ip}")
        while True:
            self.connected = False
            try:
                with self._control:
                    self.connected = True
                    self.cam_name = self._control.name

                    self._control.prepare()

                    prev_remaining = dt.timedelta(hours=99)
                    started = False
                    while True:
                        self.cam_state = self._control.get_state()

                        should_record = self._app.should_record
                        if should_record:
                            should_restart = False
                            if self.cam_state.recording is not None:
                                # restart if recording has stopped or less than 10s remaining
                                should_restart = not self.cam_state.recording or self.cam_state.remaining is not None and self.cam_state.remaining < dt.timedelta(seconds=10)
                            elif self.cam_state.remaining is not None:
                                # restart if recording has not yet been started or remaining time has increased significantly
                                should_restart = self.cam_state.remaining > prev_remaining + dt.timedelta(
                                    minutes=1) or not started

                            if should_restart:
                                print('restarting recording for {}'.format(self.ip))
                                try:
                                    self._control.video_record_stop()
                                except:
                                    pass

                                self._control.video_record_start()
                                started = True
                        else:
                            if self.cam_state.recording or started:
                                print('stopping recording for {}'.format(self.ip))
                                try:
                                    self._control.video_record_stop()
                                except:
                                    pass
                                started = False
                        prev_remaining = self.cam_state.remaining
                        time.sleep(1)
            except:
                traceback.print_exc()
                time.sleep(5)
                pass


if __name__ == '__main__':
    App().run()
