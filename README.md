# rx-ores

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

## Repository ownership and migration (2026-11-08)

This repo is currently `ores-truffle-oreslang/rx-ores`. The public language name is **AttoLang**; preserve `.ores` compatibility and old repo/package/CLI IDs until a separate compiler-backed and consumer-reviewed change proves replacement.

- **Belongs here:** portable reactive API semantics and bounded operator contracts.
- **Does not belong here:** compiler scheduler internals or managed event streaming SaaS.
- **Organization model:** [atto-lang](https://github.com/atto-lang) owns portable language libraries, compilers, tools, tests, core/std and examples. [atto-co](https://github.com/atto-co) separately owns managed hosting, tenant/deployment control, identity, billing and SaaS. Existing similarly named `atto-*` repos should be audited for overlap but are not necessarily transfers of this source identity.
- **Initial proposed move:** this original numeric GitHub repository ID and history into `atto-lang/rx-ores` retaining the old name. Current migration wave authorizes zero direct moves into `atto-co`. Future product carve-outs require new owner/security approval.

**Safe transfer:** announce in [issue #26](https://github.com/ores-truffle-oreslang/.github/issues/26), follow [private migration draft #25](https://github.com/ores-truffle-oreslang/.github/pull/25). Record exact source SHA/tree, ID, release tags, PRs, packages, dependencies, branch/ruleset protections, target visibility and rights, Actions/runners, App/webhook permissions, secrets, Pages, rollback authority, source/target admins and independent security review. Never mirror private source without explicit authorization. After an approved GitHub ownership transfer verify unchanged ID/tree/history, restore security policy, change consumers separately and run exact-head tests with **nonzero executed steps**. `steps=[]`/`null` is `NOT_EXECUTED`; host or structural tests cannot certify AttoLang guest execution, database safety or actor parity.
