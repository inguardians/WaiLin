# Purpose

After recent discussion with some colleagues about some GPS spoofing mysteries in [Shanghai](https://www.technologyreview.com/s/614689/ghost-ships-crop-circles-and-soft-gold-a-gps-mystery-in-shanghai/), it was noted that there is no way for an average human to detect when GPS "oddities" happen.  These changes could be well published notification from the satellite operators (reduction in selective availability, for example), un-published changes from satellite operators, GPS spoofing/jamming, or some other, yet unknown, oddities.

The intent of this project is to provide a low cost, easy to implement method for gaining access to location data with the ability to record that data over time, provide near-real time alerts on anomalies, and the ability to perform analysis on the captured data.  

The intent is to capture data from several disparate systems in order to provide multiple baselines (and observe changed in those baselines for the disparate systems).  Currently we are capturing data from GPS, GLONASS, Galileo (GNSS), ADS-B and AIS.  Currently the selected hardware for satellite based location is set to report from one technology only;  this requires 3 separate receivers, one dedicated to each technology.  The receivers can be configured to use different systems (they are quite flexible), depending on location. This gives us the ability to use BeiDou, IRNSS or QZSS depending on deployment timeline and geographic region to supplement the data gathering.


# Installing

## Initial setup

Install Raspbian on your SDcard and place in your Pi. Currently I'm accessing the Pi via ethernet, which grabs it's network configuration via DHCP.  You can also use WiFi, but we'll leave that as an exercise unto the reader.

Currently we are using Raspbian Buster.  Earlier distributions have not been tested.  Sorry.


## Install WaiLin

Right now this is just a bulleted list. If you're seeing this message, rest
assured we'll clean it up and make it more usable as soon as we can, promise!  This will at least get you started, and the project was never meant for someone that wasn't willing to tinker a little bit.

- clone repo
- cd into repo
- `sudo ./install.sh`
  - follow along with the script it will help you do:
    - udev setup
    - lat/lon setup
    - webhook setup
      - [https://support.discordapp.com/hc/en-us/articles/228383668-Intro-to-Webhooks](https://support.discordapp.com/hc/en-us/articles/228383668-Intro-to-Webhooks)
  - `sudo reboot`
- grafana setup
  - go to `http://<raspberrypi_ip>:3000/`
    - username admin
    - password admin
  - Add data source
    - InfluxDB
    - URL: `http://localhost:8086`
    - InfluxDB Details
      - database: wailin
    - click save & test
    - back
  - import workspace
    - [https://grafana.com/docs/grafana/latest/reference/export_import/](https://grafana.com/docs/grafana/latest/reference/export_import/)
    - in wailin repo, `grafana/wailin-workspace.json` is the workspace

# Hardware

* [USB Cables](https://www.amazon.com/gp/product/B07DYFN1ZQ/)
* [RS-232 to TTL adapter](https://www.amazon.com/gp/product/B07BMNB6CM/)
* [ublox M8 GPS module](https://www.ebay.com/itm/UBLOX-NEO-M8N-GPS-Module-Satellite-Engine-Chip-For-PIX-PX4-Flight-Controller/283492091587) format 1
* [ublox M8 GPS module](https://www.ebay.com/itm/NEW-Genuine-Ublox-NEO-M8N-GPS-HMC5983-Compass-Module-For-Pixhawk-APM/233148091454) format 2
* [Raspberry Pi 4 kit 4](https://www.amazon.com/gp/product/B07XTRFD3Z/)
* [RTL-SDR](https://www.amazon.com/RTL-SDR-Blog-RTL2832U-Software-Defined/dp/B011HVUEME/) 
* [SD Card](https://www.amazon.com/gp/product/B06XWN9Q99/)

A list of all of these parts can also be found [here](https://www.amazon.com/hz/wishlist/ls/2S55SRUKHFHCR?ref_=wl_share) on amazon.  If you want to be awesome, consider using Amazon Smile to support the [Rural Technology Fund](https://www.amazon.com/hz/wishlist/ls/2S55SRUKHFHCR?ref_=wl_share) with your purchase.

# Collecting Data

Using the items in the scripts folder in this repository, you can start them individual services manually in order to test data capture.  The scripts are named by the data being captured, and are the ones used to create each individual screen session on startup.

### GPS, GNSS and GLONASS

For the GPS, GNSS and GLONASS scripts (named for their respective service in the scripts directory), you may need to adjust the serial port in which they are reading from. My /dev/ttyUSBX ports are in that order noted in the scripts, as they were all tested individually.

### dump1090-fa

dump1090-fa can also use the provided script to collect data from localhost on port 30003.

### rtl-ais

rtl-ais requires the most testing, as reception is trickier and requires a more finely tuned radio (in most cases).  Additionally AIS does not travel terribly far inland, so your results may vary on reception.  You may need to adjust which RTL-SDR is used on the script with the -d option; it is set to the second RTL-SDR with -d 1.

In order to more finely use rtl-ais, it is helpful to determine the tuning offset in ppm, in order to adjust the received frequency.  Because the RTL-SDR is inexpensive, there is a fair amount of drift/inaccuracy.  Using kalibrate, we can determine the offset for passing to other tools.

To give us a starting point we will use rtl_test, let it run for a few minutes and then use the ppm offset as a start for kalibrate:

```rtl_test -p -d 1```

In my case, here are the results:

```
Found 2 device(s):
  0:  Realtek, RTL2838UHIDIR, SN: 00000001
  1:  Realtek, RTL2838UHIDIR, SN: 00000001

Using device 1: Generic RTL2832U OEM
Found Rafael Micro R820T tuner
Supported gain values (29): 0.0 0.9 1.4 2.7 3.7 7.7 8.7 12.5 14.4 15.7 16.6 19.7 20.7 22.9 25.4 28.0 29.7 32.8 33.8 36.4 37.2 38.6 40.2 42.1 43.4 43.9 44.5 48.0 49.6 
[R82XX] PLL not locked!
Sampling at 2048000 S/s.
Reporting PPM error measurement every 10 seconds...
Press ^C after a few minutes.
Reading samples in async mode...
Allocating 15 zero-copy buffers
lost at least 168 bytes
real sample rate: 2047764 current PPM: -115 cumulative PPM: -115
real sample rate: 2048005 current PPM: 3 cumulative PPM: -56
real sample rate: 2047983 current PPM: -8 cumulative PPM: -40
real sample rate: 2048004 current PPM: 2 cumulative PPM: -29
real sample rate: 2047993 current PPM: -3 cumulative PPM: -24
real sample rate: 2047990 current PPM: -5 cumulative PPM: -21
real sample rate: 2047998 current PPM: -1 cumulative PPM: -18
real sample rate: 2047962 current PPM: -18 cumulative PPM: -18
real sample rate: 2048031 current PPM: 15 cumulative PPM: -14
real sample rate: 2047994 current PPM: -3 cumulative PPM: -13
^C
```

Mine averaged out to about -13 PPM offset, so that value was passed to kalibrate in the -e parameter.  I also set a gain value from those supported from the rtl_test somewhere in the middle of the road at 28 for the -g value; I found that the max values were just too strong.  I also used the 850mHz band here in the US for the -s option.

```
kal -s 850 -g 28 -e 13 -d 1
```

Here are my results:

```
Found 2 device(s):
  0:  Generic RTL2832U OEM
  1:  Generic RTL2832U OEM

Using device 1: Generic RTL2832U OEM
Found Rafael Micro R820T tuner
Exact sample rate is: 270833.002142 Hz
[R82XX] PLL not locked!
Setting gain: 28.0 dB
kal: Scanning for GSM-850 base stations.
GSM-850:
    chan:  237 (891.0MHz - 38.961kHz)    power:  253201.60
```
Then use the stronger channel with -c to have a more accurate offset calculated. I have only one available (I live in the middle of nowhere...).
	
```
kal -c 237 -g 28 -e 13 -d 1
```
And here are my results (yours may differ):

```
Found 2 device(s):
  0:  Generic RTL2832U OEM
  1:  Generic RTL2832U OEM

Using device 1: Generic RTL2832U OEM
Found Rafael Micro R820T tuner
Exact sample rate is: 270833.002142 Hz
[R82XX] PLL not locked!
Setting gain: 28.0 dB
kal: Calculating clock frequency offset.
Using GSM-850 channel 237 (891.0MHz)
Tuned to 891.000000MHz (reported tuner error: 0Hz)
average		[min, max]	(range, stddev)
- 38.925kHz		[-38994, -38844]	(150, 46.878014)
overruns: 0
not found: 0
average absolute error: 56.687 ppm
```

This ppm value can now be provided to rtl_ais for more accurate tuning with the -p option.  One should update the `ais.sh` script to reflect your individual PPM offset.  It can be started manually with the following command, using the determiend PPM offset rounded down to the nearest whole number:

```
rtl_ais -n -p 56 -d 1
```

# Execution on Startup

Getting all of the scripts to execute on startup is quite easy in two steps.  First, copy the scripts to the `pi` user's home directory:

```
cd ~
cd WaiLin/scripts
cp *.sh ~
```

We've even included some systemd style startup scripts in the WaiLin `startup` directory, which we need to copy into `/etc/systemd/system`

```
cd ~
cd WaiLin/scripts
sudo cp *.service /etc/systemd/system
```

Perform the following to add them to systemd, and enable them for autostart.

```
systemctl daemon-reload
systemctl enable gps galileo glonass adsb ais
```
Note that the ADS-B reception is already started by a separate system service.  The script referenced here merely creates a netcat (nc) session to port 30003 to retrieve the data.

# Logging Data to SQL

Under Development

# Configuring Alerts

Under Development

# Centralized Data Submission

Under Development

# Development Efforts

## Initial Features

* Capture data from 3 GPS modules and two SDRs
* Normalize data with defined data points (more?)
	* Satellite: Satellite technology, position, position lock
	* 	AIS: Transponder ID, location
	* 	ADS-B: Transponder ID, location
* Store data locally in a database (sqlite3?)
	* 	retrieve satellite data in a useful format for mapping
	* 	retrieve ADS-B and AIS data in a useful format for mapping
* Realtime analysis and alerting based on positional deltas/changes where
	* 	GPS location changes by more than X feet over X time period
	* 	GLONASS location changes by more than X feet over X time period
	* 	GNSS location changes by more than X feet over X time period
	* 	Any one technology differs from the other (GPS, GLONASS, GNSS) by more than X feet over x time
	* 	Alerts via e-mail, STDOUT (SMS?)	


## Looking to the Future
* Submit data in real time to a central location, shared between users all over the world
	* 	Needs logins, API, data sharing model, etc.
* Visualization of data, alerting on anomalies
* Dshieild.org style data acquisition and sharing
