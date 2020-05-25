# our initial table:
table = {
    0: ['A', 'B', 'C', 'D'],
    1: [123, 2, 32, 321],
    2: [133, 2.1, 33, 123],
    3: [143, 3.1e4, 34, 111],
    4: [163, 3, 35, 222],
    5: [143, 4, 36, 333],
    6: [123, 4, 37, 444],
}

# our function provided by the user:
func = "(int(round(('A'*'B)+('C'*'A') + 4, 0)) + max('D, 'B))/'A'"
new_column_name = "E"

# our filters:
operators = ["max", "min", "int", "round", "+", "-", "/", "*", "(", ")", " ", ",", "'", '"']
operators.sort(key=lambda x: len(x), reverse=True)  # systematically remove the longest word first.
numbers = list('1234567890e.')
permitted = operators + numbers


def strip(text, replacements):
    for word in replacements:
        text = text.replace(word, "")
        if not text:
            break
    return text


def replace(text, dictionary):
    for k, v in dictionary.items():
        text = text.replace(k, str(v))
    return text


def evaluate_custom_expression(user_defined_function, new_column_name, table):
    """
    :param user_defined_function:
    :param new_column_name:
    :param table:
    :return:
    """

    table_headers = table[0]
    table[0] += [new_column_name]

    remainder = strip(user_defined_function, table_headers + permitted)
    if remainder:
        raise ValueError(f"Bad sign near '{strip(func, table_headers + permitted)}' in '{user_defined_function}'")

    for row_index in (i for i in table if i > 0):
        data = {k: str(v) for k, v in zip(table_headers, table[row_index])}
        new_func = strip(replace(func, data), ["'", '"'])  # replace column names with values and remove text marks.

        if strip(new_func, permitted):  # check that no malicious content is left in the string
            raise ValueError(f"Bad sign near '{strip(new_func, permitted)}' in '{func}'")

        table[row_index] += [eval(new_func)]  # evaluate the string as if it was math.


evaluate_custom_expression(func, new_column_name, table)
for k, v in table.items():
    print(k, ":", v)

# 0 : ['A', 'B', 'C', 'D', 'E']
# 1 : [123, 2, 32, 321, 36.642276422764226]
# 2 : [133, 2.1, 33, 123, 36.05263157894737]
# 3 : [143, 31000.0, 34, 111, 31250.81118881119]
# 4 : [163, 3, 35, 222, 39.38650306748466]
# 5 : [143, 4, 36, 333, 42.35664335664335]
# 6 : [123, 4, 37, 444, 44.642276422764226]
