"""Deterministic interleavings for the bounded demand/terminal model.

Not Oreslang ReadableStream/WritableStream runtime execution or performance proof.
"""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from demand_stream_model import DemandStream, ProtocolError, Terminal


class StreamInterleavingTests(unittest.TestCase):
    def test_repeated_seeded_demand_cancel_error_complete_races(self):
        rng = random.Random(173)
        for trial in range(2048):
            model = DemandStream(capacity=rng.randint(1, 5))
            for tick in range(40):
                operation = rng.randrange(6)
                if operation == 0:
                    model.request(rng.randint(0, 8))
                elif operation == 1:
                    model.emit(tick)
                elif operation == 2:
                    model.next()
                elif operation == 3:
                    model.terminate(Terminal.CANCELLED)
                elif operation == 4:
                    model.terminate(Terminal.COMPLETED)
                else:
                    model.terminate(Terminal.FAILED)
                with self.subTest(trial=trial):
                    model.invariant()
                    self.assertLessEqual(len(model.queue), model.capacity)
                    if model.terminal is not None:
                        self.assertEqual(model.teardowns, 1)
                        self.assertFalse(model.emit(tick))
                        self.assertFalse(model.request(1))

    def test_backpressure_does_not_overwrite_queued_item(self):
        model = DemandStream(capacity=1)
        self.assertTrue(model.request(2))
        self.assertTrue(model.emit("first"))
        self.assertFalse(model.emit("second"))
        self.assertEqual(model.next(), ("ITEM", "first"))
        self.assertTrue(model.emit("second"))
        self.assertEqual(model.next(), ("ITEM", "second"))
        self.assertEqual(model.next(), ("PENDING", None))
        self.assertTrue(model.invariant())

    def test_invalid_terminal_and_capacity_are_rejected(self):
        for capacity in (0, -1, True, 1025):
            with self.subTest(capacity=capacity), self.assertRaises(ProtocolError):
                DemandStream(capacity=capacity)
        with self.assertRaises(ProtocolError):
            DemandStream().terminate("CANCELLED")


if __name__ == "__main__":
    unittest.main()
