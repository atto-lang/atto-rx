"""Unit tests for benchmark admission; no Oreslang compiler required."""
from pathlib import Path
import runpy
import tempfile
import unittest

BENCH = runpy.run_path(str(Path(__file__).resolve().parents[1] / "bench" / "benchmark.py"))
require_common_compiler_pin = BENCH["require_common_compiler_pin"]
PIN_A = "a" * 40
PIN_B = "b" * 40


def sample(root, name, pin):
    program = Path(root) / name / "bench" / "pipeline.ores"
    program.parent.mkdir(parents=True)
    program.write_text("// test fixture\n")
    if pin is not None:
        (program.parent.parent / "compiler.lock").write_text(pin + "\n")
    return name, program


class BenchmarkAdmissionTest(unittest.TestCase):
    def test_identical_exact_pins_admitted(self):
        with tempfile.TemporaryDirectory() as root:
            pairs = [sample(root, name, PIN_A) for name in ("pull", "callbacks", "channels")]
            self.assertEqual(require_common_compiler_pin(pairs), PIN_A)

    def test_mixed_revisions_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            pairs = [sample(root, "pull", PIN_A), sample(root, "channels", PIN_B)]
            with self.assertRaisesRegex(SystemExit, "Refusing cross-compiler benchmark"):
                require_common_compiler_pin(pairs)

    def test_invalid_and_missing_lock_fail_closed(self):
        with tempfile.TemporaryDirectory() as root:
            for bad_pin in ("abc", "A" * 40, None):
                pairs = [sample(root, "pull" + (bad_pin or "missing"), bad_pin)]
                with self.assertRaises(SystemExit):
                    require_common_compiler_pin(pairs)


if __name__ == "__main__":
    unittest.main()
