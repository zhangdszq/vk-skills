# Event Subscription

Read this file when the user asks about Megaview event push, webhooks, callback URLs, verification token, or encrypt key.

## What the docs confirm

Megaview describes an event subscription flow rather than a large endpoint matrix in the bundled page.

### Subscription flow

1. Optionally configure `Encrypt Key`
2. Optionally modify `Verification Token`
3. Configure the callback request URL
4. Receive and process Megaview HTTP `POST` event callbacks

## What to tell the user

When the user wants to integrate event subscription:

- confirm the callback URL they want Megaview to call
- ask whether they want payload signature protection through `Encrypt Key`
- ask whether they already have a `Verification Token` convention in their system
- tell them events are pushed to their endpoint through HTTP `POST`

## Use cases

This reference is appropriate for:

- webhook receiver design
- callback verification logic
- deciding whether to enable encryption
- planning how Megaview events fit into an existing backend

## Conservative note

The bundled docs do not expose a detailed event-type catalog here. If the user needs exact event names or payload schemas and they are not present elsewhere in the workspace, say that the current bundled reference only confirms the subscription workflow, not the full event matrix.
