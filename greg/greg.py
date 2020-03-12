#!/usr/bin/env python3
from flask import Flask, escape, request
from influxdb import InfluxDBClient

app = Flask(__name__)

influx_client = InfluxDBClient('localhost', 8086, 'root', 'root', 'wailin')

def position_influxdb_point(src, station_id, time, lat, lon, satnav_time):
    return {
        "measurement": "satnav",
        "tags": {
            "src": src,
            "station_id": station_id
        },
        "time": time,
        "fields": {
            "lat": lat,
            "lon": lon,
            "satnav_time": satnav_time
        }
    }

# Endpoint for ingesting SATNAV data (GPS, GLONASS, GALILEO)
# Input is the request body json, formatted like this:
#
# TODO json
#
# Current security risks:
#   - no limit to batch size
#   - no client rate-limiting
#   - no client verification (they are who they say they are)
#   - no client authorization (they are allowed to do what they want to do)
@app.route('/satnav', methods=['POST'])
def satnav():
    data = request.get_json()
    src = data['src']
    station_id = data['station_id']
    influx_points = [
        position_influxdb_point(src, station_id, p['sys_time'], p['lat'], p['lon'], p['satnav_time'])
            for p in data['readings']
    ]
    influx_client.write_points(influx_points, time_precision='s')
    return ''
