#!/usr/bin/env bash
# Finds Arduino serial devices
# Taken mostly from https://unix.stackexchange.com/a/144735/166456

for sysdevpath in $(find /sys/bus/usb/devices/usb*/ -name dev); do
  syspath="${sysdevpath%/dev}"
  devname="$(udevadm info -q name -p $syspath)"
  if [[ "$devname" == "bus/"* ]]; then
    continue
  fi

  # Get info for the device and export to variables
  # run `udevadm info -p $(udevadm info -q path -n /dev/ttyACM0)` to see available variables
  eval "$(udevadm info -q property --export -p $syspath)"
  if [[ -n "$ID_SERIAL" ]] && [[  "$ID_VENDOR_ID" == 2341 ]]; then
    echo "$DEVNAME"
  fi
done
