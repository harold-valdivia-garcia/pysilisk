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
