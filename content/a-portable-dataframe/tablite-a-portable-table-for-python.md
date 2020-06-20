We're all tired of reinventing the wheel when we need to process a bit of data.

- Pandas has a huge memory overhead.
- Numpy just doesn't seem pythonic anymore.
- Arrows isn't ready
- SQLite is great but just too slow.

So what do we do? We write a custom built class for the problem at hand and
discover that we've just spent 3 hours doing something that should have taken
20 minutes.

### Enter tablite
A python library for tables that does everything you need.

- it handles all datatypes: str,float,bool,int,date,datetime,time.
- you can select columns as `table['A']` and you can select rows as `table['A'][4:8]`
- you can dump to json as `table.to_json()` and you can load it with `Table.from_json(json_str)`
- it does type checking when you append and replace data, and allows you to update with `table['A'][2] = new value`
- it checks if the header name is already in use.
- you can add any type of metadata to the table as `table.metadata['some key'] = 'some value'`
- you can ask `column_xyz in Table.colums`

Here are some examples:

```
# 1. Create the table.
table = Table()

# 2. Add a column
table.add_column('A', int, False)

# 3. check that it really is there.
assert 'A' in table

# 4. Add another column that doesn't tolerate None's
table.add_column('B', str, allow_empty=False)

# 5. appending a couple of rows:
table.add_row((1, 'hello'))
table.add_row((2, 'world'))

# 6. converting to json is easy:
table_as_json = table.to_json()

# 7. loading from json is easy:
table2 = Table.from_json(table_as_json)

# 8. for storing in a database, I recommend to zip the json.
zipped = zlib.compress(table_as_json.encode())

# 9. copying is easy:
table3 = table.copy()

# 10. comparing tables are straight forward:
assert table == table2 == table3

# 11. comparing metadata is also straight forward 
# (for example if you want to append the one table to the other)
table.compare(table3)  # will raise exception if they're different.

# 12. The plus operator `+` also works:
table3x2 = table3 + table3
assert len(table3x2) == len(table3) * 2

# 13. and so does plus-equal: +=
table3x2 += table3
assert len(table3x2) == len(table3) * 3

# 14. updating values is familiar to any user who likes a list:
assert 'A' in table.columns
assert isinstance(table.columns['A'], list)
last_row = -1
table['A'][last_row] = 44
table['B'][last_row] = "Hallo"

# 15. type verification is included, and complaints if you're doing it wrong:
try:
    table.columns['A'][0] = 'Hallo'
    assert False, "A TypeError should have been raised."
except TypeError:
    assert True

# 16. slicing is easy:
table_chunk = table2[2:4]
assert isinstance(table_chunk, Table)

# 17. we will handle duplicate names gracefully.
table2.add_column('B', int, allow_empty=True)
assert set(table2.columns) == {'A', 'B', 'B_1'}

# 18. you can delete a column as key...
del table2['B_1']
assert set(table2.columns) == {'A', 'B'}

# 19. adding a computed column is easy:
table.add_column('new column', str, allow_empty=False, data=[f"{r}" for r in table.rows])

# 20. iterating over the rows is easy:
print(table)
for row in table.rows:
    print(row)

# 21 .updating a column with a function is easy:
f = lambda x: x * 10
table['A'] = [f(r) for r in table['A']]

# 22. using regular indexing will also work.
for ix, r in enumerate(table['A']):
    table['A'][ix] = r * 10

# 23. and it will tell you if you're not allowed:
try:
    f = lambda x: f"'{x} as text'"
    table['A'] = [f(r) for r in table['A']]
    assert False, "The line above must raise a TypeError"
except TypeError as error:
    print("The error is:", str(error))

# 24. works with all datatypes ...
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

# ...to and from json:
table4_json = table4.to_json()
table5 = Table.from_json(table4_json)

assert table4 == table5

# 25. doing lookups is supported by indexing:
table6 = Table()
table6.add_column('A', str, data=['Alice', 'Bob', 'Bob', 'Ben', 'Charlie', 'Ben', 'Albert'])
table6.add_column('B', str, data=['Alison', 'Marley', 'Dylan', 'Affleck', 'Hepburn', 'Barnes', 'Einstein'])

index = table6.index('A')  # single key.
assert index[('Bob',)] == {1, 2}

index2 = table6.index('A', 'B')  # multiple keys.
assert index2[('Bob', 'Dylan')] == {2}

# 26. And finally: You can add metadata until the cows come home:
table5.metadata['db_mapping'] = {'A': 'customers.customer_name',
                                 'A_2': 'product.sku',
                                 'A_4': 'locations.sender'}

```

### At this point you know it's a solid bread and butter table. 
### No surprises. Now onto the real time savers

**_Iteration_** supports for loops and list comprehension at the speed of c: 

Just use `[r for r in table.rows]`, or:

    for row in table.rows:
        row ...

Here's a more practical use case:

```
# 1 .Imagine a table with columns a,b,c,d,e (all integers) like this:
t = Table()
_ = [t.add_column(header=c, datatype=int, allow_empty=False, data=[i for i in range(5)]) for c in 'abcde']

# 2. we want to add two new columns using the functions:
def f1(a,b,c): return a+b+c+1
def f2(b,c,d): return b*c*d

# 3. and we want to compute two new columns 'f' and 'g':
t.add_column(header='f', datatype=int, allow_empty=False)
t.add_column(header='g', datatype=int, allow_empty=True)

# 4. we can now use the filter, to iterate over the table:
for row in t.filter('a', 'b', 'c', 'd'):
    a, b, c, d = row

    # 4. ... and add the values to the two new columns
    t['f'].append(f1(a, b, c))
    t['g'].append(f2(b, c, d))

assert len(t) == 5
assert len(t.columns) == len('abcdefg')
```

**_Sort_** supports multi-column sort as simple as `table.sort(**{'A': False, 'B': True, 'C': False})`

Here's an example:

```
table7 = Table()
table7.add_column('A', int, data=[1, None, 8, 3, 4, 6, 5, 7, 9], allow_empty=True)
table7.add_column('B', int, data=[10, 100, 1, 1, 1, 1, 10, 10, 10])
table7.add_column('C', int, data=[0, 1, 0, 1, 0, 1, 0, 1, 0])

table7.sort(**{'B': False, 'C': False, 'A': False})

table7_sorted = [
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
```
As you can see, the table is sorted first by column `B` in ascending order, then
by column 'C' and finally by column 'A'. Note that `None` is handled as `float('-inf')`


**_Index_** supports multi-key indexing using args: `table.index('B','C')`. 

This gives you a dictionary with the key as a tuple and the indices as a set, e.g. 

    indices = {
        (1, 44): {2,3,33,35}
        (2, 44): {4,5,32}
    }

**_Filter_** allows selection of particular rows like: 

    for row in table.filter('b', 'a', 'a', 'c')
        b,a,a,c = row


**_All_** allows copy of a table where "all" criteria match.

This allows you to use custom functions like this:

```
before = [r for r in table2.rows]
assert before == [(1, 'hello'), (2, 'world'), (1, 'hello'), (44, 'Hallo')]

# as is filtering for ALL that match:
filter_1 = lambda x: 'llo' in x
filter_2 = lambda x: x > 3

after = table2.all(**{'B': filter_1, 'A': filter_2})

assert [r for r in after.rows] == [(44, 'Hallo')]
```

**_Any_** allows copy of a table where "any" criteria match.

```
after = table2.any(**{'B': filter_1, 'A': filter_2})

assert [r for r in after.rows] == [(1, 'hello'), (1, 'hello'), (44, 'Hallo')]
```


**_SQL JOINs_** are supported out of the box! 

Here are a couple of examples:

```
# We start with creating two tables:
left = Table()
left.add_column('number', int, allow_empty=True, data=[1, 2, 3, 4, None])
left.add_column('colour', str, data=['black', 'blue', 'white', 'white', 'blue'])

right = Table()
right.add_column('letter', str, allow_empty=True, data=['a', 'b,', 'c', 'd', None])
right.add_column('colour', str, data=['blue', 'white', 'orange', 'white', 'blue'])
```

**Left join**
```
# SELECT number, letter FROM left LEFT JOIN right on left.colour == right.colour
left_join = left.left_join(right, keys=['colour'], columns=['number', 'letter'])
```

**Inner join**
```
# SELECT number, letter FROM left JOIN right ON left.colour == right.colour
inner_join = left.inner_join(right, keys=['colour'],  columns=['number','letter'])
```


**Outer join**
```
# SELECT number, letter FROM left OUTER JOIN right ON left.colour == right.colour
outer_join = left.outer_join(right, keys=['colour'], columns=['number','letter'])
```



**_GroupBy_** operations are supported using the GroupBy class:

```
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

g += t2

g_out = [
    (0, 0, 1, 1, 2, 1, 1, 2, 1, 1.0, 0.0, 0.0, 1, 1, 0),
    (1, 1, 4, 4, 8, 4, 4, 2, 1, 4.0, 0.0, 0.0, 4, 4, 1),
    (2, 2, 7, 7, 14, 7, 7, 2, 1, 7.0, 0.0, 0.0, 7, 7, 8),
    (3, 3, 10, 10, 20, 10, 10, 2, 1, 10.0, 0.0, 0.0, 10, 10, 27),
    (4, 4, 13, 13, 26, 13, 13, 2, 1, 13.0, 0.0, 0.0, 13, 13, 64)
]

for row in g.rows:
    g_out.remove(row)
assert not g_out  # g_out is empty.
```
 
Note that groupby is instantiated on it's own, without any data, and then
data is added using `+=` ? That's because I wanted the GroupBy class to be
friendly to updates that otherwise might run out of memory.

Here's the case:

```
# 1. Imagine you have a large number of files that you want to summarize.
#    For this you first need a groupby operation:

g = GroupBy(keys=['a','b'], functions=[('c', StandardDeviation), ('d', Average)])

# 2. now you can just iterate over the files and not having to worry about 
#    the memory footprint:

files = Path(__file__).parent / 'archive'
assert files.isdir()  
for file in files.iterdir():
    json_str = json.loads(file.read())
    table = Table.from_json(json)
    g += table

# 3. Once all files have been summarized, you can read the results using
#    Pythons friendly for loop:

for a, b, stdev, avg in g.rows:
     ...

```

This concludes the mega-tutorial to `tablite`. There's nothing more to it.
But oh buy it'll save a lot of time.

All code snippets are available in the [example.py](example.py) and on from 
pypi as `pip install tablite`





