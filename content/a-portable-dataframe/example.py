import zlib
import json
import xlrd
from time import process_time, process_time_ns
from itertools import count
from datetime import datetime, date, time
from functools import lru_cache
from collections import defaultdict
from pathlib import Path


class DataTypes(object):
    # supported datatypes.
    int = int
    str = str
    float = float
    bool = bool
    date = date
    datetime = datetime
    time = time

    # reserved keyword for Nones:
    digits = '1234567890'
    decimals = set('1234567890-+eE.')
    integers = set('1234567890-+')
    nones = {'null', 'Null', 'NULL', '#N/A', '#n/a', "", 'None', None}

    date_formats = {  # Note: Only recognised ISO8601 formats are accepted.
        "NNNN-NN-NN": lambda x: date(*(int(i) for i in x.split("-"))),
        "NNNN-N-NN": lambda x: date(*(int(i) for i in x.split("-"))),
        "NNNN-NN-N": lambda x: date(*(int(i) for i in x.split("-"))),
        "NNNN-N-N": lambda x: date(*(int(i) for i in x.split("-"))),
        "NN-NN-NNNN": lambda x: date(*[int(i) for i in x.split("-")][::-1]),
        "N-NN-NNNN": lambda x: date(*[int(i) for i in x.split("-")][::-1]),
        "NN-N-NNNN": lambda x: date(*[int(i) for i in x.split("-")][::-1]),
        "N-N-NNNN": lambda x: date(*[int(i) for i in x.split("-")][::-1]),
        "NNNN.NN.NN": lambda x: date(*(int(i) for i in x.split("."))),
        "NNNN.N.NN": lambda x: date(*(int(i) for i in x.split("."))),
        "NNNN.NN.N": lambda x: date(*(int(i) for i in x.split("."))),
        "NNNN.N.N": lambda x: date(*(int(i) for i in x.split("."))),
        "NN.NN.NNNN": lambda x: date(*[int(i) for i in x.split(".")][::-1]),
        "N.NN.NNNN": lambda x: date(*[int(i) for i in x.split(".")][::-1]),
        "NN.N.NNNN": lambda x: date(*[int(i) for i in x.split(".")][::-1]),
        "N.N.NNNN": lambda x: date(*[int(i) for i in x.split(".")][::-1]),
        "NNNN/NN/NN": lambda x: date(*(int(i) for i in x.split("/"))),
        "NNNN/N/NN": lambda x: date(*(int(i) for i in x.split("/"))),
        "NNNN/NN/N": lambda x: date(*(int(i) for i in x.split("/"))),
        "NNNN/N/N": lambda x: date(*(int(i) for i in x.split("/"))),
        "NN/NN/NNNN": lambda x: date(*[int(i) for i in x.split("/")][::-1]),
        "N/NN/NNNN": lambda x: date(*[int(i) for i in x.split("/")][::-1]),
        "NN/N/NNNN": lambda x: date(*[int(i) for i in x.split("/")][::-1]),
        "N/N/NNNN": lambda x: date(*[int(i) for i in x.split("/")][::-1]),
        "NNNN NN NN": lambda x: date(*(int(i) for i in x.split(" "))),
        "NNNN N NN": lambda x: date(*(int(i) for i in x.split(" "))),
        "NNNN NN N": lambda x: date(*(int(i) for i in x.split(" "))),
        "NNNN N N": lambda x: date(*(int(i) for i in x.split(" "))),
        "NN NN NNNN": lambda x: date(*[int(i) for i in x.split(" ")][::-1]),
        "N N NNNN": lambda x: date(*[int(i) for i in x.split(" ")][::-1]),
        "NN N NNNN": lambda x: date(*[int(i) for i in x.split(" ")][::-1]),
        "N NN NNNN": lambda x: date(*[int(i) for i in x.split(" ")][::-1]),
        "NNNNNNNN": lambda x: date(*(int(x[:4]), int(x[4:6]), int(x[6:]))),
    }

    datetime_formats = {  # Note: Only recognised ISO8601 formats are accepted.

        # year first
        'NNNN-NN-NNTNN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x), # -T
        'NNNN-NN-NNTNN:NN': lambda x: DataTypes.pattern_to_datetime(x),

        'NNNN-NN-NN NN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, T=" "),  # - space
        'NNNN-NN-NN NN:NN': lambda x: DataTypes.pattern_to_datetime(x, T=" "),

        'NNNN/NN/NNTNN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/'),  # / T
        'NNNN/NN/NNTNN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/'),

        'NNNN/NN/NN NN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', T=" "),  # / space
        'NNNN/NN/NN NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', T=" "),

        'NNNN NN NNTNN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd=' '),  # space T
        'NNNN NN NNTNN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd=' '),

        'NNNN NN NN NN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd=' ', T=" "),  # space
        'NNNN NN NN NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd=' ', T=" "),

        # day first
        'NN-NN-NNNNTNN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='-', T=' ', day_first=True),  # - T
        'NN-NN-NNNNTNN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='-', T=' ', day_first=True),

        'NN-NN-NNNN NN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='-', T=' ', day_first=True),  # - space
        'NN-NN-NNNN NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='-', T=' ', day_first=True),

        'NN/NN/NNNNTNN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', day_first=True),  # / T
        'NN/NN/NNNNTNN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', day_first=True),

        'NN/NN/NNNN NN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', T=' ', day_first=True),  # / space
        'NN/NN/NNNN NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', T=' ', day_first=True),

        'NN NN NNNNTNN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', day_first=True),  # space T
        'NN NN NNNNTNN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', day_first=True),

        'NN NN NNNN NN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', day_first=True),  # space
        'NN NN NNNN NN:NN': lambda x: DataTypes.pattern_to_datetime(x, ymd='/', day_first=True),

        # compact formats - type 1
        'NNNNNNNNTNNNNNN': lambda x: DataTypes.pattern_to_datetime(x, compact=1),
        'NNNNNNNNTNNNN': lambda x: DataTypes.pattern_to_datetime(x, compact=1),
        'NNNNNNNNTNN': lambda x: DataTypes.pattern_to_datetime(x, compact=1),
        # compact formats - type 2
        'NNNNNNNNNN': lambda x: DataTypes.pattern_to_datetime(x, compact=2),
        'NNNNNNNNNNNN': lambda x: DataTypes.pattern_to_datetime(x, compact=2),
        'NNNNNNNNNNNNNN': lambda x: DataTypes.pattern_to_datetime(x, compact=2),
        # compact formats - type 3
        'NNNNNNNNTNN:NN:NN': lambda x: DataTypes.pattern_to_datetime(x, compact=3),
    }

    @staticmethod
    def pattern_to_datetime(iso_string, ymd=None, T=None, compact=0, day_first=False):
        assert isinstance(iso_string, str)
        if compact:
            s = iso_string
            if compact == 1:  # has T
                slices = [(0, 4, "-"), (4, 6, "-"), (6, 8, "T"), (9, 11, ":"), (11, 13, ":"), (13, len(s), "")]
            elif compact == 2:  # has no T.
                slices = [(0, 4, "-"), (4, 6, "-"), (6, 8, "T"), (8, 10, ":"), (10, 12, ":"), (12, len(s), "")]
            elif compact == 3:  # has T and :
                slices = [(0, 4, "-"), (4, 6, "-"), (6, 8, "T"), (9, 11, ":"), (12, 14, ":"), (15, len(s), "")]
            else:
                raise TypeError
            iso_string = "".join([s[a:b] + c for a, b, c in slices if b <= len(s)])
            iso_string = iso_string.rstrip(":")

        if day_first:
            s = iso_string
            iso_string = "".join((s[6:10],"-", s[3:5], "-", s[0:2], s[10:]))

        if "," in iso_string:
            iso_string = iso_string.replace(",", ".")

        dot = iso_string[::-1].find('.')
        if 0 < dot < 10:
            ix = len(iso_string) - dot
            microsecond = int(float(f"0{iso_string[ix-1:]}") * 10 ** 6)
            iso_string = iso_string[:len(iso_string) - dot ] + str(microsecond).rjust(6, "0")
        if ymd:
            iso_string = iso_string.replace(ymd, '-', 2)
        if T:
            iso_string = iso_string.replace(T, "T")
        return datetime.fromisoformat(iso_string)

    @staticmethod
    def to_json(v):
        if v is None:
            return v
        if isinstance(v, int):
            return v
        elif isinstance(v, str):
            return v
        elif isinstance(v, float):
            return v
        elif isinstance(v, bool):
            return str(v)
        elif isinstance(v, date):
            return v.isoformat()
        elif isinstance(v, time):
            return v.isoformat()
        elif isinstance(v, datetime):
            return v.isoformat()
        else:
            raise TypeError(f"The datatype {type(v)} is not supported.")

    @staticmethod
    def from_json(v, dtype):
        if v in DataTypes.nones:
            return None
        if dtype is int:
            return int(v)
        elif dtype is str:
            return str(v)
        elif dtype is float:
            return float(v)
        elif dtype is bool:
            return bool(v)
        elif dtype is date:
            return date.fromisoformat(v)
        elif dtype is datetime:
            return datetime.fromisoformat(v)
        elif dtype is time:
            return time.fromisoformat(v)
        else:
            raise TypeError(f"The datatype {str(dtype)} is not supported.")


    @staticmethod
    @lru_cache(maxsize=256)
    def infer(v, dtype):
        if v is DataTypes.nones:
            return None
        if dtype is int:
            return DataTypes._infer_int(v)
        elif dtype is str:
            return DataTypes._infer_str(v)
        elif dtype is float:
            return DataTypes._infer_float(v)
        elif dtype is bool:
            return DataTypes._infer_bool(v)
        elif dtype is date:
            return DataTypes._infer_date(v)
        elif dtype is datetime:
            return DataTypes._infer_datetime(v)
        elif dtype is time:
            return DataTypes._infer_time(v)
        else:
            raise TypeError(f"The datatype {str(dtype)} is not supported.")

    @staticmethod
    def _infer_bool(value):
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            raise ValueError("it's an integer.")
        elif isinstance(value, float):
            raise ValueError("it's a float.")
        elif isinstance(value, str):
            if value.lower() == "true":
                return True
            elif value.lower() == "false":
                return False
            else:
                raise ValueError
        else:
            raise ValueError

    @staticmethod
    def _infer_int(value):
        if isinstance(value, bool):
            raise ValueError("it's a boolean")
        if isinstance(value, int):
            return value
        elif isinstance(value, float):
            if int(value) == value:
                return int(value)
            raise ValueError("it's a float")
        elif isinstance(value, str):
            value = value.replace('"', '').replace(" ", "")
            value_set = set(value)
            if value_set - DataTypes.integers:  # set comparison.
                raise ValueError
            return int(float(value))
        else:
            raise ValueError

    @staticmethod
    def _infer_float(value):
        if isinstance(value, int):
            raise ValueError("it's an integer")
        if isinstance(value, float):
            return value
        elif isinstance(value, str):
            value = value.replace('"','')
            dot_index, comma_index = value.find('.'), value.find(',')
            if 0 < dot_index < comma_index:  # 1.234,567
                value = value.replace('.', '')  # --> 1234,567
                value = value.replace(',', '.') # --> 1234.567
            elif dot_index > comma_index > 0:  # 1,234.678
                value = value.replace(',', '.')
            elif comma_index and dot_index == -1:
                value = value.replace(',', '.')
            else:
                pass

            value_set = set(value)

            if not value_set.issubset(DataTypes.decimals):
                raise TypeError

            # if it's a string, do also
            # check that reverse conversion is valid,
            # otherwise we have loss of precision. F.ex.:
            # int(0.532) --> 0

            float_value = float(value)
            if value_set.intersection('Ee'):  # it's scientific notation.
                v = value.lower()
                if v.count('e') != 1:
                    raise ValueError("only 1 e in scientific notation")

                e = v.find('e')
                v_float_part = float(v[:e])
                v_exponent = int(v[e+1:])
                return float(f"{v_float_part}e{v_exponent}")

            elif "." in str(float_value) and not "." in value_set:
                # when traversing through Datatype.types,
                # integer is presumed to have failed for the column,
                # so we ignore this and turn it into a float...
                reconstructed_input = str(int(float_value))

            elif "." in value:
                precision = len(value) - value.index(".") - 1
                formatter = '{0:.' + str(precision) + 'f}'
                reconstructed_input = formatter.format(float_value)

            else:
                reconstructed_input = str(float_value)

            if value.lower() != reconstructed_input:
                raise ValueError

            return float_value
        else:
            raise ValueError

    @staticmethod
    def _infer_date(value):
        if isinstance(value, date):
            return value
        elif isinstance(value, str):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pattern = "".join(["N" if n in DataTypes.digits else n for n in value])
                f = DataTypes.date_formats.get(pattern, None)
                if f:
                    return f(value)
                else:
                    raise ValueError
        else:
            raise ValueError

    @staticmethod
    def _infer_datetime(value):
        if isinstance(value, datetime):
            return value
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                if '.' in value:
                    dot = value.find('.')
                elif ',' in value:
                    dot = value.find(',')
                else:
                    dot = len(value)

                pattern = "".join(["N" if n in DataTypes.digits else n for n in value[:dot]])
                f = DataTypes.datetime_formats.get(pattern, None)
                if f:
                    return f(value)
                else:
                    raise ValueError
        else:
            raise ValueError

    @staticmethod
    def _infer_time(value):
        if isinstance(value, time):
            return value
        elif isinstance(value, str):
            return time.fromisoformat(value)
        else:
            raise ValueError

    @staticmethod
    def _infer_str(value):
        if isinstance(value, str):
            return value
        else:
            return str(value)

    # Order is very important!
    types = [datetime, date, time, int, bool, float, str]


def datatype_inference_tests():
    # integers
    assert DataTypes.infer(1, int) == 1
    assert DataTypes.infer(0, int) == 0
    assert DataTypes.infer(-1, int) == -1
    assert DataTypes.infer('1', int) == 1
    assert DataTypes.infer('0', int) == 0
    assert DataTypes.infer('-1', int) == -1
    assert DataTypes.infer('"1000028"', int) == 1000028

    # floats
    assert DataTypes.infer("2932,500", float) == 2932.5
    assert DataTypes.infer("2932.500", float) == 2932.5
    assert DataTypes.infer("-2932.500", float) == -2932.5
    assert DataTypes.infer("2.932,500", float) == 2932.5
    assert DataTypes.infer("2.932e5", float) == 2.932e5
    assert DataTypes.infer("-2.932e5", float) == -2.932e5
    assert DataTypes.infer("10e5", float) == 10e5
    assert DataTypes.infer("-10e5", float) == -10e5

    # booleans
    assert DataTypes.infer('true', bool) is True
    assert DataTypes.infer('True', bool) is True
    assert DataTypes.infer('TRUE', bool) is True
    assert DataTypes.infer('false', bool) is False
    assert DataTypes.infer('False', bool) is False
    assert DataTypes.infer('FALSE', bool) is False

    # dates
    isodate = date(1990, 1, 1)
    assert DataTypes.infer(isodate.isoformat(), date) == isodate
    assert DataTypes.infer("1990-01-01", date) == date(1990, 1, 1)  # date with minus
    assert DataTypes.infer("2003-09-25", date) == date(2003, 9, 25)

    assert DataTypes.infer("25-09-2003", date) == date(2003, 9, 25)  # year last.
    assert DataTypes.infer("10-09-2003", date) == date(2003, 9, 10)

    assert DataTypes.infer("1990.01.01", date) == date(1990, 1, 1)  # date with dot.
    assert DataTypes.infer("2003.09.25", date) == date(2003, 9, 25)
    assert DataTypes.infer("25.09.2003", date) == date(2003, 9, 25)
    assert DataTypes.infer("10.09.2003", date) == date(2003, 9, 10)

    assert DataTypes.infer("1990/01/01", date) == date(1990, 1, 1)  # date with slash
    assert DataTypes.infer("2003/09/25", date) == date(2003, 9, 25)
    assert DataTypes.infer("25/09/2003", date) == date(2003, 9, 25)
    assert DataTypes.infer("10/09/2003", date) == date(2003, 9, 10)

    assert DataTypes.infer("1990 01 01", date) == date(1990, 1, 1)  # date with space
    assert DataTypes.infer("2003 09 25", date) == date(2003, 9, 25)
    assert DataTypes.infer("25 09 2003", date) == date(2003, 9, 25)
    assert DataTypes.infer("10 09 2003", date) == date(2003, 9, 10)

    assert DataTypes.infer("20030925", date) == date(2003, 9, 25)  # "iso stripped format strip"
    assert DataTypes.infer("19760704", date) == date(1976, 7, 4)  # "random format"),

    assert DataTypes.infer("7 4 1976", date) == date(1976, 4, 7)
    # assert DataTypes.infer("14 jul 1976", date) == date(1976, 7, 14)
    # assert DataTypes.infer("4 Jul 1976", date) == date(1976, 7, 4)

    # NOT HANDLED - ambiguous formats due to lack of 4 digits for year.
    # ("10 09 03", date(2003, 10, 9), "date with space"),
    # ("25 09 03", date(2003, 9, 25), "date with space"),
    # ("03 25 Sep", date(2003, 9, 25), "strangely ordered date"),
    # ("25 03 Sep", date(2025, 9, 3), "strangely ordered date"),
    # "10-09-03", date(2003, 10, 9),
    # ("10.09.03", date(2003, 10, 9), "date with dot"),
    # ("10/09/03", date(2003, 10, 9), "date with slash"),

    # NOT HANDLED - MDY formats are US locale.
    # assert DataTypes.infer("09-25-2003", date) == date(2003, 9, 25)
    # assert DataTypes.infer("09.25.2003", date) == date(2003, 9, 25)
    # assert DataTypes.infer("09/25/2003", date) == date(2003, 9, 25)
    # assert DataTypes.infer("09 25 2003", date) == date(2003, 9, 25)
    # assert DataTypes.infer('13NOV2017', date) == date(2017, 11, 13) # GH360

    # times
    isotime = time(23, 12, 11)
    assert DataTypes.infer(isotime.isoformat(), time) == time(23, 12, 11)
    assert DataTypes.infer("23:12:11", time) == time(23, 12, 11)
    assert DataTypes.infer("23:12:11.123456", time) == time(23, 12, 11, 123456)

    # datetimes
    isodatetime = datetime.now()
    assert DataTypes.infer(isodatetime.isoformat(), datetime) == isodatetime
    dirty_date = datetime(1990, 1, 1, 23, 12, 11, int(0.003 * 10 ** 6))
    assert DataTypes.infer("1990-01-01T23:12:11.003000", datetime) == dirty_date  # iso minus T microsecond
    assert DataTypes.infer("1990-01-01T23:12:11.003", datetime) == dirty_date  #
    assert DataTypes.infer("1990-01-01 23:12:11.003", datetime) == dirty_date  # iso space
    assert DataTypes.infer("1990/01/01T23:12:11.003", datetime) == dirty_date  # iso slash T
    assert DataTypes.infer("10/04/2007 00:00", datetime) == datetime(2007,4,10,0,0)
    assert DataTypes.infer("1990/01/01 23:12:11.003", datetime) == dirty_date  # iso slash
    assert DataTypes.infer("1990 01 01T23:12:11.003", datetime) == dirty_date  # iso space T
    assert DataTypes.infer("1990 01 01 23:12:11.003", datetime) == dirty_date  # iso space

    assert DataTypes.infer("2003-09-25T10:49:41", datetime) == datetime(2003, 9, 25, 10, 49, 41)  # iso minus T fields omitted.
    assert DataTypes.infer("2003-09-25T10:49", datetime) == datetime(2003, 9, 25, 10, 49)
    assert DataTypes.infer("2003-09-25T10", datetime) == datetime(2003, 9, 25, 10)

    assert DataTypes.infer("20080227T21:26:01.123456789", datetime) == datetime(2008, 2, 27, 21, 26, 1, 123456)  # high precision seconds
    assert DataTypes.infer("20030925T104941", datetime) == datetime(2003, 9, 25, 10, 49, 41)  # iso nospace T fields omitted.
    assert DataTypes.infer("20030925T1049", datetime) == datetime(2003, 9, 25, 10, 49, 0)
    assert DataTypes.infer("20030925T10", datetime) == datetime(2003, 9, 25, 10)

    assert DataTypes.infer("199709020908", datetime) == datetime(1997, 9, 2, 9, 8)
    assert DataTypes.infer("19970902090807", datetime) == datetime(1997, 9, 2, 9, 8, 7)
    assert DataTypes.infer("2003-09-25 10:49:41,502", datetime) == datetime(2003, 9, 25, 10, 49, 41, 502000)  # python logger format
    assert DataTypes.infer('0099-01-01T00:00:00', datetime) == datetime(99, 1, 1, 0, 0)  # 99 ad
    assert DataTypes.infer('0031-01-01T00:00:00', datetime) == datetime(31, 1, 1, 0, 0)  # 31 ad

    # NOT HANDLED. ambiguous format. Year is not 4 digits.
    # ("950404 122212", datetime(1995, 4, 4, 12, 22, 12), "random format"),
    # ("04.04.95 00:22", datetime(1995, 4, 4, 0, 22), "random format"),

    # NOT HANDLED. Month and Day names are locale dependent.
    # ("Thu Sep 25 10:36:28 2003", datetime(2003, 9, 25, 10, 36, 28), "date command format strip"),
    # ("Thu Sep 25 2003", datetime(2003, 9, 25), "date command format strip"),
    # ("  July   4 ,  1976   12:01:02   am  ", datetime(1976, 7, 4, 0, 1, 2), "extra space"),
    # ("Wed, July 10, '96", datetime(1996, 7, 10, 0, 0), "random format"),
    # ("1996.July.10 AD 12:08 PM", datetime(1996, 7, 10, 12, 8), "random format"),
    # ("7-4-76", datetime(1976, 7, 4), "random format"),
    # ("0:01:02 on July 4, 1976", datetime(1976, 7, 4, 0, 1, 2), "random format"),
    # ("July 4, 1976 12:01:02 am", datetime(1976, 7, 4, 0, 1, 2), "random format"),
    # ("Mon Jan  2 04:24:27 1995", datetime(1995, 1, 2, 4, 24, 27), "random format"),
    # ("Jan 1 1999 11:23:34.578", datetime(1999, 1, 1, 11, 23, 34, 578000), "random format"),


class Column(list):
    def __init__(self, header, datatype, allow_empty, data=None):
        super().__init__()
        assert isinstance(header, str)
        self.header = header
        assert isinstance(datatype, type)
        assert hasattr(DataTypes, datatype.__name__)
        self.datatype = datatype
        assert isinstance(allow_empty, bool)
        self.allow_empty = allow_empty

        if data:
            for v in data:
                self.append(v)  # append does the type check.

    def __eq__(self, other):
        if not isinstance(other, Column):
            a, b = self.__class__.__name__, other.__class__.__name__
            raise TypeError(f"cannot compare {a} with {b}")

        return all([
            self.header == other.header,
            self.datatype == other.datatype,
            self.allow_empty == other.allow_empty,
            len(self) == len(other),
            all(a == b for a, b in zip(self, other))
        ])

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return f"Column({self.header},{self.datatype},{self.allow_empty}) # ({len(self)} rows)"

    def __copy__(self):
        return self.copy()

    def copy(self):
        return Column(self.header, self.datatype, self.allow_empty, data=self[:])

    def to_json(self):
        return json.dumps({
            'header': self.header,
            'datatype': self.datatype.__name__,
            'allow_empty': self.allow_empty,
            'data': json.dumps([DataTypes.to_json(v) for v in self])
        })

    @classmethod
    def from_json(cls, json_):
        j = json.loads(json_)
        j['datatype'] = dtype = getattr(DataTypes, j['datatype'])
        j['data'] = [DataTypes.from_json(v, dtype) for v in json.loads(j['data'])]
        return Column(**j)

    def type_check(self, value):
        """ helper that does nothing unless it raises an exception. """
        if value is None:
            if not self.allow_empty:
                raise ValueError("None is not permitted.")
            return
        if not isinstance(value, self.datatype):
            raise TypeError(f"{value} is not of type {self.datatype}")

    def append(self, __object) -> None:
        self.type_check(__object)
        super().append(__object)

    def replace(self, values) -> None:
        assert isinstance(values, list)
        if len(values) != len(self):
            raise ValueError("input is not of same length as column.")
        for v in values:
            self.type_check(v)
        self.clear()
        self.extend(values)

    def __setitem__(self, key, value):
        self.type_check(value)
        super().__setitem__(key, value)


def basic_column_tests():
    # creating a column remains easy:
    c = Column('A', int, False)

    # so does adding values:
    c.append(44)
    c.append(44)
    assert len(c) == 2

    # and converting to and from json
    d = c.to_json()
    c2 = Column.from_json(d)
    assert len(c2) == 2

    # comparing columns is easy:
    assert c == c2
    assert c != Column('A', str, False)


class Table(object):
    def __init__(self, **kwargs):
        self.columns = {}
        self.metadata = {**kwargs}

    def __eq__(self, other):
        if not isinstance(other, Table):
            a, b = self.__class__.__name__, other.__class__.__name__
            raise TypeError(f"cannot compare {a} with {b}")
        if self.metadata != other.metadata:
            return False
        if any(a != b for a, b in zip(self.columns.values(), other.columns.values())):
            return False
        return True

    def __len__(self):
        """ returns length of longest column."""
        return max(len(c) for c in self.columns.values())

    def __bool__(self):
        return any(self.columns)

    def __copy__(self):
        t = Table()
        for col in self.columns.values():
            t.add_column(col.header, col.datatype, col.allow_empty, data=col[:])
        t.metadata = self.metadata.copy()
        return t

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        variation = ""
        lengths = {k: len(v) for k, v in self.columns.items()}
        if len(set(lengths.values())) != 1:
            longest_col = max(lengths.values())
            variation = f"(except {', '.join([f'{k}({v})' for k,v in lengths.items() if v < longest_col])})"
        return f"{self.__class__.__name__}() # {len(self.columns)} columns x {len(self)} rows {variation}"

    def show(self, *items):
        """ shows the table.
        param: items: column names, slice.
        :returns None. Output is printed to stdout.
        """
        if any(not isinstance(i, (str, slice)) for i in items):
            raise SyntaxError(f"unexpected input: {[not isinstance(i, (str, slice)) for i in items]}")

        slices = [i for i in items if isinstance(i, slice)]
        if len(slices) > 2: raise SyntaxError("1 > slices")
        if not slices:
            slc = slice(0, len(self), None)
        else:
            slc = slices[0]
        assert isinstance(slc, slice)

        headers = [i for i in items if isinstance(i, str)]
        if any(h not in self.columns for h in headers):
            raise ValueError(f"column not found: {[h for h in headers if h not in self.columns]}")
        if not headers:
            headers = list(self.columns)

        # starting to produce output
        c_lens = {}
        for h in headers:
            col = self.columns[h]
            assert isinstance(col, Column)
            c_lens[h] = max([len(col.header), len(str(col.datatype.__name__)), len(str(False))] + [len(str(v)) for v in col[slc]])

        print("+", "+".join(["=" * c_lens[h] for h in headers]), "+", sep="")
        print("|", "|".join([h.center(c_lens[h], " ") for h in headers]), "|", sep="")
        print("|", "|".join([self.columns[h].datatype.__name__.center(c_lens[h], " ") for h in headers]), "|", sep="")
        print("|", "|".join([str(self.columns[h].allow_empty).center(c_lens[h], " ") for h in headers]), "|", sep="")
        print("+", "+".join(["-" * c_lens[h] for h in headers]), "+", sep="")
        for row in self.filter(*tuple(headers) + (slc, )):
            print("|", "|".join([str(v).rjust(c_lens[h]) for v, h in zip(row, headers)]), "|", sep="")
        print("+", "+".join(["=" * c_lens[h] for h in headers]), "+", sep="")

    def copy(self):
        return self.__copy__()

    def to_json(self):
        # return json.dumps([c.to_json() for c in self.columns.values()])
        return json.dumps({
            'metadata' : self.metadata,
            'columns': [c.to_json() for c in self.columns.values()]
        })

    @classmethod
    def from_json(cls, json_):
        t = Table()
        data = json.loads(json_)
        t.metadata = data['metadata']
        for c in data['columns']:
            col = Column.from_json(c)
            col.header = t.check_for_duplicate_header(col.header)
            t.columns[col.header] = col
            t.__setattr__(col.header, col)
        return t

    def check_for_duplicate_header(self, header):
        assert isinstance(header, str)
        if not header:
            header = 'None'
        new_header = header
        counter = count(start=1)
        while hasattr(self, new_header):
            new_header = f"{header}_{next(counter)}"  # valid attr names must be ascii.
        return new_header

    def add_column(self, header, datatype, allow_empty=False, data=None):
        assert isinstance(header, str)
        header = self.check_for_duplicate_header(header)
        self.columns[header] = Column(header, datatype, allow_empty, data=data)

    def add_row(self, values):
        if not isinstance(values, tuple):
            raise TypeError(f"expected tuple, got {type(values)}")
        if len(values) != len(self.columns):
            raise ValueError(f"expected {len(self.columns)} values not {len(values)}: {values}")
        for value, col in zip(values, self.columns.values()):
            col.append(value)

    def __contains__(self, item):
        return item in self.columns

    def __iter__(self):
        raise AttributeError("use Table.rows or Table.columns")

    def __getitem__(self, item):
        """ returns rows as a tuple """
        if isinstance(item, int):
            item = slice(item,item+1,1)
        if isinstance(item, slice):
            start = 0 if item.start is None else item.start
            step = 1 if item.step is None else item.step
            stop = len(self.columns) if item.stop is None else item.stop

            t = Table()
            for col in self.columns.values():
                t.add_column(col.header, col.datatype, col.allow_empty, col[start:stop:step])
            return t
        else:
            return self.columns[item]

    def __setitem__(self, key, value):
        if key in self.columns and isinstance(value, list):
            c = self.columns[key]
            c.clear()
            for v in value:
                c.append(v)
        else:
            raise TypeError(f"Use add_column to add_column: {key}")

    def __delitem__(self, key):
        """ delete column as key """
        if key in self.columns:
            del self.columns[key]
        else:
            raise KeyError(f"key not found")

    def __setattr__(self, name, value):
        if isinstance(name, str) and hasattr(self, name):
            if name in self.columns and isinstance(value, list):
                col = self.columns[name]
                col.replace(value)
                return
        super().__setattr__(name, value)

    def compare(self, other):
        """ compares the metadata of two tables."""
        if not isinstance(other, Table):
            a, b = self.__class__.__name__, other.__class__.__name__
            raise TypeError(f"cannot compare type {b} with {a}")

        if self.metadata != other.metadata:
            raise ValueError("tables have different metadata.")
        for a, b in [[self, other], [other, self]]:  # check both dictionaries.
            for name, col in a.columns.items():
                if name not in b.columns:
                    raise ValueError(f"Column {name} not in other")
                col2 = b.columns[name]
                if col.datatype != col2.datatype:
                    raise ValueError(f"Column {name}.datatype different: {col.datatype}, {col2.datatype}")
                if col.allow_empty != col2.allow_empty:
                    raise ValueError(f"Column {name}.allow_empty is different")
        return True

    def __iadd__(self, other):
        """ enables Table_1 += Table_2 """
        self.compare(other)
        for h, col in self.columns.items():
            c2 = other.columns[h]
            col.extend(c2[:])
        return self

    def __add__(self, other):
        """ enables Table_3 = Table_1 + Table_2 """
        self.compare(other)
        cp = self.copy()
        for h, col in cp.columns.items():
            c2 = other.columns[h]
            col.extend(c2[:])
        return cp

    @property
    def rows(self):
        """ enables iteration

        for row in table.rows:
            print(row)

        """
        for ix in range(len(self)):
            item = tuple(c[ix] if ix < len(c) else None for c in self.columns.values())
            yield item

    def index(self, *args):
        """ Creates index on *args columns as d[(key tuple, ) = {index1, index2, ...} """
        idx = defaultdict(set)
        for ix, key in enumerate(self.filter(*args)):
            idx[key].add(ix)
        return idx

    def _sort_index(self, **kwargs):
        if not isinstance(kwargs, dict):
            raise ValueError("Expected keyword arguments")
        if not kwargs:
            kwargs = {c: False for c in self.columns}

        for k, v in kwargs.items():
            if k not in self.columns:
                raise ValueError(f"no column {k}")
            if not isinstance(v, bool):
                raise ValueError(f"{k} was mapped to {v} - a non-boolean")
        none_substitute = float('-inf')

        rank = {i: tuple() for i in range(len(self))}
        for key in kwargs:
            unique_values = {v: 0 for v in self.columns[key] if v is not None}
            for r, v in enumerate(sorted(unique_values, reverse=kwargs[key])):
                unique_values[v] = r
            for ix, v in enumerate(self.columns[key]):
                rank[ix] += (unique_values.get(v, none_substitute), )

        new_order = [(r, i) for i, r in rank.items()]  # tuples are listed and sort...
        new_order.sort()
        sorted_index = [i for r, i in new_order]  # new index is extracted.

        rank.clear()  # free memory.
        new_order.clear()

        return sorted_index

    def sort(self, **kwargs):
        """ Perform multi-pass sorting with precedence given order of column names.
        :param kwargs: keys: columns, values: 'reverse' as boolean.
        """
        sorted_index = self._sort_index(**kwargs)
        for col_name, col in self.columns.items():
            assert isinstance(col, Column)
            col.replace(values=[col[ix] for ix in sorted_index])

    def is_sorted(self, **kwargs):
        sorted_index = self._sort_index(**kwargs)
        if any(ix != i for ix, i in enumerate(sorted_index)):
            return False
        return True

    def filter(self, *items):
        """ enables iteration on a limited number of headers:

        >>> table.columns
        'a','b','c','d','e'

        for row in table.filter('b', 'a', 'a', 'c'):
            b,a,a,c = row ...

        returns values in same order as headers. """
        if any(not isinstance(i, (str, slice)) for i in items):
            raise SyntaxError(f"unexpected input: {[not isinstance(i, (str, slice)) for i in items]}")

        slices = [i for i in items if isinstance(i, slice)]
        if len(slices) > 2: raise SyntaxError("1 > slices")
        if not slices:
            slc = slice(None, len(self), None)
        else:
            slc = slices[0]
        assert isinstance(slc, slice)

        if slc.stop < 0:
            start = len(self) + slc.stop
            stop = len(self)
            step = 1 if slc.step is None else slc.step
        else:
            start = 0 if slc.start is None else slc.start
            stop = slc.stop
            step = 1 if slc.step is None else slc.step

        headers = [i for i in items if isinstance(i, str)]
        if any(h not in self.columns for h in headers): 
            raise ValueError(f"column not found: {[h for h in headers if h not in self.columns]}") 
        
        L = [self.columns[h] for h in headers]
        for ix in range(start, stop, step):
            item = tuple(c[ix] if ix < len(c) else None for c in L)
            yield item

    def all(self, **kwargs):
        """
        returns Table for rows where ALL kwargs match
        :param kwargs: dictionary with headers and values / boolean callable
        """
        if not isinstance(kwargs, dict):
            raise TypeError("did you remember to add the ** in front of your dict?")
        if not all(k in self.columns for k in kwargs):
            raise ValueError(f"Unknown column(s): {[k for k in kwargs if k not in self.columns]}")

        ixs = None
        for k, v in kwargs.items():
            col = self.columns[k]
            if ixs is None:  # first header.
                if callable(v):
                    ix2 = {ix for ix, i in enumerate(col) if v(i)}
                else:
                    ix2 = {ix for ix, i in enumerate(col) if v == i}

            else:  # remaining headers.
                if callable(v):
                    ix2 = {ix for ix in ixs if v(col[ix])}
                else:
                    ix2 = {ix for ix in ixs if v == col[ix]}

            if not isinstance(ixs, set):
                ixs = ix2
            else:
                ixs = ixs.intersection(ix2)

            if not ixs:  # There are no matches.
                break

        t = Table()
        for col in self.columns.values():
            t.add_column(col.header, col.datatype, col.allow_empty, data=[col[ix] for ix in ixs])
        return t

    def any(self, **kwargs):
        """
        returns Table for rows where ANY kwargs match
        :param kwargs: dictionary with headers and values / boolean callable
        """
        if not isinstance(kwargs, dict):
            raise TypeError("did you remember to add the ** in front of your dict?")

        ixs = set()
        for k, v in kwargs.items():
            col = self.columns[k]
            if callable(v):
                ix2 = {ix for ix, r in enumerate(col) if v(r)}
            else:
                ix2 = {ix for ix, r in enumerate(col) if v == r}
            ixs.update(ix2)

        t = Table()
        for col in self.columns.values():
            t.add_column(col.header, col.datatype, col.allow_empty, data=[col[ix] for ix in ixs])
        return t

    def _join_type_check(self, other, keys, columns):
        if not isinstance(other, Table):
            raise TypeError(f"Expected other to be type Table, not {type(other)}")
        if not isinstance(keys, list) and all(isinstance(k,str) for k in keys):
            raise TypeError(f"Expected keys as list of strings, not {type(keys)}")
        if not all(k in self.columns and k in other.columns for k in keys):
            union = list(self.columns) + list(other.columns)
            raise ValueError(f"column(s) not found: {[k for k in keys if k not in union]}")

    def left_join(self, other, keys, columns):
        """
        :param other: self, other = (left, right)
        :param keys: list of keys for the join
        :param columns: list of columns to retain
        :return: new table

        Example:
        SQL:   SELECT number, letter FROM left LEFT JOIN right on left.colour == right.colour
        Table: left_join = left_table.left_join(right_table, keys=['colour'], columns=['number', 'letter'])
        """
        self._join_type_check(other, keys, columns)  # raises if error

        left_join = Table()
        for col_name in columns:
            if col_name in self.columns:
                col = self.columns[col_name]
            elif col_name in other.columns:
                col = other.columns[col_name]
            else:
                raise ValueError(f"column name '{col_name}' not in any table.")
            left_join.add_column(col_name, col.datatype, allow_empty=True)

        left_ixs = range(len(self))
        right_idx = other.index(*keys)

        for left_ix in left_ixs:
            key = tuple(self[h][left_ix] for h in keys)
            right_ixs = right_idx.get(key, (None,))
            for right_ix in right_ixs:
                for col_name, column in left_join.columns.items():
                    if col_name in self:
                        column.append(self[col_name][left_ix])
                    elif col_name in other:
                        if right_ix is not None:
                            column.append(other[col_name][right_ix])
                        else:
                            column.append(None)
                    else:
                        raise Exception('bad logic')
        return left_join

    def inner_join(self, other, keys, columns):
        """
        :param other: table
        :param keys: list of keys
        :param columns: list of columns to retain
        :return: new Table

        Example:
        SQL:   SELECT number, letter FROM left INNER JOIN right ON left.colour == right.colour
        Table: inner_join = left_table.inner_join_with(right_table, keys=['colour'],  columns=['number','letter'])
        """
        self._join_type_check(other, keys, columns)  # raises if error

        inner_join = Table()
        for col_name in columns:
            if col_name in self.columns:
                col = self.columns[col_name]
            elif col_name in other.columns:
                col = other.columns[col_name]
            else:
                raise ValueError(f"column name '{col_name}' not in any table.")
            inner_join.add_column(col_name, col.datatype, allow_empty=True)

        key_union = set(self.filter(*keys)).intersection(set(other.filter(*keys)))

        left_ixs = self.index(*keys)
        right_ixs = other.index(*keys)

        for key in key_union:
            for left_ix in left_ixs.get(key, set()):
                for right_ix in right_ixs.get(key, set()):
                    for col_name, column in inner_join.columns.items():
                        if col_name in self:
                            column.append(self[col_name][left_ix])
                        elif col_name in other:
                            column.append(other[col_name][right_ix])
                        else:
                            raise Exception("bad logic.")
        return inner_join

    def outer_join(self, other, keys, columns):
        """
        :param other: table
        :param keys: list of keys
        :param columns: list of columns to retain
        :return: new Table

        Example:
        SQL:   SELECT number, letter FROM left OUTER JOIN right ON left.colour == right.colour
        Table: outer_join = left_table.outer_join(right_table, keys=['colour'], columns=['number','letter'])
        """
        self._join_type_check(other, keys, columns)  # raises if error

        outer_join = Table()
        for col_name in columns:
            if col_name in self.columns:
                col = self.columns[col_name]
            elif col_name in other.columns:
                col = other.columns[col_name]
            else:
                raise ValueError(f"column name '{col_name}' not in any table.")
            outer_join.add_column(col_name, col.datatype, allow_empty=True)

        left_ixs = range(len(self))
        right_idx = other.index(*keys)
        right_keyset = set(right_idx)

        for left_ix in left_ixs:
            key = tuple(self[h][left_ix] for h in keys)
            right_ixs = right_idx.get(key, (None,))
            right_keyset.discard(key)
            for right_ix in right_ixs:
                for col_name, column in outer_join.columns.items():
                    if col_name in self:
                        column.append(self[col_name][left_ix])
                    elif col_name in other:
                        if right_ix is not None:
                            column.append(other[col_name][right_ix])
                        else:
                            column.append(None)
                    else:
                        raise Exception('bad logic')

        for right_key in right_keyset:
            for right_ix in right_idx[right_key]:
                for col_name, column in outer_join.columns.items():
                    if col_name in self:
                        column.append(None)
                    elif col_name in other:
                        column.append(other[col_name][right_ix])
                    else:
                        raise Exception('bad logic')
        return outer_join


def basic_table_tests():
    # creating a table incrementally is straight forward:
    table = Table()
    table.add_column('A', int, False)
    assert 'A' in table

    table.add_column('B', str, allow_empty=False)
    assert 'B' in table

    # appending rows is easy:
    table.add_row((1, 'hello'))
    table.add_row((2, 'world'))

    # converting to and from json is easy:
    table_as_json = table.to_json()
    table2 = Table.from_json(table_as_json)

    zipped = zlib.compress(table_as_json.encode())
    a, b = len(zipped), len(table_as_json)
    print("zipping reduces to", a, "from", b, "bytes, e.g.", round(100 * a / b, 0), "% of original")

    # copying is easy:
    table3 = table.copy()

    # and checking for headers is simple:
    assert 'A' in table
    assert 'Z' not in table

    # comparisons are straight forward:
    assert table == table2 == table3

    # even if you only want to check metadata:
    table.compare(table3)  # will raise exception if they're different.

    # append is easy as + also work:
    table3x2 = table3 + table3
    assert len(table3x2) == len(table3) * 2

    # and so does +=
    table3x2 += table3
    assert len(table3x2) == len(table3) * 3

    # type verification is included:
    try:
        table.columns['A'][0] = 'Hallo'
        assert False, "A TypeError should have been raised."
    except TypeError:
        assert True

    # updating values is familiar to any user who likes a list:
    assert 'A' in table.columns
    assert isinstance(table.columns['A'], list)
    last_row = -1
    table['A'][last_row] = 44
    table['B'][last_row] = "Hallo"

    assert table != table2

    # if you try to loop and forget the direction, Table will tell you
    try:
        for row in table: # wont pass
            assert False, "not possible. Use for row in table.rows or for column in table.columns"
    except AttributeError:
        assert True

    _ = [table2.add_row(row) for row in table.rows]

    before = [r for r in table2.rows]
    assert before == [(1, 'hello'), (2, 'world'), (1, 'hello'), (44, 'Hallo')]

    # as is filtering for ALL that match:
    filter_1 = lambda x: 'llo' in x
    filter_2 = lambda x: x > 3

    after = table2.all(**{'B': filter_1, 'A': filter_2})

    assert list(after.rows) == [(44, 'Hallo')]

    # as is filtering or for ANY that match:
    after = table2.any(**{'B': filter_1, 'A': filter_2})

    assert list(after.rows) == [(1, 'hello'), (1, 'hello'), (44, 'Hallo')]

    # Imagine a table with columns a,b,c,d,e (all integers) like this:
    t = Table()
    for c in 'abcde':
        t.add_column(header=c, datatype=int, allow_empty=False, data=[i for i in range(5)])

    # we want to add two new columns using the functions:
    def f1(a,b,c): return a+b+c+1
    def f2(b,c,d): return b*c*d

    # and we want to compute two new columns 'f' and 'g':
    t.add_column(header='f', datatype=int, allow_empty=False)
    t.add_column(header='g', datatype=int, allow_empty=True)

    # we can now use the filter, to iterate over the table:
    for row in t.filter('a', 'b', 'c', 'd'):
        a, b, c, d = row

        # ... and add the values to the two new columns
        t['f'].append(f1(a, b, c))
        t['g'].append(f2(b, c, d))

    assert len(t) == 5
    assert list(t.columns) == list('abcdefg')
    t.show()


    # slicing is easy:
    table_chunk = table2[2:4]
    assert isinstance(table_chunk, Table)

    # we will handle duplicate names gracefully.
    table2.add_column('B', int, allow_empty=True)
    assert set(table2.columns) == {'A', 'B', 'B_1'}

    # you can delete a column as key...
    del table2['B_1']
    assert set(table2.columns) == {'A', 'B'}

    # adding a computed column is easy:
    table.add_column('new column', str, allow_empty=False, data=[f"{r}" for r in table.rows])

    # part of or the whole table is easy:
    table.show()

    table.show('A', slice(0, 1))

    # updating a column with a function is easy:
    f = lambda x: x * 10
    table['A'] = [f(r) for r in table['A']]

    # using regular indexing will also work.
    for ix, r in enumerate(table['A']):
        table['A'][ix] = r * 10

    # and it will tell you if you're not allowed:
    try:
        f = lambda x: f"'{x} as text'"
        table['A'] = [f(r) for r in table['A']]
        assert False, "The line above must raise a TypeError"
    except TypeError as error:
        print("The error is:", str(error))


    # works with all datatypes:
    now = datetime.now()

    table4 = Table()
    table4.add_column('A', int, False, data=[-1, 1])
    table4.add_column('A', int, True, data=[None, 1])  # None!
    table4.add_column('A', float, False, data=[-1.1, 1.1])
    table4.add_column('A', str, False, data=["", "1"])
    table4.add_column('A', bool, False, data=[False, True])
    table4.add_column('A', datetime, False, data=[now, now])
    table4.add_column('A', date, False, data=[now.date(), now.date()])
    table4.add_column('A', time, False, data=[now.time(), now.time()])

    table4_json = table4.to_json()
    table5 = Table.from_json(table4_json)

    # .. to json and back.
    assert table4 == table5

    # And finally: I can add metadata:
    table5.metadata['db_mapping'] = {'A': 'customers.customer_name',
                                     'A_2': 'product.sku',
                                     'A_4': 'locations.sender'}

    # which also jsonifies without fuzz.
    table5_json = table5.to_json()
    table5_from_json = Table.from_json(table5_json)
    assert table5 == table5_from_json

def lookup_tests():  # doing lookups is supported by indexing:
    table6 = Table()
    table6.add_column('A', str, data=['Alice', 'Bob', 'Bob', 'Ben', 'Charlie', 'Ben', 'Albert'])
    table6.add_column('B', str, data=['Alison', 'Marley', 'Dylan', 'Affleck', 'Hepburn', 'Barnes', 'Einstein'])

    index = table6.index('A')  # single key.
    assert index[('Bob',)] == {1, 2}

    index2 = table6.index('A', 'B')  # multiple keys.
    assert index2[('Bob', 'Dylan')] == {2}


def sql_join_tests():  # a couple of examples with SQL join:

    left = Table()
    left.add_column('number', int, allow_empty=True, data=[1, 2, 3, 4, None])
    left.add_column('colour', str, data=['black', 'blue', 'white', 'white', 'blue'])

    right = Table()
    right.add_column('letter', str, allow_empty=True, data=['a', 'b', 'c', 'd', None])
    right.add_column('colour', str, data=['blue', 'white', 'orange', 'white', 'blue'])

    # left join
    # SELECT number, letter FROM left LEFT JOIN right on left.colour == right.colour
    left_join = left.left_join(right, keys=['colour'], columns=['number', 'letter'])
    left_join.show()

    # inner join
    # SELECT number, letter FROM left JOIN right ON left.colour == right.colour
    inner_join = left.inner_join(right, keys=['colour'], columns=['number', 'letter'])
    inner_join.show()

    # outer join
    # SELECT number, letter FROM left OUTER JOIN right ON left.colour == right.colour
    outer_join = left.outer_join(right, keys=['colour'], columns=['number', 'letter'])
    outer_join.show()

    assert left_join != inner_join
    assert inner_join != outer_join
    assert left_join != outer_join


def sortation_tests():  # Sortation

    table7 = Table()
    table7.add_column('A', int, data=[1, None, 8, 3, 4, 6, 5, 7, 9], allow_empty=True)
    table7.add_column('B', int, data=[10, 100, 1, 1, 1, 1, 10, 10, 10])
    table7.add_column('C', int, data=[0, 1, 0, 1, 0, 1, 0, 1, 0])

    assert not table7.is_sorted()

    sort_order = {'B': False, 'C': False, 'A': False}

    table7.sort(**sort_order)

    assert list(table7.rows) == [
        (4, 1, 0),
        (8, 1, 0),
        (3, 1, 1),
        (6, 1, 1),
        (1, 10, 0),
        (5, 10, 0),
        (9, 10, 0),
        (7, 10, 1),
        (None, 100, 1)
    ]

    assert list(table7.filter('A', 'B', slice(4, 8))) == [(1, 10), (5, 10), (9, 10), (7, 10)]

    assert table7.is_sorted(**sort_order)


class GroupbyFunction(object):
    def __init__(self, datatype):
        hasattr(DataTypes, datatype.__name__)
        self.datatype = datatype


class Limit(GroupbyFunction):
    def __init__(self, datatype):
        super().__init__(datatype)
        self.value = None
        self.f = None

    def update(self, value):
        if value is None:
            pass
        elif self.value is None:
            self.value = value
        else:
            self.value = self.f((value, self.value))


class Max(Limit):
    def __init__(self, datatype):
        super().__init__(datatype)
        self.f = max


class Min(Limit):
    def __init__(self, datatype):
        super().__init__(datatype)
        self.f = min


class Sum(Limit):
    def __init__(self, datatype):
        super().__init__(datatype)
        self.f = sum


class First(GroupbyFunction):
    def __init__(self, datatype):
        super().__init__(datatype)
        self.value = None

    def update(self, value):
        if self.value is None:
            if value is not None:
                self.value = value


class Last(GroupbyFunction):
    def __init__(self, datatype):
        super().__init__(datatype)
        self.value = None

    def update(self, value):
        if value is not None:
            self.value = value


class Count(GroupbyFunction):
    def __init__(self, datatype):
        super().__init__(datatype=int)  # datatype will be int no matter what type is given.
        self.value = 0

    def update(self, value):
        if value is not None:
            self.value += 1


class CountUnique(GroupbyFunction):
    def __init__(self, datatype):
        super().__init__(datatype=int)  # datatype will be int no matter what type is given.
        self.items = set()

    def update(self, value):
        if value is not None:
            self.items.add(value)
            self.value = len(self.items)


class Average(GroupbyFunction):
    def __init__(self, datatype):
        super().__init__(datatype=float)  # datatype will be float no matter what type is given.
        self.sum = 0
        self.count = 0
        self.value = 0

    def update(self, value):
        if value is not None:
            self.sum += value
            self.count += 1
            self.value = self.sum / self.count


class StandardDeviation(GroupbyFunction):
    def __init__(self, datatype):
        super().__init__(datatype=float)  # datatype will be float no matter what type is given.
        self.count = 0
        self.mean = 0
        self.c = 0.0

    def update(self, value):
        if value is not None:
            self.count += 1
            dt = value - self.mean
            self.mean += dt / self.count
            self.c += dt * (value - self.mean)

    @property
    def value(self):
        if self.count <= 1:
            return 0.0
        variance = self.c / (self.count - 1)
        return variance ** (1 / 2)


class Histogram(GroupbyFunction):
    def __init__(self, datatype):
        super().__init__(datatype)
        self.hist = defaultdict(int)

    def update(self, value):
        if value is not None:
            self.hist[value] += 1


class Median(Histogram):
    def __init__(self, datatype):
        super().__init__(datatype)

    @property
    def value(self):
        midpoint = sum(self.hist.values()) / 2
        total = 0
        for k, v in self.hist.items():
            total += v
            if total > midpoint:
                return k


class Mode(Histogram):
    def __init__(self, datatype):
        super().__init__(datatype)

    @property
    def value(self):
        L = [(v, k) for k, v in self.hist.items()]
        L.sort(reverse=True)
        frequency, most_frequent = L[0]  # top of the list.
        return most_frequent


class GroupBy(object):
    functions = [
        Max, Min, Sum, First, Last,
        Count, CountUnique,
        Average, StandardDeviation, Median, Mode
    ]
    function_names = {f.__name__: f for f in functions}

    def __init__(self, keys, functions):
        """
        :param keys: headers for grouping
        :param functions: list of headers and functions.
        :return: None.
        """
        assert isinstance(keys, list)
        assert len(set(keys)) == len(keys), "duplicate key found."
        self.keys = keys

        assert isinstance(functions, list)
        assert all(len(i) == 2 for i in functions)
        assert all(isinstance(a, str) and issubclass(b, GroupbyFunction) for a, b in functions)
        self.groupby_functions = functions  # list with header name and function name

        self.output = None   # class Table.
        self.required_headers = None  # headers for reading input.
        self.data = defaultdict(list)  # key: [list of groupby functions]
        self.function_classes = []  # initiated functions.

        # Order is preserved so that this is doable:
        # for header, function, function_instances in zip(self.groupby_functions, self.function_classes) ....

    def setup(self, table):
        self.output = Table()
        self.required_headers = self.keys + [h for h, fn in self.groupby_functions]

        for h in self.keys:
            col = table[h]
            self.output.add_column(header=h, datatype=col.datatype, allow_empty=False)  # add column for keys

        self.function_classes = []
        for h, fn in self.groupby_functions:
            col = table[h]
            assert isinstance(col, Column)
            f_instance = fn(col.datatype)
            assert isinstance(f_instance, GroupbyFunction)
            self.function_classes.append(f_instance)

            function_name = f"{fn.__name__}({h})"
            self.output.add_column(header=function_name, datatype=f_instance.datatype, allow_empty=True)  # add column for fn's.

    def __iadd__(self, other):
        """
        To view results use `for row in self.rows`
        To add more data use self += new data (Table)
        """
        assert isinstance(other, Table)
        if self.output is None:
            self.setup(other)
        else:
            self.output.compare(other)  # this will raise if there are problems

        for row in other.filter(*self.required_headers):
            d = {h: v for h, v in zip(self.required_headers, row)}
            key = tuple([d[k] for k in self.keys])
            functions = self.data.get(key)
            if not functions:
                functions = [fn.__class__(fn.datatype) for fn in self.function_classes]
                self.data[key] = functions

            for (h, fn), f in zip(self.groupby_functions, functions):
                f.update(d[h])
        return self

    def _generate_table(self):
        for key, functions in self.data.items():
            row = key + tuple(fn.value for fn in functions)
            self.output.add_row(row)
        self.data.clear()  # hereby we only create the table once.
        self.output.sort(**{k: False for k in self.keys})

    @property
    def table(self):
        if self.output is None:
            return None

        if self.data:
            self._generate_table()

        assert isinstance(self.output, Table)
        return self.output

    @property
    def rows(self):
        if self.output is None:
            return None

        if self.data:
            self._generate_table()

        assert isinstance(self.output, Table)
        for row in self.output.rows:
            yield row

    def pivot(self, columns):
        """ pivots the groupby so that `columns` become new columns.

        :param args: column names
        :param values_as_rows: boolean, if False: values as columns.
        :return: New Table

        Example:
        g.show()
        +=====+=====+======+======+
        |  a  |  b  |Max(f)|Sum(f)|
        | int | int | int  | int  |
        |False|False| True | True |
        +-----+-----+------+------+
        |    0|    0|     1|     3|
        |    1|    1|     4|    12|
        |    2|    2|     7|    21|
        |    3|    3|    10|    30|
        |    4|    4|    13|    39|
        +=====+=====+======+======+

        g.pivot('b')
        +=====+==========+==========+==========+==========+==========+==========+==========+==========+==========+==========+
        |  a  |Max(f,b=0)|Sum(f,b=0)|Max(f,b=1)|Sum(f,b=1)|Max(f,b=2)|Sum(f,b=2)|Max(f,b=3)|Sum(f,b=3)|Max(f,b=4)|Sum(f,b=4)|
        | int |   int    |   int    |   int    |   int    |   int    |   int    |   int    |   int    |   int    |   int    |
        |False|   True   |   True   |   True   |   True   |   True   |   True   |   True   |   True   |   True   |   True   |
        +-----+----------+----------+----------+----------+----------+----------+----------+----------+----------+----------+
        |    0|         1|         3|      None|      None|      None|      None|      None|      None|      None|      None|
        |    1|      None|      None|         4|        12|      None|      None|      None|      None|      None|      None|
        |    2|      None|      None|      None|      None|         7|        21|      None|      None|      None|      None|
        |    3|      None|      None|      None|      None|      None|      None|        10|        30|      None|      None|
        |    4|      None|      None|      None|      None|      None|      None|      None|      None|        13|        39|
        +=====+==========+==========+==========+==========+==========+==========+==========+==========+==========+==========+

        """
        if not isinstance(columns, list):
            raise TypeError(f"expected columns as list, not {type(columns)}")
        if not all(isinstance(i,str) for i in columns):
            raise TypeError(f"column name not str: {[i for i in columns if not isinstance(i,str)]}")

        if self.output is None:
            return None

        if self.data:
            self._generate_table()

        assert isinstance(self.output, Table)
        if any(i not in self.output.columns for i in columns):
            raise ValueError(f"column not found in groupby: {[i not in self.output.columns for i in columns]}")

        sort_order = {k: False for k in self.keys}
        if not self.output.is_sorted(**sort_order):
            self.output.sort(**sort_order)

        t = Table()
        for col_name, col in self.output.columns.items():  # add vertical groups.
            if col_name in self.keys and col_name not in columns:
                t.add_column(col_name, col.datatype, allow_empty=False)

        tup_length = 0
        for column_key in self.output.filter(*columns):  # add horizontal groups.
            col_name = ",".join(f"{h}={v}" for h, v in zip(columns, column_key))  # expressed "a=0,b=3" in column name "Sum(g, a=0,b=3)"
            for (header, function), function_instances in zip(self.groupby_functions, self.function_classes):
                t.add_column(f"{function.__name__}({header},{col_name})", datatype=function_instances.datatype, allow_empty=True)
                tup_length += 1

        # add rows.
        key_index = {k: i for i, k in enumerate(self.output.columns)}
        old_v_keys = tuple(None for k in self.keys if k not in columns)

        for row in self.output.rows:
            v_keys = tuple(row[key_index[k]] for k in self.keys if k not in columns)
            if v_keys != old_v_keys:
                t.add_row(v_keys + tuple(None for i in range(tup_length)))
                old_v_keys = v_keys

            function_values = [v for h, v in zip(self.output.columns, row) if h not in self.keys]

            col_name = ",".join(f"{h}={row[key_index[h]]}" for h in columns)
            for (header, function), fi in zip(self.groupby_functions, function_values):
                column_key = f"{function.__name__}({header},{col_name})"
                t[column_key][-1] = fi

        return t


def groupby_tests():
    t = Table()
    for c in 'abcde':
        t.add_column(header=c, datatype=int, allow_empty=False, data=[i for i in range(5)])

    # we want to add two new columns using the functions:
    def f1(a, b, c):
        return a + b + c + 1

    def f2(b, c, d):
        return b * c * d

    # and we want to compute two new columns 'f' and 'g':
    t.add_column(header='f', datatype=int, allow_empty=False)
    t.add_column(header='g', datatype=int, allow_empty=True)

    # we can now use the filter, to iterate over the table:
    for row in t.filter('a', 'b', 'c', 'd'):
        a, b, c, d = row

        # ... and add the values to the two new columns
        t['f'].append(f1(a, b, c))
        t['g'].append(f2(b, c, d))

    assert len(t) == 5
    assert list(t.columns) == list('abcdefg')
    t.show()


    g = GroupBy(keys=['a', 'b'],
                functions=[('f', Max),
                           ('f', Min),
                           ('f', Sum),
                           ('f', First),
                           ('f', Last),
                           ('f', Count),
                           ('f', CountUnique),
                           ('f', Average),
                           ('f', StandardDeviation),
                           ('a', StandardDeviation),
                           ('f', Median),
                           ('f', Mode),
                           ('g', Median)])
    t2 = t + t
    assert len(t2) == 2 * len(t)
    t2.show()

    g += t2

    assert list(g.rows) == [
        (0, 0, 1, 1, 2, 1, 1, 2, 1, 1.0, 0.0, 0.0, 1, 1, 0),
        (1, 1, 4, 4, 8, 4, 4, 2, 1, 4.0, 0.0, 0.0, 4, 4, 1),
        (2, 2, 7, 7, 14, 7, 7, 2, 1, 7.0, 0.0, 0.0, 7, 7, 8),
        (3, 3, 10, 10, 20, 10, 10, 2, 1, 10.0, 0.0, 0.0, 10, 10, 27),
        (4, 4, 13, 13, 26, 13, 13, 2, 1, 13.0, 0.0, 0.0, 13, 13, 64)
    ]

    g.table.show()

    g2 = GroupBy(keys=['a', 'b'], functions=[('f', Max), ('f', Sum)])
    g2 += t + t + t

    g2.table.show()

    pivot_table = g2.pivot(columns=['b'])

    pivot_table.show()


# reading and writing data.
# --------------------------
def split_by_sequence(text, sequence):
    chunks = tuple()
    for element in sequence:
        idx = text.find(element)
        if idx < 0:
            raise ValueError(f"'{element}' not in row")
        chunk, text = text[:idx], text[len(element) + idx:]
        chunks += (chunk,)
    chunks += (text,)  # the remaining text.
    return chunks


def detect_encoding(path):
    assert isinstance(path, Path)
    for encoding in ['ascii', 'utf-8', 'utf-16', 'windows-1252']:
        try:
            _ = path.open('r', encoding=encoding).read(100)
            return encoding
        except (UnicodeDecodeError, UnicodeError):
            pass
    raise UnicodeDecodeError


def detect_seperator(path, encoding):
    """
    :param path: pathlib.Path objects
    :param encoding: file encoding.
    :return: 1 character.

    After reviewing the logic in the CSV sniffer, I concluded that all it
    really does is to look for a non-text character. As the separator is
    determined by the first line, which almost always is a line of headers,
    the text characters will be utf-8,16 or ascii letters plus white space.
    This leaves the characters ,;:| and \t as potential separators, with one
    exception: files that use whitespace as separator. My logic is therefore
    to (1) find the set of characters that intersect with ',;:|\t' which in
    practice is a single character, unless (2) it is empty whereby it must
    be whitespace.
    """
    text = ""
    for line in path.open('r', encoding=encoding):  # pick the first line only.
        text = line
        break
    seps = set(',\t;:|').intersection(text)
    if not seps:
        if " " in text:
            return " "
        else:
            raise ValueError("separator not detected")
    if len(seps) == 1:
        return seps.pop()
    else:
        frq = [(text.count(i), i) for i in seps]
        frq.sort(reverse=True)  # most frequent first.
        return frq[0][-1]


def text_reader(path, split_sequence=None, sep=None):
    """ txt, tab & csv reader """
    if not isinstance(path, Path):
        raise ValueError(f"expected pathlib.Path, got {type(path)}")

    # detect newline format
    windows = '\n'
    unix = '\r\n'

    encoding = detect_encoding(path)  # detect encoding

    if split_sequence is None and sep is None:  #
        sep = detect_seperator(path, encoding)

    t = Table()
    t.metadata['filename'] = path.name
    n_columns = None
    with path.open('r', encoding=encoding) as fi:
        for line in fi:
            end = windows if line.endswith(windows) else unix

            line = line.rstrip(end)
            if split_sequence:
                values = split_by_sequence(line, split_sequence)
            elif line.count('"') >= 2 or line.count("'") >= 2:
                values = text_escape(line, sep=sep)
            else:
                values = tuple((i.lstrip().rstrip() for i in line.split(sep)))

            if not t.columns:

                for v in values:
                    header = v.rstrip(" ").lstrip(" ")
                    t.add_column(header, datatype=str, allow_empty=True)
                n_columns = len(values)
            else:
                if n_columns - 1 == len(values):
                    values += ('', )
                t.add_row(values)
    return [t]  # file-reader expects a list of tables.


def text_escape(s, escape='"', sep=';'):
    """ escapes text marks using a depth measure. """
    assert isinstance(s, str)
    word, words = [], tuple()
    in_esc_seq = False
    for ix, c in enumerate(s):
        if c == escape:
            if in_esc_seq:
                if ix+1 != len(s) and s[ix + 1] != sep:
                    word.append(c)
                    continue  # it's a fake escape.
                in_esc_seq = False
            else:
                in_esc_seq = True
            if word:
                words += ("".join(word),)
                word.clear()
        elif c == sep and not in_esc_seq:
            if word:
                words += ("".join(word),)
                word.clear()
        else:
            word.append(c)

    if word:
        if word:
            words += ("".join(word),)
            word.clear()
    return words


def text_escape_tests():
    te = text_escape('"t"')
    assert te == ("t",)

    te = text_escape('"t";"3";"2"')
    assert te == ("t", "3", "2")

    te = text_escape('"this";"123";234;"this";123;"234"')
    assert te == ('this', '123', '234', 'this', '123', '234')

    te = text_escape('"this";"123";"234"')
    assert te == ("this", "123", "234")

    te = text_escape('"this";123;234')
    assert te == ("this", "123", "234")

    te = text_escape('"this";123;"234"')
    assert te == ("this", "123", "234")

    te = text_escape('123;"1\'3";234')
    assert te == ("123", "1'3", "234"), te

    te = text_escape('"1000627";"MOC;Sportpouzdro;pás;krk;XL;černá";"2.080,000";"CM3";2')
    assert te == ("1000627", "MOC;Sportpouzdro;pás;krk;XL;černá", "2.080,000", "CM3", '2')

    te = text_escape('"1000294";"S2417DG 24"" LED monitor (210-AJWM)";"47.120,000";"CM3";3')
    assert te == ('1000294', 'S2417DG 24"" LED monitor (210-AJWM)', '47.120,000', 'CM3', '3')


def excel_reader(path):
    if not isinstance(path, Path):
        raise ValueError(f"expected pathlib.Path, got {type(path)}")
    sheets = xlrd.open_workbook(str(path), logfile='', on_demand=True)
    assert isinstance(sheets, xlrd.Book)
    tables = []
    for sheet in sheets.sheets():
        if sheet.nrows == sheet.ncols == 0:
            continue
        else:
            table = excel_sheet_reader(sheet)
            table.metadata['filename'] = path.name
            tables.append(table)
    return tables


def excel_datetime(value):
    Y, M, D, h, m, s = xlrd.xldate_as_tuple(value, 0)
    if all((Y, M, D, h, m, s)):
        return f"{Y}-{M}-{D}T{h}-{m}-{s}"
    if all((Y, M, D)):
        return f"{Y}-{M}-{D}"
    if all((h, m, s)):
        return f"{h}:{m}:{s}"
    return value  # .. we tried...


def excel_sheet_reader(sheet):
    assert isinstance(sheet, xlrd.sheet.Sheet)

    excel_datatypes = {0: lambda x: None,  # empty string
                       1: lambda x: str(x),  # unicode string
                       2: lambda x: x,  # numeric int or float
                       3: lambda x: excel_datetime(x),  # datetime float
                       4: lambda x: True if x == 1 else False,  # boolean
                       5: lambda x: str(x)}  # error code

    t = Table()
    t.metadata['sheet_name'] = sheet.name

    for column_index in range(sheet.ncols):
        data = []
        for row_index in range(sheet.nrows):
            etype = sheet.cell_type(row_index, column_index)
            value = sheet.cell_value(row_index, column_index)
            data.append(excel_datatypes[etype](value))

        dtypes = {type(v) for v in data[1:]}
        allow_empty = True if None in dtypes else False
        dtypes.discard(None)

        if len(dtypes) == 1:
            header, dtype, data = str(data[0]), dtypes.pop(), data[1:]
        else:
            header, dtype, data = str(data[0]), str, [str(v) for v in data[1:]]
        t.add_column(header, dtype, allow_empty, data)
    return t


def zip_reader(path):
    if not isinstance(path, Path):
        raise ValueError(f"expected pathlib.Path, got {type(path)}")
    raise NotImplementedError


def log_reader(path):
    if not isinstance(path, Path):
        raise ValueError(f"expected pathlib.Path, got {type(path)}")
    for line in path.open()[:10]:
        print(repr(line))
    print("please declare separators. Blank return means 'done'.")
    split_sequence = []
    while True:
        response = input(">")
        if response == "":
            break
        print("got", repr(response))
        split_sequence.append(response)
    table = text_reader(path, split_sequence=split_sequence)
    return table


def find_format(table):
    """ common function for harmonizing formats AFTER import. """
    assert isinstance(table, Table)

    for col_name, column in table.columns.items():
        values = set(column)  # reduce the values to the minimum set.

        ni = DataTypes.nones.intersection(values)  # remove known values for None.
        if ni:
            column.allow_empty = True
            for i in ni:
                values.remove(i)
        else:
            column.allow_empty = False

        works = []
        if not values:
            works.append((0, DataTypes.str))
        else:
            for dtype in DataTypes.types:  # try all datatypes.
                c = 0
                for v in values:
                    try:
                        DataTypes.infer(v, dtype)  # handles None gracefully.
                        c += 1
                    except (ValueError, TypeError):
                        break
                works.append((c, dtype))
                if c == len(values):
                    break  # we have a complete match for the simplest
                    # dataformat for all values. No need to do more work.

        for c, dtype in works:
            if c == len(values):
                column.datatype = dtype
                column.replace([DataTypes.infer(v, dtype) if v not in DataTypes.nones else None for v in column])
                break


def file_reader(path, **kwargs):
    assert isinstance(path, Path)
    readers = {
        'csv': [text_reader, {}],
        'tsv': [text_reader, {'sep': "\t"}],
        'txt': [text_reader, {}],
        'xls': [],
        'xlsx': [excel_reader, {}],
        'xlsm': [],
        'excelsheet': [],
        'zip': [],
        'log': [log_reader, {'sep': False}]
    }

    extension = path.name.split(".")[-1]
    reader, default_kwargs = readers[extension]
    kwargs = {**default_kwargs, **kwargs}

    tables = reader(path, **kwargs)
    assert isinstance(tables, list), "programmer forgot to return a list of tables."
    assert all(isinstance(i, Table) for i in tables), "programmer returned something else than a Table"
    for table in tables:
        find_format(table)
    return tables


# file reader tests.
#---------------------

def text_reader_test_00():
    csv_file = Path(__file__).parent / "files" / "123.csv"

    table7 = Table(filename=csv_file.name)
    table7.metadata['filename'] = '123.csv'
    table7.add_column('A', int, data=[1, None, 8, 3, 4, 6, 5, 7, 9], allow_empty=True)
    table7.add_column('B', int, data=[10, 100, 1, 1, 1, 1, 10, 10, 10])
    table7.add_column('C', int, data=[0, 1, 0, 1, 0, 1, 0, 1, 0])
    sort_order = {'B': False, 'C': False, 'A': False}
    table7.sort(**sort_order)

    headers = ", ".join([c for c in table7.columns])
    data = [headers]
    for row in table7.rows:
        data.append(", ".join(str(v) for v in row))

    s = "\n".join(data)
    print(s)
    csv_file.write_text(s)  # write
    tr_table = file_reader(csv_file)[0]  # read
    csv_file.unlink()  # cleanup

    tr_table.show()
    find_format(tr_table)

    assert tr_table == table7


def text_reader_test_01():
    path = Path(__file__).parent / "files" / 'amcap_test_data.csv'
    assert path.exists()
    table = file_reader(path)[0]
    table.show()

    amcap_test_data = Table(filename=path.name)
    for int_type in ['sku', 'quantity', "ti", "hi"]:
        amcap_test_data.add_column(int_type, int)
    for float_type in ["L", "W", "H", "weight", ]:
        amcap_test_data.add_column(float_type, float)
    for date_type in ["order_date", "ship_date"]:
        amcap_test_data.add_column(date_type, date)
    for boolean in ["liquid", "manual", "fragile"]:
        amcap_test_data.add_column(boolean, bool)

    assert table.compare(amcap_test_data), table.compare(amcap_test_data)
    assert len(table) == 5


def text_reader_test_02():
    path = Path(__file__).parent / "files" / 'book1.csv'
    assert path.exists()
    table = file_reader(path)[0]
    table.show(slice(0,10))

    book1_csv = Table(filename=path.name)
    book1_csv.add_column('a', int)
    for float_type in list('bcdef'):
        book1_csv.add_column(float_type, float)

    assert table.compare(book1_csv), table.compare(book1_csv)
    assert len(table) == 45


def text_reader_test_03():
    path = Path(__file__).parent / "files" / 'book1.txt'
    assert path.exists()
    table = file_reader(path)[0]
    table.show(slice(0,10))

    book1_csv = Table(filename=path.name)
    book1_csv.add_column('a', int)
    for float_type in list('bcdef'):
        book1_csv.add_column(float_type, float)

    assert table.compare(book1_csv), table.compare(book1_csv)
    assert len(table) == 45


def text_reader_test_04():
    path = Path(__file__).parent / "files" / 'box_packer_test_data.csv'
    assert path.exists()
    table = file_reader(path)[0]
    table.show(slice(0, 10))

    book1_csv = Table(filename=path.name)
    headers = "TestCase,Numerat.,Denom.,Volume,Gross weight,pcs per outer,L (carton),W (carton),H (carton),Effective Casepack per layer (Ti),Effective pcs per layer,Hi (1.20m) CHEP,Hi (2.00m) CHEP,Hi (1.80m) 1-WAY,Effective pieces per 1.275m pallet,Packed pallet height,Total Netto weight,Total Netto Volume,Waste%A"
    headers = headers.split(",")
    book1_csv.add_column(headers[0], str)
    for float_type in headers[1:]:
        book1_csv.add_column(float_type.rstrip().lstrip(), float)

    assert table.compare(book1_csv), table.compare(book1_csv)
    assert len(table) == 5856, len(table)


def text_reader_test_05():
    path = Path(__file__).parent / "files" / 'empty_column_values.csv'
    assert path.exists()
    table = file_reader(path)[0]
    table.show(slice(0, 10))
    table.show(slice(-15))

    book1_csv = Table(filename=path.name)
    headers = "Date,OrderId,Customer,SKU,Qty"
    headers = headers.split(",")
    book1_csv.add_column(headers[0], date, allow_empty=True)
    for float_type in headers[1:4]:
        book1_csv.add_column(float_type.rstrip().lstrip(), int, allow_empty=True)
    book1_csv.add_column(headers[-1], float, allow_empty=True)

    assert table.compare(book1_csv), table.compare(book1_csv)
    assert len(table) == 53, len(table)


def text_reader_test_06():
    path = Path(__file__).parent / "files" / 'encoding_utf8_test.csv'
    assert path.exists()
    table = file_reader(path, sep=';')[0]
    table.show(slice(0, 10))
    table.show(slice(-15))

    book1_csv = Table(filename=path.name)
    book1_csv.add_column('Item', int)
    book1_csv.add_column('Materiál', str)
    book1_csv.add_column('Objem', float)
    book1_csv.add_column('Jednotka objemu', str)
    book1_csv.add_column('Free Inv Pcs', int)

    assert table.compare(book1_csv), table.compare(book1_csv)
    assert len(table) == 99, len(table)


def text_reader_test_07():
    path = Path(__file__).parent / "files" / 'encoding_windows1250_test.csv'
    assert path.exists()
    table = file_reader(path, sep=';')[0]
    table.show(slice(0, 10))
    table.show(slice(-15))

    book1_csv = Table(filename=path.name)
    book1_csv.add_column('Item', int)
    book1_csv.add_column('Materiál', str)
    book1_csv.add_column('Objem', float)
    book1_csv.add_column('Jednotka objemu', str)
    book1_csv.add_column('Free Inv Pcs', int)
    assert table.compare(book1_csv), table.compare(book1_csv)
    assert len(table) == 99, len(table)


def text_reader_test_08():
    path = Path(__file__).parent / "files" / 'frito.csv'
    assert path.exists()
    start = process_time_ns()
    table = file_reader(path)[0]
    end = process_time_ns()
    fields = len(table) * len(table.columns)
    print("{:,} fields/seccond".format(round(1e9 * fields / max(1, end - start), 0)))

    table_source = Table(filename=path.name)
    table_source.add_column('prod_slbl', int)
    table_source.add_column('sale_date', datetime)
    table_source.add_column('cust_nbr', int)
    table_source.add_column('Prod Tkt Descp Txt', str)
    table_source.add_column('Case Qty', int)
    table_source.add_column('EA Location', str)
    table_source.add_column('CDY/Cs', int)
    table_source.add_column('EA/Cs', int)
    table_source.add_column('EA/CDY', int)
    table_source.add_column('Ordered As', str)
    table_source.add_column('Picked As', str)
    table_source.add_column('Cs/Pal', int)
    table_source.add_column('SKU', int)
    table_source.add_column('Order_Number', str)
    table_source.add_column('cases', int)
    assert table.compare(table_source)
    assert len(table) == 9999, len(table)


def text_reader_test_09():
    path = Path(__file__).parent / "files" / 'large_skus.csv'
    assert path.exists()
    start = process_time_ns()
    table = file_reader(path)[0]
    end = process_time_ns()
    table.show(slice(5))
    fields = len(table) * len(table.columns)
    print("{:,} fields/seccond".format(round(1e9 * fields / max(1, end - start), 0)))

    large_skus = Table(filename=path.name)
    large_skus.add_column('LadeGrp', int, False)
    large_skus.add_column('Einkaufsgruppe (Purchase Group)', int, False)
    large_skus.add_column('Artikelnummer (SKU ID)', int, False)
    large_skus.add_column('Artikeltext (SKU description)', str, False)
    large_skus.add_column('Breite cm (width)', str, True)
    large_skus.add_column('L�nge cm (length)', str, True)
    large_skus.add_column('H�he cm (height)', str, True)
    large_skus.add_column('Volumen cm� (cube)', str, True)
    large_skus.add_column('Bruttogewicht kg (weight)', str, True)
    large_skus.add_column('DMk', str, True)
    large_skus.add_column('Aktuelle Pick-Strategie (currently picked strategie)in Berbersdorf', str, True)
    large_skus.add_column('Kolli Inhalt (case quantity)', float, True)
    large_skus.add_column('Lagen Inhalt (cases per layer)', float, True)
    large_skus.add_column('Paletten Inhalt (pallet quantity)', float, True)
    large_skus.add_column('Umkarton Inhalt (pieces per outer package)', str, True)
    large_skus.add_column('Display-paletten (display pallet)', str, True)

    assert table.compare(large_skus)
    assert len(table) == 45745, len(table)


def text_reader_test_10():
    path = Path(__file__).parent / "files" / 'messy_orderlines.csv'
    assert path.exists()
    start = process_time_ns()
    table = file_reader(path)[0]
    end = process_time_ns()
    table.show(slice(5))
    fields = len(table) * len(table.columns)
    print("{:,} fields/seccond".format(round(1e9 * fields / max(1, end - start), 0)))

    messy_orderlines = Table(filename=path.name)
    messy_orderlines.add_column('Date', date, False)
    messy_orderlines.add_column('OrderId', int, False)
    messy_orderlines.add_column('Customer', int, False)
    messy_orderlines.add_column('SKU', int, False)
    messy_orderlines.add_column('Qty', float, False)

    assert table.compare(messy_orderlines)
    assert len(table) == 1997, len(table)


def text_reader_test_11():
    path = Path(__file__).parent / "files" / 'messy_skus.csv'
    assert path.exists()
    start = process_time_ns()
    table = file_reader(path)[0]
    end = process_time_ns()
    table.show(slice(5))
    fields = len(table) * len(table.columns)
    print("{:,} fields/seccond".format(round(1e9 * fields / max(1, end - start), 0)))

    messy_skus = Table(filename=path.name)
    messy_skus.add_column('SKU', int, True)
    messy_skus.add_column('Length', str, True)  # there's a minus in one field.
    messy_skus.add_column('Width', str, True)
    messy_skus.add_column('Height', str, True)

    assert table.compare(messy_skus)
    assert len(table) == 1358, len(table)


def text_reader_test_12():
    path = Path(__file__).parent / "files" / 'orderline_data_to_forecast.csv'
    assert path.exists()
    start = process_time_ns()
    table = file_reader(path)[0]
    end = process_time_ns()
    table.show(slice(5))

    fields = len(table) * len(table.columns)
    print("{:,} fields/seccond".format(round(1e9 * fields / max(1, end - start), 0)))

    old = Table(filename=path.name)  # date,orderid,customerid,sku,quantity
    old.add_column('date', datetime, False)
    old.add_column('orderid', int, False)
    old.add_column('customerid', int, False)
    old.add_column('sku', int, False)
    old.add_column('quantity', int, False)

    assert table.compare(old)
    assert len(table) == 11324, len(table)


def text_reader_test_13():
    path = Path(__file__).parent / "files" / 'orderlines.csv'
    assert path.exists()
    start = process_time_ns()
    table = file_reader(path)[0]
    end = process_time_ns()
    table.show(slice(5))
    fields = len(table) * len(table.columns)
    print("{:,} fields/seccond".format(round(1e9 * fields / max(1, end - start), 0)))

    messy_orderlines = Table(filename=path.name)
    messy_orderlines.add_column('Date', date, False)
    messy_orderlines.add_column('OrderId', int, False)
    messy_orderlines.add_column('Customer', int, False)
    messy_orderlines.add_column('SKU', int, False)
    messy_orderlines.add_column('Qty', int, False)

    assert table.compare(messy_orderlines)
    assert len(table) == 1997, len(table)


def text_reader_test_14():
    path = Path(__file__).parent / "files" / 'sap_sample.txt'
    assert path.exists()
    # test part 1: split using user defined sequence.
    start = process_time_ns()
    header = "    | Delivery |  Item|Pl.GI date|Route |SC|Ship-to   |SOrg.|Delivery quantity|SU| TO Number|Material    |Dest.act.qty.|BUn|Typ|Source Bin|Cty"
    split_sequence = ["|"] * header.count('|')
    table = file_reader(path, split_sequence=split_sequence)[0]
    end = process_time_ns()
    table.show(slice(5))

    fields = len(table)*len(table.columns)
    print("{:,} fields/seccond".format(round(1e9 * fields / max(1, end - start), 0)))

    sap_sample = Table(filename=path.name)
    sap_sample.add_column('None', str, True)
    sap_sample.add_column('Delivery', int, False)
    sap_sample.add_column('Item', int, False)
    sap_sample.add_column('Pl.GI date', date, False)
    sap_sample.add_column('Route', str, False)
    sap_sample.add_column('SC', str, False)
    sap_sample.add_column('Ship-to', str, False)
    sap_sample.add_column('SOrg.', str, False)
    sap_sample.add_column('Delivery quantity', int, False)
    sap_sample.add_column('SU', str, False)
    sap_sample.add_column('TO Number', int, False)
    sap_sample.add_column('Material', str, False)
    sap_sample.add_column('Dest.act.qty.', int, False)
    sap_sample.add_column('BUn', str, False)
    sap_sample.add_column('Typ', str, False)
    sap_sample.add_column('Source Bin', str, False)
    sap_sample.add_column('Cty|', str, False)

    assert table.compare(sap_sample)
    assert len(table) == 20, len(table)


def excel_reader_test_01():

    path = Path(__file__).parent / "files" / 'book1.xlsx'
    assert path.exists()
    start = process_time_ns()
    tables = file_reader(path)
    end = process_time_ns()

    fields = sum(len(t)*len(t.columns) for t in tables)
    print("{:,} fields/seccond".format(round(1e9 * fields / max(1, end - start), 0)))

    sheet1 = Table(filename=path.name, sheet_name='Sheet1')
    for column_name in list('abcdef'):
        sheet1.add_column(column_name, int, False)

    sheet2 = Table(filename=path.name, sheet_name='Sheet2 ')  # there's a deliberate white space at the end!
    sheet2.add_column('a', int, False)
    for column_name in list('bcdef'):
        sheet2.add_column(column_name, float, False)

    books = [sheet1, sheet2]

    for book, table in zip(books, tables):
        table.show(slice(5))
        assert table.compare(book)
        assert len(table) == 45, len(table)


def excel_reader_test_02():
    path = Path(__file__).parent / "files" / 'aldi_unit_test_data.xlsx'
    assert path.exists()
    start = process_time_ns()
    tables = file_reader(path)
    end = process_time_ns()

    fields = sum(len(t) * len(t.columns) for t in tables)
    print("{:,} fields/seccond".format(round(1e9 * fields / max(1, end - start), 0)))

    sheet1 = Table(filename=path.name, sheet_name='Data')
    sheet1.add_column('Date', date, False)

    columns = ['Pallets_2016', 'Pallets_2024', 'Pallets_2030', 'AMCAP_2016', 'AMCAP_2024', 'AMCAP_2030', 'Total Cases', 'ContainerCases']
    for column_name in columns:
        sheet1.add_column(column_name, int, False)

    sheet2 = Table(filename=path.name, sheet_name='SKU A')
    sheet2.add_column('Date', date, False)
    sheet2.add_column('SKU', str, False)

    columns = ['Pallets_2016', 'AMCAP_2016', 'Pallets_2024', 'AMCAP_2024', 'Pallets_2030', 'AMCAP_2030', 'Xdock2016', 'Xdock2024', 'Xdock2030']
    for column_name in columns:
        sheet2.add_column(column_name, int, False)

    sheet3 = Table(filename=path.name, sheet_name='SKU B')
    sheet3.add_column('Date', date, False)
    sheet3.add_column('SKU', str, False)

    columns = ['Pallets_2016', 'AMCAP_2016', 'Pallets_2024', 'AMCAP_2024', 'Pallets_2030', 'AMCAP_2030', 'Xdock2016', 'Xdock2024', 'Xdock2030']
    for column_name in columns:
        sheet3.add_column(column_name, int, False)

    books = [sheet1, sheet2, sheet3]

    for book, table in zip(books, tables):
        table.show(slice(5))
        assert table.compare(book)
        assert len(table) == 365, len(table)


def excel_reader_test_03():
    path = Path(__file__).parent / "files" / 'datetime_test_case.xlsx'
    assert path.exists()
    table = file_reader(path)[0]
    table.show()

    sheet1 = Table(filename=path.name, sheet_name='Sheet1')
    sheet1.add_column('Date', date, False)
    sheet1.add_column('numeric value', int, False)
    sheet1.add_column('string', date, False)
    sheet1.add_column('bool', bool, False)

    assert table.compare(sheet1)
    assert len(table) == 2, len(table)



# all tests
# ---------
datatype_inference_tests()
basic_column_tests()
basic_table_tests()
lookup_tests()
sql_join_tests()
sortation_tests()
groupby_tests()
text_escape_tests()
text_reader_test_00()
text_reader_test_01()
text_reader_test_02()
text_reader_test_03()
text_reader_test_04()
text_reader_test_05()
text_reader_test_06()
text_reader_test_07()
text_reader_test_08()
text_reader_test_09()
text_reader_test_10()
text_reader_test_11()
text_reader_test_12()
text_reader_test_13()
text_reader_test_14()
excel_reader_test_01()
excel_reader_test_02()
excel_reader_test_03()