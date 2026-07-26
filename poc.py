#!/usr/bin/env python3

# SPDX-License-Identifier: MPL-2.0

# XXX: PoC file, this will eventually be deleted once the refactoring is complete.

import sys
import serial
import re
import json
import paho.mqtt.client as mqtt
from dotenv import dotenv_values


def read_u8(payload, pos):
    """Read one byte (2 ASCII hex chars)."""
    return int(payload[pos : pos + 2], 16), pos + 2


def read_u16(payload, pos):
    """Read one big-endian 16-bit value (4 ASCII hex chars)."""
    return int(payload[pos : pos + 4], 16), pos + 4


def read_s16(payload, pos):
    """Read one signed big-endian 16-bit value."""
    value, pos = read_u16(payload, pos)
    if value & 0x8000:
        value -= 0x10000
    return value, pos


def ascii_sum(s):
    return sum(s.encode())


def twos_complement(s):
    return (-ascii_sum(s)) & 0xFFFF


def parse_frame(frame):
    """
    Parse the BMS ASCII response.
    """
    if not isinstance(frame, str):
        try:
            frame = frame.decode("ascii", errors="strict").strip()
        except UnicodeDecodeError as e:
            raise ValueError(f"Invalid ASCII in frame: {e}")

    if not frame.startswith("~"):
        raise ValueError("Frame does not start with '~'")

    if len(frame) < 18:
        raise ValueError("Frame too short")

    # Remove '~'
    body = frame[1:]

    if not re.fullmatch(r"[0-9A-Fa-f]+", body):
        raise ValueError(f"Invalid hex characters in {body}")

    # Header is always 16 ASCII hex chars
    header = body[:16]
    payload = body[16:]

    pos = 0

    result = {}
    result["header"] = header

    # SOC???
    soc, pos = read_u8(payload, pos)
    result["soc"] = soc

    # Pack voltage
    pack_voltage, pos = read_u16(payload, pos)
    result["pack_voltage"] = pack_voltage / 100.0

    # Number of cells
    cell_count, pos = read_u8(payload, pos)
    result["cell_count"] = cell_count

    # Cell voltages
    cells = []
    for _ in range(cell_count):
        mv, pos = read_u16(payload, pos)
        cells.append(round(mv / 1000.0, 3))  # round() needed?

    result["cell_voltages"] = cells
    result["cell_min"] = min(cells)
    result["cell_max"] = max(cells)
    result["cell_delta"] = round(max(cells) - min(cells), 3)
    result["cell_min_index"] = cells.index(min(cells)) + 1  # TODO: add autodiscovery
    result["cell_max_index"] = cells.index(max(cells)) + 1  # TODO: add autodiscovery

    # Temperature sensors
    temperatures = []
    for _ in range(3):
        t, pos = read_u16(payload, pos)
        temperatures.append(t / 10.0)

    result["temperatures"] = {
        "env": temperatures[0],
        "pack": temperatures[1],
        "mos": temperatures[2],
        "cells": [],
    }

    temperature_count, pos = read_u8(payload, pos)
    for _ in range(temperature_count):
        t, pos = read_u16(payload, pos)
        result["temperatures"]["cells"].append(t / 10.0)

    current, pos = read_s16(payload, pos)
    result["current"] = current / 100.0

    for _ in range(3):  # skip unidentified three "00"
        tmp, pos = read_u8(payload, pos)
        # print(tmp) # always "0"

    soh, pos = read_u8(payload, pos)
    result["soh"] = soh

    tmp, pos = read_u8(payload, pos)
    # print(tmp) # always "1"?

    capacity_full, pos = read_u16(payload, pos)
    result["capacity_full"] = capacity_full / 100.0

    # XXX: really?
    result["soc"] = round(result["soc"] / result["capacity_full"] * 100, 2)

    capacity_remaining, pos = read_u16(payload, pos)
    result["capacity_remaining"] = capacity_remaining / 100.0

    cycles, pos = read_u16(payload, pos)
    result["cycles"] = cycles

    voltage_bitmap, pos = read_u16(payload, pos)
    print(f"Bitmap voltage:     {voltage_bitmap:016b}")

    cell_overvoltage_protection = voltage_bitmap & 1  # bit 0
    result["cell_overvoltage_protection"] = cell_overvoltage_protection

    cell_overvoltage_alarm = (voltage_bitmap >> 4) & 1  # bit 4
    result["cell_overvoltage_alarm"] = cell_overvoltage_alarm

    cell_voltage_diff_alarm = (voltage_bitmap >> 8) & 1  # bit 8
    result["cell_voltage_diff_alarm"] = cell_voltage_diff_alarm

    current_status_bitmap, pos = read_u16(payload, pos)
    print(f"Bitmap current:     {current_status_bitmap:016b}")

    temperature_status_bitmap, pos = read_u16(payload, pos)
    print(f"Bitmap temperature: {temperature_status_bitmap:016b}")

    warning_status_bitmap, pos = read_u16(payload, pos)
    print(f"Bitmap warning:     {warning_status_bitmap:016b}")

    for _ in range(5):
        tmp, pos = read_u16(payload, pos)
        print(f"Bitmap ???:         {tmp:016b}")

    balance_bitmap, pos = read_u16(payload, pos)
    print(f"Bitmap balance:     {balance_bitmap:016b}")

    cell_balancing = []
    for cell in range(16):
        balancing = 1 if balance_bitmap & (1 << cell) else 0
        # TODO: should probably be a bool but we need to implement binary_sensor first
        cell_balancing.append(balancing)
        if balancing:
            print(f"Cell {cell + 1} balancing")

    result["cell_balancing"] = cell_balancing

    for _ in range(6):
        tmp, pos = read_u16(payload, pos)
        print(f"Bitmap ???:         {tmp:016b}")

    tmp, pos = read_u8(payload, pos)
    print(tmp)

    # TODO: assert no remaning payload left

    # checksum_expected, pos = read_u16(payload, pos)
    checksum_expected = hex(int(body[-4:], 16))
    checksum_computed = hex(twos_complement(body[:-4]))

    print("checksum_expected", checksum_expected)
    print("checksum computed", checksum_computed)
    if checksum_computed != checksum_expected:
        raise ValueError("Bad checksum")

    # print("\nBalancing?:")
    # debug = int.from_bytes(data[48:50], "big")
    # print(f"Bitmap: {debug}")
    # print(f"Bits  : {debug:016b}")

    # 320 when ??? (no change with or without OV)
    #
    # 340 when balancing is ON? or is it OV flag?
    # 330 when balancing is OFF?
    # balancing only when cell_max < 3.60V???

    # 3.65V+ triggers OV alarm
    # 3.50V clears OV?

    # float = 54.3V --> shunt at 54.17V and 0.0A
    # float = 54.4V --> shunt at 54.23V and 0.0A

    result["remaining_payload"] = payload[pos:]

    return result


########################################################

if len(sys.argv) == 2:
    print("Argument passed, parsing single frame.")

    frame = sys.argv[1]
    print(f"The argument passed is: {frame}")

    payload = parse_frame(frame)
    print("\nDecoded payload:")
    print(payload)

    sys.exit(0)


config = dotenv_values(".env")

client = mqtt.Client()
client.username_pw_set(config["MQTT_USERNAME"], config["MQTT_PASSWORD"])
client.connect(config["MQTT_HOST"], int(config["MQTT_PORT"]), 60)


ser = serial.Serial(
    config["BMS_PORT"],
    int(config["BMS_BAUD"]),
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=2,
)

# print(ser.get_settings())

REQUEST = b"~22014A42E00201FD28\r"
print("Sending request...")
ser.reset_input_buffer()
ser.write(REQUEST)

frame = ser.read_until(b"\r")

print("\nASCII response:")
print(frame)

payload = parse_frame(frame)
print("\nDecoded payload:")
print(payload)


DEVICE = {
    "identifiers": ["bms_16s"],
    "name": "Battery BMS",
    "manufacturer": "Unknown",
    "model": "16S BMS",
}

DISCOVERY_PREFIX = "homeassistant"
# TODO: rename to "homeassistant/tr1363/battery"?


def publish_sensor(
    client,
    object_id,
    name,
    value_template,
    unit=None,
    precision=None,
    device_class=None,
    state_class="measurement",
    icon=None,
):
    payload = {
        "name": name,
        "unique_id": object_id,
        "state_topic": "bms/state",
        "value_template": value_template,
        "device": DEVICE,
    }

    if unit:
        payload["unit_of_measurement"] = unit

    if precision:
        payload["suggested_display_precision"] = precision

    if device_class:
        payload["device_class"] = device_class

    if state_class:
        payload["state_class"] = state_class

    if icon:
        payload["icon"] = icon

    client.publish(
        f"{DISCOVERY_PREFIX}/sensor/{object_id}/config",
        json.dumps(payload),
        retain=True,
    )


publish_sensor(
    client,
    "bms_header",
    "Frame header",
    "{{ value_json.header }}",  # FIXME: cannot pass string to HASS
)

publish_sensor(
    client,
    "bms_soc",
    "SOC",
    "{{ value_json.soc }}",
    "%",
    0,
)

publish_sensor(
    client,
    "bms_capacity_remaining",
    "Capacity remaining",
    "{{ value_json.capacity_remaining }}",
    "Ah",
    2,
)

publish_sensor(
    client,
    "bms_capacity_full",
    "Capacity full",
    "{{ value_json.capacity_full }}",
    "Ah",
    2,
)

publish_sensor(
    client,
    "bms_pack_voltage",
    "Pack Voltage",
    "{{ value_json.pack_voltage }}",
    "V",
    2,
    "voltage",
)

for i in range(16):
    publish_sensor(
        client,
        f"bms_cell_{i + 1:02d}",
        f"Cell {i + 1} voltage",
        f"{{{{ value_json.cell_voltages[{i}] }}}}",
        "V",
        3,
        "voltage",
    )

    publish_sensor(
        client,
        f"bms_cell_{i + 1:02d}_balancing",
        f"Cell {i + 1} balancing",
        f"{{{{ value_json.cell_balancing[{i}] }}}}",
        "",
    )

publish_sensor(
    client,
    "bms_cell_min",
    "Cell Min",
    "{{ value_json.cell_min }}",
    "V",
    3,
    "voltage",
)

publish_sensor(
    client,
    "bms_cell_max",
    "Cell Max",
    "{{ value_json.cell_max }}",
    "V",
    3,
    "voltage",
)

publish_sensor(
    client,
    "bms_cell_delta",
    "Cell Delta",
    "{{ value_json.cell_delta }}",
    "V",
    3,
)

publish_sensor(
    client,
    "bms_temp_env",
    "Temperature env",
    "{{ value_json.temperatures.env }}",
    "°C",
    0,
    "temperature",
)

publish_sensor(
    client,
    "bms_temp_pack",
    "Temperature pack",
    "{{ value_json.temperatures.pack }}",
    "°C",
    0,
    "temperature",
)

publish_sensor(
    client,
    "bms_temp_mos",
    "Temperature MOS",
    "{{ value_json.temperatures.mos }}",
    "°C",
    0,
    "temperature",
)

publish_sensor(
    client,
    "bms_current",
    "Current",
    "{{ value_json.current }}",
    "A",
    2,
    "current",
)

publish_sensor(
    client,
    "bms_soh",
    "SOH",
    "{{ value_json.soh }}",
    "%",
    0,
)

publish_sensor(
    client,
    "bms_cycles",
    "Cycles",
    "{{ value_json.cycles }}",
    "",
    0,
)

publish_sensor(
    client,
    "bms_cell_overvoltage_protection",
    "Cell overvoltage protection",
    "{{ value_json.cell_overvoltage_protection }}",
    "",
)

client.publish(
    "bms/state",
    json.dumps(payload),
    retain=True,
)

print("\nDone.")
ser.close()
