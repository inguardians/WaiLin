#!/bin/sh

debug_output=/dev/null

if [ "$DEBUG" ]; then
    debug_output=/var/log/wailin/gps.log
fi

(stty raw; cat) < /dev/ttyGPS | tee -a "$debug_output" | python3 /opt/wailin/station/satnav-to-greg.py --src GPS --station_id ponyville
