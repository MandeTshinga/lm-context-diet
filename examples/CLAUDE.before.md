# CLAUDE.md

Guidance for working on **Aurora**, an order management service (Django 5, PostgreSQL 16, Celery, S3).

## Absolute rules

- **Never run migrations against production directly.** Always go through `make deploy-migrate`, which takes a snapshot first.
- **Never commit to `main`.** Branch, open a PR, wait for CI.
- Secrets live in `.env`, which is gitignored. **Do not** put a real key in `settings.py`, not even as a default.

## Architecture

Aurora is a monolith with three Celery queues. The `orders` app owns the state machine, `billing` talks to the payment provider, `notify` sends mail and webhooks.

### The order state machine

Orders move through `draft → placed → paid → fulfilled → closed`, with `cancelled` reachable from any state before `fulfilled`.

The state machine was originally a set of boolean flags on the `Order` model (`is_paid`, `is_shipped`, `is_cancelled`). That worked until we hit an order that was both cancelled and shipped, which nobody could explain. We spent two days reconstructing the history from the audit log before finding a race between the webhook handler and the admin action.

In March we replaced the flags with an explicit `status` column plus a `transition()` method that validates the move. The migration backfilled 340,000 rows in batches of 5,000 because a single `UPDATE` locked the table for eleven minutes on staging.

We considered `django-fsm` and rejected it, because it wanted to own the model save path and we already had a custom `save()` doing audit logging. We also looked at storing transitions in a separate table, which is cleaner, but it would have needed a join on every list view and the order list is the hottest page in the product.

**Always call `order.transition(to=...)` rather than assigning `order.status` directly.** Direct assignment skips validation and the audit entry.

The `transition()` method raises `InvalidTransition`, which the API layer maps to a 409. It does not raise on a no-op transition to the same state, which was a deliberate choice so that webhook retries are idempotent.

### Billing

`billing` wraps the payment provider SDK. Every call goes through `billing.client.call()`, which adds a request ID and retries on 5xx with exponential backoff.

The provider changed their idempotency semantics in their v3 API. In v2, an idempotency key was scoped to the endpoint. In v3 it is scoped to the account, which means reusing a key across two different endpoints now returns the first response rather than an error. We found this out in production when a refund returned a charge object. The fix was to prefix every key with the endpoint name.

**Always pass an idempotency key on any call that moves money.** The helper `billing.keys.for_order(order, action)` builds one correctly.

Webhooks arrive on `/hooks/billing/`. Signature verification uses the raw request body, so **never** read `request.POST` before verifying, because Django's form parsing consumes the stream and the signature will not match. This cost us an afternoon.

We store every webhook payload in `billing_webhookevent` before processing it, including ones we reject. Disk is cheap and this table has resolved four disputes with the provider.

### Notifications

`notify` sends transactional mail through the provider's API and fires customer webhooks.

Templates live in `notify/templates/mail/`. They were originally inline strings in the task functions, which made them impossible to preview. We moved them to files in June, and added `make mail-preview` which renders every template with fixture data into `/tmp/mail-preview/`.

The webhook sender had a bug where a customer endpoint returning a 301 caused an infinite redirect loop, because `requests` follows redirects by default and the customer's load balancer was redirecting to itself. **Always set `allow_redirects=False` on outbound customer webhooks.**

Retries are 5 attempts over 24 hours with jitter. After that the event lands in `notify_deadletter` and an operator has to replay it manually with `make notify-replay ID=...`.

## Deployment

Deploys go through GitHub Actions to ECS. The pipeline builds an image, runs tests, pushes to ECR, then updates the service.

The original pipeline ran migrations as part of the container start command. This broke the first time we scaled to two tasks, because both containers ran the migration simultaneously and one of them failed on a duplicate index. We moved migrations to a separate one-off task that runs before the service update.

Rollbacks are `make rollback`, which points the service at the previous task definition. **Note that a rollback does not roll back migrations**, so any migration must be backwards compatible with the previous release. In practice this means: add columns as nullable, deploy, backfill, then make them non-null in a later release.

We tried blue-green deployment and abandoned it, because the Celery workers hold long-running tasks and draining them took longer than the deployment window allowed.

Static files go to S3 through `collectstatic` in the build step, not at runtime. The bucket has a lifecycle rule that deletes objects older than 90 days, which once deleted the static files of a release we had pinned for a customer. The rule now excludes the `static/` prefix.

**Always check `make deploy-status` after a deploy** rather than assuming the pipeline's green check means the service is healthy. The pipeline goes green when ECS accepts the update, not when the new tasks pass their health checks.

## Testing

Tests run with pytest. `make test` runs the fast suite, `make test-all` includes the slow integration tests that hit a real Postgres.

Fixtures are factory_boy factories in `tests/factories.py`. **Do not** create model instances directly in tests, because several models have required fields that get added over time and direct instantiation breaks silently when they do.

We had a long period where the test suite was flaky, roughly one failure in twenty runs, always in the billing tests. The cause was a shared module-level `Client` instance carrying state between tests. Every test now gets a fresh client through the `billing_client` fixture.

Coverage is measured but not enforced, deliberately. We tried a 90 % gate and it produced tests that asserted nothing in order to touch lines.

**Always run `make test-all` before opening a PR that touches billing or migrations.** The fast suite mocks the payment provider entirely.

## Changelog

- **2026-06-14** — Moved mail templates out of task functions into files. Added `make mail-preview`.
- **2026-05-02** — Webhook redirect loop fixed. `allow_redirects=False` everywhere outbound.
- **2026-04-19** — S3 lifecycle rule excluded the static prefix after it deleted a pinned release.
- **2026-03-28** — Replaced boolean status flags with an explicit state machine. Backfilled 340,000 rows in batches.
- **2026-03-05** — Migrations moved out of container start into a dedicated one-off task.
- **2026-02-11** — Billing idempotency keys prefixed with the endpoint name after the v3 API change.
- **2026-01-22** — Webhook payloads persisted before processing, including rejected ones.
