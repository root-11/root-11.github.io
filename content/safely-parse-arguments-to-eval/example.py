# our initial table:
table = {
    0: ['A', 'B', 'C', 'D'],
    1: [123, 2, 32, 321],
    2: [133, 2, 33, 123],
    3: [143, 3, 34, 111],
    4: [163, 3, 35, 222],
    5: [143, 4, 36, 333],
    6: [123, 4, 37, 444],
}

# our function provided by the user:
func = "(int(round(('A'*'B)+('C'*'A') + 4, 0)) + max('D, 'B))/'A'"
new_column_name = "E"

# our filters:
operators = {"max", "min", "int", "round", "+", "-", "/", "*", "(", ")", " ", ",", "'", '"'}
numbers = set('1234567890')

# 1. first check the function:
table_headers = table[0]

remainder = func
for word in list(numbers) + list(operators) + table_headers:
    remainder = remainder.replace(word, "")
if remainder:
    raise ValueError(f"Bad sign near '{remainder}' in '{func}'")

# 2. now process the rows.
for row_index in table:
    if row_index == 0:
        table[0] = table[0] + [new_column_name]
        continue
    row = table[row_index]

    data = {k: str(v) for k, v in zip(table_headers, row)}
    # example data = {'A': 123, 'B': 2, 'C': 32, 'D': 321}

    # 1. remove text marks.
    new_func = func
    new_func = new_func.replace("'", "").replace('"', '')

    # 2. replace column names with values
    for k, v in data.items():
        new_func = new_func.replace(k, str(v))

    # 3. we check that no malicious content is left in the string
    # for example a malicious user could put insert `sys.exit()` maliciously.

    c = new_func.replace(" ", "")
    for word in operators.union(numbers):
        c = c.replace(word, "")
        if not c:
            break
    if c:  # it's not safe!
        raise ValueError(f"Bad sign near '{c}' in '{func}'")

    # 4. we use pythons interpreter to evaluate the string as if it was math.
    table[row_index] = row + [eval(new_func)]

for k, v in table.items():
    print(k, ":", v)

# 0 : ['A', 'B', 'C', 'D', 'E']
# 1 : [123, 2, 32, 321, 36.642276422764226]
# 2 : [133, 2, 33, 123, 35.954887218045116]
# 3 : [143, 3, 34, 111, 37.80419580419581]
# 4 : [163, 3, 35, 222, 39.38650306748466]
# 5 : [143, 4, 36, 333, 42.35664335664335]
# 6 : [123, 4, 37, 444, 44.642276422764226]
