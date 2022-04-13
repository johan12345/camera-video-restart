Lumix Video Restart
===================

I use a Panasonic Lumix G81 DLSM camera, not only for photography, but often also for video filming. Unfortunately, the European model of this and most similar cameras is limited to a continuous recording time of 30 minutes, which may not be enough in certain circumstances (e.g. when recording concerts or theatre performances). However, the camera can be controlled via Wi-Fi using an API that was [reverse-engineered here](https://www.personal-view.com/talks/discussion/6703/control-your-gh3-from-a-web-browser-now-with-video-/p1) and thankfully implemented in Python by [Michael Hand](https://github.com/palmdalian/python_lumix_control).

This simple script uses the abovementioned Python wrapper of the API to automatically restart the video recording on one of the compatible cameras automatically once the time limit has been reached. It also allows you to start and stop the recording from your phone or laptop using a web-based UI.

<img alt="Screenshot of the web UI" src="res/screenshot.png" width="300"/>

Intended use
------------

The script is intended to be installed on a portable device, such as a Raspberry Pi or a laptop, that is connected to the same Wi-Fi network as the camera. This network does not need to have internet access. The most convenient way is to set up a Raspberry Pi with integrated Wi-Fi to host its own wireless network that the camera can then be connected to. This can be configured using the `hostapd` package as described in various [guides](https://learn.sparkfun.com/tutorials/setting-up-a-raspberry-pi-3-as-an-access-point/all) on the internet.

To connect the script to the camera, make sure the camera always gets the same IP address.
If you're using `hostapd`, you can configure this in `/etc/dnsmasq.conf` by adding a line like this:
```
dhcp-host=AB:CD:EF:12:34:56,LUMIX,192.168.50.11
```
(replacing the first part with the actual MAC address of the camera).

To run the script as a service on Linux, use the following systemd configuration, saved in `/etc/systemd/system/lumix_video_restart.conf`:

```
[Unit]
Description=Runs Web UI on localhost:8000 to restart Lumix camera

[Service]
User=pi
WorkingDirectory=/home/pi/lumix_control
ExecStart=/home/pi/lumix_control/video_time_webui.py
Restart=always

[Install]
WantedBy=multi-user.target
```
The web UI should then be reachable on port 8000.


Open issues / possible improvements
-----------------------------------

This script was built as a single-use tool without high standards for code quality or flexibility. I have some ideas for additional features that would be useful to add, but currently no concrete plans to work on them. If you want to help, please feel free to send a PR!

- **Support for other camera models** - it might work, but I did not test it. I know that there are some deviations in the return values of the API for older cameras such as the GH3, so some changes may be needed for those.
- **Support for multiple cameras at the same time** is currently not implemented
- **Support for use with the camera's own hotspot** - may work, but has not been tested
- **Automatic discovery of camera IPs** is apparently possible through the SSDP protocol, but currently not implemented
- Live view of the camera stream through the web UI, additional camera settings, etc.

