from src.server import create_flask_server




if __name__ == "__main__":
    record_path = "out/runs"
    start_server = create_flask_server(
        record_path,
    )
    start_server()
