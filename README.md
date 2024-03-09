# Grid Simulator

## Getting Started

### Install the dependencies

```bash
pip install -r requirements.txt
```

### Run the server

```bash
python server.py
```

## API Reference

### `GET /realtime/next`

This endpoint retrieves the next state for the current real-time run.

- **Response**
  - **200 OK**: Returns the next state in JSON format.

### `GET /runs`

This endpoint retrieves a list of available runs.

- **Response**
  - **200 OK**: Returns a JSON object containing a list of run IDs.

### `GET /runs/<string:run_id>`

This endpoint retrieves parameters for a specific run.

- **Parameters**
  - `run_id` (string): The ID of the run.

- **Response**
  - **200 OK**: Returns a JSON object containing the parameters of the specified run.

### `GET /runs/<string:run_id>/states/<int:idx>`

This endpoint retrieves a specific state for a given run.

- **Parameters**
  - `run_id` (string): The ID of the run.
  - `idx` (int): The index of the state.

- **Response**
  - **200 OK**: Returns a JSON object containing the specified state.
