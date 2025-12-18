import datetime
import json
import threading
import time
from timeit import default_timer

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator

from src.config import (
    INCREMENT_MINUTES,
)
from src.core.util.buffer import make_buffer
from src.simulators import synchronous


class MeterRequest(BaseModel):
    # Field constraints handle the "MAX_METERS" check automatically
    num_meters: int = Field(..., alias="numMeters", gt=0, le=30)
    start_date: datetime.datetime = Field(..., alias="startDate")

    # Custom validator for the "past date" check
    @field_validator("start_date")
    @classmethod
    def must_be_in_past(cls, v: datetime.datetime) -> datetime.datetime:
        if v >= datetime.datetime.now():
            raise ValueError("Start date must be in the past")
        return v

    class Config:
        populate_by_name = True


class SimulationThead(threading.Thread):
    def __init__(self, target, *args, **kwargs):
        super().__init__(target=target, *args, **kwargs)
        self.exception = None

    def run(self):
        try:
            super().run()
        except Exception as e:
            print("SimulationThread Error", e)
            self.exception = e


app = FastAPI()
origins = ["https://energy-trading.belsabbagh.me", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    init_start = default_timer()
    await ws.accept()
    time_delta = datetime.timedelta(hours=24)
    data = await ws.receive_json()
    start_date: datetime.datetime = datetime.datetime.fromisoformat(data["startDate"])
    num_meters = int(data["numMeters"])
    end_date = start_date + time_delta
    append_state, fetch_next_state, immutable_iter, _ = make_buffer()
    simulate = synchronous.make_simulate(append_state)
    simulate_thread = SimulationThead(
        target=simulate,
        args=(
            num_meters,
            start_date,
            end_date,
            datetime.timedelta(minutes=INCREMENT_MINUTES),
        ),
    )
    init_time = default_timer() - init_start
    simulate_thread.start()
    print(f"Initialization took {init_time:3} seconds.")

    run_start = default_timer()
    res = await ws.send_json(
        {
            "status": "started",
            "parameters": {
                "START_DATE": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                "END_DATE": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                "NUM_METERS": num_meters,
            },
        }
    )
    try:
        while simulate_thread.is_alive():
            state = fetch_next_state()
            if state is None:
                continue
            res = await ws.send_json({"status": "running", "state": state})
            time.sleep(0.1)
        if simulate_thread.exception is not None:
            raise simulate_thread.exception
        result = {
            "status": "done",
            "debug": {
                "time_taken": f"{default_timer() - run_start}",
            },
            "parameters": {
                "START_DATE": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                "END_DATE": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                "NUM_METERS": num_meters,
            },
        }
        res = await ws.send_json(result)
    except Exception as e:
        res = await ws.send_json({"status": "error", "message": str(e)})


@app.post("/run")
def run(data: MeterRequest):
    init_start = default_timer()
    time_delta = datetime.timedelta(hours=24)
    start_date: datetime.datetime = data.start_date
    num_meters = data.num_meters
    end_date = start_date + time_delta
    append_state, fetch_next_state, immutable_iter, _ = make_buffer()
    simulate = synchronous.make_simulate(append_state)
    simulate_thread = SimulationThead(
        target=simulate,
        args=(
            num_meters,
            start_date,
            end_date,
            datetime.timedelta(minutes=INCREMENT_MINUTES),
        ),
    )
    init_time = default_timer() - init_start
    simulate_thread.start()
    print(f"Initialization took {init_time:3} seconds.")

    def stream():
        run_start = default_timer()
        yield (
            "data: "
            + json.dumps(
                {
                    "status": "started",
                    "parameters": {
                        "START_DATE": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "END_DATE": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "NUM_METERS": num_meters,
                    },
                }
            )
            + "\n\n"
        )
        try:
            while simulate_thread.is_alive():
                state = fetch_next_state()
                if state is None:
                    continue
                yield (
                    "data: "
                    + json.dumps({"status": "running", "state": state})
                    + "\n\n"
                )
            if simulate_thread.exception is not None:
                raise simulate_thread.exception
            result = json.dumps(
                {
                    "status": "done",
                    "debug": {
                        "time_taken": f"{default_timer() - run_start}",
                    },
                    "parameters": {
                        "START_DATE": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "END_DATE": end_date.strftime("%Y-%m-%d %H:%M:%S"),
                        "NUM_METERS": num_meters,
                    },
                }
            )
            yield "data: " + result + "\n\n"

        except Exception as e:
            yield "data: " + json.dumps({"status": "error", "message": str(e)}) + "\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
