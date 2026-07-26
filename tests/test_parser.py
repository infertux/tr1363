import pytest
from tr1363.parser import InvalidFrame, Parser

parser = Parser()


def test_status_frame():
    status = parser.parse_frame(
        "~22014A00E0C60027101532100D2B0D2C0D2A0D290D2C0D2A0D2B0D2C0D2A0D2A0D2E0D2B0D2D0D2B0D2C0E6E0122011801220401180122012201220077000000610157C357C300DA011000010000000100230000000000000000800000000000000000000000000000D4FD"
    )

    # assert status.soc == 99.99
    assert status.pack_voltage == 54.26
    assert status.current == 1.19
    assert status.cell_voltages[15] == 3.694


def test_corrupted_frame():
    with pytest.raises(InvalidFrame):
        parser.parse_frame("~22014A00E0C60027101532100D2BCORRUPTED")
