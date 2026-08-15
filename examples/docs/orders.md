# `orders` — the order state machine

> The rule that applies **before** you touch an order lives in [`../CLAUDE.after.md`](../CLAUDE.after.md):
> always call `order.transition(to=...)` rather than assigning `order.status` directly.
> This file holds the reasoning behind it.

## Why an explicit status column

The state machine was originally a set of boolean flags on the `Order` model (`is_paid`, `is_shipped`, `is_cancelled`). That worked until we hit an order that was both cancelled and shipped, which nobody could explain. We spent two days reconstructing the history from the audit log before finding a race between the webhook handler and the admin action.

In March we replaced the flags with an explicit `status` column plus a `transition()` method that validates the move.

## The backfill

The migration backfilled 340,000 rows in batches of 5,000, because a single `UPDATE` locked the table for eleven minutes on staging.

## Alternatives we rejected

**`django-fsm`** wanted to own the model save path, and we already had a custom `save()` doing audit logging.

**Transitions in a separate table** is cleaner, but it would have needed a join on every list view, and the order list is the hottest page in the product.

## Why a no-op transition does not raise

`transition()` raises `InvalidTransition`, which the API layer maps to a 409. It deliberately does **not** raise on a transition to the state the order is already in, so that webhook retries stay idempotent.
