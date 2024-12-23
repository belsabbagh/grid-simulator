import tensorflow as tf
import numpy as np
import random


from src.core.transaction_quality.scoring import mk_calculate_transaction_score_function

keras_load_model = tf.keras.models.load_model


def mk_select_random_offers_function(count: int = 5):
    def select_random_offers_function(offers) -> list[dict]:
        return random.sample(offers, count)

    return select_random_offers_function


def load_model(model_path):
    model = keras_load_model(model_path)

    def predict(x):
        return model.predict(x)

    return predict


def load_model_weights(model_path):
    model = keras_load_model(model_path)
    w = model.get_weights()[0]

    def predict(x):
        return np.dot(w, x)
    
    return predict

def load_json_model(model_path):
    with open(model_path, "r") as f:
        model = tf.keras.models.model_from_json(f.read())
    weights = model.get_weights()[0]

    def predict(x):
        return np.dot(weights, x)

    return predict

def mk_predict_function(
    efficiency_model_path, duration_model_path, quality_model_path, load_model
):
    efficiency_model = load_json_model(efficiency_model_path)
    duration_model = load_json_model(duration_model_path)
    quality_model = load_json_model(quality_model_path)

    if efficiency_model is None:
        raise Exception("Efficiency model was not loaded")
    if duration_model is None:
        raise Exception("Duration model was not loaded")

    def predict_function(
        grid_load_gwh, grid_temp_c, voltage_v, global_intensity_A, transaction_amount_wh
    ) -> tuple[float, float]:
        """The predict function returns a tuple of (efficiency, duration) with the measuring units being (ratio, hours)"""
        grid_loss = efficiency_model([[grid_load_gwh, grid_temp_c]])
        efficiency = (grid_load_gwh - grid_loss[0][0]) / grid_load_gwh
        duration = duration_model(
            [[voltage_v, global_intensity_A, efficiency, transaction_amount_wh]]
        )
        return efficiency, duration[0][0]

    return predict_function


def mk_fitness_function(efficiency_model_path, duration_model_path, quality_model_path, weights=None):
    predict = mk_predict_function(
        efficiency_model_path, duration_model_path, quality_model_path, load_model_weights
    )
    if weights is None:
        weights = (1, -1, 1, -1, 1, -1)

    calculate_transaction_score = mk_calculate_transaction_score_function()

    def fitness(amount_needed, offer: dict, metrics: list[float]) -> float:
        """This function should return a fitness score for the offer.
        - Higher efficiency should be better
        - Lower duration should be better
        - Higher quality should be better
        - Lower market participation should be better
        - Lower amount offered - amount needed should be better
        """
        efficiency, duration = predict(
            metrics[0],
            metrics[1],
            metrics[2],
            metrics[3],
            offer["amount"],
        )
        quality = calculate_transaction_score(offer["amount"] - amount_needed, duration)
        params = (
            efficiency,
            duration,
            quality,
            offer["participation_count"],
            amount_needed,
            offer["amount"],
        )
        return np.dot(weights, params)

    return fitness


def mk_choose_best_offers_function(
    efficiency_model_path, duration_model_path, quality_model_path, count: int = 5, weights=None
):
    fitness = mk_fitness_function(
        efficiency_model_path, duration_model_path, quality_model_path, weights
    )

    def choose_best_offers_function(
        amount_needed: float, offers: list[dict], metrics: list[float]
    ) -> list[tuple[dict, float]]:
        """This function should return the best offers from the list of offers and their scores."""
        random_select = mk_select_random_offers_function(count)
        if len(offers) > count:
            offers = random_select(offers)
        fitness_scores: map[tuple[dict, float]] = map(
            lambda offer: (offer, fitness(amount_needed, offer, metrics)), offers
        )
        best: list[tuple[dict, float]] = sorted(
            fitness_scores, key=lambda x: x[1], reverse=True
        )[:count]
        return best

    return choose_best_offers_function
