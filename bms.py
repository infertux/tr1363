import serial
import re
import json
import paho.mqtt.client as mqtt
from dotenv import dotenv_values

DEVICE = {
    "identifiers": ["bms_16s"],
    "name": "Battery BMS",
    "manufacturer": "Unknown",
    "model": "16S BMS",
}

DISCOVERY_PREFIX = "homeassistant"


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


config = dotenv_values(".env")

client = mqtt.Client()
client.username_pw_set(config["MQTT_USERNAME"], config["MQTT_PASSWORD"])
client.connect(config["MQTT_HOST"], int(config["MQTT_PORT"]), 60)

publish_sensor(
    client,
    "bms_pack_voltage",
    "Pack Voltage",
    "{{ value_json.pack_voltage }}",
    "V",
    2,
    "voltage",
)

publish_sensor(
    client,
    "bms_temp1",
    "Temperature 1",
    "{{ value_json.temperatures.t1 }}",
    "°C",
    0,
    "temperature",
)

publish_sensor(
    client,
    "bms_temp2",
    "Temperature 2",
    "{{ value_json.temperatures.t2 }}",
    "°C",
    0,
    "temperature",
)

publish_sensor(
    client,
    "bms_temp3",
    "Temperature 3",
    "{{ value_json.temperatures.t3 }}",
    "°C",
    0,
    "temperature",
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
    precision=3,
)

for i in range(16):
    publish_sensor(
        client,
        f"bms_cell_{i + 1:02d}",
        f"Cell {i + 1}",
        f"{{{{ value_json.cells[{i}] }}}}",
        "V",
        3,
        "voltage",
    )

publish_sensor(
    client,
    "bms_debug",
    "Debug",
    "{{ value_json.debug }}",
)

publish_sensor(
    client,
    "bms_raw",
    "Raw frame",
    "{{ value_json.raw }}",
)

REQUEST = b"~22014A42E00201FD28\r"


def ascii_hex_to_bytes(frame):
    """
    Convert:
        ~22014A00E0...
    into:
        22 01 4A 00 E0 ...
    """
    # s = frame.decode("ascii", errors="ignore").strip()
    s = ""
    try:
        s = frame.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as e:
        raise ValueError(f"Invalid ASCII in frame: {e}")

    if not s.startswith("~"):
        raise ValueError("Frame does not start with '~'")

    s = s[1:]

    if not re.fullmatch(r"[0-9A-Fa-f]+", s):
        raise ValueError(f"Invalid hex characters in {s}")

    out = bytearray()

    for i in range(0, len(s), 2):
        try:
            out.append(int(s[i : i + 2], 16))
        except:
            break

    return out


ser = serial.Serial(
    config["BMS_PORT"],
    int(config["BMS_BAUD"]),
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=2,
)

# ser.rtscts = False
# ser.dsrdtr = False
# ser.xonxoff = False
print(ser.get_settings())

print("Sending request...")
ser.reset_input_buffer()
ser.write(REQUEST)

raw = ser.read_until(b"\r")

print("\nASCII response:")
print(raw)

data = ascii_hex_to_bytes(raw)

# print("\nDecoded bytes with indexes:\n")
#
# for i, b in enumerate(decoded):
#    print(f"{i:02d}: {b:02X}")

# index += 1 # move to first cell voltage
#
# if index + cells * 2 > len(decoded):
#    raise("Not enough bytes.")
#
# print("Big-endian:")
#
# for i in range(cells):
#    hi = decoded[index + i * 2]
#    lo = decoded[index + i * 2 + 1]
#    mv = (hi << 8) | lo
#    pack_voltage += mv
#    print(f"  Cell {i+1:02d}: {mv/1000:.3f} V")
#

# data = bytes.fromhex(decoded)

cell_count = data[11]

print(f"Cell count: {cell_count}")

if cell_count != 16:
    raise ValueError("Wrong cell count")

offset = 12

# Cell voltages
pack_voltage = 0
cells = []
for i in range(cell_count):
    mv = int.from_bytes(data[offset : offset + 2], "big")
    pack_voltage += mv
    cells.append(mv / 1000)
    offset += 2
pack_voltage = round(pack_voltage / 1000, 2)

print("\nCell voltages:")
for i, v in enumerate(cells, 1):
    print(f"Cell {i:2}: {v} V")

# 3 temperature sensors found even though there are 5 on the battery screen
temps = []
for i in range(3):
    temp = int.from_bytes(data[offset : offset + 2], "big") / 10.0
    temps.append(temp)
    offset += 2

print("\nTemperatures:")
for i, temp in enumerate(temps, 1):
    print(f"Temp {i}: {temp:.1f} °C")

print("\nBalancing?:")
debug = int.from_bytes(data[48:50], "big")
print(f"Bitmap: 0x{debug:04X}")
print(f"Bits  : {debug:016b}")

# 0x140 but NOT about OV alarm + protection (no change with or without OV)
# 0x14A with OV alarm bot NOT protection

# 3.65V+ triggers OV alarm

# float = 54.3V --> shunt at 54.17V and 0.0A
# float = 54.4V --> shunt at 54.23V and 0.0A

# pack_voltage = (data[6] << 8 | data[7]) / 100.0
# print(f"Pack voltage???: {pack_voltage:.2f} V")

# Remaining bytes (if any)
if offset < len(data):
    print("\nRemaining bytes:")
    print(data[offset:].hex().upper())


payload = {
    "pack_voltage": pack_voltage,
    "temperatures": {
        "t1": temps[0],
        "t2": temps[1],
        "t3": temps[2],
    },
    "cells": cells,
    "cell_min": min(cells),
    "cell_max": max(cells),
    "cell_delta": max(cells) - min(cells),
    "cell_min_index": cells.index(min(cells)) + 1,  # TODO
    "cell_max_index": cells.index(max(cells)) + 1,  # TODO
    "debug": debug,
    "raw": raw.decode(),
}

client.publish(
    "bms/state",
    json.dumps(payload),
    retain=True,
)

print("\nDone.")
ser.close()
