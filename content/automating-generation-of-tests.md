It's often a challenge to assure that tests cover all combinations of inputs when they're written by hand.
The logical thing is therefore NOT to write them by hand. Let python do that for you.

Here's an example.  
I have a function, that I'd like to test for various inputs. It works for what I intended, but I'd like to check.
In addition I'd like to see all the cases where the code raises an exception.

    def adder(a, b):  # function to test.
        """ adds a to b"""
        return a + b

 
the input options are integers, floats, lists and strings:

    options = [9, 9.0, [9], "9"] 

I also need a template that reflects the test I would write, should I have written it by hand. This is a string akin
to this:

    test_template = """
    
    def test_adder_{}():
        _ = adder{}
    """

With these 3 components, I can now generate my tests automatically and write any that fail out automatically.
 
    from pathlib import Path
    from itertools import product
    

    def test_discovery():
        test_number = 0
        for c in product(*[options, options]):  # the cartesian product of all inputs.
            test_number += 1  
            try:  
                adder(*c)  # the exercise of my target function
            except Exception:
                new_test = test_template.format(test_number, c)   # formatting of the test template to a test.
                with Path(__file__).open('a') as fo:  # appending the test to this script.
                    fo.write(new_test)


When the function `test_discovery`, above, is called, it will **append** the tests that raise `exeception`, like this:

    test_discovery() 
    
    
    def test_adder_3():
        _ = adder(9, [9])
    
    
    def test_adder_4():
        _ = adder(9, '9')
    
    
    def test_adder_7():
        _ = adder(9.0, [9])
    
    
    def test_adder_8():
        _ = adder(9.0, '9')
    
    
    def test_adder_9():
        _ = adder([9], 9)
    
    
    def test_adder_10():
        _ = adder([9], 9.0)
    
    
    def test_adder_12():
        _ = adder([9], '9')
    
    
    def test_adder_13():
        _ = adder('9', 9)
    
    
    def test_adder_14():
        _ = adder('9', 9.0)
    
    
    def test_adder_15():
        _ = adder('9', [9])


As you may notice the test name numbers are not chronological, as the tests that pass have not been written.

Neat he?


