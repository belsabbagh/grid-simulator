import datetime
from src.types import Trade
import hashlib


def calculate_trade_hash(trade: Trade) -> str:
    return hashlib.sha256(str(trade).encode()).hexdigest()


def make_block(data: dict, hash_fn):
    data["hash"] = hash_fn(data)
    return data


def mk_blockchain_service(genesis_data, hash_fn):
    blockchain = [
        make_block(
            {
                "index": 0,
                "body": genesis_data,
                "hash": "0",
                "timestamp": str(datetime.datetime.now()),
                "nonce": 0,
            },
            hash_fn,
        )
    ]

    def blockchain_iterator():
        yield from blockchain

    def add_block(content, nonce):
        data = {
            "index": len(blockchain),
            "body": content,
            "hash": blockchain[-1]["hash"],
            "timestamp": str(datetime.datetime.now()),
            "nonce": nonce,
        }
        blockchain.append(make_block(data, hash_fn))
        return data

    def valid_chain():
        for i in range(1, len(blockchain)):
            if not all(
                [
                    blockchain[i - 1]["hash"] == blockchain[i]["hash"],
                    blockchain[i - 1]["index"] + 1 == blockchain[i]["index"],
                ]
            ):
                return False

    def latest_block():
        return blockchain[-1]

    return {
        "blockchain_iterator": blockchain_iterator,
        "add_block": add_block,
        "valid_chain": valid_chain,
        "latest_block": latest_block,
    }


def mk_trade_blockchain_service():
    return mk_blockchain_service(
        "Genesis Trade Data",
        calculate_trade_hash,
    )
