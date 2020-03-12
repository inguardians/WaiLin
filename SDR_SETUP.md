Initially you'll need to do some configuration of your Pi to add some tools for later development, such as RTL-SDR libraries, screen, Git, and a few others.  The install uses the default lower privilege pi user hence the use of sudo:

```
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install git build-essential libtool automake autoconf librtlsdr-dev libfftw3-dev \
librtlsdr-dev rtl-sdr librtlsdr0 libusb-1.0-0-dev pkg-config libncurses5-dev lighttpd \
libbladerf-dev cmake debhelper dh-systemd
```
Next up, installing the individual components for receivers.

## Component Install

### Install rtl-sdr tools from source

For whatever reason, I could not get Kalibrate to compile with the Raspbian packages, but doing it this way in addition to the apt way worked later:

```
cd ~
git clone git://git.osmocom.org/rtl-sdr.git
cd  rtl-sdr
mkdir build
cd build
cmake ../ -DINSTALL_UDEV_RULES=ON
make
sudo make install
sudo ldconfig
cd ~
sudo cp ./rtl-sdr/rtl-sdr.rules /etc/udev/rules.d/
sudo reboot
```

### Install Kalibrate

```
cd ~
git clone https://github.com/steve-m/kalibrate-rtl
cd kalibrate-rtl/
./bootstrap && CXXFLAGS='-W -Wall -O3'
./configure
make
sudo make install
```

### Install dump1090-FA

```
cd ~
git clone https://github.com/flightaware/dump1090.git dump1090-fa
cd dump1090-fa/
sudo dpkg-buildpackage -b   
cd ..
ls -la
sudo dpkg -i dump1090-fa_*_*.deb
service lighttpd force-reload
sudo reboot
```
If your RTL-SDR is connected, dump1090-fa will start on boot and you can navigate to `http://<Pi IP Address>:8080/` to view output.  By default dump1090-fa uses the first RTL-SDR installed (IE -d 0).

If you added your RTL-SDR after the boot and dump1090-fa was already started, you can restart it with `systemctl restart dump1090-fa.service`

### Install rtl-ais

```
cd ~
git clone https://github.com/dgiardini/rtl-ais
cd rtl-ais/
make
sudo cp rtl_ais /usr/local/bin
```

When you use rtl_ais (standalone or via the configured scripts), you will need to be sure to specify the second RTL-SDR with the -d 1 option, because only one set of software can use it at a time.  The script should do this automatically.

### Additional Installation Resources

I've used some of these guides to get going:

* [http://gordon.celesta.me/2018/04/13/raspberry-pi-real-time-flight-tracker-updated.html](http://gordon.celesta.me/2018/04/13/raspberry-pi-real-time-flight-tracker-updated.html)
* [https://discussions.flightaware.com/t/version-3-7-0-of-dump1090-fa-piaware/47874](https://discussions.flightaware.com/t/version-3-7-0-of-dump1090-fa-piaware/47874)
* [https://discussions.flightaware.com/t/how-to-log-dump1090-output-to-file-on-pi/17710](https://discussions.flightaware.com/t/how-to-log-dump1090-output-to-file-on-pi/17710)
* [https://www.rtl-sdr.com/rtl-sdr-tutorial-cheap-ais-ship-tracking/](https://www.rtl-sdr.com/rtl-sdr-tutorial-cheap-ais-ship-tracking/)
* [https://www.fontenay-ronan.fr/ais-receiver-on-a-raspberry-pi-with-rtl-sdr/](https://www.fontenay-ronan.fr/ais-receiver-on-a-raspberry-pi-with-rtl-sdr/)
* [http://idoroseman.com/connecting-ublox-max-m8q-to-the-raspberry-pi/](http://idoroseman.com/connecting-ublox-max-m8q-to-the-raspberry-pi/)
* [https://learn.sparkfun.com/tutorials/getting-started-with-u-center-for-u-blox/all](https://learn.sparkfun.com/tutorials/getting-started-with-u-center-for-u-blox/all)
* [https://www.u-blox.com/en/product/u-center](https://www.u-blox.com/en/product/u-center)
