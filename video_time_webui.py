#!/usr/bin/python3

import datetime as dt
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from camera_control.lumix_control import LumixCameraControl

IP = ["192.168.50.11", "192.168.50.12"]
state = {
    'should_record': False,
    'cameras': {i: {} for i in IP}
}


def camera_control_thread(ip, state):
    control = LumixCameraControl(ip)

    while True:
        my_state = state['cameras'][ip]
        my_state['connected'] = False
        try:
            with control:
                my_state['connected'] = True

                control.prepare()

                prev_remaining = dt.timedelta(hours=99)
                started = False
                while True:
                    cam_state = control.get_state()

                    should_record = state['should_record']
                    if should_record:
                        should_restart = False
                        if cam_state.recording is not None:
                            # restart if recording has stopped or less than 10s remaining
                            should_restart = not cam_state.recording or cam_state.remaining < dt.timedelta(seconds=10)
                        elif cam_state.remaining is not None:
                            # restart if recording has not yet been started or remaining time has increased significantly
                            should_restart = cam_state.remaining > prev_remaining + dt.timedelta(minutes=1) or not started

                        if should_restart:
                            print('restarting recording for {}'.format(ip))
                            try:
                                control.video_record_stop()
                            except:
                                pass

                            control.video_record_start()
                            started = True
                    else:
                        if cam_state.recording or started:
                            print('stopping recording for {}'.format(ip))
                            try:
                                control.video_record_stop()
                            except:
                                pass
                            started = False
                    prev_remaining = cam_state.remaining
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

server_address = ("0.0.0.0", 8000)
server = HTTPServer(server_address, WebUiServer)
print(f"Server starting at http://{server_address[0]}:{server_address[1]}")

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
    
server.server_close()
print("Server stopped")




