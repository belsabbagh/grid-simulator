import pandas as pd
from scoring import calculate_transaction_score


def add_score_and_remove_parameters(df):
    # Calculate the score using existing parameters
    df['score'] = df.apply(lambda row: calculate_transaction_score(row['waste'], row['time'], row['distance']), axis=1)
    
    # Remove the waste, time, and distance columns since they are no longer needed
    df = df.drop(['waste', 'time', 'distance'], axis=1)
    
    return df
