"""Initial smoke test for the SmartMaint project."""

import smartmaint


def test_package_version_is_defined() -> None:
    """Verify that the SmartMaint package can be imported."""
    assert smartmaint.__version__ == "0.1.0"
