from formats.neogeo.sprites import decode_decrypted_tile, TILE_BYTES


def test_first_pixel_plane_zero():
    raw = bytearray(TILE_BYTES)
    raw[0x40] = 0x01
    pixels = decode_decrypted_tile(raw, 0)
    assert pixels[0] == 1
    assert sum(1 for p in pixels if p) == 1


def test_pixel_eight_plane_zero():
    raw = bytearray(TILE_BYTES)
    raw[0x00] = 0x01
    pixels = decode_decrypted_tile(raw, 0)
    assert pixels[8] == 1
