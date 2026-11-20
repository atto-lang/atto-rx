"""Minimal demand/terminal/cancellation oracle for a fourth stream-native Rx.

This is a protocol reference, not executable Oreslang or a chosen Rx design.
Every event is a linearized abstract transition; races require interleaving tests.
"""
from collections import deque
from enum import Enum


class ProtocolError(ValueError):
    pass


class Terminal(Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class DemandStream:
    def __init__(self, *, capacity=1):
        if type(capacity) is not int or not 1 <= capacity <= 1024:
            raise ProtocolError("invalid bounded stream capacity")
        self.capacity = capacity
        self.demand = 0
        self.queue = deque()
        self.terminal = None
        self.teardowns = 0
        self.accepted = 0
        self.delivered = 0
        self.cancel_discarded = 0

    def request(self, n):
        if type(n) is not int or not 0 <= n <= (1 << 31) - 1:
            raise ProtocolError("request count outside bounded demand")
        if self.terminal is not None:
            return False
        if self.demand > (1 << 31) - 1 - n:
            raise ProtocolError("demand overflow")
        self.demand += n
        return True

    def emit(self, value):
        if self.terminal is not None:
            return False
        if self.demand == 0 or len(self.queue) >= self.capacity:
            return False
        self.demand -= 1
        self.queue.append(value)
        self.accepted += 1
        return True

    def next(self):
        if self.terminal is Terminal.CANCELLED:
            return "CANCELLED", None
        if self.queue:
            self.delivered += 1
            return "ITEM", self.queue.popleft()
        if self.terminal is Terminal.COMPLETED:
            return "COMPLETED", None
        if self.terminal is Terminal.FAILED:
            return "ERROR", None
        return "PENDING", None

    def terminate(self, terminal):
        if type(terminal) is not Terminal:
            raise ProtocolError("invalid stream terminal")
        if self.terminal is not None:
            return False
        self.terminal = terminal
        self.teardowns += 1
        self.demand = 0
        if terminal is Terminal.CANCELLED:
            self.cancel_discarded += len(self.queue)
            self.queue.clear()
        return True

    def invariant(self):
        if not (0 <= len(self.queue) <= self.capacity and self.demand >= 0):
            raise AssertionError("violated bounded credit invariant")
        if self.accepted != self.delivered + self.cancel_discarded + len(self.queue):
            raise AssertionError("item lost or delivered more than once")
        if self.teardowns not in (0, 1) or (self.terminal is None) != (self.teardowns == 0):
            raise AssertionError("terminal/teardown not exactly once")
