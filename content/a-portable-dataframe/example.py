# After having spent a bit of time on protobuf, I've found it to be -
# apologies Googlers - an over engineered format in excess of my needs.

# So what exactly do i need?
#
# A table that can:
# - store data on a columnar basis.
# - each column has header, datatype, allows empty fields
# - I can access the columns in the table as a namedtuple.
# - add/remove rows.
# - add/remove columns.
# - is readable
# - compresses / reads from compressed format in a single function.
# - allows fast index access to elements in each column

import zlib
import json
from itertools import count
from datetime import datetime, date, time


class DataTypes(object):
    str = str
    float = float
    bool = bool
    int = int
    date = date
    time = time
    datetime = datetime
    # alias for private labels
    text = str
    decimal = float
    boolean = bool
    integer = int

    # reserved keyword for None in JavaScript:
    none = 'null'

    @staticmethod
    def to_json(v):
        if v is None:
            return DataTypes.none
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
        if v == DataTypes.none:
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
            all(a == b for a, b in zip(self, other))
        ])

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

    def replace(self, values):
        if len(values) != len(self):
            raise ValueError("input is not of same length as column.")
        _ = [self.type_check(v) for v in values]
        self.clear()
        self.extend(values)

    def __setitem__(self, key, value):
        self.type_check(value)
        super().__setitem__(key, value)


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

    def __init__(self):
        self.columns = {}
        self.metadata = {}

    def __eq__(self, other):
        if not isinstance(other, Table):
            a, b = self.__class__.__name__, other.__class__.__name__
            raise TypeError(f"cannot compare {a} with {b}")
        return all([a == b for a, b in zip(self.columns.values(), other.columns.values())])

    def __len__(self):
        """ returns length of longest column."""
        return max(len(c) for c in self.columns.values())

    def __bool__(self):
        return any(self.columns)

    def __copy__(self):
        t = Table()
        t.columns = {k: v.copy() for k, v in self.columns.items()}
        return t

    def __str__(self):
        variation = ""
        lengths = {k: len(v) for k, v in self.columns.items()}
        if set(lengths.values()) != 1:
            longest_col = max(lengths.values())
            variation = f"(except {', '.join([f'{k}({v})' for k,v in lengths.items() if v < longest_col])})"
        return f"<{self.__class__.__name__}> {len(self.columns)} columns x {len(self)} rows {variation}"

    def copy(self):
        return self.__copy__()

    def to_json(self):
        return json.dumps([c.to_json() for c in self.columns.values()])

    @classmethod
    def from_json(cls, json_):
        df = Table()
        for c in json.loads(json_):
            col = Column.from_json(c)
            col.header = df.check_for_duplicate_header(col.header)
            df.columns[col.header] = col
            df.__setattr__(col.header, col)
        return df

    def check_for_duplicate_header(self, header):
        assert isinstance(header, str)
        new_header = header
        counter = count(start=1)
        while hasattr(self, new_header):
            new_header = f"{header}_{next(counter)}"  # valid attr names must be ascii.
        return new_header

    def add_column(self, header, datatype, allow_empty=False, data=None):
        assert isinstance(header, str)
        header = self.check_for_duplicate_header(header)
        c = Column(header, datatype, allow_empty, data=data)
        self.__setattr__(header, c)
        self.columns[header] = c

    def add_row(self, values):
        if not isinstance(values, tuple):
            raise TypeError(f"expected tuple, got {type(values)}")
        if len(values) != len(self.columns):
            raise ValueError(f"expected {len(self.columns)} values not {len(values)}: {values}")
        for value, col in zip(values, self.columns.values()):
            col.append(value)

    def __getitem__(self, item):
        """ returns rows as a tuple """
        assert isinstance(item, slice)
        start = 0 if item.start is None else item.start
        step = 1 if item.step is None else item.step
        stop = len(self.columns) if item.stop is None else item.stop

        t = Table()
        for col in self.columns.values():
            t.add_column(col.header, col.datatype, col.allow_empty, col[start:stop:step])
        return t

    def __delattr__(self, item):
        """ delete column as a attribute """
        if item in self.columns:
            del self.columns[item]
        super().__delattr__(item)

    def __delitem__(self, key):
        """ delete column as key """
        if key in self.columns:
            del self.columns[key]
            super().__delattr__(key)
        else:
            raise KeyError(f"key not found")

    def __setattr__(self, name, value):
        if hasattr(self, name):
            if name in self.columns and isinstance(value, list):
                col = self.columns[name]
                col.replace(value)
                return
        super().__setattr__(name, value)

    @property
    def rows(self):
        for ix in range(len(self)):
            item = tuple(c[ix] if ix < len(c) else None for c in self.columns.values())
            yield item

    def filter(self, *headers):
        """ returns values in same order as headers. """
        L = [self.columns[h] for h in headers]
        for ix in range(len(self)):
            item = tuple(c[ix] if ix < len(c) else None for c in L)
            yield item

    def all(self, **kwargs):
        """
        returns Table for rows where ALL kwargs match
        :param kwargs: dictionary with headers and values/callable
        """
        d = kwargs
        if not isinstance(d, dict):
            raise TypeError("did you remember to add the ** in front of your dict?")

        ixs = set(range(len(self)))
        for k, v in d.items():
            col = self.columns[k]
            if callable(v):
                ix2 = {ix for ix in ixs if v(col[ix])}
            else:
                ix2 = {ix for ix in ixs if v == col[ix]}

            if ixs is None:
                ixs = ix2
            else:
                ixs = ixs.intersection(ix2)

        t = Table()
        for col in self.columns.values():
            t.add_column(col.header, col.datatype, col.allow_empty, [col[ix] for ix in ixs])
        return t

    def any(self, **kwargs):
        """
        returns Table for rows where ANY kwargs match
        :param kwargs: dictionary with headers and values
        """
        d = kwargs
        if not isinstance(d, dict):
            raise TypeError("did you remember to add the ** in front of your dict?")

        ixs = set()
        for k, v in d.items():
            col = self.columns[k]
            if callable(v):
                ix2 = {ix for ix, r in enumerate(col) if v(r)}
            else:
                ix2 = {ix for ix, r in enumerate(col) if v == r}
            ixs.update(ix2)

        t = Table()
        for col in self.columns.values():
            t.add_column(col.header, col.datatype, col.allow_empty, [col[ix] for ix in ixs])
        return t


# creating a table incrementally is straight forward:
table = Table()
table.add_column('A', int, False)
assert hasattr(table, 'A')

table.add_column('B', str, allow_empty=False)
assert hasattr(table, 'B')

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
assert 'A' in table.columns
assert 'Z' not in table.columns

# comparisons are straight forward:
assert table == table2 == table3

# type verification is included:
try:
    table.A[1] = 'Hallo'
    assert False, "A TypeError should have been raised."
except TypeError:
    assert True

# updating values is familiar to any user who likes a list:
assert hasattr(table, 'A')
assert isinstance(table.A, list)
table.A[1] = 44
table.B[1] = "Hallo"

assert table != table2

# append is easy:
_ = [table2.add_row(row) for row in table.rows]

before = [r for r in table2.rows]
assert before == [(1, 'hello'), (2, 'world'), (1, 'hello'), (44, 'Hallo')]

# as is filtering for ALL that match:
filter_1 = lambda x: 'llo' in x
filter_2 = lambda x: x > 3

after = table2.all(**{'B': filter_1, 'A': filter_2})

assert [r for r in after.rows] == [(44, 'Hallo')]

# as is filtering or for ANY that match:
after = table2.any(**{'B': filter_1, 'A': filter_2})

assert [r for r in after.rows] == [(1, 'hello'), (1, 'hello'), (44, 'Hallo')]

# slicing is easy:
table_chunk = table2[2:4]
assert isinstance(table_chunk, Table)

# we will handle duplicate names gracefully.
table2.add_column('B', int, allow_empty=True)
assert set(table2.columns) == {'A', 'B', 'B_1'}

# you can delete a column as attribute...
del table2.B_1
assert set(table2.columns) == {'A', 'B'}

# ... or using the header as key
del table2['A']
assert set(table2.columns) == {'B'}

# adding a computed column is easy:
table.add_column('new column', str, allow_empty=False, data=[f"{r}" for r in table.rows])

# iterating over the rows is easy:
print(table)
for row in table.rows:
    print(row)

# updating a column with a function is easy:
f = lambda x: x * 10
table.A = [f(r) for r in table.A]

# and it will tell you if you're not allowed:
try:
    f = lambda x: f"'{x} as text'"
    table.A = [f(r) for r in table.A]
    assert False, "The line above must raise a TypeError"
except TypeError as error:
    print("The error is:", str(error))

# using regular indexing will also work.
for ix, r in enumerate(table.A):
    table.A[ix] = r * 10


# works with all datatypes:
now = datetime.now()

table4 = Table()
table4.add_column('A', int, False, data=[-1, 1])
table4.add_column('A', int, True, data=[None, 1])  # None!
table4.add_column('A', DataTypes.integer, False, data=[-1, 1])
table4.add_column('A', float, False, data=[-1.1, 1.1])
table4.add_column('A', DataTypes.decimal, False, data=[-1.1, 1.1])
table4.add_column('A', str, False, data=["", "1"])
table4.add_column('A', DataTypes.text, False, data=["", "1"])
table4.add_column('A', bool, False, data=[False, True])
table4.add_column('A', DataTypes.boolean, False, data=[False, True])
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



