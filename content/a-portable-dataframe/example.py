import zlib
import json
from itertools import count
from datetime import datetime, date, time
from collections import defaultdict


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
            slc = slice(0, None, None)
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
        return json.dumps([c.to_json() for c in self.columns.values()])

    @classmethod
    def from_json(cls, json_):
        t = Table()
        for c in json.loads(json_):
            col = Column.from_json(c)
            col.header = t.check_for_duplicate_header(col.header)
            t.columns[col.header] = col
            t.__setattr__(col.header, col)
        return t

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
                    raise ValueError(f"Column {name}.datatype different")
                if col.allow_empty != col2.allow_empty:
                    raise ValueError(f"Column {name}.allow_empty is different")

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
            slc = slice(0,None,None)
        else:
            slc = slices[0]
        assert isinstance(slc, slice)

        start = 0 if slc.start is None else slc.start
        step = 1 if slc.step is None else slc.step
        stop = len(self) if slc.stop is None else slc.stop

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
        assert isinstance(other, Table)
        assert isinstance(keys, list)
        assert all(k in self.columns and k in other.columns for k in keys)

        left_join = Table()
        for col_name in columns:
            if col_name in self.columns:
                col = self.columns[col_name]
            elif col_name in other.columns:
                col = other.columns[col_name]
            else:
                raise ValueError(f"column name '{col_name}' not in any table.")
            left_join.add_column(col_name, col.datatype, allow_empty=True)

        left_ixs = range(len(left))
        right_idx = right.index(*keys)

        for left_ix in left_ixs:
            key = tuple(left[h][left_ix] for h in keys)
            right_ixs = right_idx.get(key, (None,))
            for right_ix in right_ixs:
                for col_name, column in left_join.columns.items():
                    if col_name in left:
                        column.append(left[col_name][left_ix])
                    elif col_name in right:
                        if right_ix is not None:
                            column.append(right[col_name][right_ix])
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
        inner_join = Table()
        for col_name in columns:
            if col_name in self.columns:
                col = self.columns[col_name]
            elif col_name in other.columns:
                col = other.columns[col_name]
            else:
                raise ValueError(f"column name '{col_name}' not in any table.")
            inner_join.add_column(col_name, col.datatype, allow_empty=True)

        key_union = set(left.filter(*keys)).intersection(set(right.filter(*keys)))

        left_ixs = left.index(*keys)
        right_ixs = right.index(*keys)

        for key in key_union:
            for left_ix in left_ixs.get(key, set()):
                for right_ix in right_ixs.get(key, set()):
                    for col_name, column in inner_join.columns.items():
                        if col_name in left:
                            column.append(left[col_name][left_ix])
                        elif col_name in right:
                            column.append(right[col_name][right_ix])
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
        outer_join = Table()
        for col_name in columns:
            if col_name in self.columns:
                col = self.columns[col_name]
            elif col_name in other.columns:
                col = other.columns[col_name]
            else:
                raise ValueError(f"column name '{col_name}' not in any table.")
            outer_join.add_column(col_name, col.datatype, allow_empty=True)

        left_ixs = range(len(left))
        right_idx = right.index(*keys)
        right_keyset = set(right_idx)

        for left_ix in left_ixs:
            key = tuple(left[h][left_ix] for h in keys)
            right_ixs = right_idx.get(key, (None,))
            right_keyset.discard(key)
            for right_ix in right_ixs:
                for col_name, column in outer_join.columns.items():
                    if col_name in left:
                        column.append(left[col_name][left_ix])
                    elif col_name in right:
                        if right_ix is not None:
                            column.append(right[col_name][right_ix])
                        else:
                            column.append(None)
                    else:
                        raise Exception('bad logic')

        for right_key in right_keyset:
            for right_ix in right_idx[right_key]:
                for col_name, column in outer_join.columns.items():
                    if col_name in left:
                        column.append(None)
                    elif col_name in right:
                        column.append(right[col_name][right_ix])
                    else:
                        raise Exception('bad logic')
        return outer_join


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

# + also work:
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

# append is easy:
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

# todo: check that metadata travels in json too.

# doing lookups is supported by indexing:
table6 = Table()
table6.add_column('A', str, data=['Alice', 'Bob', 'Bob', 'Ben', 'Charlie', 'Ben', 'Albert'])
table6.add_column('B', str, data=['Alison', 'Marley', 'Dylan', 'Affleck', 'Hepburn', 'Barnes', 'Einstein'])

index = table6.index('A')  # single key.
assert index[('Bob',)] == {1, 2}

index2 = table6.index('A', 'B')  # multiple keys.
assert index2[('Bob', 'Dylan')] == {2}


# a couple of examples with SQL join:
left = Table()
left.add_column('number', int, allow_empty=True, data=[1, 2, 3, 4, None])
left.add_column('colour', str, data=['black', 'blue', 'white', 'white', 'blue'])

right = Table()
right.add_column('letter', str, allow_empty=True, data=['a', 'b', 'c', 'd', None])
right.add_column('colour', str, data=['blue', 'white', 'orange', 'white', 'blue'])

# left join
# SELECT number, letter FROM left LEFT JOIN right on left.colour == right.colour
left_join = left.left_join(right, keys=['colour'], columns=['number', 'letter'])

# inner join
# SELECT number, letter FROM left JOIN right ON left.colour == right.colour
inner_join = left.inner_join(right, keys=['colour'], columns=['number', 'letter'])

# outer join
# SELECT number, letter FROM left OUTER JOIN right ON left.colour == right.colour
outer_join = left.outer_join(right, keys=['colour'], columns=['number', 'letter'])


# Sortation
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

    def pivot(self, columns, values_as_rows=True):
        """ pivots the groupby so that `columns` become new columns.

        :param args: column names
        :param values_as_rows: boolean, if False: values as columns.
        :return: New Table

        Example:
        g.show()
        +=====+=====+=====+======+
        |  a  |  b  |  c  |sum(g)|
        | int | int | int | int  |
        |False|False|False|False |
        +-----+-----+-----+------+
        |    0|    0|    0|    10|
        |    0|    1|    1|    11|
        |    0|    2|    1|    12|
        |    1|    1|    1|    14|
        |    1|    1|    2|    13|
        +=====+=====+=====+======+

        g.pivot('c')
        +=====+=====+==========+===========+
        |  a  |  b  |sum(g,c=0)| max(g,c=0)|
        | int | int |   int    |     int   |  ...
        |False|False|   True   |    True   |
        +-----+-----+----------+-----------+
        |    0|    0|       10|            |
        |    0|    1|         |          11|
        |    0|    2|         |          12|
        |    1|    1|         |          14|
        +=====+=====+======+=====+============+============+
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



