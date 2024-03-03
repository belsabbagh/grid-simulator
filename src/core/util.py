import datetime

def date_range(start: datetime.datetime, end: datetime.datetime, delta: datetime.timedelta):
    current = start
    while current < end:
        yield current
        current += delta
