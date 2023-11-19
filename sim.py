import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, HourLocator
import random
from datetime import datetime, timedelta
import time
import socket
import json
import threading

connected_meter_sockets = []


# takes the dataset "https://www.kaggle.com/datasets/uciml/electric-power-consumption-data-set" that
# contains the power consumption of a household every minute for 4 years and averages the power consumption
# to a new dataframe that contains the average power consumption for every minute of the day.
def average_by_time(input_file_path, output_file_path):
    dtype_dict = {
        "Date": str,
        "Time": str,
        "Global_active_power": float,
        "Global_reactive_power": float,
        "Voltage": float,
        "Global_intensity": float,
        "Sub_metering_1": float,
        "Sub_metering_2": float,
        "Sub_metering_3": float,
    }

    # Specify non-numeric values to be treated as NaN
    na_values = ["?"]

    df = pd.read_csv(
        input_file_path, delimiter=";", dtype=dtype_dict, na_values=na_values
    )

    df.fillna(0, inplace=True)

    # Group by 'Time' and calculate the average for each group
    average_data = df.groupby("Time").mean()

    average_data.to_csv(output_file_path)


# generates a dataframe that contains the simulated power generated by solar panels
# for every minute of the day. I arbitrarily chose non zero values to be between the hours
# of 7 am and 7 pm. The values are generated by a linear function that increases from 0 to
# a peak value at 2 pm and then decreases back to 0 at 7 pm. The peak value is calculated
# by taking the average of the minimum and maximum power generated by solar panels in a year
# and then dividing that by 365 to get the average daily power generated and then dividing that
# by 6 to get the average power generated in 6 hours of sunlight.
def generate_solar_power_df():
    # Create a DataFrame with time incrementing every minute from 00:00:00 to 23:59:00
    start_time = datetime.strptime("00:00:00", "%H:%M:%S")
    end_time = datetime.strptime("23:59:00", "%H:%M:%S")
    time_index = pd.date_range(start=start_time, end=end_time, freq="1T")
    solar_df = pd.DataFrame(index=time_index)

    # Calculate peak solar power based on the given annual range
    annual_range = (546 + 874) / 2  # Average of 546 and 874 kWh
    daily_range = annual_range / 365  # Daily average power generation
    peak_solar_power = daily_range / 6  # Assuming 6 hours of sunlight daily

    # Generate synthetic solar power values
    solar_df["Simulated_Solar_Power"] = 0
    solar_df["Time"] = solar_df.index.strftime("%H:%M:%S")
    solar_df["Sun_intensity"] = 0

    # Set solar power values to increase until the peak time and then decrease
    peak_time = datetime.strptime("14:00:00", "%H:%M:%S").time()
    peak_index = solar_df.index.indexer_at_time(peak_time)

    # Set solar power values to increase until the peak time and then decrease
    solar_df.loc[
        : time_index[peak_index][0], "Simulated_Solar_Power"
    ] = peak_solar_power * np.linspace(
        0, 1, len(solar_df.loc[: time_index[peak_index][0]]), endpoint=False
    )

    solar_df.loc[
        time_index[peak_index][0] :, "Simulated_Solar_Power"
    ] = peak_solar_power * np.linspace(
        1, 0, len(solar_df.loc[time_index[peak_index][0] :]), endpoint=False
    )

    # Fill all other values outside the range with zeros
    solar_df.loc[
        (solar_df.index.time < datetime.strptime("07:00:00", "%H:%M:%S").time())
        | (solar_df.index.time > datetime.strptime("19:00:00", "%H:%M:%S").time()),
        "Simulated_Solar_Power",
    ] = 0

    # Save the DataFrame to a file with the same format
    solar_df.to_csv("gen.txt", index=False, header=True, sep=";")

    return solar_df


def plot_usage(df):
    # Convert 'Time' column to datetime for better plotting
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S")

    # Plot power consumption columns over 24 hours
    plt.figure(figsize=(12, 6))

    plt.plot(df["Time"], df["Global_reactive_power"], label="Global Reactive Power")
    plt.plot(df["Time"], df["Sub_metering_1"], label="Sub Metering 1")
    plt.plot(df["Time"], df["Sub_metering_2"], label="Sub Metering 2")
    # plt.plot(df['Time'], df['Sub_metering_3'], label='Sub Metering 3')
    plt.plot(
        df["Time"],
        df["Global_active_power"],
        label="Global Active Power",
        linewidth=4,
        color="blue",
    )

    plt.title(
        "Average Power Consumption Of An Average Household Over 24 Hours (say average one more time))"
    )
    plt.xlabel("Time")
    plt.ylabel("Power Consumption (kW or Wh)")
    plt.legend()

    plt.gca().xaxis.set_major_locator(HourLocator())
    plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))

    plt.xticks(rotation=45, ha="right")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_solar_power(file):
    # Read the gen.txt file
    df = pd.read_csv(file, sep=";")

    # Convert 'Time' column to datetime for better plotting
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S")

    # Plot simulated solar power over 24 hours
    plt.figure(figsize=(12, 6))
    plt.plot(df["Time"], df["Simulated_Solar_Power"], label="Simulated Solar Power")

    plt.title("Simulated Solar Power Generation Over 24 Hours")
    plt.xlabel("Time")
    plt.ylabel("Solar Power Generation (kWh)")
    plt.legend()

    # Set x-axis ticks and labels for every hour
    plt.gca().xaxis.set_major_locator(HourLocator())
    plt.gca().xaxis.set_major_formatter(DateFormatter("%H:%M:%S"))

    plt.xticks(rotation=45, ha="right")  # Rotate x-axis labels for better readability
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def generate_random_power_consumption(df, T, range_min=0, range_max=2):
    # Convert 'Time' column to datetime for comparison
    df["Time"] = pd.to_datetime(df["Time"], format="%H:%M:%S")

    # Convert input time 'T' to datetime
    T_datetime = datetime.strptime(T, "%H:%M:%S")

    # Find the closest time in the DataFrame
    closest_time = min(df["Time"], key=lambda x: abs(x - T_datetime))

    # Get the index of the closest time
    idx = df.index[df["Time"] == closest_time][0]

    # Get the actual value at that time
    actual_value = df.iloc[idx]["Global_active_power"]

    # Generate a random value within the specified range
    random_value = actual_value + random.uniform(range_min, range_max)

    return random_value


def generate_random_power_generated(T, df, deviation_range=(0, 0.1)):
    # Extract time from T
    time_format = "%H:%M:%S"
    current_time = datetime.strptime(T, time_format).time()

    # Convert 'Time' column to datetime.time for comparison
    df["Time"] = pd.to_datetime(df["Time"], format=time_format).dt.time

    # Check if the time is within the range of simulated solar power data
    if current_time < df["Time"].min() or current_time > df["Time"].max():
        return 0  # If time is outside the range, return zero

    # Find the corresponding row in the DataFrame
    row = df[df["Time"] == current_time]
    print(row)

    # If the row is found, get the simulated solar power value and add random deviation
    if not row.empty:
        simulated_power = row["Simulated_Solar_Power"].values[0]
        random_deviation = np.random.uniform(deviation_range[0], deviation_range[1])
        print((simulated_power + (simulated_power * random_deviation)) * 10)
        return (
            simulated_power + (simulated_power * random_deviation)
        ) * 10  # 10 solar panels per household
    else:
        print("ROW VERY EMPTY")
        return 0  # If row is not found, return zero


def send_random_values_to_meters(meter_socket, df, df2, current_time_str):
    # Generate random consumption and generated values
    random_consumption = generate_random_power_consumption(
        df, current_time_str
    )  # Update with your desired time
    random_generated = generate_random_power_generated(
        current_time_str, df2
    )  # Update with your desired time

    # Create a dictionary with consumption and generated values
    data = {
        "type": "update",
        "consumption": random_consumption,
        "generated": random_generated,
    }

    # Send the data to the meter
    print(f"Sending data to meter: {data}")
    meter_socket.sendall(bytes(str(data), "utf-8"))
    meter_update_ui.append(
        {"consumption": random_consumption, "generation": random_generated}
    )


def handle_meter_connection(meter_socket):
    try:
        # Perform any initialization or handshake with the meter here
        # ...

        # Generate a random available port for the meter to use
        init_port = random.randint(1024, 65535)

        # Send the initialization data to the meter
        init_data = {"init_port": init_port}
        meter_socket.sendall(bytes(str(init_data), "utf-8"))

        connected_meter_sockets.append(meter_socket)

        while True:
            # Handle any other communication with the meter if needed
            # ...

            # Simulate real-time updates by sending new random values
            time.sleep(60)  # Update with your desired interval
            send_random_values_to_meters(meter_socket)

    except Exception as e:
        print(f"Error handling meter connection: {e}")
    finally:
        # Remove the socket from the list when the connection is terminated
        connected_meter_sockets.remove(meter_socket)
        meter_socket.close()


def wait_for_meters():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 5000))
    server_socket.listen()

    while True:
        meter_socket, addr = server_socket.accept()
        print(f"Meter connected: {addr}")
        meter_thread = threading.Thread(
            target=handle_meter_connection, args=(meter_socket,)
        )
        meter_thread.start()


if __name__ == "__main__":
    # dataset used https://www.kaggle.com/datasets/uciml/electric-power-consumption-data-set
    # average_by_time('data.txt', 'output.txt')

    df = pd.read_csv("data/output.txt")
    df2 = pd.read_csv("data/gen.txt", sep=";")

    # plot_usage(df)

    # no dataset for power generated by households from solar panels so generated some.
    # solar_df = generate_solar_power_df()
    # print(solar_df[['Time', 'Simulated_Solar_Power']])

    # plot_solar_power('gen.txt')

    # time_input = '08:00:00'
    # random_consumption = generate_random_power_consumption(df, time_input)
    # random_consumption2 = generate_random_power_consumption(df, time_input)
    # print(f"Actual power consumption at {time_input}: {random_consumption:.2f} kW")
    # print(f"Actual power consumption at {time_input}: {random_consumption2:.2f} kW")

    # df = pd.read_csv("gen.txt", sep=';')
    # T = "12:30:00"
    # result = generate_random_power_generated(T, df)
    # print(f"Simulated power generated at {T}: {result} kWh")

    num_houses = 12
    households = [{"consumption": 0, "generated": 0} for _ in range(num_houses)]
    households_sockets = []

    # Set the initial global time
    global_time = datetime.strptime("12:00:00", "%H:%M:%S")

    # Define the time increment in seconds
    time_increment = 1

    # Specify the duration of simulation in seconds (e.g., simulate for 24 hours)
    simulation_duration = 24 * 60 * 60

    meter_listener_thread = threading.Thread(target=wait_for_meters)
    meter_listener_thread.start()

    # Simulate the passage of time
    for _ in range(0, simulation_duration, time_increment):
        meter_update_ui = []
        print(f"Current time: {global_time.strftime('%H:%M:%S')}")
        print(generate_random_power_generated("12:00:15", df2))
        print("Entering the loop...")
        # Get the current time in string format
        current_time_str = global_time.strftime("%H:%M:%S")

        for meter_socket in connected_meter_sockets.copy():
            send_random_values_to_meters(meter_socket, df, df2, current_time_str)
        ui_msg = {
            "type": "update",
            "time": current_time_str,
            "meter_update": meter_update_ui,
        }

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect(("localhost", 1234))
        server.send(bytes(str(ui_msg), "utf-8"))
        server.close()

        # Increment the global time
        global_time += timedelta(minutes=1)

        # Pause for 2 seconds (simulating real-time passage)
        time.sleep(time_increment)