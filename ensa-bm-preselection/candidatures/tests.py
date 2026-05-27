import importlib.util
import pathlib
import unittest


def _load_tests_module(name: str):
    base_dir = pathlib.Path(__file__).resolve().parent / "tests"
    path = base_dir / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"candidatures.{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for attr_name, attr_value in module.__dict__.items():
        if isinstance(attr_value, type) and issubclass(attr_value, unittest.TestCase):
            globals()[attr_name] = attr_value


for module_name in ("test_services", "test_views", "test_integration"):
    _load_tests_module(module_name)
