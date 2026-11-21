import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from calculator import calculate
from login import hash_password, verify_password

class TestApp(unittest.TestCase):
    def test_calculator(self):
        self.assertEqual(calculate("2+3*4"), 14)
    def test_password(self):
        h = hash_password("abc")
        self.assertTrue(verify_password("abc", h))
        self.assertFalse(verify_password("wrong", h))

if __name__ == "__main__":
    unittest.main()