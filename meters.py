from src.core.meter import Meter


if __name__ == "__main__":
    meter_list = []
    threads = []
    num_meters = 12
    for i in range(num_meters):
        meter = Meter(i)
        meter_list.append(meter)
        thread1, thread2 = meter.start()
        threads.extend([thread1, thread2])
    print(f"Started {num_meters} meters")
    for thread in threads:
        thread.join()
    print("All threads joined. Exiting.")
