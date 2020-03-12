#!/usr/bin/env python3
import pynmea2
import re
import datetime
from datetime import timezone
from influxdb import InfluxDBClient

# Store once per minute's worth of data
influxdb_batch_size = 60

station_src = "gps"
station_id = "ponyville"

# Generates a single influxdb entry for a position.
# Takes the latitude and longitude normalized to floats such that
# negative lat = s, positive lat = n
# negative lon = w, positive lon = e
# satnav_time = integer UNIX timestamp in seconds
# src = one of GPS GLONASS GALILEO
# station = station ID
def position_influxdb_point(lat, lon, satnav_time, src, station):
    return {
        "measurement": "position",
        "tags": {
            "src": src,
            "station": station
        },
        "time": satnav_time,
        "fields": {
            "lat": lat,
            "lon": lon
        }
    }


client = InfluxDBClient('localhost', 8086, 'root', 'root', 'wailin')


with open("gps.log", "r", encoding='ascii', errors='replace') as satnav_file:
    # list which holds datapoints batched to send to influxdb
    batch = []

    # regex for filtering to only RMC (Recommended Minimum GPS Data) sentence lines
    # RMC contains lat/lon/time/date which are all things we need
    rmc_rgx = re.compile(r"\A\s*\$GPRMC")

    for ln in satnav_file:
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
                    position_influxdb_point(
                        msg.latitude,
                        msg.longitude,
                        int(msg.datetime.replace(tzinfo=timezone.utc).timestamp()),
                        station_src,
                        station_id
                    )
                )
        except pynmea2.ParseError as e:
            pass

        if len(batch) >= influxdb_batch_size:
            # Write points using second-precision, since that's what GPS gives us
            client.write_points(batch, time_precision='s')

            # Clear batch for new data
            batch.clear()

    # Write any remaining points from the final batch
    if len(batch) > 0:
        client.write_points(batch, time_precision='s')
