from dataclasses import dataclass
import tensorflow as tf

load_model = tf.keras.models.load_model

def mk_predict_function(efficiency_model_path, duration_model_path, quality_model_path):
    # Load models
    efficiency_model = load_model(efficiency_model_path)
    duration_model = load_model(duration_model_path)
    quality_model = load_model(quality_model_path)
    
    if efficiency_model is None:
        raise Exception("Efficiency model was not loaded")
    if duration_model is None:
        raise Exception("Duration model was not loaded")

    # Create predict function
    def predict_function(grid_load_gwh, grid_temp_c, voltage_v, global_intensity_A, transaction_amount_wh)-> tuple[float,float]:
        """The predict function returns a tuple of (efficiency, duration) with the measuring units being (ratio, hours)"""
        grid_loss = efficiency_model.predict([[grid_load_gwh, grid_temp_c]])
        efficiency = (grid_load_gwh - grid_loss[0][0]) / grid_load_gwh
        duration = duration_model.predict([[voltage_v, global_intensity_A, efficiency, transaction_amount_wh]])
        return efficiency, duration[0][0]

    # Return
    return predict_function

@dataclass
class Offer:
    amount: float
    source: str
    
@dataclass
class Trade:
    amount: float
    source: str
    destination: str
    timestamp: str
    duration: float
    efficiency: float
    quality: float

@dataclass
class GridMetrics:
    load: float
    temperature: float
    voltage: float
    intensity: float

def get_selling_history(meter_id: str):
    """This function should return a list of trades that the meter sold in the past"""
    return []
    
def mk_fitness_function(efficiency_model_path, duration_model_path, quality_model_path):
    predict = mk_predict_function(efficiency_model_path, duration_model_path, quality_model_path)

    def fitness(amount_needed, offer: Offer, metrics: GridMetrics) -> float:
        """This function should return a fitness score for the offer"""
        efficiency, duration = predict(metrics.load, metrics.temperature, metrics.voltage, metrics.intensity, offer.amount)
        selling_history = get_selling_history(offer.source)
        return 1/(offer.amount - amount_needed)

    return fitness


def mk_choose_best_offers_function(efficiency_model_path, duration_model_path, quality_model_path, count: int = 5):
    fitness = mk_fitness_function(efficiency_model_path, duration_model_path, quality_model_path)

    def choose_best_offers_function(amount_needed, offers, metrics: GridMetrics) -> list[Offer]:
        """This function should return the best offers from the list of offers"""
        return sorted(offers, key=lambda offer: fitness(amount_needed, offer, metrics), reverse=True)[:count]
        
    return choose_best_offers_function
