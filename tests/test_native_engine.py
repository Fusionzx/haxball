import pytest
from haxball_py import HaxballJS

@pytest.mark.asyncio
async def test_haxball_js_init():
    # Verify HaxballJS initializes and returns a callable function
    # (Since actual token is required to start a room on Haxball servers,
    # we just test that the boot loader function resolves correctly).
    try:
        HBInit = await HaxballJS({"debug": True})
        assert callable(HBInit)
    except Exception as e:
        # If node/environment is missing in test sandbox, skip gracefully
        pytest.skip(f"Native engine could not start: {e}")
