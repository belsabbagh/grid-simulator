import datetime as dt
import random
import pvlib

import pandas as pd

from src.types import TimeGenerator

TIME_FORMAT = "%H:%M:%S"

def generate_random(t: dt.datetime, df: pd.DataFrame, deviation: float) -> float:
    """This function generates a random value based on the time in the dataframe."""
    time = t
    value: float = df.loc[time]['value']
    random_value: float = random.uniform(-deviation, deviation)
    return value + random_value


def mk_gen_df(start_date, end_date, increment) -> pd.DataFrame:
    """This is where you load the generated power dataframe. The dataframe should have a column named "value" and an index of type datetime.datetime."""
    location = pvlib.location.Location(latitude=32.2, longitude=-30)
    times = pd.date_range(
        start=start_date, end=end_date, freq=increment
    )
    solpos = location.get_solarposition(times)
    irradiance = pvlib.irradiance.get_total_irradiance(
        surface_tilt=30,
        surface_azimuth=180,
        solar_zenith=solpos["apparent_zenith"],
        solar_azimuth=solpos["azimuth"],
        dni=1000,
        ghi=100,
        dhi=50,
        dni_extra=1367,
        airmass=2,
    )
    module_parameters = module_parameters = {
        "A0": 1.0,
        "A1": 0.06,
        "A2": 0.2,
        "A3": 0.3,
        "A4": 0.4,
        "B0": 0.05,
        "B1": 0.08,
        "B2": 0.15,
        "B3": 0.25,
        "B4": 0.35,
        "B5": 0.45,
        "C0": 1.5,
        "C1": 2.0,
        "C2": 3.0,
        "C3": 4.0,
        "C4": 5.0,
        "C5": 6.0,
        "C6": 7.0,
        "C7": 8.0,
        "Isco": 8.5,
        "Impo": 7.5,
        "Voco": 35.0,
        "Vmpo": 30.0,
        "Aisc": 0.005,
        "Aimp": 0.004,
        "Bvoco": -0.3,
        "Mbvoc": -0.03,
        "Bvmpo": -0.25,
        "Mbvmp": -0.02,
        "N": 1.2,
        "Cells_in_Series": 60,
        "IXO": 4.5,
        "IXXO": 5.0,
        "FD": 0.5,
    }

    power_output = pvlib.pvsystem.sapm(
        effective_irradiance=irradiance["poa_global"],
        temp_cell=25,
        module=module_parameters,
    )['p_mp'] * 2.3/ 1000
    gen: pd.DataFrame = pd.DataFrame(power_output, columns=["value"])
    gen.index = times
    return gen


def mk_con_df(start_date, end_date, increment) -> pd.DataFrame:
    """
    This is where you load the consumed power dataframe. 
    The dataframe should have a column named "value" 
    and an index of type datetime.datetime.
    """
    con = pd.read_csv("data/output.txt")
    idx_range = pd.date_range(start=start_date, end=end_date, freq=increment)
    values = [con.loc[con['Time'] == t.time().strftime(TIME_FORMAT)]['Global_active_power'].values[0] for t in idx_range]
    con = pd.DataFrame(values, columns=["value"])
    con.index = idx_range
    return con

def mk_instance_generator(
    start_date: dt.datetime, end_date: dt.datetime, increment: dt.timedelta,
    d: float,
) -> TimeGenerator[tuple[float, float]]:
    gen: pd.DataFrame = mk_gen_df(start_date, end_date, increment)
    con: pd.DataFrame = mk_con_df(start_date, end_date, increment)

    def instance_generator(t: dt.datetime) -> tuple[float, float]:
        return generate_random(t, gen, d), generate_random(t, con, d)

    return instance_generator


def generate_normal_random_parameters(means, deviations) -> list[float]:
    # generate a normmally distributed random number for each mean and deviation
    return [
        random.random() * deviation + mean for mean, deviation in zip(means, deviations)
    ]


def mk_grid_state_generator() -> TimeGenerator[list[float]]:

    means: list[float] = [0.4, 20, 239.696, 3.132]
    devs: list[float] = [0.1, 1, 1, 0.1]

    def generate_grid_state(_t: dt.datetime):
        """It returns a list of 4 parameters: load, temperature, voltage, intensity in that order."""
        return generate_normal_random_parameters(means, devs)

    return generate_grid_state
