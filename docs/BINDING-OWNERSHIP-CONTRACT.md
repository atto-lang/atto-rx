# RX pull-stream binding and ownership contract

**Acceptance contract, not a statement of support in the current compiler pin.** This document may land independently of the compiler implementation. Every case below requires compiler-backed evidence before a pin or API is promoted.

Compiler convergence: [oreslang-source.java #411](https://github.com/ores-truffle-oreslang/oreslang-source.java/pull/411).

| Declaration | Can rebind? | Can mutate referent through this path? |
| --- | --- | --- |
| `const x` | no | no |
| `val x` / `const mut x` | no | yes, if exclusive ownership permits |
| `let x` | yes | no |
| `let mut x` | yes | yes, if exclusive ownership permits |

For stream internals, scalar counters such as `let int cursor` remain reassignable; a stable mutable subscription object can use `val`. Keep mutating `self` receiver effects explicit and ensure `const` access paths cannot mutate a subscription indirectly via `next()`, `cancel()`, or collection methods. Shared/frozen inputs require a read-only view.

Local channels can eventually transport safe callable references/owned values inside a single execution domain. Actor mailboxes remain serialized and prohibit raw pointers, closures, borrowed views, or shared mutable alias graphs. Do not use reactive adapters to bypass actor isolation.

For Future-returning select APIs supported by the pinned compiler, retain or await completion and cancel losing registrations. Static `do nb select` must not be assumed to return `Future<void>`: its completion/cancellation contract requires separate runtime evidence. Bound detached registrations and prove that blocking select releases the native carrier using one carrier and multiple contenders.

Tests to add once compiler #411 lands: val-mutable and const-readonly subscription, mutable-self effects, nested readonly collection accesses, future lifetimes, mailbox capability rejection, cancellation of losing select registrations.
