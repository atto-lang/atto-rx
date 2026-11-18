# rx-ores

## AttoLang migration and authoritative specification (2026-11-18)

**AttoLang** is the current public name of Oreslang. This `ores-truffle-oreslang/rx-ores` repository retains its historical context. **Current AttoLang destination:** [atto-lang/atto-rx](https://github.com/atto-lang/atto-rx). Legacy source and commands below reflect this checkout; do not automatically substitute new CLI names or claim feature parity. These repositories are not assumed to have identical Git histories, issues, pull requests, or implementation results.

**The canonical language specification is [atto-lang/atto-spec](https://github.com/atto-lang/atto-spec)**. Portable `.atto` modules belong in [atto-common-source](https://github.com/atto-lang/atto-common-source) and executed cross-backend positive/negative fixtures in [atto-platform-conformance](https://github.com/atto-lang/atto-platform-conformance). The proposed modern rules include `snake_case` methods, ownership `borrow!`/`take!`/`share!`/`copy!`/`copy!!`, [implicit borrowing](https://github.com/atto-lang/atto-spec/blob/main/language/implicit-argument-borrow-v1.md), [file/module constants including nonthrowing launch-time environment reads](https://github.com/atto-lang/atto-spec/blob/main/language/file-module-const-v1.md), and [separate bitwise-shift and directional-stream operators](https://github.com/atto-lang/atto-spec/blob/main/language/bitwise-and-stream-operators-v1.md). These are contract/design directions, not a claim this legacy implementation supports all syntax.

Preserve historic `.ores` paths, command names, ABI/wire names and pinned fixtures until verified replacements exist. Avoid Python support tooling/tests; prefer Rust. Do not infer successful compilation, actor isolation or cross-backend parity from README examples, host-only tests, or zero-step GitHub Actions. Document exact commit/tree, target, toolchain, executed guest tests and explicit failures/unsupported status.

Standalone pull/Future-oriented reactive streams for Oreslang.

This repository is the home of rx-ores. The compiler/runtime owns generic
language primitives such as `Future<T>`, `await`, callables, ownership and
scheduling; it does **not** own the reactive library.

## Source model

`src/rx.ores` is a file/code unit, not an implicit module or package. Its nominal classes are ordinary top-level file-scoped declarations and consumers select them explicitly with `import class`; the file is not wrapped in a synthetic module:

```ores
import * as rx from './src/rx.ores';
import class Observable, Subscription from './src/rx.ores';
```

The initial implementation is demand-driven. `subscribe()` creates independent
subscription state and each `next()` admits at most one item. There is no
prefetch queue. `take(0)` consumes nothing and cancellation is idempotent.

RX APIs use Oreslang's pointerless ownership model. Callback signatures use
ordinary managed value/reference types such as `Fnc<T, bool>`; they never encode
ownership with `&T`, `T*`, unary `&`, or unary `*`. When this library needs
to make a temporary read borrow explicit, it uses `rt borrow value`. Explicit
ownership transitions belong to the reserved runtime surface (`rt copy`,
`rt share`, `rt borrow`, `rt take`, and related runtime reference
operations), not C/Rust-style pointer operators.

Finite pull state is stored directly in subscription objects. `from_future()`
uses Oreslang's native Future/await suspension path; it does not invent a second
callback scheduler. Native Future values may be prepared first with `map`,
`compose` / `flatMap`, and `onSuccess`; guest callbacks resume as Ores
scheduler/actor turns rather than producer-thread callbacks. Higher-order
operators currently include `map`, `filter` and `take`.

This repository intentionally stays separate from:
- **rx-ores-callbacks** — synchronous push/callback composition.
- **rx-oreslang-channels** — pull semantics whose coordination state and hot
  sources use Channel/select.

The separation is deliberate so identical workloads can measure the costs and
strengths of each execution model before any hybrid/high-performance library is
designed.

## Validation

```sh
python3 scripts/setup.py
source .work/env.sh
python3 scripts/test.py
```

The benchmark driver lives in `bench/benchmark.py`; `bench/pipeline.ores`
is this implementation's common map/filter/take workload.

## Compiler compatibility checkpoint (2026-10-06)

This repository tracks the latest 10 compiler PRs as **unmerged proposals**, without changing its stable compiler pin or API behavior. See [docs/compiler-pr-sync.md](docs/compiler-pr-sync.md) for rx-ores-specific migration invariants, dependencies and validation gates.
