#!/usr/bin/python3
from lumix_control import CameraControl
import xml.etree.ElementTree as ET
import datetime as dt
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

IP = "192.168.50.11"
state = {
    'should_record': False
}


def camera_control_thread(ip, state):
    control = CameraControl(ip)  # IP of camera

    while True:
        state['connected'] = False
        try:
            control.start_camera_control()
            state['connected'] = True
            
            while True:
                cam_state = ET.fromstring(control.get_state().text).find('state')
                remaining = dt.timedelta(seconds=int(cam_state.find('video_remaincapacity').text))
                rec = cam_state.find('rec').text == 'on'
                
                state['rec'] = rec
                state['remaining'] = remaining.total_seconds()
                
                if state['should_record']:
                    should_restart = not rec or remaining < dt.timedelta(seconds=10)
                    if should_restart:
                        print('restarting record for {}'.format(ip))
                        control.video_record_stop()
                        control.video_record_start()
                else:
                    if rec:
                        print('stopping recording for {}'.format(ip))
                        control.video_record_stop()   
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
        
thread = threading.Thread(target=camera_control_thread, args=(IP, state), daemon=True)
thread.start()
        
server = HTTPServer(("0.0.0.0", 8000), WebUiServer)
print("Server starting")

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
    
server.server_close()
print("Server stopped")




