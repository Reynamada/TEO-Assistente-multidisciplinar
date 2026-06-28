import importlib
import sys
import os

# Resolve the path to the backend.app package and extend package path
_backend_app_path = os.path.join(os.path.dirname(__file__), "backend", "app")
__path__.append(_backend_app_path)
if _backend_app_path not in sys.path:
    sys.path.insert(0, _backend_app_path)

# Import the actual backend.app package
_backend_app = importlib.import_module("backend.app")

# Re-export its public attributes (modules, classes, functions) if __all__ is defined
if hasattr(_backend_app, "__all__"):
    __all__ = _backend_app.__all__
    for _name in __all__:
        globals()[_name] = getattr(_backend_app, _name)
else:
    # Expose all non-private attributes
    __all__ = [name for name in dir(_backend_app) if not name.startswith("_")]
    for _name in __all__:
        globals()[_name] = getattr(_backend_app, _name)

# Ensure "app" resolves to this package
sys.modules['app'] = _backend_app
