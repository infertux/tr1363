# TR1363

An open-source implementation and documentation of the TR1363 Battery Management System (BMS) protocol.

This project provides a complete Python parser, MQTT bridge, and Home Assistant integration, allowing battery data to be monitored locally without the manufacturer's Windows application.

The protocol has been reverse engineered entirely through observation and experimentation. The goal of this repository is to document the protocol, encourage collaboration, and eventually provide a complete reference implementation for the DR Battery BMS family.

> **Work in progress:** The protocol is still being decoded. While most commonly used fields are understood, some remain undocumented. Contributions and captured frames are welcome.

---

## Usage

### As a Home Assistant (MQTT) bridge

```bash
./homeassistant.py
```

### As a Python library

```python
from tr1363 import TR1363

bms = TR1363("/dev/ttyUSB0")

status = bms.read_status()

print(status.soc)
print(status.current)
print(status.cell_voltages)
```

## Features

- Decode proprietary TR1363 serial protocol
- Python parser with named fields
- MQTT publisher
- Home Assistant MQTT auto-discovery
- Cell voltage monitoring
- Pack voltage
- Charge/discharge current
- State of Charge (SOC)
- Temperatures
- Status and protection flags
- Passive balancing status bitmap
- Reverse-engineered protocol documentation

---

## Motivation

The official Windows application requires proprietary software to access battery information and only provides CSV dumps of the data.

This project aims to:

- document the protocol
- eliminate dependence on the official application
- integrate the battery with Home Assistant
- make battery data available for automation and long-term logging
- understand the internal behaviour of the BMS

---

## Current Status

### Confirmed

- Frame structure
- Checksum
- Cell voltages
- Pack voltage
- Current
- Temperatures
- SOC?
- Status bitmaps
- Balance bitmap
- MQTT integration
- Home Assistant auto-discovery

### Under Investigation

- Remaining undocumented fields
- Settings command
- Firmware differences between hardware revisions

---

## Repository Structure

```
docs/
    protocol.md
    frame_format.md
    commands.md
    balancing.md

python/
    parser.py
    mqtt_bridge.py

captures/

homeassistant/
    autodiscovery.py

README.md
LICENSE
```

---

## Example Output

```json
{
  "soc": 98.90,
  "pack_voltage": 54.53,
  "current": -1.42,
  "cell_delta": 0.252,
  "max_cell": 3.620,
  "min_cell": 3.368,
  "balance_bitmap": "0000000000010000"
}
```

---

## Hardware

Currently tested with:

- LFP Battery 16S LiFePO₄ battery
- CH340 USB-RS485 adapter
- Python 3.10+
- Home Assistant

Other battery models may work but have not yet been verified.

---

## Passive balancing behavior (experimentally determined)

Extensive testing has revealed several characteristics of the passive balancing algorithm.

### Observed behaviour

- Passive balancing is only active while the BMS detects charging.
- Cells become eligible for balancing at **3.50 V**.
- Balancing stops when cell voltage reaches **3.75 V**.
- Balancing is not continuous. The BMS drives the bleed resistors with an intermittent PWM-like duty cycle.
- Under the tested conditions, the observed duty cycle is approximately **30%**.
- If charging current stops, balancing also stops.

These values are experimentally determined and may vary between firmware revisions.

### Practical implications

Because balancing is only active while charging and only within a relatively narrow voltage window, charger settings have a significant impact on balancing effectiveness.

In testing:

- A float voltage of **54.2 V** kept the highest cell within the balancing window, but charging current dropped to zero, preventing balancing.
- A float voltage of **54.3 V** maintained charging, allowing balancing to continue, although the highest cell occasionally exceeded the upper balancing threshold.

The BMS appears to regulate balancing by periodically enabling and disabling the bleed resistor rather than balancing continuously, making the effective balancing current significantly lower than the hardware bleed current. As a result, correcting large cell imbalances can require many hours or even several days of continuous charging.

## Configuration Parameters

The official Windows application allows writing configuration parameters to the BMS. Access to these settings is protected by a password.

**Default configuration password:**

```
666666
```

> **Warning**
>
> Changing BMS parameters can permanently alter the battery's behavior and may lead to battery damage or unsafe operating conditions if incorrect values are used. Modify settings only if you fully understand their purpose.

### Confirmed Configurable Parameters

The following parameter has been successfully modified and verified:

| Parameter | Default | Verified Range | Notes |
|----------|--------:|---------------:|------|
| Cell balancing start voltage (aka "Starting V") | **3500 mV** | **3410–3500 mV** | The Windows application refuses values below **3410 mV**. |

### Experimental Findings

By lowering the balancing start voltage from **3500 mV** to **3410 mV**, the BMS begins passive balancing significantly earlier during the charge cycle. This increases the amount of time available for balancing before cells reach the upper voltage limit, potentially improving balancing effectiveness on heavily imbalanced battery packs.

## Development

`pip install -e .`

Source files stay where they are. Every change is immediately available. No reinstall necessary.

## Testing

`pytest`

## Contributing

Contributions are welcome.

Especially useful are:

- protocol captures
- firmware differences
- undocumented commands
- parser improvements
- Home Assistant integrations
- additional hardware revisions

If you have a battery that behaves differently, please open an issue and include raw protocol captures.

---

## Disclaimer

This project is completely independent of DR Battery.

The protocol has been reverse engineered from publicly observable communication between the battery and the official application.

Use this software at your own risk. Writing incorrect values to a BMS can permanently damage a battery or create hazardous conditions. At present, this repository focuses on **read-only monitoring**.

---

## License

This project is licensed under the **Mozilla Public License Version 2.0 (MPL-2.0)**.

See [LICENSE](LICENSE) for details.

