Imagine we have a program that runs for longer than we'd ideally like.  
For example we need to update a progress bar or similar. 
How would we change the program so that we can perform the interrupt making the code any harder to read?

Let's start with the basic program:
    
    def batchprogram(data):
        for ix, item in enumerate(data):
            data[ix] = item + 1
    
        for ix, item in enumerate(data):
            data[ix] = item * item
    
        total = sum(data)
        for ix, item in enumerate(data):
            data[ix] = item / total
    
        return data
    
    
    print(batchprogram(data=[1,2,3,4]))
    >>> [0.07407407407407407, 0.16666666666666666, 0.2962962962962963, 0.46296296296296297]

As the computational complexity is O(n), this would potentially run for a long time.  
To return the control to the main process at a minimum cost of complexity, all we have 
to add is a modest `yield`: 

    
    def batchprogram2(data):
        for ix, item in enumerate(data):
            data[ix] = item + 1
            yield
    
        for ix, item in enumerate(data):
            data[ix] = item * item
            yield
    
        total = sum(data)
        yield
        for ix, item in enumerate(data):
            data[ix] = item / total
            yield
    
        yield data

The change to the code is acceptable: Insert a yield and you're almost done.  
For the controller to display progress we can use dots:

    for ix, step in enumerate(batchprogram2(data=[1,2,3,4])):
        print("", end=".")
    print(data)
    ..............
    [0.07407407407407407, 0.16666666666666666, 0.2962962962962963, 0.46296296296296297]


If I wanted more explicit information about progress, I can add it to the `yield`:
    
    def batchprogram3(data):
        n = len(data)
    
        for ix, item in enumerate(data):
            data[ix] = item + 1
            yield f"step 1 - {ix}/{n} complete"
    
        for ix, item in enumerate(data):
            data[ix] = item * item
            yield f"step 2 - {ix}/{n} complete"
    
        yield f"step 3 - started"
        total = sum(data)
        yield f"step 3 - done"
    
        for ix, item in enumerate(data):
            data[ix] = item / total
            yield f"step 4 - {ix}/{n} complete"
    
        yield data
    
    
    for step in batchprogram3(data=[1,2,3,4]):
        if isinstance(step, str):
            print(step)
        else:
            data = step
    print(data)
    
Result:  

    step 1 - 0/4 complete
    step 1 - 1/4 complete
    step 1 - 2/4 complete
    step 1 - 3/4 complete
    step 2 - 0/4 complete
    step 2 - 1/4 complete
    step 2 - 2/4 complete
    step 2 - 3/4 complete
    step 3 - started
    step 3 - done
    step 4 - 0/4 complete
    step 4 - 1/4 complete
    step 4 - 2/4 complete
    step 4 - 3/4 complete
    [0.07407407407407407, 0.16666666666666666, 0.2962962962962963, 0.46296296296296297]

Almost a classic.

