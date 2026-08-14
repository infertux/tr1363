from dataclasses import dataclass, field


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

    soh: int = field(
        default=-1,
        metadata={
            "name": "State of Health",
            "device_class": None,
            "state_class": "measurement",
            "suggested_display_precision": None,
            "unit_of_measurement": "%",
        },
    )

    cycles: int = field(
        default=-1,
        metadata={
            "name": "Cycles Count",
            "device_class": None,
            "state_class": "measurement",
            "suggested_display_precision": None,
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

    cell_min_voltage: float = field(
        default=-1.0,
        metadata={
            "name": "Min Cell Voltage",
            "device_class": "voltage",
            "state_class": "measurement",
            "suggested_display_precision": 3,
            "unit_of_measurement": "V",
        },
    )

    cell_max_voltage: float = field(
        default=-1.0,
        metadata={
            "name": "Max Cell Voltage",
            "device_class": "voltage",
            "state_class": "measurement",
            "suggested_display_precision": 3,
            "unit_of_measurement": "V",
        },
    )

    cell_min_index: int = field(
        default=-1,
        metadata={
            "name": "Min Cell Index",
            "device_class": None,
            "state_class": "measurement",
            "suggested_display_precision": None,
            "unit_of_measurement": None,
        },
    )

    cell_max_index: int = field(
        default=-1,
        metadata={
            "name": "Max Cell Index",
            "device_class": None,
            "state_class": "measurement",
            "suggested_display_precision": None,
            "unit_of_measurement": None,
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

    cell_balancing_bitmap: int = field(
        default=-1,
        metadata={
            "name": "Cell Balancing Bitmap",
            "device_class": None,
            "state_class": "measurement",
            "unit_of_measurement": None,
            "suggested_display_precision": 0,
        },
    )

    cell_over_voltage_protection: int = field(  # TODO: should be binary_sensor?
        default=-1,
        metadata={
            "name": "Cell Over Voltage Protection",
            "device_class": None,
            "state_class": "measurement",
            "unit_of_measurement": None,
            "suggested_display_precision": None,
        },
    )

    temperature_env: int = field(
        default=-1,
        metadata={
            "name": "Temperature env",
            "device_class": "temperature",
            "state_class": "measurement",
            "suggested_display_precision": None,
            "unit_of_measurement": "°C",
        },
    )

    temperature_pack: int = field(
        default=-1,
        metadata={
            "name": "Temperature pack",
            "device_class": "temperature",
            "state_class": "measurement",
            "suggested_display_precision": None,
            "unit_of_measurement": "°C",
        },
    )

    temperature_mosfet: int = field(
        default=-1,
        metadata={
            "name": "Temperature mosfet",
            "device_class": "temperature",
            "state_class": "measurement",
            "suggested_display_precision": None,
            "unit_of_measurement": "°C",
        },
    )

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
