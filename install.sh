#!/bin/bash

set -e

if [ "$(whoami)" != "root" ]; then
    printf "err: re-run as root\n"
    exit 1
fi

# Takes name of device (GPS/SATNAV/GLONASS) in $1
# appends device udev rule to udev_rules global
udev_rules=""
prompt_for_satnav_device() {
    old_devs="$(find /dev -name '*ttyUSB*')"

    printf 'Plug in a %s device if you have one and then press enter.' "$1"
    read -r
    printf 'Scanning...\n'
    sleep 3

    new_devs="$(find /dev -name '*ttyUSB*')"

    new_tty="$(printf '%s\n%s' "$old_devs" "$new_devs" | sort | uniq -u | grep -o '/dev/ttyUSB[0-9]\+')"

    if [ -n "$new_tty" ]; then
        tty_path="$(udevadm info --query=path "$new_tty" | sed 's/ttyUSB.*$/*/')"
        udev_rules="$(printf '%s\n\nACTION=="add", SUBSYSTEM=="tty", DEVPATH=="%s", SYMLINK+="tty%s"' "$udev_rules" "$tty_path" "$1")"
        printf 'Device registered.\n'
    else
        printf 'No new devices found. skipping\n'
    fi
}

create_udev_rules() {
    # udev rules
    udev_rules_path="/etc/udev/rules.d/20-usb-serial.rules"
    if [ "$1" = "force" ] || [ -f "$udev_rules_path" ]; then
        printf "udev rules already exist. skipping\n"
        return 0
    fi
    udev_rules=""
    printf 'We need to create some udev rules so we can access your GPS devices.\nThis is an interactive process that requires physical access to your hardware.\n\n'
    # put rules in /etc/udev/rules.d/20-usb-serial.rules

    # udevadm info --query property --export <device>
    # ID_PATH line
    printf "Please unplug all GPS/GLONASS/GALILEO devices and then press enter."
    read -r
    prompt_for_satnav_device GPS
    prompt_for_satnav_device GALILEO
    prompt_for_satnav_device GLONASS
    printf '%s\n' "$udev_rules" >> "$udev_rules_path"
    printf 'udev rules written to %s\n' "$udev_rules_path"
    printf 'Devices are registered based on the physical USB ports your satnav devices are\nusing, as well as the physical USB ports your USB hubs are plugged into if you\nare using a hub. if you ever move anything around, re-run this script with: \n\n%s --register-devices\n\n' "$0"
}


install_influx_and_grafana() {
    apt-get update -y
    sudo apt-get install -y apt-transport-https

    # Add InfluxDB repos
    wget -qO- https://repos.influxdata.com/influxdb.key | sudo apt-key add -
    source /etc/os-release
    echo "deb https://repos.influxdata.com/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/influxdb.list

    # Add Grafana repos
    wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
    echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list 

    # apt-get update again
    apt-get update -y

    # Install InfluxDB and Grafana
    apt-get install -y influxdb grafana

    # daemon-reload
    systemctl daemon-reload


    # Configure InfluxDB
    # TODO make it not listen on 0.0.0.0

    # Enable/Start InfluxDB
    systemctl unmask influxdb.service
    systemctl start influxdb.service

    # Enable/Start Grafana
    systemctl enable grafana-server
    systemctl start grafana-server

    # Create InfluxDB WaiLin Table
    attempts=3
    while [ $attempts -gt 0 ] && ! influx -execute 'CREATE DATABASE wailin'; do
        attempts=$(( attempts - 1 ))
        printf 'error executing influx query. this is probably because it is not running yet. will retry %s more times\n' $attempts
        sleep 5
    done
}


install_service_file() {
    cp ./startup/"$1" /etc/systemd/system/"$1"
    chown root:root /etc/systemd/system/"$1"
    systemctl daemon-reload
    systemctl enable "$1"
}

install_wailin() {
    # === setup our code ===
    apt-get install -y python3 python3-pip
    wailin_folder=/opt/wailin

    ## install station code
    install_service_file gps.service
    install_service_file galileo.service
    install_service_file glonass.service
    mkdir -p "$wailin_folder"/station
    cp station/* "$wailin_folder"/station
    (
        cd "$wailin_folder"/station
        # TODO set version restrictions in requirements.txt
        pip3 install -r requirements.txt
    )

    ## install greg code
    install_service_file greg.service
    cp ./startup/alerting.service /etc/systemd/system/alerting.service
    chown root:root /etc/systemd/system/alerting.service
    install_service_file alerting.timer
    mkdir -p "$wailin_folder"/greg
    cp greg/* "$wailin_folder"/greg
    (
        cd "$wailin_folder"/greg
        mv wailin.conf /etc/wailin.conf
        chown root:root /etc/wailin.conf
        # TODO set version restrictions in requirements.txt
        pip3 install -r requirements.txt
    )

    ## logging and permissions
    mkdir -p /var/log/wailin
    chown -R pi:pi /var/log/wailin
    chown -R pi:pi "$wailin_folder"

    ## recommend post-setup
    printf '\n'
    printf '%s\n' 'You need to edit /etc/wailin.conf to set:'
    printf '%s\n' '- latitude'
    printf '%s\n' '- longitude'
    printf '%s\n' '- alerting webhook'
    printf '\n'
    printf '%s' 'Do you wanna do that now? [Y/n]'
    read -r edit_config
    if [ "$edit_config" != "n" ] && [ "$edit_config" != "N" ]; then
        nano /etc/wailin.conf
    fi
}

main() {
    if [ "$1" = "--register-devices" ]; then
        create_udev_rules force
        exit 0
    else
        create_udev_rules
        install_influx_and_grafana
        install_wailin
        printf '\n'
        printf '%s' 'You need to reboot to get everything working. reboot now? [y/N] '
        read -r do_reboot
        if [ "$do_reboot" = "y" ] || [ "$do_reboot" = "Y" ]; then
            printf 'rebooting!\n'
            reboot
        fi
    fi
}

main
