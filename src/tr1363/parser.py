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
                raise InvalidFrame(f"Invalid ASCII in frame: {e}")

        if not frame.startswith("~"):
            raise InvalidFrame("Frame does not start with '~'")

        header_size = 14

        if len(frame) < header_size + 1:
            raise InvalidFrame("Frame too short")

        # Remove initial '~'
        body = frame[1:]

        if not re.fullmatch(r"[0-9A-Fa-f]+", body):
            raise InvalidFrame(f"Invalid hex characters in {body}")

        header = body[:header_size]
        payload = body[header_size:]

        status = Status()
        result = {}  # TODO: remove
        pos = 0

        # print(header)
        assert header in [
          "22014A00E0C600",
          "22014A00E0C620"
          "22014A00E2C600",
          "22014A00e0C600",
          "22014a00E0C600",
        ]

        # SOC
        soc, pos = read_u16(payload, pos)
        status.soc = soc / 100.0

        # Pack voltage
        pack_voltage, pos = read_u16(payload, pos)
        status.pack_voltage = pack_voltage / 100.0

        # Number of cells
        cell_count, pos = read_u8(payload, pos)

        # Cell voltages
        cells = []
        for _ in range(cell_count):
            mv, pos = read_u16(payload, pos)
            voltage = round(mv / 1000.0, 3)  # round() needed?
            cells.append(voltage)
            # status.cell_voltages.append(voltage)

        status.cell_voltage_min = min(cells)
        status.cell_voltage_max = max(cells)
        status.cell_voltage_delta = round(max(cells) - min(cells), 3)

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
            print(tmp) # always "0"
            assert tmp == 0

        soh, pos = read_u8(payload, pos)
        status.soh = soh

        tmp, pos = read_u8(payload, pos)
        # print(tmp) # always "1"?
        assert tmp == 1

        capacity_full, pos = read_u16(payload, pos)
        status.capacity_full = capacity_full / 100.0

        capacity_remaining, pos = read_u16(payload, pos)
        status.capacity_remaining = capacity_remaining / 100.0

        cycles, pos = read_u16(payload, pos)
        status.cycles = cycles

        voltage_bitmap, pos = read_u16(payload, pos)
        print(f"Bitmap voltage:     {voltage_bitmap:016b}")

        cell_over_voltage_protection = voltage_bitmap & 1  # bit 0
        status.cell_over_voltage_protection = cell_over_voltage_protection

        cell_over_voltage_alarm = (voltage_bitmap >> 4) & 1  # bit 4
        result["cell_over_voltage_alarm"] = cell_over_voltage_alarm

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
        status.cell_balancing = balance_bitmap
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
        print("tmp", tmp)
        assert tmp == 0

        checksum_expected, pos = read_u16(payload, pos)
        assert pos == len(body) - header_size  # assert no remaining payload

        # checksum is 16 bits so we strip the last 4 ASCII chars
        checksum_computed = twos_complement(body[:-4])

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

        print("result =", result)
        print("status =", status)

        return status
