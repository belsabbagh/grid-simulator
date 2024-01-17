waste_weight = 0.4
time_weight = 0.3
distance_weight = 0.3

def calculate_transaction_score(waste, time, distance):
    # Normalize values 
    normalized_waste = waste / max(waste, time, distance)
    normalized_time = time / max(waste, time, distance)
    normalized_distance = distance / max(waste, time, distance)

    # Calculate the transaction score using the weighted sum
    score = (waste_weight * normalized_waste) + (time_weight * normalized_time) + (distance_weight * normalized_distance)

    return score