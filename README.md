# rx-ores

Standalone pull/Future-oriented reactive library for Oreslang.

This repository is the home of rx-ores. Reactive operators are intentionally no
longer part of `oreslang-source.java`; the compiler/runtime should provide generic
language primitives such as `Future`/ `await`, not own the RX package.

## Source model

Ores files are Unix-style code units, not implicit modules or packages. The
library entry file is `src/rx.ores`; callers choose a local namespace:

```ores
import * as rx from './src/rx.ores';
import class Observable, Subscription from './src/rx.ores';
```

An explicit `define module X as ... end` is only used when a file deliberately
contains a module namespace.

## Execution model

This variant is pull-oriented. `subscribe()` creates a subscription and
`next()` requests one `Option<T>`. `from_future` suspends through the ordinary
Ores Future/await runtime. There is no `Channel<T>` in subscription cursor or
cancellation state: a single command closure owns each subscription's mutable
state while class receivers remain immutable.

Initial operators: `from_values`, `from_future`, `map`, `filter`, `take`,
and `first`.

A Future can be transformed before it enters the pull stream without changing
the subscription model:

```ores
val Future<int> prepared = fetch()
    .map(transform)
    .compose(next_async)
    .onSuccess(observer);
val Observable<int> source = rx.from_future(prepared);
```

`map`, `compose` / `flatMap`, and `onSuccess` are native Ores Future
combinators. Their guest callbacks run as Ores scheduler/actor turns rather than
on producer completion threads.

The first standalone surface intentionally keeps cancellation's boolean return
as an acknowledgement while the internal command is idempotent; refining that
return to distinguish first-transition/already-terminal should not add a second
mutable owner or hot-path allocation.

## Validation

`compiler.lock` pins the exact compiler contract. Run:

```sh
python3 scripts/setup.py
source .work/env.sh
python3 scripts/test.py
```

The cross-variant performance protocol lives in `bench/README.md`.
