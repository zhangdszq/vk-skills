# Solution Recipes

Read this file when the user wants a higher-level integration flow driven by their own business IDs.

This reference is the fastest way to map natural-language business tasks to Megaview solution APIs.

## Use this file when

The user says things like:

- "按我们业务系统的客户 ID 创建"
- "用 origin_deal_id 查"
- "创建音频会话"
- "创建或追加 IM 会话"
- "把转录稿直接灌进 Megaview"

## Recipe 1: Create customer from third-party business data

- Endpoint: `POST /openapi/solution/v1/deals`

### Confirmed core fields

- `origin_deal_id` required
- `name` required
- `type` required, docs say current value should be `1`
- `amount` required
- `plan_to_deal_at` required
- `deal_stage` optional
- `create_at` optional

### When to choose this recipe

Use it when the caller wants Megaview to create a customer directly from their own CRM identifier, without first converting to Megaview deal IDs.

## Recipe 2: Create audio conversation

- Endpoint: `POST /openapi/solution/v1/conversations/audio`

### Confirmed core fields

- `origin_conv_id` required
- `name` required
- `begin_time` required
- `end_time` optional
- either `file_tokens` or `file_url`
- `origin_user_id` required
- optional `origin_deal_id`
- optional `origin_account_id`
- optional `origin_contact_id`
- optional `customize_fields`

### Relationship guidance from the docs

The docs describe three optional association slots:

- `origin_deal_id`
- `origin_account_id`
- `origin_contact_id`

Use only the combinations that match the user's actual sales process. If they are unsure, do not auto-fill all three.

## Recipe 3: Create or append IM conversation

- Endpoint: `POST /openapi/solution/v1/conversations/im`

### Confirmed core fields

- `origin_conv_id` required
- `name` required
- `begin_time` required
- `end_time` optional
- `is_group` required
- `origin_user_id` required
- optional `customize_fields`

This endpoint is meant for either:

- creating a new IM conversation
- appending new chat records onto an existing one

If the user mentions "单聊/群聊", make sure `is_group` aligns with that statement.

## Recipe 4: Create transcript-record conversation

- Endpoint: `POST /openapi/solution/v1/conversations/transcript_records`

### Confirmed core fields

- `origin_conv_id` required
- `name` required
- `begin_time` required
- `end_time` optional
- `origin_user_id` required
- optional customer associations such as `origin_deal_id`
- `transcript_records` list

### Confirmed transcript record item fields

Each transcript row needs:

- `origin_entity_id`
- `entity_type`, enum docs show `user` or `customer`
- `content`
- `begin_time`
- `end_time` optional

### Special note

The docs mention a not-connected call can still be imported when the transcript array has length `1` and content contains wording like "响铃未接通".

## Recipe 5: Query by third-party IDs

Use these when the user wants to query existing Megaview data without first looking up native IDs.

| Task | Method | Endpoint |
| --- | --- | --- |
| Query department | `GET` | `/openapi/organization/v1/origin_departments/:origin_department_id` |
| Query user | `GET` | `/openapi/organization/v1/origin_users/:origin_user_id` |
| Query account | `GET` | `/openapi/crm/v1/origin_accounts/:origin_account_id` |
| List account contacts | `POST` | `/openapi/crm/v1/origin_accounts/:origin_account_id/contacts` |
| Query contact | `GET` | `/openapi/crm/v1/origin_contacts/:origin_contact_id` |
| Query deal | `GET` | `/openapi/crm/v1/origin_deals/:origin_deal_id` |
| Query deal summary | `GET` | `/openapi/crm/v1/origin_deals/:origin_deal_id/summary_pro` |
| Query deal score | `GET` | `/openapi/crm/v1/origin_deals/:origin_deal_id/score_result` |
| Query conversation | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id` |
| Query ASR | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/asr_data` |
| Batch query conversations | `POST` | `/openapi/conversation/v1/origin_conversations/list` |
| Query labels | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/account_labels` |
| Query todos | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/todos` |
| Query events | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/events` |
| Query dimension | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/dimension` |
| Query score | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/score_result` |
| Query summary | `GET` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id/summary_pro` |

## Recipe 6: Update by third-party IDs

Use these when the source of truth is still the caller's own business ID space.

| Task | Method | Endpoint |
| --- | --- | --- |
| Update department | `PUT` | `/openapi/organization/v1/origin_departments/:origin_department_id` |
| Update user | `PUT` | `/openapi/organization/v1/origin_users/:origin_user_id` |
| Dimission user | `POST` | `/openapi/organization/v1/origin_users/dimission/:origin_user_id` |
| Bind account contact | `PUT` | `/openapi/crm/v1/origin_accounts/:origin_account_id/bind_contact` |
| Update contact | `PUT` | `/openapi/crm/v1/origin_contacts/:origin_contact_id` |
| Update deal | `PUT` | `/openapi/crm/v1/origin_deals/:origin_deal_id` |
| Bind deal contact | `PUT` | `/openapi/crm/v1/origin_deals/:origin_deal_id/bind_contact` |
| Update conversation | `PUT` | `/openapi/conversation/v1/origin_conversations/:origin_conversation_id` |

## Conservative behavior

If a solution page looks inconsistent with its title, do not force execution.

Instead:

1. say the page appears inconsistent
2. point to the canonical module equivalent
3. ask whether the user wants the safer canonical route
