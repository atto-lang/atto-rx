"""Unit tests for benchmark admission; no Oreslang compiler required."""
from pathlib import Path
import runpy
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

BENCH = runpy.run_path(str(Path(__file__).resolve().parents[1] / "bench" / "benchmark.py"))
require_common_compiler_pin = BENCH["require_common_compiler_pin"]
require_live_compiler_checkout = BENCH["require_live_compiler_checkout"]
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


class RuntimeCompilerIdentityTest(unittest.TestCase):
    def built(self, root):
        source = Path(root) / ".work" / "oreslang-source.java"
        classes = source / "target" / "classes"
        classes.mkdir(parents=True)
        return source, str(classes)

    def test_missing_compiler_tree_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(SystemExit, "Missing built compiler"):
                require_live_compiler_checkout(PIN_A, "", Path(root))

    def test_stale_classpath_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            self.built(root)
            with self.assertRaisesRegex(SystemExit, "ORES_CLASSPATH omits"):
                require_live_compiler_checkout(PIN_A, "/not/this/compiler", Path(root))

    def test_compiler_commit_must_match_pin(self):
        with tempfile.TemporaryDirectory() as root:
            source, cp = self.built(root)
            with patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=PIN_B)):
                with self.assertRaisesRegex(SystemExit, "does not match compiler.lock"):
                    require_live_compiler_checkout(PIN_A, cp, Path(root))
            with patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=PIN_A)):
                self.assertEqual(require_live_compiler_checkout(PIN_A, cp, Path(root)), str(source))

    def test_compiler_tree_mirror_identity(self):
        with tempfile.TemporaryDirectory() as root:
            source, cp = self.built(root)
            (Path(root) / "compiler-tree.txt").write_text(PIN_A + "\n")
            with patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=PIN_B)):
                with self.assertRaisesRegex(SystemExit, "does not match compiler-tree.txt"):
                    require_live_compiler_checkout(PIN_A, cp, Path(root))
            with patch("subprocess.run", return_value=SimpleNamespace(returncode=0, stdout=PIN_A)) as run:
                self.assertEqual(require_live_compiler_checkout(PIN_B, cp, Path(root)), str(source))
                self.assertEqual(run.call_args.args[0][-1], "HEAD^{tree}")


if __name__ == "__main__":
    unittest.main()
