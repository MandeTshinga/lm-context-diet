# CLAUDE.md

Guidance for working on **Aurora**, an order management service (Django 5, PostgreSQL 16, Celery, S3).

## Absolute rules

- **Never run migrations against production directly.** Always go through `make deploy-migrate`, which takes a snapshot first.
- **Never commit to `main`.** Branch, open a PR, wait for CI.
- Secrets live in `.env`, which is gitignored. **Do not** put a real key in `settings.py`, not even as a default.

## Architecture

A monolith with three Celery queues. `orders` owns the state machine, `billing` talks to the payment provider, `notify` sends mail and webhooks.

Orders move through `draft → placed → paid → fulfilled → closed`, with `cancelled` reachable from any state before `fulfilled`.

**Always call `order.transition(to=...)` rather than assigning `order.status` directly.** Direct assignment skips validation and the audit entry.

> **📖 State machine rationale, the `django-fsm` decision, the 340,000-row backfill, why a no-op transition must not raise:** [`docs/orders.md`](docs/orders.md)

### Billing

**Always pass an idempotency key on any call that moves money.** The helper `billing.keys.for_order(order, action)` builds one correctly.

Webhooks arrive on `/hooks/billing/`. Signature verification uses the raw request body, so **never** read `request.POST` before verifying, because Django's form parsing consumes the stream and the signature will not match.

> **📖 Retry and backoff policy, the v3 idempotency incident, why every payload is persisted before processing:** [`docs/billing.md`](docs/billing.md)

### Notifications

**Always set `allow_redirects=False` on outbound customer webhooks.**

Retries are 5 attempts over 24 hours with jitter. After that the event lands in `notify_deadletter` and an operator has to replay it manually with `make notify-replay ID=...`.

> **📖 Template layout, `make mail-preview`, the redirect-loop incident:** [`docs/notify.md`](docs/notify.md)

## Deployment

**Note that a rollback does not roll back migrations**, so any migration must be backwards compatible with the previous release. In practice this means: add columns as nullable, deploy, backfill, then make them non-null in a later release.

**Always check `make deploy-status` after a deploy** rather than assuming the pipeline's green check means the service is healthy. The pipeline goes green when ECS accepts the update, not when the new tasks pass their health checks.

Migrations run as a dedicated one-off task before the service update, never at container start.

> **📖 Pipeline stages, the two-task migration race, the abandoned blue-green attempt, the S3 lifecycle incident:** [`docs/deployment.md`](docs/deployment.md)

## Testing

`make test` runs the fast suite, `make test-all` includes the slow integration tests that hit a real Postgres.

Fixtures are factory_boy factories in `tests/factories.py`. **Do not** create model instances directly in tests, because several models have required fields that get added over time and direct instantiation breaks silently when they do.

**Always run `make test-all` before opening a PR that touches billing or migrations.** The fast suite mocks the payment provider entirely.

Coverage is measured but not enforced, deliberately.

> **📖 The flaky-suite investigation, why the 90 % coverage gate was removed:** [`docs/testing.md`](docs/testing.md)

---

**📜 Dated history of changes:** [`docs/CHANGELOG.md`](docs/CHANGELOG.md)
