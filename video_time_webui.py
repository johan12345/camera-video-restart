#!/usr/bin/python3

import datetime as dt
import json
import threading
import time
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, HTTPServer

from lumix_control import CameraControl

IP = ["192.168.50.11", "192.168.50.12"]
state = {
    'should_record': False,
    'cameras': {i: {} for i in IP}
}


def camera_control_thread(ip, state):
    control = CameraControl(ip)  # IP of camera

    while True:
        my_state = state['cameras'][ip]
        my_state['connected'] = False
        try:
            control.start_camera_control()
            my_state['connected'] = True

            try:
                # set Cinelike D profile
                control.set_setting({
                    'type': 'colormode',
                    'value': 'cinelike_d'
                })
            except:
                pass

            prev_remaining = dt.timedelta(hours=99)
            started = False
            while True:
                cam_state = ET.fromstring(control.get_state().text).find('state')
                remaining = dt.timedelta(seconds=int(cam_state.find('video_remaincapacity').text))

                rec_elem = cam_state.find('rec')
                if rec_elem is not None:
                    # G81
                    rec = rec_elem.text == 'on'
                else:
                    rec = None

                my_state['rec'] = rec
                my_state['remaining'] = remaining.total_seconds()

                should_record = state['should_record']
                if should_record:
                    if rec is not None:
                        # G81
                        should_restart = not rec or remaining < dt.timedelta(seconds=10)
                    else:
                        # GH3
                        should_restart = remaining > prev_remaining + dt.timedelta(minutes=1) or not started
                    if should_restart:
                        print('restarting record for {}'.format(ip))
                        try:
                            control.video_record_stop()
                        except:
                            pass
                        control.video_record_start()
                        started = True
                else:
                    if rec:
                        print('stopping recording for {}'.format(ip))
                        try:
                            control.video_record_stop()
                        except:
                            pass
                        started = False
                prev_remaining = remaining
                time.sleep(1)
        except:
            time.sleep(5)
            pass
    
    
class WebUiServer(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            with open("webui.html", "rb") as file:
                for line in file:
                    self.wfile.write(line)
        elif self.path == "/get_state":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(state), "utf-8"))
        else:
            self.send_response(404)
            
    def do_POST(self):
        if self.path == "/record":
            self.send_response(204)   
            self.end_headers() 
            data = self.rfile.read(int(self.headers['Content-Length']))
            if data == b'true':
                state['should_record'] = True
            elif data == b'false':
                state['should_record'] = False
        else:
            self.send_response(404)

for ip in IP:
    thread = threading.Thread(target=camera_control_thread, args=(ip, state), daemon=True)
    thread.start()
        
server = HTTPServer(("0.0.0.0", 8000), WebUiServer)
print("Server starting")

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
    
server.server_close()
print("Server stopped")




