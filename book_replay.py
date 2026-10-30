"""Independent synthetic book replay; no SDK, networking or strategy logic."""
from __future__ import annotations

import re
import sys

MAXIMUM = 1_000_000_000


def number(token: str, allow_zero: bool = False) -> int:
    if not re.fullmatch(r"[0-9]+", token) or len(token) > 64:
        raise ValueError("invalid integer")
    value = int(token)
    if value > MAXIMUM or value < (0 if allow_zero else 1):
        raise ValueError("integer outside contract")
    return value


class Book:
    def __init__(self) -> None:
        self.bids: dict[int, int] = {}
        self.asks: dict[int, int] = {}
        self.sequence = 0
        self.ready = False

    def status(self, reason: str) -> str:
        bid = max(self.bids) if self.bids else None
        ask = min(self.asks) if self.asks else None
        fields = [reason, str(int(self.ready)), str(self.sequence)]
        fields += [str(bid), str(self.bids[bid])] if bid is not None else ["-", "-"]
        fields += [str(ask), str(self.asks[ask])] if ask is not None else ["-", "-"]
        return "|".join(fields)

    def halt(self, reason: str) -> str:
        self.ready = False
        return self.status(reason)

    def process(self, line: str) -> str | None:
        if any(not (32 <= ord(c) <= 126 or c in '\t\n\r\v\f') for c in line):
            return self.halt("INVALID")
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            return None
        if parts == ["D"]:
            return self.halt("DISCONNECTED")
        try:
            if parts[0] == "S" and len(parts) == 6:
                sequence, bid, bid_qty, ask, ask_qty = map(number, parts[1:])
                if sequence < self.sequence:
                    return self.halt("STALE_SNAPSHOT")
                if bid >= ask:
                    return self.halt("CROSSED")
                self.bids, self.asks = {bid: bid_qty}, {ask: ask_qty}
                self.sequence, self.ready = sequence, True
                return self.status("SNAPSHOT")
            if parts[0] == "U" and len(parts) == 5:
                sequence, price = number(parts[1]), number(parts[3])
                quantity = number(parts[4], allow_zero=True)
                if parts[2] not in ("B", "A"):
                    raise ValueError("unknown side")
                if not self.ready:
                    return self.status("NOT_READY")
                if sequence <= self.sequence:
                    return self.status("STALE")
                if sequence != self.sequence + 1:
                    return self.halt("GAP")
                bids, asks = self.bids.copy(), self.asks.copy()
                side = bids if parts[2] == "B" else asks
                if quantity == 0:
                    if price not in side:
                        return self.halt("UNKNOWN_DELETE")
                    del side[price]
                else:
                    side[price] = quantity
                if bids and asks and max(bids) >= min(asks):
                    return self.halt("CROSSED")
                self.bids, self.asks, self.sequence = bids, asks, sequence
                return self.status("UPDATE")
        except ValueError:
            pass
        return self.halt("INVALID")


if __name__ == "__main__":
    state = Book()
    # Binary LF-delimited records avoid platform universal-newline/Control-Z differences.
    for raw in sys.stdin.buffer:
        try:
            record = raw.decode('ascii')
        except UnicodeDecodeError:
            print(state.halt('INVALID'))
            continue
        result = state.process(record)
        if result is not None:
            print(result)
