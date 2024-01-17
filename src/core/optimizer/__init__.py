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
