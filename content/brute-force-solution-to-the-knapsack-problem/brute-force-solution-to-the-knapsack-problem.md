Computing the brute force solution is rarely the best way to go except when checking other solvers. However, as running the test suite can be time-consuming, it's nice to have tools that run reasonably quickly.

The knapsack problem is an optimisation problem where a combination of items must respect weight or volume constraints and have the highest possible value.


To test a solver for the knapsack problem it is helpful to generate all unique combinations
of items, so that the evalution is exhaustive. I will refer to this `set` as the 
`unique_powerset`. Here's an example:

        unique_powerset([1,1,1,2,2,3]) --> [
            (1,), (1, 1), (1, 1, 1), (2,), (2, 2), (3,),
            (1, 2), (1, 1, 2), (1, 1, 1, 2),
            (1, 2, 2), (1, 1, 2, 2), (1, 1, 1, 2, 2),
            (1, 3), (1, 1, 3), (1, 1, 1, 3),
            (2, 3), (2, 2, 3), (1, 2, 3),
            (1, 1, 2, 3), (1, 1, 1, 2, 3),
            (1, 2, 2, 3), (1, 1, 2, 2, 3),
            (1, 1, 1, 2, 2, 3)
        ] # 23 records

This should be viewed in contrast to the [powerset](https://docs.python.org/3/library/itertools.html#itertools-recipes)
which would generate repeated values:

        powerset([1,1,1,2,2,3]) --> [
            (),
            (1,), (1,), (1,),
            (2,), (2,),
            (3,),
            (1, 1), (1, 1), (1, 1),
            (1, 2), (1, 2), (1, 2), (1, 2), (1, 2), (1, 2),
            (1, 3), (1, 3), (1, 3),
            ... cut for brevity ...
            (1, 1, 1, 2, 2), (1, 1, 1, 2, 3), (1, 1, 1, 2, 3),
            (1, 1, 2, 2, 3), (1, 1, 2, 2, 3), (1, 1, 2, 2, 3)
        ] # 63 records.

As the number of duplicate values grow, the number of redundant options
grows exponentially if using powerset.
In the example above the powerset generates 63 vs the 23 unique options
generated in the unique_powerset.

The assertion `set(powerset(iterable)) == unique_powerset(iterable)` must
always be true, and whilst the former method is available, powerset of
any iterables longer than 20 items, become intolerable except for the most
patient programmers.

The trick is therefore the generate the unique powerset without having to filter 
the duplicates. This calls for some combinatorial tricks, but explaining these 
without the context they're applied in, would be rather pointless.

So without further ado, this is the full code:

    from itertools import combinations
    
    
    def unique_powerset(iterable):
        # first we summarize the iterable into blocks of identical values. Example:
        # [1,1,1,2,2,3] -->
        # d = {
        #     1: [[1],[1,1],[1,1,1]],
        #     2: [[2],[2,2]],
        #     3: [[3]]
        #     }
        d = {i: iterable.count(i) for i in set(iterable)}
        blocks = {i: [] for i in set(iterable)}
        for k, v in d.items():
            for i in range(1, v + 1):
                blocks[k].append([k] * i)
    
        # Next we generate the powersets of the unique values only:
        for r in range(1, len(blocks) + 1):
            for clusters in combinations(blocks, r):
                # each 'cluster' is now an element from the powerset of the
                # unique elements --> (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)
    
                # first we set indices for the accessing the first element in
                # the clusters values:
                c_index = [0 for _ in clusters]
                # this allows us to increment each index in values of each block.
                # Hereby c_index = [0,1,0] on the cluster (1,2,3) becomes [1,2,2,3].
    
                # next we set the upper limit to control the incremental iteration
                c_limit = [len(blocks[i]) for i in clusters]
    
                while not all(a == b for a, b in zip(c_index, c_limit)):
                    # harvest combination
                    result = []
                    for idx, grp in enumerate(clusters):  # (1,2,3)
                        values = blocks[grp]  # v = 1:[[1],[1,1]. [1,1,1]]
                        value_idx = c_index[idx]  # [0,0,0]
                        value = values[value_idx]
                        result.extend(value)
                    yield tuple(result)
    
                    # update the indices:
                    reset_idx = None
                    for i in range(len(clusters)):  # counter position.
                        if c_index[i] < c_limit[i]:
                            c_index[i] += 1  # counter value
    
                        if c_index[i] == c_limit[i]:
                            reset_idx = i
                        else:
                            break
    
                    # reset the preceding values in indices if the counter position
                    # has incremented.
                    if reset_idx is not None and reset_idx + 1 < len(clusters):
                        for j in range(reset_idx + 1):
                            c_index[j] = 0
    

End.

