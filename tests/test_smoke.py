"""Initial smoke test for the SmartMaint project."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIRECTORY = PROJECT_ROOT / "src"

sys.path.insert(0, str(SOURCE_DIRECTORY))

import smartmaint


class TestProjectSmoke(unittest.TestCase):
    """Verify that the initial package is accessible."""

    def test_package_version_is_defined(self) -> None:
        self.assertEqual(smartmaint.__version__, "0.1.0")


if __name__ == "__main__":
    unittest.main()
