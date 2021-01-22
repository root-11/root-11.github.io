from math import gcd
from itertools import combinations


def integer_ratio(values):
    """ returns the smallest integers that maintain the ratio between the values

    Example:
        >>> L = [8.1, -32.4, 20.25, 72.9]  # All values are reducible with 4.05
        >>> integer_ratio(L)
        [2, -8, 5, 18]

    """
    if any(isinstance(i, float) for i in values):
        factor = 10 ** max([len(str(v)) - str(v).index('.') for v in values if isinstance(v, float)])
    else:
        factor = 1

    z = {int(factor * v) for v in values}
    while len(z) > 1:
        z = {gcd(a, b) for a, b in combinations(z, 2)}
    common = z.pop()

    return [int(factor * i) // common for i in values]


if __name__ == "__main__":
    assert integer_ratio([1, 2, 3, 4]) == [1, 2, 3, 4]
    assert integer_ratio([8.1, -32.4, 20.25, 72.9]) == [2, -8, 5, 18]
    assert integer_ratio([1, 10, 100, 1000]) == [1, 10, 100, 1000]
