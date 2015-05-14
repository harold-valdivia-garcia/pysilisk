from datetime import date
from datetime import datetime

class NullConstrain(object):
    """Identifiers for the 'NULL' and 'NOT NULL'
    constrains in the Create-Table statement
    """
    NULL = 0
    NOT_NULL = 1

    @classmethod
    def from_string(cls, str_constrain):
        str_constrain = str_constrain.upper()
        if str_constrain.upper() in ['', 'NULL']:
            return cls.NULL
        elif str_constrain == 'NOT NULL':
            return cls.NOT_NULL


class SQLDataType(object):
    """Identifiers and Names of the SQL Data-types supported by Pisilisk"""
    INTEGER = 0  # Integer of 4-bytes
    FLOAT = 1    # Double-precision of 8-bytes
    DATETIME = 2 # Implemented using a double-precision of 8-bytes (timestamp)
    DATE = 3     # Implemented using an integer of 4-bytes
    VARCHAR = 4  # String of variable size
    CHAR =  5    # String of fix size

    _type_names = ['INTEGER', 'FLOAT', 'DATETIME', 'DATE', 'VARCHAR', 'CHAR']
    _type_ids = [INTEGER, FLOAT, DATETIME, DATE, VARCHAR, CHAR]
    _hash_name_ids = {t:v for t,v in zip(_type_names, _type_ids)}
    _hash_id_names = {v:t for v,t in zip(_type_ids, _type_names)}

    @classmethod
    def from_string(cls, type_name):
        if type_name in cls._hash_name_ids:
            return cls._hash_name_ids[type_name]
        else:
            raise DataTypeException(type_name)

    @classmethod
    def to_string(cls, data_value):
        if data_value in cls._hash_id_names:
            return cls._hash_id_names[data_value]
        else:
            raise DataTypeException(data_value)


class DataTypeException(Exception):
    def __init__(self, unsupported_data_type):
        self.unsupported_data_type = unsupported_data_type
        self.message = "Unsupported data-type: %s" % unsupported_data_type


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

    def to_int4(self):
        return self.day + self.month*100 + self.year*10000

    @classmethod
    def from_int4(cls, date_as_int):
        year = date_as_int // 10000
        month = date_as_int % 10000 // 100
        day = date_as_int % 100
        return cls(year, month, day)
