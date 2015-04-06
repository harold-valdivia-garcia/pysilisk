from unittest import TestCase
from pysilisk.types import DateTime
from datetime import datetime
import time
import os
import struct
import io

import math


class TestDateTime(TestCase):
    def setUp(self):
        # Create a DateTime using a float
        f = 1428344506.305786 # 2015-04-06 14:21:46.305785
        self.test_float = f

    def test_to_timestamp(self):
        dt = DateTime.from_timestamp(self.test_float)
        tm = dt.to_timestamp()
        self.assertEqual(dt.to_timestamp(), self.test_float)

    def test_totimestamp_and_timestamp(self):
        dt = DateTime.from_timestamp(self.test_float)
        tm = dt.to_timestamp()
        pytm = dt.timestamp() # python's timestamp
        diff_tm = math.fabs(tm - pytm)
        DIFF_TOLERANCE = 0.000001  # On avg the diff is  0.000000953
        self.assertGreater(DIFF_TOLERANCE, diff_tm)
