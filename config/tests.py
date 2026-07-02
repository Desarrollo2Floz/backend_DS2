import importlib
import types
import pytest

@pytest.mark.parametrize(
    "module_name",
    ["config.asgi", "config.wsgi"]
)
def test_application_is_callable(module_name):
    mod = importlib.import_module(module_name)
    assert hasattr(mod, "application")
    assert isinstance(mod.application, types.FunctionType) or callable(mod.application)

def test_settings_module_is_set():
    import os
    assert os.getenv("DJANGO_SETTINGS_MODULE") == "config.settings"