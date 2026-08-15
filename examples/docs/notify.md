# `notify` — transactional mail and customer webhooks

> The rule that applies **before** you send anything outbound lives in
> [`../CLAUDE.after.md`](../CLAUDE.after.md): always set `allow_redirects=False`
> on outbound customer webhooks. This file holds the reasoning.

## Templates

Templates live in `notify/templates/mail/`. They were originally inline strings in the task functions, which made them impossible to preview.

We moved them to files in June and added `make mail-preview`, which renders every template with fixture data into `/tmp/mail-preview/`.

## The redirect loop

The webhook sender had a bug where a customer endpoint returning a 301 caused an infinite redirect loop, because `requests` follows redirects by default and the customer's load balancer was redirecting to itself.

## Retries and the dead letter queue

Retries are 5 attempts over 24 hours with jitter. After that the event lands in `notify_deadletter` and an operator has to replay it manually with `make notify-replay ID=...`.
