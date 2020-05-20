from datetime import date, time, datetime
numbers = set('1234567890')
reference = {'Y': 'year', 'M': 'month', 'D': 'day', 'h': 'hour', 'm': 'minute', 's': "second", 'u': "microsecond"}
reference_rank = 'usmhDMY'


def get_interval_reference(interval):
    for c in interval:
        if c in reference:
            return reference[c]
    raise ValueError(f"interval must be one of {reference.keys()}")


def get_interval(interval):
    return int("".join([i for i in interval if i in numbers]))


def floor(value, interval):
    if not isinstance(value, (datetime, date, time)):
        raise TypeError(f"Got {type(value)}, expected datetime, date or time")
    ir = get_interval_reference(interval)  # ex. 10m --> m --> minute
    iv = get_interval(interval)  # ex. 10m --> 10
    v = getattr(value, ir)  # ex. 23:47:11 --> 47
    floor_v = (v // iv) * iv   # ex. (47 // 10) * 10 = 40
    irv = {ir: floor_v}  # ex. {minute: 40}

    for c in reference_rank:  # deliberately starting from the smallest value.
        lower_reference = reference[c]
        if lower_reference == ir:
            return value.replace(**irv)
        if hasattr(value, lower_reference):
            min_value = getattr(value.min, lower_reference)
            value = value.replace(**{lower_reference: min_value})


d = date(1990, 7, 11)
print(d, "-->", floor(d, '2M'))
# 1990-07-11 --> 1990-06-01

d = datetime(1990, 7, 11, 23, 1, 1)
print(d, "-->", floor(d, '1h'))
# 1990-07-11 23:01:01 --> 1990-07-11 23:00:00


t = time(23,47,11)
print(t, "-->", floor(t, "10m"))
# 23:47:11 --> 23:40:00


d = date(1990, 7, 11)
print(d, "-->", floor(d, '1M'))
# 1990-07-11 --> 1990-07-01

