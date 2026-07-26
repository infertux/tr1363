#!/usr/bin/env python3

from dotenv import dotenv_values
from tr1363 import TR1363

config = dotenv_values(".env")

bms = TR1363(config["BMS_PORT"])

status = bms.read_status()

print("Status", status)

print("First cell voltage: ", status.cell_voltages[0])
