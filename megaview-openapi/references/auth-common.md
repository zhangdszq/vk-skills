# Auth And Common Rules

Read this file for every Megaview task before reading any module-specific reference.

## Base URL

- Host: `https://open.megaview.com`

## Auth flow

Megaview server APIs use bearer auth.

### Token endpoint

- `POST /openapi/auth/v1/app_access_token/internal`

### Request body

- `app_key`
- `app_secret`

### Response highlights

- `data.app_access_token`
- `data.token_type`
- `data.expire`

### Token lifecycle notes

- `app_access_token` max validity is 2 hours
- if the previous token still has more than 30 minutes left, Megaview returns the same token and does not refresh expiry
- if the previous token has less than 30 minutes left, Megaview may return a new token while the previous token is still valid for a period

## Required headers

For most server APIs:

- `Content-Type: application/json`
- `Authorization: Bearer <access_token>`

## Common response shape

```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

Interpretation:

- `code == 0` means business success
- non-zero `code` means a Megaview business failure even if HTTP is `200`

## Common errors to mention

These are the most useful errors to surface during diagnosis:

- `400000 invalid param`: parameter validation failed
- `400001 miss required param`: missing required parameter
- `400002 list element too long`: list argument too large
- `400003 app rate limited`: throttled, retry after reset window
- `400004 authorization invalid`: auth header missing or token invalid
- `400005 authorization Need a Bearer`: header format must be `Bearer <token>`
- `400006 api request forbidden`: API permission restriction
- `500000 internal error`: Megaview internal error, retry or escalate

## Rate limits

Megaview documents three org-level rate-limit tiers:

- `Light`: 100 QPS
- `Medium`: 50 QPS
- `Heavy`: 10 QPS

If the user is orchestrating bulk sync, warn them to batch requests accordingly.

## ID routing rules

Use the identifier type to choose the endpoint family.

### Canonical Megaview IDs

Use organization / CRM / conversation module APIs when the user has Megaview-native IDs such as:

- `department_id`
- `open_user_id`
- `account_id`
- `contact_id`
- `deal_id`
- `conversation_id`
- `todo_id`

### Third-party IDs

Use solution or origin APIs when the user has IDs from their own system such as:

- `origin_department_id`
- `origin_user_id`
- `origin_account_id`
- `origin_contact_id`
- `origin_deal_id`
- `origin_conversation_id`
- `origin_conv_id`

### Create semantics

- canonical create APIs usually require `uniq_token`
- solution create APIs usually require `origin_*`

Do not swap these just because the names look similar.

## Time formats

Megaview examples accept both:

- `2021-01-01 00:00:00`
- `2021-01-01T00:00:00+08:00`

If the user gives an ambiguous timestamp, normalize it before drafting or executing.

## Execution helper

Use the bundled script:

`scripts/megaview_request.py`

Preferred credential sources:

1. explicit values from the user
2. environment variables:
   - `MEGAVIEW_APP_KEY`
   - `MEGAVIEW_APP_SECRET`
3. shared credentials file:
   - `~/.vk-cowork/megaview_credentials.json`
4. bundled skill credentials file:
   - `data/megaview_credentials.json`

The script automatically:

- gets an access token
- injects the bearer header
- replaces `:path_param` placeholders
- sends the final request
- prints structured JSON

## Known doc quirks

These quirks are important enough to mention when relevant:

1. The CRM account update doc uses `openapi/crm/v1/accounts/:account_id` without a leading `/`.
   Treat the real path as `/openapi/crm/v1/accounts/:account_id`.

2. The solution page titled `变更客户备注名信息` appears to point to the conversation account-label query endpoint instead of an update API.
   Do not trust that page blindly. Cross-check with the canonical CRM account update endpoint.

3. A solution page for `查询会话沟通概要` points to `/openapi/conversation/v1/conversations/:conversation_id/lineage`.
   Do not treat lineage as the primary summary endpoint. For actual沟通概要, prefer the conversation `summary_pro` endpoint and only mention the doc inconsistency as a warning.

## Behavior rule

If the user asks for a live Megaview call but does not provide enough information, do not fabricate placeholders and pretend the call can run.

Instead:

1. name the exact endpoint
2. list the missing parameters
3. provide a ready-to-fill command template

## Confidence labeling rule

When answering from this skill, explicitly separate:

- `documented`: the path and behavior are confirmed in the bundled references
- `needs verification`: the path or payload detail is inferred, inconsistent, or not fully confirmed

If a path is only inferred, say that plainly instead of writing it as settled fact.
