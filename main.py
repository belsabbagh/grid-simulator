from src.gui import App

meter_ids = [str(i) for i in range(1, 13)]
app = App(meter_ids)


if __name__ == "__main__":
    grid = app.window.grid
    grid.connect_all((128, 64, 0))
    grid.color_meter("1", (0, 255, 0))
    grid.set_text_meter("1", "100")
    grid.connect("1", "6", (255, 0, 0))
    app.exec()
