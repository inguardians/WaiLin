#!/bin/sh

debug_output=/dev/null

if [ "$DEBUG" ]; then
    debug_output=/var/log/wailin/glonass.log
fi

(stty raw; cat) < /dev/ttyGLONASS | tee -a "$debug_output" | python3 /opt/wailin/station/satnav-to-greg.py --src GLONASS --station_id ponyville
