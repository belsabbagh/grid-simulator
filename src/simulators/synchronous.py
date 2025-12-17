import pickle
from typing import Dict, List, Tuple

from src.config import DEVIATION, NUM_METERS
from src.core.data_generator import mk_grid_state_generator, mk_instance_generator
from src.core.optimizer import mk_choose_best_offers_function
from src.core.util import date_range, fmt_grid_state
from src.types import SimulateFunction


def calc_sizeof_offers_msg(n):
    example_offer = {
        "source": ("localhost", 94065),
        "price": 0.0,
        "amount": 0.0,
    }
    return n * len(pickle.dumps(example_offer))


offers_msg_size = calc_sizeof_offers_msg(NUM_METERS)


class Meter:
    id: str
    surplus: float = 0
    sold_count: int = 0

    def __init__(self, id: str) -> None:
        self.id = id

    def read_env(self, gen: float, con: float) -> float:
        """Get generation and consumption and return surplus"""
        self.surplus = gen - con
        return self.surplus

    def choose_offer(
        self, offers: List[dict], grid_state: List[float], trade_chooser
    ) -> Tuple[Dict, float]:
        return trade_chooser(self.surplus, offers, grid_state)


def make_simulate(append_state) -> SimulateFunction:
    def simulate(n, start_date, end_date, datetime_delta):
        trade_chooser = mk_choose_best_offers_function(
            "models/grid-loss.json",
            "models/duration.json",
            "models/grid-loss.json",
            weights=None,
        )
        meters: Dict[str, Meter] = {f"{i}": Meter(f"{i}") for i in range(n)}
        ledger: List[Dict] = []
        data_generator = mk_instance_generator(
            start_date, end_date, datetime_delta, DEVIATION
        )
        grid_state_generator = mk_grid_state_generator()
        for t in date_range(start_date, end_date, datetime_delta):
            grid_state = grid_state_generator(t)
            offers: List[Dict[str, str | int | float]] = []
            for i, m in meters.items():
                gen, con = data_generator(t)
                m.read_env(gen, con)
                if m.surplus > 0:
                    offers.append(
                        {
                            "source": i,
                            "amount": m.surplus,
                            "participation_count": m.sold_count,
                        }
                    )

            trades: Dict[str, str | None] = {}
            requests: Dict[str, List[Tuple[str, float]]] = {}
            transfers: Dict[str, float] = {}
            for i, m in meters.items():
                if m.surplus > 0:
                    trades[i] = None
                    continue
                choices = m.choose_offer(offers, grid_state, trade_chooser)
                if not choices:
                    trades[i] = None
                    continue
                offer, fitness = choices[0]
                trades[i] = offer["source"]
                requests[offer["source"]] = (
                    [(i, fitness)]
                    if requests.get(offer["source"]) is None
                    else requests[offer["source"]] + [(i, fitness)]
                )

            for seller, buyers in requests.items():
                buyer, fitness = sorted(buyers, key=lambda x: x[1], reverse=True)[0]
                amount = meters[seller].surplus
                ledger.append(
                    {
                        "source": seller,
                        "buyer": buyer,
                        "amount": meters[seller].surplus,
                        "time": t,
                    }
                )
                meters[seller].sold_count += 1
                transfers[buyer] = min(
                    min(
                        amount,
                        grid_state[-1]
                        * grid_state[-2]
                        * datetime_delta.total_seconds(),
                    ),
                    abs(meters[buyer].surplus),
                )
                transfers[seller] = -abs(transfers[buyer])
            meter_display_ids = {addr: i for i, addr in enumerate(meters.keys(), 1)}
            meter_states = [
                {
                    "id": meter_display_ids[i],
                    "surplus": m.surplus,
                    "sent": transfers.get(i, 0),
                    "in_trade": (
                        meter_display_ids.get(trades.get(i, None), "")
                        if i in trades
                        else None
                    ),
                    "participation_count": m.sold_count,
                }
                for i, m in meters.items()
            ]
            append_state(
                {
                    "time": t.strftime("%H:%M:%S"),
                    "meters": meter_states,
                    "grid_state": fmt_grid_state(grid_state),
                }
            )

    return simulate
