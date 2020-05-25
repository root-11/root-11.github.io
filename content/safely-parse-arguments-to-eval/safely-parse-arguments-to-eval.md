We often want to allow users to execute arbitrary command-like statements without having 
to write a parser form scratch and at the same time worry that the user might attempt
something malicious.

Let's start with an example where the user who knows nothing of python needs to perform 
some math using a custom function, where the data source is a table and the function 
needs to be performed on each row.

| # | A | B | C | D |
|---|---|---|---|---|
|1|123| 2 | 32|321|
|2|133| 2.1 | 33|123|
|3|143| 3.1e4 | 34|111|
|4|163| 3 | 35|222|
|5|143| 4 | 36|333|
|6|123| 4 | 37|444|

The user defines the function for column **`E`** as:  

    `func = "(int(round(('A'*'B)+('C'*'A') + 4, 0)) + max('D, 'B))/'A'"`

When looping over the table, we want to add column `E` to the table as the result of the function.  
To do so, we will need to:  

1. check the function for malicious content.
2. if okay, evaluate the function and return the result.

We start with the table:


    table = {
        0: ['A',   'B', 'C', 'D'],
        1: [123,     2,  32, 321],
        2: [133,   2.1,  33, 123],
        3: [143, 3.1e4,  34, 111],
        4: [163,     3,  35, 222],
        5: [143,     4,  36, 333],
        6: [123,     4,  37, 444],
    }
    

and the function provided by the user:


    func = "(int(round(('A'*'B)+('C'*'A') + 4, 0)) + max('D, 'B))/'A'"
    new_column_name = "E"

With the following filters, we can check the function by seeing
if anything is left after pruning the function.

First we need the filters, with the longest word first, so we don't accidentally
remove a shorter word that is a sub-string in a longer word, like for example
`round` which is permitted in `rounddown`:
    
    
    operators = {"max", "min", "int", "round", "+", "-", "/", "*", "(", ")", " ", ",", "'", '"'}
    operators.sort(key=lambda x: len(x), reverse=True)  # guarantees longest word first.
    numbers = list('1234567890e.')
    permitted = operators + numbers

The pruning function is straight forward:

    def strip(text, replacements):
        for word in replacements:
            text = text.replace(word, "")
            if not text:
                break
        return text

Now we can check the function and raise a value error if it is malformed:

    table_headers = table[0]
    
    remainder = strip(func)
    if remainder:
        raise ValueError(f"Bad sign near '{remainder}' in '{func}'")


At this point we now know the function is not malicious, but we don't know if any
combination of column names and data can produce malicious content.

To process the rows, we will therefore have to substitute each heading with data
and check it in the same manner. To do so we need a short helper:

    def replace(text, dictionary):
        for k, v in dictionary.items():
            text = text.replace(k, str(v))
        return text


The user defined function can now be processed by:

1. checking the UDF for invalid content.
2. processing each row, by:
3. replacing the headers to values from the row.
4. getting rid of the remaining text marks.
5. check that no malicious content is left in the string
6. evaluate the string as if it was math and update the table with the calculated value.

Like this:

   
    def evaluate_custom_expression(user_defined_function, new_column_name, table):
        """
        :param user_defined_function: string
        :param new_column_name: string
        :param table: dictionary {row: list of values}
        """
 
        # [1]       
        table_headers = table[0]   
        table[0] += [new_column_name]

        remainder = strip(user_defined_function, table_headers + permitted)
        if remainder:
            raise ValueError(f"Bad sign near '{strip(func, table_headers + permitted)}' in '{user_defined_function}'")
    
        # [2]
        for row_index in (i for i in table if i > 0):
            data = {k: str(v) for k, v in zip(table_headers, table[row_index])}  # [3]  
            new_func = strip(replace(func, data), ["'", '"'])  # [4]
       
            if strip(new_func, permitted):  # [5]
                raise ValueError(f"Bad sign near '{strip(new_func, permitted)}' in '{func}'")
            table[row_index] += [eval(new_func)]  # [6] 

Example:

    evaluate_custom_expression(func, new_column_name, table)
    for k, v in table.items():
        print(k, ":", v)

    # outputs:
    0 : ['A', 'B', 'C', 'D', 'E']
    1 : [123, 2, 32, 321, 36.642276422764226]
    2 : [133, 2.1, 33, 123, 36.05263157894737]
    3 : [143, 31000.0, 34, 111, 31250.81118881119]
    4 : [163, 3, 35, 222, 39.38650306748466]
    5 : [143, 4, 36, 333, 42.35664335664335]
    6 : [123, 4, 37, 444, 44.642276422764226]



All the code is available in [example.py](example.py).

