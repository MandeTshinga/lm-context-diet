# `billing` — payment provider integration

> The two rules that apply **before** you call anything live in [`../CLAUDE.after.md`](../CLAUDE.after.md):
> always pass an idempotency key on calls that move money, and never read `request.POST`
> on the webhook endpoint before verifying the signature. This file holds the reasoning.

## The client wrapper

Every call goes through `billing.client.call()`, which adds a request ID and retries on 5xx with exponential backoff.

## The v3 idempotency incident

The provider changed their idempotency semantics in their v3 API.

In v2, an idempotency key was scoped to the endpoint. In v3 it is scoped to the account, which means reusing a key across two different endpoints now returns the first response rather than an error.

We found this out in production when a refund returned a charge object. The fix was to prefix every key with the endpoint name, which is what `billing.keys.for_order(order, action)` does.

## Why signature verification is fragile

Verification uses the raw request body. Django's form parsing consumes the stream, so touching `request.POST` first makes the signature fail to match. This cost us an afternoon.

## Why every payload is persisted

We store every webhook payload in `billing_webhookevent` before processing it, including ones we reject. Disk is cheap, and this table has resolved four disputes with the provider.
