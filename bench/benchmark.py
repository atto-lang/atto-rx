#!/usr/bin/env python3
"""Benchmark the three rx-ores execution models with one repeated pipeline spec."""
from __future__ import annotations
import argparse
from pathlib import Path
import os
import statistics
import subprocess
import time

ITERATIONS = 20_000
RAW_ITEMS_PER_PIPELINE = 5  # take(3) after map/filter stops after source item 5
EXPECTED = {
    "pull": str(ITERATIONS * 3),
    "callbacks": str(ITERATIONS * 5),
    "channels": str(ITERATIONS * 3),
}

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pull", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--callbacks", type=Path, required=True)
    parser.add_argument("--channels", type=Path, required=True)
    parser.add_argument("--preflight", type=int, default=2)
    parser.add_argument("--samples", type=int, default=9)
    args = parser.parse_args()

    cp = os.environ["ORES_CLASSPATH"]
    command = [
        os.environ.get("JAVA", "java"),
        "--enable-native-access=ALL-UNNAMED",
        "-Dpolyglot.engine.WarnInterpreterOnly=false",
        "-cp", cp,
        "dev.oreslang.launcher.OresMain",
    ]
    roots = {
        "pull": args.pull,
        "callbacks": args.callbacks,
        "channels": args.channels,
    }

    for name, root in roots.items():
        program = root / "bench" / "pipeline.ores"
        for _ in range(args.preflight):
            run_once(command, program, EXPECTED[name])
        samples = [run_once(command, program, EXPECTED[name]) for _ in range(args.samples)]
        median = statistics.median(samples)
        ordered = sorted(samples)
        p95 = ordered[min(len(ordered) - 1, int((len(ordered) - 1) * 0.95))]
        pipelines_per_second = ITERATIONS / median
        ns_per_source_item = median * 1e9 / (ITERATIONS * RAW_ITEMS_PER_PIPELINE)
        print(
            f"{name:10} median={median*1000:9.3f} ms "
            f"p95={p95*1000:9.3f} ms "
            f"pipelines/s={pipelines_per_second:12.1f} "
            f"ns/source-item={ns_per_source_item:10.1f}"
        )

def run_once(command: list[str], program: Path, expected: str) -> float:
    started = time.perf_counter()
    result = subprocess.run(command + [str(program)], text=True, capture_output=True, check=False)
    elapsed = time.perf_counter() - started
    if result.returncode:
        raise SystemExit(result.stdout + result.stderr)
    actual = result.stdout.strip()
    if actual != expected:
        raise SystemExit(f"{program}: expected checksum {expected!r}, got {actual!r}")
    return elapsed

if __name__ == "__main__":
    main()
