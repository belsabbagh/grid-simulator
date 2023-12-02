import datetime
import time
from src.core.data_generator import make_instance_generator

if __name__ == '__main__':
    gen = make_instance_generator(0.1)
    startdate = datetime.datetime(2010, 1, 1, 10, 0, 0)
    enddate = datetime.datetime(2010, 1, 1, 18, 59, 59)
    t = startdate
    while t <= enddate:
        print("Surplus" if gen(t)[0] - gen(t)[1] > 0 else "Deficit")
        t += datetime.timedelta(minutes=1)