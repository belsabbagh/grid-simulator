import msvcrt
import subprocess
import time

SLEEP_TIME = 3

if __name__ == "__main__":
    # Run the three scripts in parallel
    main = subprocess.Popen(["python", "main.py"])
    time.sleep(SLEEP_TIME)
    sim = subprocess.Popen(["python", "sim.py"])
    time.sleep(SLEEP_TIME)
    meters = subprocess.Popen(["python", "meters.py"])

    # wait for key event esc
    while True:
        if msvcrt.kbhit() and msvcrt.getch() == chr(27).encode():
            main.kill()
            sim.kill()
            meters.kill()
            print("Terminated simulation")
            break
