# Changelog

Dated history, extracted from `CLAUDE.md`. Not loaded automatically. Consulted when you need to know when and why something changed.

- **2026-06-14** — Moved mail templates out of task functions into files. Added `make mail-preview`.
- **2026-05-02** — Webhook redirect loop fixed. `allow_redirects=False` everywhere outbound.
- **2026-04-19** — S3 lifecycle rule excluded the static prefix after it deleted a pinned release.
- **2026-03-28** — Replaced boolean status flags with an explicit state machine. Backfilled 340,000 rows in batches.
- **2026-03-05** — Migrations moved out of container start into a dedicated one-off task.
- **2026-02-11** — Billing idempotency keys prefixed with the endpoint name after the v3 API change.
- **2026-01-22** — Webhook payloads persisted before processing, including rejected ones.
