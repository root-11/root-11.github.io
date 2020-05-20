I often encounter people who struggle to merge two data sets where the datasets
have different resolution on datetime. It really shouldn't be a
problem, but it often comes to the choice of replacing the last value with zero or similar.
I prefer round to floor. Here are a couple of examples:


Round a date to the first of the month:  

    d = date(1990, 7, 11)
    print(d, "-->", floor(d, '1M'))  
    # 1990-07-11 --> 1990-07-01


Round a time down to the nearest 10 minute interval:


    t = time(23,47,11)
    print(t, "-->", floor(t, "10m"))  
    # 23:47:11 --> 23:40:00 
    
Round a datetime to a whole hour:


    d = datetime(1990, 7, 11, 23, 1, 1)
    print(d, "-->", floor(d, '1h'))  
    # 1990-07-11 23:01:01 --> 1990-07-11 23:00:00


Round a date to first of every second month (because I can):


    d = date(1990, 7, 11)  
    print(d, "-->", floor(d, '2M'))  
    # 1990-07-11 --> 1990-06-01



So how does it work?  
There are 4 parts:


First, setting up the reference system requires that we can detect numbers and the
letter value used for rounding.


    numbers = set('1234567890')
    reference = {'Y': 'year', 'M': 'month', 'D': 'day', 
                 'h': 'hour', 'm': 'minute', 's': "second", 'u': "microsecond"}
    reference_rank = 'usmhDMY'  # deliberately starting from the smallest value.

Second, to interpret of the rounding system now boils down to finding the first character
and looking it up in the dictionary `reference` 


    def get_interval_reference(interval):
        for c in interval:
            if c in reference:
                return reference[c]
        raise ValueError(f"interval must be one of {reference.keys()}")

Third, interpreting the numerical value works the same way:


    def get_interval(interval):
        return int("".join([i for i in interval if i in numbers]))


Fourth and final rounding the value is done easily using all datetime functions
`replace` method. We just need to remember one thing: That all values preceding
the rounded value must be zero. But that's it.


    from datetime import date, time, datetime
    
    def floor(value, interval):
        if not isinstance(value, (datetime, date, time)):
            raise TypeError(f"Got {type(value)}, expected datetime, date or time")
        ir = get_interval_reference(interval)  # ex. 10m --> m --> minute
        iv = get_interval(interval)            # ex. 10m --> 10
        v = getattr(value, ir)                 # ex. 23:47:11 --> 47
        floor_v = (v // iv) * iv               # ex. (47 // 10) * 10 = 40
        irv = {ir: floor_v}                    # ex. {minute: 40}
    
        for c in reference_rank:  
            lower_reference = reference[c]
            if lower_reference == ir:
                return value.replace(**irv)
            if hasattr(value, lower_reference):
                min_value = getattr(value.min, lower_reference)
                value = value.replace(**{lower_reference: min_value})


An example is available (as usual) as [example.py](example.py)