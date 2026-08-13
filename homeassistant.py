#!/usr/bin/env python3

# SPDX-License-Identifier: MPL-2.0

from dataclasses import fields, asdict
from dotenv import dotenv_values
import atexit
import json
import logging
import paho.mqtt.client as mqtt
import time

from tr1363 import TR1363
from tr1363.models import Status
from tr1363.parser import CRCError, InvalidFrame

DEVICE_ID = "bms_tr1363"

DEVICE = {
    "identifiers": [DEVICE_ID],
    "manufacturer": "Unknown",
    "model": "TR1363",
    "name": "BMS TR1363",
}

DISCOVERY_PREFIX = "homeassistant"
STATE_TOPIC = f"{DEVICE_ID}/state"

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

logging.basicConfig(level=logging.DEBUG)


def exit_handler():
    #global mqttc
    print("Disconnecting from MQTT")
    mqttc.disconnect()
    mqttc.loop_stop()
    print("Disconnected from MQTT")


atexit.register(exit_handler)


def main():
    env = dotenv_values(".env")

    mqttc.enable_logger()
    mqttc.username_pw_set(env["MQTT_USERNAME"], env["MQTT_PASSWORD"])
    mqttc.connect(env["MQTT_HOST"], int(env["MQTT_PORT"]))
    mqttc.loop_start()

    for field in fields(Status):
        id = field.name
        unique_id = f"sensor.{DEVICE_ID}_{id}"

        config = {
            "device": DEVICE,
            "state_topic": STATE_TOPIC,
            "unique_id": unique_id,
            "default_entity_id": unique_id,
            "name": field.metadata["name"],
            "value_template": f"{{{{ value_json.{id} }}}}",
            "state_class": field.metadata["state_class"],
        }

        if field.metadata["device_class"]:
            config["device_class"] = field.metadata["device_class"]

        if field.metadata["unit_of_measurement"]:
            config["unit_of_measurement"] = field.metadata["unit_of_measurement"]

        if field.metadata["suggested_display_precision"]:
            config["suggested_display_precision"] = field.metadata["suggested_display_precision"]

        print(config)

        mqttc.publish(
            f"{DISCOVERY_PREFIX}/sensor/{DEVICE_ID}/{id}/config",
            json.dumps(config),
            retain=False,
        )

        time.sleep(0.1)

    bms = TR1363(env["BMS_PORT"], env["BMS_BAUD"])

    while True:
        try:
            status = bms.read_status()
            mqttc.publish(STATE_TOPIC, json.dumps(asdict(status)), retain=False)
            time.sleep(1)
        except CRCError as e:
            print("Ignoring corrupted frame:", e)
        except InvalidFrame as e:
            print("Ignoring invalid frame:", e)


if __name__ == "__main__":
    main()
