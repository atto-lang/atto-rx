#!/usr/bin/env python3
"""Round-robin wall-clock benchmark for the three rx-ores execution models.

Each implementation must execute the same 20,000-pipeline workload and sum
the same downstream emitted values. A run fails closed if compiler pins differ.
Timed samples include one Ores JVM launch; these are prototype measurements,
not cross-hardware, scheduler, latency or allocation benchmarks.
"""
from __future__ import annotations

import argparse
import math
import os
import re
from pathlib import Path
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PARENT = ROOT.parent
# Every variant sums the three emitted values (6, 8, 10) per iteration.
EXPECTED = "480000"
PIPELINES_PER_SAMPLE = 20_000

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    p.add_argument("--warmups", type=int, default=3)
    p.add_argument("--runs", type=int, default=10)
    p.add_argument("--callbacks-root", type=Path,
                   default=Path(os.environ.get("RX_CALLBACKS_ROOT",
                                                DEFAULT_PARENT / "rx-ores-callbacks")))
    p.add_argument("--channels-root", type=Path,
                   default=Path(os.environ.get("RX_CHANNELS_ROOT",
                                                DEFAULT_PARENT / "rx-oreslang-channels")))
    return p

def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return ordered[low]
    weight = pos - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight

def require_common_compiler_pin(implementations: list[tuple[str, Path]]) -> str:
    """Prevent accidentally comparing different compiler/runtime revisions."""
    pins = {}
    for name, program in implementations:
        pin_file = program.parent.parent / "compiler.lock"
        if not pin_file.is_file():
            raise SystemExit(f"{name}: missing compiler.lock: {pin_file}")
        pin = pin_file.read_text().strip()
        if not re.fullmatch(r"[0-9a-f]{40}", pin):
            raise SystemExit(f"{name}: invalid compiler.lock (expected full lowercase SHA)")
        pins[name] = pin
    if len(set(pins.values())) != 1:
        details = ", ".join(f"{name}={sha}" for name, sha in pins.items())
        raise SystemExit(f"Refusing cross-compiler benchmark; align pins first: {details}")
    return next(iter(pins.values()))


def require_live_compiler_checkout(expected_pin: str, classpath: str,
                                   root: Path = ROOT) -> str:
    """Check the actual executable compiler input, not just three lockfiles."""
    source = root / ".work" / "oreslang-source.java"
    classes = source / "target" / "classes"
    if not source.is_dir() or not classes.is_dir():
        raise SystemExit("Missing built compiler tree; run scripts/setup.py first")
    entries = [Path(entry).resolve() for entry in classpath.split(os.pathsep)
               if entry]
    if classes.resolve() not in entries:
        raise SystemExit("ORES_CLASSPATH omits the compiler's target/classes")

    def git_rev(revision: str) -> str:
        result = subprocess.run(["git", "-C", str(source), "rev-parse", revision],
                                capture_output=True, text=True, timeout=20)
        if result.returncode:
            raise SystemExit("Compiler checkout Git identity unavailable")
        value = result.stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{40}", value):
            raise SystemExit("Compiler checkout revision is not an exact SHA")
        return value

    expected_tree_file = root / "compiler-tree.txt"
    if expected_tree_file.is_file():
        expected_tree = expected_tree_file.read_text().strip()
        if not re.fullmatch(r"[0-9a-f]{40}", expected_tree):
            raise SystemExit("Invalid compiler-tree.txt Git tree SHA")
        actual_tree = git_rev("HEAD^{tree}")
        if actual_tree != expected_tree:
            raise SystemExit("Compiler checkout tree does not match compiler-tree.txt")
    else:
        if git_rev("HEAD") != expected_pin:
            raise SystemExit("Compiler checkout commit does not match compiler.lock")
    return str(source)


def main() -> int:
    args = parser().parse_args()
    if args.warmups < 0 or args.runs < 1:
        raise SystemExit("--warmups must be >= 0 and --runs must be >= 1")

    classpath = os.environ.get("ORES_CLASSPATH")
    if not classpath:
        raise SystemExit("Set ORES_CLASSPATH (run scripts/setup.py first).")
    java = os.environ.get("JAVA", "java")
    command = [
        java,
        "--enable-native-access=ALL-UNNAMED",
        "-Dpolyglot.engine.WarnInterpreterOnly=false",
        "-cp",
        classpath,
        "dev.oreslang.launcher.OresMain",
    ]

    implementations = [
        ("pull", ROOT / "bench" / "pipeline.ores"),
        ("callbacks", args.callbacks_root.resolve() / "bench" / "pipeline.ores"),
        ("channels", args.channels_root.resolve() / "bench" / "pipeline.ores"),
    ]
    compiler_pin = require_common_compiler_pin(implementations)
    require_live_compiler_checkout(compiler_pin, classpath)
    for name, program in implementations:
        if not program.is_file():
            raise SystemExit(f"{name}: missing benchmark program: {program}")
        checked = subprocess.run(
            command + ["--check", str(program)],
            text=True,
            capture_output=True,
            timeout=60,
        )
        if checked.returncode or ": error:" in checked.stderr:
            sys.stderr.write(checked.stdout + checked.stderr)
            raise SystemExit(f"{name}: benchmark failed static validation")

    def run_one(name: str, program: Path, timed: bool) -> float:
        start = time.perf_counter()
        result = subprocess.run(
            command + [str(program)],
            text=True,
            capture_output=True,
            timeout=180,
        )
        elapsed = time.perf_counter() - start
        if result.returncode or ": error:" in result.stderr:
            sys.stderr.write(result.stdout + result.stderr)
            raise SystemExit(f"{name}: benchmark execution failed")
        actual = result.stdout.strip()
        if actual != EXPECTED:
            raise SystemExit(f"{name}: expected its checksum {EXPECTED}, got {actual!r}")
        return elapsed if timed else 0.0

    # Rotate the first implementation each round to reduce order/thermal bias.
    for round_index in range(args.warmups):
        for offset in range(len(implementations)):
            name, program = implementations[(round_index + offset) % len(implementations)]
            run_one(name, program, False)

    samples: dict[str, list[float]] = {name: [] for name, _ in implementations}
    for round_index in range(args.runs):
        for offset in range(len(implementations)):
            name, program = implementations[(round_index + offset) % len(implementations)]
            samples[name].append(run_one(name, program, True))

    print(f"workload: {PIPELINES_PER_SAMPLE} pipelines/sample; emitted-value checksum={EXPECTED}")
    print(f"common compiler pin: {compiler_pin}")
    print("| implementation | median ms | p95 ms | min ms | pipelines/s |")
    print("| --- | ---: | ---: | ---: | ---: |")
    medians: dict[str, float] = {}
    for name, _ in implementations:
        values = samples[name]
        median = statistics.median(values)
        medians[name] = median
        p95 = percentile(values, 0.95)
        minimum = min(values)
        throughput = PIPELINES_PER_SAMPLE / median
        print(f"| {name} | {median * 1000:.2f} | {p95 * 1000:.2f} | "
              f"{minimum * 1000:.2f} | {throughput:,.0f} |")

    fastest_name = min(medians, key=medians.get)
    fastest = medians[fastest_name]
    print()
    print(f"fastest median: {fastest_name}")
    for name, _ in implementations:
        print(f"{name}: {medians[name] / fastest:.2f}x fastest median")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
