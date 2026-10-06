# RX benchmark protocol

The benchmark compares three intentionally distinct implementations:

- `rx-ores`: pull/Future-oriented subscription state, no channels in the data path.
- `rx-ores-callbacks`: synchronous callback push with cooperative early stop.
- `rx-oreslang-channels`: pull subscriptions whose state/coordination uses Ores channels.

Each `bench/pipeline.ores` runs 20,000 copies of the same logical pipeline:

`[1..8] -> map(*2) -> filter(>4) -> take(3) -> drain`.

The third accepted element comes from source item 5, so every implementation
does equivalent useful source work. The external harness reports pipelines/sec
and estimated ns/source-item. Work is repeated inside one guest execution to
amortize JVM startup. Run multiple samples after warmup; do not compare one-off
startup time.

Example from a directory containing sibling clones:

```sh
source rx-ores/.work/env.sh
python3 rx-ores/bench/benchmark.py \
  --callbacks ./rx-ores-callbacks \
  --channels ./rx-oreslang-channels
```

Do not publish performance numbers unless the checksum matches for every sample.
