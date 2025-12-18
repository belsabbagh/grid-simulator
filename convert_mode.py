import tensorflow as tf
import pandas as pd


def export_weights_to_csv(json_path, weights_path, output_csv):
    # 1. Load the architecture from JSON
    with open(json_path, "r") as f:
        model_json = f.read()

    model = tf.keras.models.model_from_json(model_json)

    # 2. Load the actual weights into the architecture
    # Note: Ensure the weights file matches the architecture
    model.load_weights(weights_path)

    weight_data = []

    # 3. Iterate through layers to extract weights
    for layer in model.layers:
        weights = layer.get_weights()
        if not weights:
            continue

        # weights[0] is typically the kernel/weights matrix
        # weights[1] is typically the bias vector
        for i, w in enumerate(weights):
            layer_type = "weight" if i == 0 else "bias"
            flattened = w.flatten()

            for idx, val in enumerate(flattened):
                weight_data.append(
                    {
                        "layer_name": layer.name,
                        "type": layer_type,
                        "index": idx,
                        "value": val,
                    }
                )

    # 4. Save to CSV
    df = pd.DataFrame(weight_data)
    df.to_csv(output_csv, index=False)
    print(f"Successfully exported weights to {output_csv}")


# Usage
export_weights_to_csv(
    "models/grid-loss.json", "models/grid-loss.h5", "models/grid-loss-weights.csv"
)
export_weights_to_csv(
    "models/duration.json", "models/duration.h5", "models/duration-weights.csv"
)
