# atto-rx

Reactive programming utilities and stream composition for AttoLang.

## Naming migration and language authority

This repository is maintained at [atto-lang/atto-rx](https://github.com/atto-lang/atto-rx); use `https://github.com/atto-lang/atto-rx.git` for Git remotes and canonical `.atto` source examples. The normative language contract is [atto-spec](https://github.com/atto-lang/atto-spec), with executable guest evidence tracked by [atto-platform-conformance](https://github.com/atto-lang/atto-platform-conformance). Follow current ownership, borrowing, effects, actor, and syntax rules there; do not infer implemented features from a README or unexecuted CI.

## Responsibilities

Reactive composition, stream contracts, and interactions with actors, tasks, and channels.

## Design guidelines

- Keep application-facing contracts separate from hosted Atto services.
- Explicitly specify error, cancellation, concurrency, and resource-lifecycle behavior where applicable.
- Document supported compiler backends, host restrictions, wire formats, and compatibility constraints.

## Development and verification

Use the source tree and CI for verified build/test commands. Tests should cover positive cases, invalid inputs, lifecycle behavior, and cross-backend interoperability where relevant.

## Status

This README describes the project's intended role. It does not imply that the listed APIs or platforms are already implemented or supported.

## Related

- [AttoLang](https://github.com/atto-lang)
- [Language specification](https://github.com/atto-lang/atto-spec)
- [Platform conformance](https://github.com/atto-lang/atto-platform-conformance)

## Repository ownership and contribution routing

**Belongs here:** General reactive stream composition, flow control, subscriptions and stream-to-actor/task integration.

**Belongs elsewhere:** Per-channel observable adapters in atto-rx-channels; task combinators in atto-rx-tasks; callback bridges in atto-rx-callbacks.

**Security and portability boundary:** Explicitly bound buffering/backpressure, close and cancel races, and do not transfer closures through actor channels.

AttoLang is the canonical project name; new source, examples and documentation use `.atto` and the `atto-lang` repository organization. This README defines scope, not feature readiness.

**Acceptance:** name exact source SHA/tree, runtime/toolchain, positive and negative checks and execution receipt before claiming support. Host-only tests and empty CI steps do not prove guest execution.
