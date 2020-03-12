#!/usr/bin/env python3
import requests
import os
import sys
from influxdb import InfluxDBClient

influx_client = InfluxDBClient('localhost', 8086, 'root', 'root', 'wailin')

env_webhook = os.environ.get('ALERT_WEBHOOK')
env_median_lat = os.environ.get('LATITUDE')
env_median_lon = os.environ.get('LONGITUDE')

if env_webhook == None or env_webhook == "":
    print("alerting.py: ALERT_WEBHOOK environment variable not defined, exiting")
    sys.exit(0)

if env_median_lat == None or env_median_lat == "":
    print("alerting.py: LATITUDE environment variable not defined, exiting")
    sys.exit(0)

if env_median_lon == None or env_median_lon == "":
    print("alerting.py: LONGITUDE environment variable not defined, exiting")
    sys.exit(0)

webhook = env_webhook
median_lat = float(env_median_lat)
median_lon = float(env_median_lon)

# basically we looked at some data collected over awhile and saw that
# 95% of points were within 120ft radius (two standard deviations)
# so on any given day 5% of points should be outside that radius.
# if a significant number more points are outside that radius, that's
# when we should send an alert. we use 10% as our alerting level
alerting_threshold=0.1


# 10,000 KM per 90 degrees according to https://sciencing.com/convert-latitude-longtitude-feet-2724.html
# 60ft = 0.018288km
# threshold = 0.018288 * 90 / 10000
satnav_radius = (0.018288 * 2) * 90.0 / 10000.0


min_lat = median_lat - satnav_radius
max_lat = median_lat + satnav_radius
min_lon = median_lon - satnav_radius
max_lon = median_lon + satnav_radius

result_count_total_measurements = influx_client.query(r"""
    SELECT COUNT(*) FROM satnav
    WHERE
        time > now() - 1d
    GROUP BY src,station_id
""")

result_count_outside_radius = influx_client.query(r"""
    SELECT COUNT(*) FROM satnav
    WHERE
        ( lat > {} OR lat < {} OR lon > {} OR lon < {} )
        AND time > now() - 1d
    GROUP BY src,station_id
""".format(max_lat, min_lat, max_lon, min_lon))


for (series, tags) in result_count_outside_radius.keys():
    k = (series, tags)
    total = next(result_count_total_measurements[k])
    outside_radius = next(result_count_outside_radius[k])

    # lat and lon should always have the same count but in case they dont
    # im taking the ratio of anomalies for each one separately and then
    # using the maximum of those ratios
    alert_ratio_lat = outside_radius["count_lat"] / total["count_lat"]
    alert_ratio_lon = outside_radius["count_lon"] / total["count_lon"]
    alert_ratio = max(alert_ratio_lat, alert_ratio_lon)

    if alert_ratio > alerting_threshold:
        # Pardon my hand-made float formatting, i dont feel like looking
        # up the standard way to do this
        whole = int(alert_ratio * 100)
        frac = int(((alert_ratio * 100) - whole) * 100)
        payload = {
            "content": "ALERT: {}.{}% of {} points were outside expected uncertainty radius.".format(whole, frac, tags["src"])
        }
        print(payload)
        requests.post(webhook, json=payload)
