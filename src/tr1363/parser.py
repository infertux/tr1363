"""Converts raw payloads into Python objects."""

import re

from .models import Status


class InvalidFrame(Exception):
    pass


class CRCError(Exception):
    pass


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


def ascii_sum(s):
    return sum(s.encode())


def twos_complement(s):
    return (-ascii_sum(s)) & 0xFFFF


# TODO: keep the offset internally:
# class Cursor:
#
#     def __init__(self, data: bytes):
#         self.data = data
#         self.offset = 0
#
#     def u16(self):
#         ...


class Parser:
    def parse_frame(self, frame):
        """
        Parse the BMS ASCII response.
        """
        if not isinstance(frame, str):
            try:
                frame = frame.decode("ascii", errors="strict").strip()
            except UnicodeDecodeError as e:
                raise ValueError(f"Invalid ASCII in frame: {e}")

        if not frame.startswith("~"):
            raise InvalidFrame("Frame does not start with '~'")

        if len(frame) < 18:
            raise InvalidFrame("Frame too short")

        # Remove '~'
        body = frame[1:]

        if not re.fullmatch(r"[0-9A-Fa-f]+", body):
            raise InvalidFrame(f"Invalid hex characters in {body}")

        # Header is always 16 ASCII hex chars
        header = body[:16]
        payload = body[16:]

        status = Status()
        pos = 0

        result = {}
        result["header"] = header

        # SOC???
        soc, pos = read_u8(payload, pos)
        status.soc = soc

        # Pack voltage
        pack_voltage, pos = read_u16(payload, pos)
        status.pack_voltage = pack_voltage / 100.0

        # Number of cells
        cell_count, pos = read_u8(payload, pos)
        result["cell_count"] = cell_count

        # Cell voltages
        cells = []
        for _ in range(cell_count):
            mv, pos = read_u16(payload, pos)
            cells.append(round(mv / 1000.0, 3))  # round() needed?
            status.cell_voltages.append(round(mv / 1000.0, 3))  # round() needed?

        result["cell_voltages"] = cells
        result["cell_min"] = min(cells)
        result["cell_max"] = max(cells)
        result["cell_delta"] = round(max(cells) - min(cells), 3)
        result["cell_min_index"] = (
            cells.index(min(cells)) + 1
        )  # TODO: add autodiscovery
        result["cell_max_index"] = (
            cells.index(max(cells)) + 1
        )  # TODO: add autodiscovery

        # Temperature sensors
        temperatures = []
        for _ in range(3):
            t, pos = read_u16(payload, pos)
            temperatures.append(t / 10.0)

        result["temperatures"] = {
            "env": temperatures[0],
            "pack": temperatures[1],
            "mos": temperatures[2],
            "cells": [],
        }

        temperature_count, pos = read_u8(payload, pos)
        for _ in range(temperature_count):
            t, pos = read_u16(payload, pos)
            result["temperatures"]["cells"].append(t / 10.0)

        current, pos = read_s16(payload, pos)
        status.current = current / 100.0

        for _ in range(3):  # skip unidentified three "00"
            tmp, pos = read_u8(payload, pos)
            # print(tmp) # always "0"

        soh, pos = read_u8(payload, pos)
        result["soh"] = soh

        tmp, pos = read_u8(payload, pos)
        # print(tmp) # always "1"?

        capacity_full, pos = read_u16(payload, pos)
        result["capacity_full"] = capacity_full / 100.0

        # XXX: really?
        # result["soc"] = round(result["soc"] / result["capacity_full"] * 100, 2)

        capacity_remaining, pos = read_u16(payload, pos)
        result["capacity_remaining"] = capacity_remaining / 100.0

        cycles, pos = read_u16(payload, pos)
        result["cycles"] = cycles

        voltage_bitmap, pos = read_u16(payload, pos)
        print(f"Bitmap voltage:     {voltage_bitmap:016b}")

        cell_overvoltage_protection = voltage_bitmap & 1  # bit 0
        result["cell_overvoltage_protection"] = cell_overvoltage_protection

        cell_overvoltage_alarm = (voltage_bitmap >> 4) & 1  # bit 4
        result["cell_overvoltage_alarm"] = cell_overvoltage_alarm

        cell_voltage_diff_alarm = (voltage_bitmap >> 8) & 1  # bit 8
        result["cell_voltage_diff_alarm"] = cell_voltage_diff_alarm

        current_status_bitmap, pos = read_u16(payload, pos)
        print(f"Bitmap current:     {current_status_bitmap:016b}")

        temperature_status_bitmap, pos = read_u16(payload, pos)
        print(f"Bitmap temperature: {temperature_status_bitmap:016b}")

        warning_status_bitmap, pos = read_u16(payload, pos)
        print(f"Bitmap warning:     {warning_status_bitmap:016b}")

        for _ in range(5):
            tmp, pos = read_u16(payload, pos)
            print(f"Bitmap ???:         {tmp:016b}")

        balance_bitmap, pos = read_u16(payload, pos)
        print(f"Bitmap balance:     {balance_bitmap:016b}")

        cell_balancing = []
        for cell in range(16):
            balancing = 1 if balance_bitmap & (1 << cell) else 0
            # TODO: should probably be a bool but we need to implement binary_sensor first
            cell_balancing.append(balancing)
            if balancing:
                print(f"Cell {cell + 1} balancing")

        result["cell_balancing"] = cell_balancing

        for _ in range(6):
            tmp, pos = read_u16(payload, pos)
            print(f"Bitmap ???:         {tmp:016b}")

        tmp, pos = read_u8(payload, pos)
        print(tmp)

        # TODO: assert no remaning payload left

        # checksum_expected, pos = read_u16(payload, pos)
        checksum_expected = hex(int(body[-4:], 16))
        checksum_computed = hex(twos_complement(body[:-4]))

        print("checksum_expected", checksum_expected)
        print("checksum computed", checksum_computed)
        if checksum_computed != checksum_expected:
            raise CRCError

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

        # return result

        return status
