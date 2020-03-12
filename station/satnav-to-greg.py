#!/usr/bin/env python3
import pynmea2
import re
import datetime
import sys
import io
import json
import requests
import getopt
import os
from datetime import timezone

def print_help_and_die():
    print("Usage: %s --src <GPS|GLONASS|GALILEO> --station_id <make_something_up> [--batch_size <number>] [--verbose]" % sys.argv[0])
    print()
    print("Options:")
    print(" -h, --help prints this help message")
    print()
    print(" -s, --src specifies the source of the satnav data")
    print("      -s GPS")
    print("     --src GLONASS")
    print("     --src GALILEO")
    print()
    print(" -i, --station_id sets the station_id. This is used when multiple devices")
    print(" are providing data to differentiate which sensors are which.")
    print("      -i ponyville")
    print("     --station_id crystal_castle")
    print()
    print(" -b, --batch_size controls how many satnav readings are buffered before")
    print(" being sent to the server. defaults to 600 readings, based on the")
    print(" assumption that the data fed into this script has one reading per second")
    print("      -b 600")
    print("     --batch_size 1200")
    print()
    print(" -v, --verbose enables verbose mode which provides some debug info")
    print()
    sys.exit(2)

# arguments or w/e
opts, leftover = getopt.getopt(sys.argv[1:], "hb:s:i:v", ["--help", "batch_size=", "src=", "station_id=", "--verbose"])

# Store once per minute's worth of data
batch_size = 600

station_src = None
station_id = os.environ.get('STATION_ID')
verbose = False

for opt, arg in opts:
    if opt in ("-h", "--help"):
        print_help_and_die()
    elif opt in ("-b", "--batch_size"):
        batch_size = int(arg)
    elif opt in ("-s", "--src"):
        station_src = arg
    elif opt in ("-i", "--station_id"):
        station_id = arg
    elif opt in ("-v", "--verbose"):
        verbose = True

if None in (station_src, station_id):
    print_help_and_die()

# Generates a single influxdb entry for a position.
# Takes the latitude and longitude normalized to floats such that
# negative lat = s, positive lat = n
# negative lon = w, positive lon = e
# satnav_time = integer UNIX timestamp in seconds
# src = one of GPS GLONASS GALILEO
# station = station ID
def position_point(lat, lon, satnav_time):
    return {"lat": lat, "lon": lon, "sys_time": satnav_time, "satnav_time": satnav_time}

count = 0
def write_batch(batch):
    global count
    count = count + 1
    if verbose:
        print("writing batch " + str(count))
    data = {
        "src": station_src,
        "station_id": station_id,
        "readings": batch
    }
    requests.post('http://localhost:5000/satnav', json=data)

# list which holds datapoints batched to send to influxdb
batch = []

# regex for filtering to only RMC (Recommended Minimum GPS Data) sentence lines
# RMC contains lat/lon/time/date which are all things we need
rmc_rgx = re.compile(r"\A\s*\$GPRMC")


for ln in io.TextIOWrapper(sys.stdin.buffer, encoding='ascii', errors='replace'):
    # Skip all non-RMC lines to speed up processing
    if rmc_rgx.match(ln) == None:
        continue

    try:
        msg = pynmea2.parse(ln)

        # RMC contains lat/lon/time/date which are all things we need
        # status of A indicates valid data
        # the isinstance check is probably not needed due to the filtering
        # regex, but we'll keep it just in case
        if isinstance(msg, pynmea2.types.talker.RMC) and msg.status == 'A':
            batch.append(
                position_point(
                    msg.latitude,
                    msg.longitude,
                    int(msg.datetime.replace(tzinfo=timezone.utc).timestamp())
                )
            )
    except:
        print('invalid nmea or bad time field: ' + ln.strip(), file = sys.stderr)
        pass

    if len(batch) >= batch_size:
        # Write points using second-precision, since that's what GPS gives us
        write_batch(batch)

        # Clear batch for new data
        batch.clear()

# Write any remaining points from the final batch
if len(batch) > 0:
    write_batch(batch)
