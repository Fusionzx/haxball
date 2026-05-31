import pytest


@pytest.fixture(autouse=True)
def reset_hbinit_cache():
    """Reset global NativeEngine cache between tests so each test gets its own event loop."""
    from haxball import _hbinit

    engine = _hbinit._engine_instance
    if engine is not None:
        engine.close()
    _hbinit._engine_instance = None
    _hbinit._hb_init_future = None
