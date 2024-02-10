import numpy as np


def mk_calculate_transaction_score_function():
    waste_weight = 0.4
    time_weight = 0.3

    def calculate_transaction_score(wasted_amount, trade_duration):
        """This function should return a score for the transaction. The higher the better. We want to minimize the waste and the time it takes to complete the transaction. The values are NOT normalized"""
        return (1 - wasted_amount) * waste_weight + (1 - trade_duration) * time_weight

    return calculate_transaction_score
