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
    "bms_header",
    "Frame header",
    "{{ value_json.header }}",  # FIXME: cannot pass string to HASS
)

publish_sensor(
    client,
    "bms_remaining_capacity",
    "Remaining capacity",
    "{{ value_json.remaining_capacity }}",
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
        f"Cell {i + 1}",
        f"{{{{ value_json.cell_voltages[{i}] }}}}",
        "V",
        3,
        "voltage",
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

REQUEST = b"~22014A42E00201FD28\r"


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


def parse_frame(frame):
    """
    Parse the BMS ASCII response.
    """
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

    # Ah
    remaining_capacity, pos = read_u8(payload, pos)
    # TODO: double check this, it's weird we're not getting the 2 decimal places
    result["remaining_capacity"] = remaining_capacity

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
        cells.append(round(mv / 1000.0, 3))

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
    }

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


ser = serial.Serial(
    config["BMS_PORT"],
    int(config["BMS_BAUD"]),
    bytesize=8,
    parity="N",
    stopbits=1,
    timeout=2,
)

# print(ser.get_settings())

print("Sending request...")
ser.reset_input_buffer()
ser.write(REQUEST)

frame = ser.read_until(b"\r")

print("\nASCII response:")
print(frame)

payload = parse_frame(frame)
print("\nDecoded payload:")
print(payload)

client.publish(
    "bms/state",
    json.dumps(payload),
    retain=True,
)

print("\nDone.")
ser.close()
