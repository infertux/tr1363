#!/usr/bin/env python3

# SPDX-License-Identifier: MPL-2.0

import paho.mqtt.client as mqtt
import json
from dotenv import dotenv_values
from dataclasses import fields, asdict

from tr1363 import TR1363
from tr1363.models import Status

DEVICE = {
    "identifiers": ["bms_16s"],
    "name": "Battery BMS",
    "manufacturer": "Unknown",
    "model": "16S BMS",
}

DISCOVERY_PREFIX = "homeassistant"
# TODO: rename to "homeassistant/tr1363/battery"?


env = dotenv_values(".env")

client = mqtt.Client()
client.username_pw_set(env["MQTT_USERNAME"], env["MQTT_PASSWORD"])
client.connect(env["MQTT_HOST"], int(env["MQTT_PORT"]), 60)

for field in fields(Status):
    id = field.name

    config = {
        "device": DEVICE,
        "state_topic": "bms/state",
        "default_entity_id": id,
        "name": field.metadata["name"],
        "value_template": f"{{{{ value_json.{id} }}}}",
        "unit_of_measurement": field.metadata["unit_of_measurement"],
        "suggested_display_precision": field.metadata["suggested_display_precision"],
        "device_class": field.metadata["device_class"],
        "state_class": field.metadata["state_class"],
    }

    # print(config)

    client.publish(
        f"{DISCOVERY_PREFIX}/sensor/{id}/config",
        json.dumps(config),
        retain=True,
    )

bms = TR1363(env["BMS_PORT"], env["BMS_BAUD"])
status = bms.read_status()
print("Status", status)

client.publish("bms/state", json.dumps(asdict(status)), retain=True)
