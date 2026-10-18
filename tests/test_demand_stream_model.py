"""Demand stream abstract interleavings and terminal regressions."""
import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from demand_stream_model import DemandStream, ProtocolError, Terminal


class DemandTests(unittest.TestCase):
    def test_zero_demand_never_produces_item(self):
        s=DemandStream(capacity=2)
        self.assertTrue(s.request(0))
        self.assertFalse(s.emit(42))
        self.assertEqual(s.next(),("PENDING",None))
        s.invariant()

    def test_one_requested_value_then_terminal_fifo(self):
        s=DemandStream(capacity=1)
        s.request(1)
        self.assertTrue(s.emit(42))
        self.assertFalse(s.emit(100))
        self.assertTrue(s.terminate(Terminal.COMPLETED))
        self.assertEqual(s.next(),("ITEM",42))
        self.assertEqual(s.next(),("COMPLETED",None))
        self.assertFalse(s.terminate(Terminal.FAILED))
        s.invariant()

    def test_cancellation_discards_once_and_refuses_late_emit(self):
        s=DemandStream(capacity=2)
        s.request(2)
        self.assertTrue(s.emit(7))
        self.assertTrue(s.emit(8))
        self.assertTrue(s.terminate(Terminal.CANCELLED))
        self.assertFalse(s.terminate(Terminal.CANCELLED))
        self.assertEqual(s.teardowns,1)
        self.assertFalse(s.request(1))
        self.assertFalse(s.emit(9))
        self.assertEqual(s.next(),("CANCELLED",None))
        self.assertEqual(s.cancel_discarded,2)
        s.invariant()

    def test_terminal_interleavings_preserve_credit_and_single_teardown(self):
        events=("request","emit","take","cancel","complete")
        for seq in itertools.permutations(events):
            s=DemandStream(capacity=1)
            for event in seq:
                if event=="request": s.request(1)
                elif event=="emit": s.emit(3)
                elif event=="take": s.next()
                elif event=="cancel": s.terminate(Terminal.CANCELLED)
                elif event=="complete": s.terminate(Terminal.COMPLETED)
                s.invariant()
            self.assertEqual(s.teardowns,1,seq)

    def test_invalid_credit_requests_fail_closed(self):
        s=DemandStream()
        for count in (True,-1,1<<31,0.5):
            with self.subTest(count=count), self.assertRaises(ProtocolError):
                s.request(count)
        s.request((1<<31)-1)
        with self.assertRaisesRegex(ProtocolError,"overflow"):
            s.request(1)
        s.invariant()


if __name__=="__main__":
    unittest.main()
