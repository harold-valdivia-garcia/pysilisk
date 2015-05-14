from unittest import TestCase
from pysilisk.types import Date


class TestDate(TestCase):
    def test_to_int4(self):
        dt = Date(year=2015, month=4, day=6)
        self.assertEqual(dt.to_int4(), 20150406)

    def test_from_int4(self):
        dt = Date.from_int4(20150406)
        self.assertEqual(dt.year, 2015)
        self.assertEqual(dt.month, 4)
        self.assertEqual(dt.day, 6)