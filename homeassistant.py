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
from tr1363.parser import InvalidFrame

DEVICE_ID = "bms_tr1363"

DEVICE = {
    "identifiers": [DEVICE_ID],
    "manufacturer": "Unknown",
    "model": "TR1363",
    "name": "BMS TR1363",
}

DISCOVERY_PREFIX = "homeassistant"
# TODO: rename to "homeassistant/tr1363/battery"?

run = True
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

logging.basicConfig(level=logging.DEBUG)


def exit_handler():
    print("run = False")
    global run
    run = False

    global mqttc
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

        config = {
            "device": DEVICE,
            "state_topic": "bms/state",
            "unique_id": f"{DEVICE_ID}_{id}",
            "name": field.metadata["name"],
            "value_template": f"{{{{ value_json.{id} }}}}",
            "state_class": field.metadata["state_class"],
        }

        if field.metadata["device_class"]:
            config["device_class"] = field.metadata["device_class"]

        if field.metadata["unit_of_measurement"]:
            config["unit_of_measurement"] = field.metadata["unit_of_measurement"]

        if field.metadata["suggested_display_precision"]:
            config["suggested_display_precision"] = field.metadata[
                "suggested_display_precision"
            ]

        # print(config)

        mqttc.publish(
            f"{DISCOVERY_PREFIX}/sensor/{id}/config",
            json.dumps(config),
            retain=False,
        )

    bms = TR1363(env["BMS_PORT"], env["BMS_BAUD"])

    while run:
        try:
            status = bms.read_status()
            mqttc.publish("bms/state", json.dumps(asdict(status)), retain=False)
            time.sleep(1)
        except InvalidFrame as e:
            print("Ignoring invalid frame: ", e)


if __name__ == "__main__":
    main()
