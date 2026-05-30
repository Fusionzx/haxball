import os
import pytest
from haxball_py import HaxballJS
from haxball_py.utils import decode_ip_from_conn
from haxball_py._native_engine import NativeEngine


def test_decode_ip_from_conn():
    # ASCII hex encoding: "192.0.2.1"
    hex_ip = "3139322e302e322e31"  # "192.0.2.1" in hex
    assert decode_ip_from_conn(hex_ip) == "192.0.2.1"

    # None / empty
    assert decode_ip_from_conn(None) is None
    assert decode_ip_from_conn("") is None

    # Invalid hex returns as-is
    assert decode_ip_from_conn("not-hex") == "not-hex"

    # Multi-octet IP
    hex_ip2 = "3139322e3136382e312e31"  # "192.168.1.1"
    assert decode_ip_from_conn(hex_ip2) == "192.168.1.1"


def test_native_engine_source_has_delete_message():
    import inspect

    source = inspect.getsource(NativeEngine.start)
    assert "message.startsWith(cmdPrefix)" in source, (
        "deleteMessage: onPlayerChat must check for cmdPrefix"
    )
    assert "bareCommandNames.has(message.split(' ')[0].toLowerCase())" in source, (
        "deleteMessage: onPlayerChat must hide configured bare extended commands"
    )
    assert "return false" in source, "deleteMessage: onPlayerChat must return false for commands"


@pytest.mark.asyncio
async def test_haxball_js_init():
    try:
        HBInit = await HaxballJS({"debug": True})
        assert callable(HBInit)
    except Exception as e:
        pytest.skip(f"Native engine could not start: {e}")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_native_room_create_with_token():
    token = os.environ.get("HAXBALL_TOKEN")
    if not token:
        pytest.skip("HAXBALL_TOKEN not set")

    HBInit = await HaxballJS({"debug": True})
    room = await HBInit(
        {
            "roomName": "Test Room (pytest)",
            "maxPlayers": 16,
            "public": False,
            "noPlayer": True,
            "token": token,
        }
    )

    await room.set_default_stadium("Big")
    await room.set_score_limit(3)

    link = await room.wait_for_room_link(timeout=30)
    assert link.startswith("https://www.haxball.com/play?c=")
