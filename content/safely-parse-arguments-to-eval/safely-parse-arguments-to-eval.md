We often want to allow users to execute arbitrary command-like statements without having 
to write a parser form scratch and at the same time worry that the user might attempt
something malicious.

Let's start with an example where the user who knows nothing of python needs to perform 
some math using a custom function, where the data source is a table and the function 
needs to be performed on each row.

| # | A | B | C | D |
|---|---|---|---|---|
|1|123| 2 | 32|321|
|2|133| 2 | 33|123|
|3|143| 3 | 34|111|
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
        0: ['A', 'B', 'C', 'D'],
        1: [123, 2, 32, 321],
        2: [133, 2.1, 33, 123],
        3: [143, 3.1e4, 34, 111],
        4: [163, 3, 35, 222],
        5: [143, 4, 36, 333],
        6: [123, 4, 37, 444],
    }
    

and the function provided by the user:


    func = "(int(round(('A'*'B)+('C'*'A') + 4, 0)) + max('D, 'B))/'A'"
    new_column_name = "E"

With the following filters, we can check the function by seeing
if anything is left after pruning the function:
    
    
    operators = {"max", "min", "int", "round", "+", "-", "/", "*", "(", ")", " ", ",", "'", '"'}
    numbers = set('1234567890e.')
    permitted = list(operators) + list(numbers)
    
    table_headers = table[0]
    
    remainder = func
    for word in table_headers + permitted:
        remainder = remainder.replace(word, "")
    if remainder:
        raise ValueError(f"Bad sign near '{remainder}' in '{func}'")


At this point we know the function is not malicious, but we don't know if any
combination of column names and data can produce malicious content.

To process the rows, we will therefore have to substitute each heading with data
and check it in the same manner:


    for row_index in table:
        if row_index == 0:
            table[0] = table[0] + [new_column_name]
            continue
        row = table[row_index]
    
        data = {k: str(v) for k, v in zip(table_headers, row)}
        # example data = {'A': 123, 'B': 2, 'C': 32, 'D': 321}
    
        # 1. replace column names with values
        new_func = func
        for k, v in data.items():
            new_func = new_func.replace(k, str(v))
    
        # 2. remove text marks.
        new_func = new_func.replace("'", "").replace('"', '')
    
        # 3. we check that no malicious content is left in the string
        # for example a malicious user could put insert `sys.exit()` maliciously.
    
        c = new_func.replace(" ", "")
        for word in permitted:  # systematically remove the longest word first.
            c = c.replace(word, "")
            if not c:
                break
        if c:  # it's not safe!
            raise ValueError(f"Bad sign near '{c}' in '{func}'")
    
        # 4. we use pythons interpreter to evaluate the string as if it was math.
        table[row_index] = row + [eval(new_func)]
    
    for k, v in table.items():
        print(k, ":", v)

    # outputs:
    # 0 : ['A', 'B', 'C', 'D', 'E']
    # 1 : [123, 2, 32, 321, 36.642276422764226]
    # 2 : [133, 2, 33, 123, 35.954887218045116]
    # 3 : [143, 3, 34, 111, 37.80419580419581]
    # 4 : [163, 3, 35, 222, 39.38650306748466]
    # 5 : [143, 4, 36, 333, 42.35664335664335]
    # 6 : [123, 4, 37, 444, 44.642276422764226]



All the code is available in [example.py](example.py).

