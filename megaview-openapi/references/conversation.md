# Conversation Module

Read this file when the task is about files, conversations, ASR, todos, events, dimensions, summaries, scores, or communication lineage.

## When to use this module

Use this module for:

- uploading audio, video, chat, or transcript files
- creating or updating conversations
- appending IM chat records
- querying ASR, todos, events, dimensions, scores, summaries, or lineage

## File endpoints

| Task | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| Upload audio/video file | `POST` | `/openapi/conversation/v1/files` | Supports local file or network file according to docs |
| Upload IM single-chat text | `POST` | `/openapi/conversation/v1/files/upload_chat_records` | Text file upload for single chat |
| Upload IM group-chat text | `POST` | `/openapi/conversation/v1/files/upload_group_chat_records` | For one-customer-one-group scenarios |
| Upload transcript records file | `POST` | `/openapi/conversation/v1/files/upload_transcript_records` | For already transcribed content |

### File note

- `file_token` is usually a prerequisite for conversation creation
- one `file_token` can only be bound to one conversation

## Canonical conversation endpoints

| Task | Method | Endpoint |
| --- | --- | --- |
| Create conversation | `POST` | `/openapi/conversation/v1/conversations` |
| Append IM single-chat content | `PUT` | `/openapi/conversation/v1/conversations/:conversation_id/doc_append` |
| Append IM group-chat content | `PUT` | `/openapi/conversation/v1/conversations/:conversation_id/groupchat_doc_append` |
| Query single conversation | `GET` | `/openapi/conversation/v1/conversations/:conversation_id` |
| Update conversation basic properties | `PUT` | `/openapi/conversation/v1/conversations/:conversation_id` |
| Batch query conversations | `POST` | `/openapi/conversation/v1/conversations/list` |
| Query ASR result | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/asr_data` |
| Query account labels | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/account_labels` |
| Query todos | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/todos` |
| Query event results | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/events` |
| Query dimension result | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/dimension` |
| List event tree | `GET` | `/openapi/conversation/v1/events/list` |
| Query conversation custom fields | `GET` | `/openapi/conversation/v1/conversations/customer_fields` |
| Query score | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/score_result` |
| Query summary | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/summary_pro` |
| Query communication lineage | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/lineage` |

For employee analytics in this workspace, do not assume the batch list must be driven by `open_user_id`.
The latest confirmed route is to use the origin-style batch query with `origin_user_id` when listing a salesperson's conversations.

## Create conversation: confirmed core fields

The docs explicitly confirm these canonical create fields:

- `uniq_token` required
- `name` required
- `begin_time` required
- `end_time` optional
- `created_deal_stage_id` optional
- `file_tokens` required
- `open_user_id` required as the owner user identity

The docs also describe optional association choices among:

- `deal_id`
- `account_id`
- `contact_id`

Use those only when the user's business relationship actually requires them.

## Todo endpoint

| Task | Method | Endpoint |
| --- | --- | --- |
| Update todo | `PUT` | `/openapi/conversation/v1/todos/:todo_id` |

### Update todo: confirmed fields

- path param `todo_id`
- body field `todo_status`, enum docs show `created` or `done`
- body field `todo_time` optional

## Origin-based conversation endpoints

Use these when the user has third-party identifiers, or when the conversation batch query is driven by `origin_user_id`:

| Task | Method | Endpoint |
| --- | --- | --- |
| Query conversation by third-party ID | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id` |
| Query ASR by third-party conversation ID | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/asr_data` |
| Batch query conversations | `POST` | `/openapi/conversation/v1/origin_conversations/list` |
| Query labels by third-party conversation ID | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/account_labels` |
| Query todos by third-party conversation ID | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/todos` |
| Query event results by third-party conversation ID | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/events` |
| Query dimension by third-party conversation ID | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/dimension` |
| Query score by third-party conversation ID | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/score_result` |
| Query summary by third-party conversation ID | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/summary_pro` |

## Ask-before-run checklist

### For file upload

Ask:

- what file type it is
- whether the file is local or remote URL
- which downstream conversation API it will feed into

### For conversation create

Ask:

- whether this is canonical or solution-style creation
- the conversation unique identifier (`uniq_token` or `origin_conv_id`)
- name
- start time
- end time if available
- owner user identity
- whether file upload has already happened
- whether the conversation should be attached to a deal, account, or contact

### For result queries

Ask only for:

- `conversation_id` or `origin_conversation_id`
- which analysis artifact is needed: `asr_data`, `todos`, `events`, `dimension`, `score_result`, `summary_pro`, `lineage`

## Common pitfalls

- ASR result URLs may be short-lived; docs say the result file is valid for 2 hours
- `account_labels` uses `origin_conversation_id` in the docs, not canonical `conversation_id`
- `lineage` docs under the solution tree still point to the canonical conversation path; call this out if the user only has an origin ID
- for employee-level analytics, do not force `origin_user_id -> open_user_id -> /conversations/list` if `/origin_conversations/list` already supports `origin_user_id`

## Lineage rule of thumb

For `lineage` specifically:

- treat `GET /openapi/conversation/v1/conversations/:conversation_id/lineage` as the documented path
- treat any `origin_conversation_id` lineage path as unconfirmed unless the user provides stronger documentation
- when the user only has `origin_conversation_id`, recommend a two-step lookup rather than inventing an origin lineage endpoint
