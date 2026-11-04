# Benchmark peer snapshot admission

The main-branch `RX library and benchmark` workflow uses read-only private
checkout credentials solely on trusted push-to-main execution. That does not
make moving peer branches suitable for reproducible measurements.

| Peer | Branch | Exact commit | Git tree |
| --- | --- | --- | --- |
| rx-ores-callbacks | `feat/callback-rx-20261006` | `57d617c6ee21efb3aa433aee3b405f1fd03e0c09` | `961ed9305162a8bf830bea4c259bca8890b875a5` |
| rx-oreslang-channels | `refactor/file-scope-rx-20261006` | `9a0e043b2b60a73b752c90b8794e7211eaebdd6d` | `4bb52386b792a770a5ccd46a339225a5390fe4ba` |

These were the branch heads inspected on 2026-10-30, not claims of compiler
compatibility or benchmark success. CI checks both HEAD and tree identity,
and refuses a silently moved branch, dirty peer checkout, or missing private
read access. To update, review new peer commit/tree pairs in a new PR.

The peer sources are imported into the *same* `rx-ores` compiler runtime
for the benchmark, and all three guest suites must execute at that exact
runtime pin before cross-model performance figures are meaningful.
Host-side workflow checks and zero-step GitHub Actions do not satisfy this
execution requirement. Never use cross-organization private-source transfer
without explicit authorization and independent approval.
