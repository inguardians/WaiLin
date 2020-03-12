#!/bin/sh

debug_output=/dev/null

if [ "$DEBUG" ]; then
    debug_output=/var/log/wailin/galileo.log
fi

(stty raw; cat) < /dev/ttyGALILEO | tee -a "$debug_output" | python3 /opt/wailin/station/satnav-to-greg.py --src GALILEO --station_id ponyville
