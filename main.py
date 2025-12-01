from src.server import create_flask_server

# add other functionality to api


if __name__ == "__main__":
    record_path = "out/runs"
    start_server = create_flask_server(
        record_path,
    )
    start_server()
