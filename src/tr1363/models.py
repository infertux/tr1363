from dataclasses import dataclass, field

# @dataclass(frozen=True)
# class Field:
#    key: str
#    name: str
#    unit: str | None
#    device_class: str | None
#    state_class: str | None
#    icon: str | None
#    entity_category: str | None


@dataclass(slots=True)
class Status:
    soc: float = field(
        default=-1.0,
        metadata={
            "name": "State of Charge",
            "device_class": "battery",
            "state_class": "measurement",
            "suggested_display_precision": 2,
            "unit_of_measurement": "%",
        },
    )

    soh: float = field(
        default=-1.0,
        metadata={
            "name": "State of Health",
            "device_class": None,
            "state_class": "measurement",
            "suggested_display_precision": 0,
            "unit_of_measurement": "%",
        },
    )

    cycles: float = field(
        default=-1.0,
        metadata={
            "name": "Cycles Count",
            "device_class": None,
            "state_class": "measurement",
            "suggested_display_precision": 0,
            "unit_of_measurement": None,
        },
    )

    capacity_full: float = field(
        default=-1.0,
        metadata={
            "name": "Full Capacity",
            "device_class": None,
            "state_class": "measurement",
            "suggested_display_precision": 2,
            "unit_of_measurement": "Ah",
        },
    )

    capacity_remaining: float = field(
        default=-1.0,
        metadata={
            "name": "Remaining Capacity",
            "device_class": None,
            "state_class": "measurement",
            "suggested_display_precision": 2,
            "unit_of_measurement": "Ah",
        },
    )

    pack_voltage: float = field(
        default=-1.0,
        metadata={
            "name": "Pack Voltage",
            "device_class": "voltage",
            "state_class": "measurement",
            "suggested_display_precision": 2,
            "unit_of_measurement": "V",
        },
    )

    current: float = field(
        default=-1.0,
        metadata={
            "name": "Current",
            "device_class": "current",
            "state_class": "measurement",
            "suggested_display_precision": 2,
            "unit_of_measurement": "A",
        },
    )

    # cell_voltages: list[float] = field(
    #    default_factory=list,
    #    metadata={
    #        "name": "Cell Voltage",
    #        "unit_of_measurement": "V",
    #        "device_class": "voltage",
    #        "state_class": "measurement",
    #        "suggested_display_precision": 3,
    #    },
    # )

    cell_voltage_min: float = field(
        default=-1.0,
        metadata={
            "name": "Min Cell Voltage",
            "device_class": "voltage",
            "state_class": "measurement",
            "suggested_display_precision": 3,
            "unit_of_measurement": "V",
        },
    )

    cell_voltage_max: float = field(
        default=-1.0,
        metadata={
            "name": "Max Cell Voltage",
            "device_class": "voltage",
            "state_class": "measurement",
            "suggested_display_precision": 3,
            "unit_of_measurement": "V",
        },
    )

    cell_voltage_delta: float = field(
        default=-1.0,
        metadata={
            "name": "Cell Voltage Delta",
            "device_class": "voltage",
            "state_class": "measurement",
            "suggested_display_precision": 3,
            "unit_of_measurement": "V",
        },
    )

    cell_balancing: float = field(
        default=-1.0,
        metadata={
            "name": "Cell Balancing Bitmap",
            "device_class": None,
            "state_class": "measurement",
            "unit_of_measurement": None,
            "suggested_display_precision": 0,
        },
    )

    cell_over_voltage_protection: float = field(  # TODO: should be binary_sensor?
        default=-1.0,
        metadata={
            "name": "Cell Over Voltage Protection",
            "device_class": None,
            "state_class": "measurement",
            "unit_of_measurement": None,
            "suggested_display_precision": 0,
        },
    )

    # temperatures: list[float] = field(default_factory=list)


# publish_sensor(
#    client,
#    "bms_header",
#    "Frame header",
#    "{{ value_json.header }}",  # FIXME: cannot pass string to HASS
# )
#
# publish_sensor(
#    client,
#    "bms_soc",
#    "SOC",
#    "{{ value_json.soc }}",
#    "%",
#    0,
# )
#
# publish_sensor(
#    client,
#    "bms_capacity_remaining",
#    "Capacity remaining",
#    "{{ value_json.capacity_remaining }}",
#    "Ah",
#    2,
# )
#
# publish_sensor(
#    client,
#    "bms_capacity_full",
#    "Capacity full",
#    "{{ value_json.capacity_full }}",
#    "Ah",
#    2,
# )
#
# publish_sensor(
#    client,
#    "bms_pack_voltage",
#    "Pack Voltage",
#    "{{ value_json.pack_voltage }}",
#    "V",
#    2,
#    "voltage",
# )
#
# for i in range(16):
#    publish_sensor(
#        client,
#        f"bms_cell_{i + 1:02d}",
#        f"Cell {i + 1} voltage",
#        f"{{{{ value_json.cell_voltages[{i}] }}}}",
#        "V",
#        3,
#        "voltage",
#    )
#
#    publish_sensor(
#        client,
#        f"bms_cell_{i + 1:02d}_balancing",
#        f"Cell {i + 1} balancing",
#        f"{{{{ value_json.cell_balancing[{i}] }}}}",
#        "",
#    )
#
# publish_sensor(
#    client,
#    "bms_cell_min",
#    "Cell Min",
#    "{{ value_json.cell_min }}",
#    "V",
#    3,
#    "voltage",
# )
#
# publish_sensor(
#    client,
#    "bms_cell_max",
#    "Cell Max",
#    "{{ value_json.cell_max }}",
#    "V",
#    3,
#    "voltage",
# )
#
# publish_sensor(
#    client,
#    "bms_cell_delta",
#    "Cell Delta",
#    "{{ value_json.cell_delta }}",
#    "V",
#    3,
# )
#
# publish_sensor(
#    client,
#    "bms_temp_env",
#    "Temperature env",
#    "{{ value_json.temperatures.env }}",
#    "°C",
#    0,
#    "temperature",
# )
#
# publish_sensor(
#    client,
#    "bms_temp_pack",
#    "Temperature pack",
#    "{{ value_json.temperatures.pack }}",
#    "°C",
#    0,
#    "temperature",
# )
#
# publish_sensor(
#    client,
#    "bms_temp_mos",
#    "Temperature MOS",
#    "{{ value_json.temperatures.mos }}",
#    "°C",
#    0,
#    "temperature",
# )
#
# publish_sensor(
#    client,
#    "bms_current",
#    "Current",
#    "{{ value_json.current }}",
#    "A",
#    2,
#    "current",
# )
#
# publish_sensor(
#    client,
#    "bms_soh",
#    "SOH",
#    "{{ value_json.soh }}",
#    "%",
#    0,
# )
#
# publish_sensor(
#    client,
#    "bms_cycles",
#    "Cycles",
#    "{{ value_json.cycles }}",
#    "",
#    0,
# )
#
# publish_sensor(
#    client,
#    "bms_cell_overvoltage_protection",
#    "Cell overvoltage protection",
#    "{{ value_json.cell_overvoltage_protection }}",
#    "",
# )
