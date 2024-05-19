Run:

    MAC_ADDRESS="$(cat /sys/class/net/wlan0/address)"
    # Populate `/etc/udev/rules.d/70-persistent-net.rules`
    sudo bash -c 'cat > /etc/udev/rules.d/70-persistent-net.rules' << EOF
    SUBSYSTEM=="ieee80211", ACTION=="add|change", ATTR{macaddress}=="${MAC_ADDRESS}", KERNEL=="phy0", \
      RUN+="/sbin/iw phy phy0 interface add ap0 type __ap", \
      RUN+="/bin/ip link set ap0 address ${MAC_ADDRESS}"
    EOF
    sudo reboot

    sudo nmcli con add con-name hotspot ifname ap0 type wifi ssid "<your SSID>"
    sudo nmcli con modify hotspot wifi-sec.key-mgmt wpa-psk
    sudo nmcli con modify hotspot wifi-sec.psk "<your password>"
    sudo nmcli con modify hotspot 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared
    sudo nmtui

Set hotspot IP to 192.168.4.1 via UI
