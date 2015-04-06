from datetime import date
from datetime import datetime

class DateTime(datetime):
    """Represents the SQL type "DATETIME"
    DateTime implements datetime without timezone support.
    DateTime is stored as a 8-bytes float (python's timestamp).

    To convert to bytes:
        buffer = struct.pack("<d", dt.to_timestamp())

    To convert from bytes:
        f = struct.unpack("<d", buffer)[0]
        dt = DateTime.from_timestamp(f)
    """

    @property
    def to_timestamp(self):
        return self._timestamp

    @classmethod
    def from_timestamp(cls, t):
        self = super(DateTime,cls).fromtimestamp(t)
        self._timestamp = t
        return self


class Date(date):
    """Represents the SQL type "DATE"
    Date is stored as a 4-byte integer using the following
    format:
        date_as_int = day + 100*month + 10000*year

    To convert to bytes:
        buffer = struct.pack("<i", dt.to_int4())

    To convert from bytes:
        f = struct.unpack("<i", buffer)[0]
        dt = Date.from_int4(f)
    """

    @property
    def to_int4(self):
        return self.day + self.month*100 + self.year*10000

    @classmethod
    def from_int4(cls, date_as_int):
        year = date_as_int // 10000
        month = date_as_int % 10000 // 100
        day = date_as_int % 100
        return cls(year, month, day)
