import numpy as np

v1 = [1, 2, 3]
v2 = [2.4, 3, -1]


def f1(v1, v2):
    return list(np.cross(v1, v2))


def f2(v1, v2):
    a1, a2, a3 = v1
    b1, b2, b3 = v2
    return [a2 * b3 - a3 * b2, -(a1 * b3 - a3 * b1), a1 * b2 - a2 * b1]


def x1():
    for i in range(100000):
        v3 = f1(v1, v2)


def x2():
    for i in range(100000):
        v4 = f2(v1, v2)


if __name__ == "__main__":
    x1()
    x2()
