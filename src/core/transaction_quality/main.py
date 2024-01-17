from dataset_preparation import add_score_and_remove_parameters
from models import *
import pandas as pd
from sklearn.model_selection import train_test_split

PATH_TO_DATASET = 'data/transaction_quality.csv'

# Load the dataset
def load_dataset(path_to_dataset):
    df = pd.read_csv(path_to_dataset)
    add_score_and_remove_parameters(df)

    return df

# Split the dataset into train and test sets
def split_dataset(df):
    X_train, X_test, y_train, y_test = train_test_split(df.drop(['score'], axis=1), df['score'], test_size=0.2, random_state=42)
    return X_train, X_test, y_train, y_test

# Train the model
def train_ml_model(model, X_train, y_train):
    model.fit(X_train, y_train)

def train_nn_model(model, X_train, y_train):
    model.fit(X_train, y_train, epochs=10, batch_size=32)


if __name__ == '__main__':
    # Load the dataset
    df = load_dataset(PATH_TO_DATASET)

    # Split the dataset into train and test sets
    X_train, X_test, y_train, y_test = split_dataset(df)

    # Train the model
    model = create_linear_regression_model()
    train_ml_model(model, X_train, y_train)

    # Evaluate the model
    print('Linear Regression Model')
    print('Train score:', model.score(X_train, y_train))
    print('Test score:', model.score(X_test, y_test))

    # Train an nn model
    model = create_standard_neural_network_model(X_train.shape[1])
    train_nn_model(model, X_train, y_train)

    # Evaluate the model
    print('Neural Network Model')
    print('Train score:', model.evaluate(X_train, y_train))
    print('Test score:', model.evaluate(X_test, y_test))

