To my great surprise I couldn't find a python package that presented a solution  
to reduce a list of floating-point values or fractions to their smallest common
ratio.

Say for example I have a list of decimal point values as a part of a pair of 
equations I need to solve, like:

`L = [8.1, -32.4, 20.25, 72.9]` 

All values are reducible with `4.05` to `[2, -8, 5, 18]` but getting to the 
result was a blur.

The function itself is as simple as computing the greatest common divisor after
dealing with the floating-point issue:


    from math import gcd
    from itertools import combinations
    
    def integer_ratio(values):
        if any(isinstance(i, float) for i in values):
            factor = 10 ** max([len(str(v)) - str(v).index('.') for v in values if isinstance(v, float)])
        else:
            factor = 1
    
        z = {int(factor * v) for v in values}
        while len(z) > 1:
            z = {gcd(a, b) for a, b in combinations(z, 2)}
        common = z.pop()
    
        return [int(factor * i) // common for i in values]


Problem solved.

Everything is available in [example.py](example.py) (as usual)