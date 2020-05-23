"""
determining the convex hull is useful for many applications, such as linear programming, where
the convex hull declares the boundadry of the solution landscape. In graph theory the convex
hull can illustrate the shortest path around nodes and hence be used to determine clusters and
overlaps between sets of nodes.

A textbook approach to solve the convex hull is to use the "left turn" approach and
visit all nodes in a sequential appraoch. This is obviously O(n).

> Andrew's monotone chain convex hull algorithm constructs the convex hull of a
> set of 2-dimensional points in {\displaystyle O(n\log n)}O(n\log n) time.
>
> It does so by first sorting the points lexicographically (first by x-coordinate,
> and in case of a tie, by y-coordinate), and then constructing upper and lower
> hulls of the points in {\displaystyle O(n)}O(n) time.
>
> An upper hull is the part of the convex hull, which is visible from the above.
> It runs from its rightmost point to the leftmost point in counterclockwise order.
> Lower hull is the remaining part of the convex hull.

[source](https://en.wikibooks.org/wiki/Algorithm_Implementation/Geometry/Convex_hull/Monotone_chain)


"""

from collections import namedtuple
from random import randint, seed
from pathlib import Path


seed(42)

Point = namedtuple('Point', ['x', 'y'])


def point_cloud(n_points, x_max=400, y_max=300):
    return [Point(x=randint(-x_max, x_max), y=randint(-y_max, y_max)) for _ in range(n_points)]


def convex_hull(points):
    n_points = len(points)
    assert n_points >= 3, "can't have a hull with < 3 points."
    points.sort(key=lambda p: (p.x, p.y))

    lower_limit_upper_hull = min(points[0].y, points[-1].y)
    upper_limit_lower_hull = max(points[0].y, points[-1].y)

    upper_hull = []
    lower_hull = []
    for point in points:

        if point.y > lower_limit_upper_hull:
            upper_hull.append(point)
            while len(upper_hull) >= 3:
                a, b, c = upper_hull[-3:]
                if right_turn(a, b, c) is True:
                    break
                else:
                    upper_hull.remove(b)

        if point.y < upper_limit_lower_hull:
            lower_hull.append(point)
            while len(lower_hull) >= 3:
                a, b, c = lower_hull[-3:]
                if right_turn(a, b, c) is False:
                    break
                else:
                    lower_hull.remove(b)

        title = Path(__file__).parent / f"{points.index(point)}.png"
        plot(points, lower_hull[::-1] + upper_hull[:-1], title=title)

    title = Path(__file__).parent / f"{len(points)}.png"
    plot(points, lower_hull[::-1] + upper_hull[:-1], title=title)

    return upper_hull[:-1] + lower_hull[::-1]


def right_turn(A, B, C):
    dxAC, dyAC = C.x - A.x, C.y - A.y
    dxAB, dyAB = B.x - A.x, B.y - A.y
    if dxAC == 0:
        aAC = float('inf')
    else:
        aAC = dyAC / dxAC
    if dxAB == 0:
        aAB = float('inf')
    else:
        aAB = dyAB / dxAB

    if aAB > aAC:  # right
        return True
    elif aAB < aAC:  # left
        return False
    else:  # straight
        return None


def plot(points, line=None, title=""):
    from matplotlib import pyplot as plt

    plt.figure()
    xs = [c.x for c in points]
    ys = [c.y for c in points]

    plt.plot(xs, ys, 'o')

    if line:
        xs = [c.x for c in line]
        ys = [c.y for c in line]
        plt.plot(xs, ys, 'bo-')
    plt.title(title)
    # plt.show()
    plt.savefig(fname=title)


def test_triangle():
    points = [Point(x, y) for x, y in [(0, 0), (0, 1), (1, 0)]]
    hull = convex_hull(points)
    plot(points, hull, title="triangle")


def test_box():
    points = [Point(x, y) for x, y in [(0, 0), (0, 1), (0.5, 0.5), (1, 1), (1, 0)]]
    hull = convex_hull(points)
    plot(points, hull, title="box")


def test_random():
    for i in range(1,4):
        points = point_cloud(2*10**i)
        hull = convex_hull(points)
        plot(points, hull, title=f"{len(hull)} @ {len(points)} points")


def animate():
    points = point_cloud(200)
    hull = convex_hull(points)
    # plot(points, hull, title=f"{len(hull)} @ {len(points)} points")


animate()
# test_random()

