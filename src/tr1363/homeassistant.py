import paho.mqtt.client as mqtt
import json

DEVICE = {
    "identifiers": ["bms_16s"],
    "name": "Battery BMS",
    "manufacturer": "Unknown",
    "model": "16S BMS",
}

DISCOVERY_PREFIX = "homeassistant"
# TODO: rename to "homeassistant/tr1363/battery"?


# def publish_sensor(
#    client,
#    object_id,
#    name,
#    value_template,
#    unit=None,
#    precision=None,
#    device_class=None,
#    state_class="measurement",
#    icon=None,
# ):
#    payload = {
#        "name": name,
#        "unique_id": object_id,
#        "state_topic": "bms/state",
#        "value_template": value_template,
#        "device": DEVICE,
#    }
#
#    if unit:
#        payload["unit_of_measurement"] = unit
#
#    if precision:
#        payload["suggested_display_precision"] = precision
#
#    if device_class:
#        payload["device_class"] = device_class
#
#    if state_class:
#        payload["state_class"] = state_class
#
#    if icon:
#        payload["icon"] = icon
#
#    client.publish(
#        f"{DISCOVERY_PREFIX}/sensor/{object_id}/config",
#        json.dumps(payload),
#        retain=True,
#    )


client = mqtt.Client()
client.username_pw_set(config["MQTT_USERNAME"], config["MQTT_PASSWORD"])
client.connect(config["MQTT_HOST"], int(config["MQTT_PORT"]), 60)

for field in Status.fields():
    payload = {
        "name": field.name,
        "unique_id": f"{serial}_{field.key}",
        "state_topic": topic,
        "value_template": f"{{{{ value_json.{field.key} }}}}",
        "unit_of_measurement": field.unit,
        "device_class": field.device_class,
        "state_class": field.state_class,
    }

    client.publish(
        "bms/state",
        json.dumps(payload),
        # retain=True,
    )
