from formats.neogeo.mame_dump import build_sprite_dump_lua


def test_dump_lua_targets_neogeo_sprite_region():
    script = build_sprite_dump_lua("out.bin")
    assert 'regions[":sprites"]' in script
    assert "region:read" in script
    assert "manager.machine:exit()" in script
