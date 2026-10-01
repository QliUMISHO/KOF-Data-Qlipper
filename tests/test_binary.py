from core.binary_reader import BinaryReader
from core.binary_writer import BinaryWriter


def test_big_endian_reader():
    reader = BinaryReader(bytes.fromhex("12 34 89 AB CD EF"))
    assert reader.read_u16_be() == 0x1234
    assert reader.read_u32_be() == 0x89ABCDEF


def test_big_endian_writer():
    writer = BinaryWriter.from_bytes(b"\x00" * 8)
    writer.write_u16_be(0, 0x1234)
    writer.write_u32_be(2, 0x89ABCDEF)
    assert bytes(writer.data[:6]) == bytes.fromhex("12 34 89 AB CD EF")
