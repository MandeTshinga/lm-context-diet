# Testing

> The two rules that apply **before** you write or open a PR live in
> [`../CLAUDE.after.md`](../CLAUDE.after.md): never instantiate models directly in tests,
> and always run `make test-all` when touching billing or migrations.
> This file holds the reasoning.

## The flaky period

The suite was flaky for a long stretch, roughly one failure in twenty runs, always in the billing tests.

The cause was a shared module-level `Client` instance carrying state between tests. Every test now gets a fresh client through the `billing_client` fixture.

## Why coverage is not enforced

Coverage is measured but not gated, deliberately. We tried a 90 % gate and it produced tests that asserted nothing in order to touch lines.
