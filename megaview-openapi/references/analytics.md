# Employee Analytics

Read this file when the user asks about employee performance, staff comparison, session score, customer score, conversation count, sales amount, wants to compare Megaview metrics with StarRocks sales data, wants to know who is weakest or should be reviewed first, or wants to pull representative call samples for coaching.

## Built-in employee mapping

The skill includes:

- `data/employees.json`

Current row format:

```json
{
  "staffName": "Abdelrahman Al-Hamdan",
  "staffId": "600000368|46677"
}
```

Interpretation:

- `staffName`: display name used by the user
- `staffId`: shared key
  - use it as Megaview `origin_user_id`
  - for StarRocks, prefer `staffName` unless a separate `staff_id` mapping is available

Existence rule for Megaview accounts:

- ignore `is_enable`
- do not ignore `is_delete`
- if the account can be found by `origin_user_id` and is not deleted, treat it as an existing account for analysis

## Main analysis flow

When the user asks for employee performance analysis, follow this chain:

1. Resolve employee names from `data/employees.json`
2. Query Megaview user info with:
   - `GET /openapi/organization/v1/origin_users/:origin_user_id`
   - only use it to confirm the account exists or enrich user metadata
   - do not exclude the employee just because `is_enable` suggests a non-active status
   - exclude the employee if `is_delete` indicates the account has been deleted
3. Query Megaview conversations with:
   - `POST /openapi/conversation/v1/origin_conversations/list`
   - filter by `origin_user_id`
4. Aggregate conversation metrics:
   - conversation count from `total_count` / returned conversations
   - conversation score from `GET /openapi/conversation/v1/conversations/:conversation_id/score_result`
5. Aggregate customer metrics:
   - unique `deal_id` values from conversations
   - customer score from `GET /openapi/crm/v1/deals/:deal_id/score_result`
6. Query StarRocks sales:
   - prefer `staffName`
   - use `staffId` only when the table really stores that identifier
7. Merge Megaview metrics and StarRocks metrics into one summary

## Performance risk review

When the user asks questions like:

- 谁最弱
- 谁应该被重点复核
- 谁应该先进入绩效评审
- 谁最有淘汰风险

Translate that into a manager-review workflow, not an automatic firing decision.

Preferred output:

- a review priority ranking
- a risk level such as `high` / `medium` / `low`
- concrete reasons grounded in metrics
- a guardrail that this is for human review only

Current script logic uses peer-relative signals from:

- `sales_amount`
- `average_conversation_score`
- `average_customer_score`
- `conversation_count`

The output should be described as:

- `performance_review`
- `review_priority_ranking`
- `urgent_manual_review` / `coach_and_recheck` / `stable`

Do not phrase the result as an automatic termination decision.

## Coaching sample flow

When the user wants representative conversations for training, follow this chain:

1. Resolve one employee from `data/employees.json`
2. Optionally query Megaview user info with:
   - `GET /openapi/organization/v1/origin_users/:origin_user_id`
3. List conversations with:
   - `POST /openapi/conversation/v1/origin_conversations/list`
4. Score an evenly distributed subset of conversations with:
   - `GET /openapi/conversation/v1/conversations/:conversation_id/score_result`
5. Pick representative low / median / high conversations
6. Pull supporting evidence with:
   - `GET /openapi/conversation/v1/conversations/:conversation_id/summary_pro`
   - `GET /openapi/conversation/v1/conversations/:conversation_id/asr_data`
7. Summarize coaching takeaways from the selected samples

## Why the flow uses origin-based conversation batch query

The employee mapping already gives `origin_user_id`, and the current best aggregation path is:

- use `origin_user_id` directly
- query `POST /openapi/conversation/v1/origin_conversations/list`
- use returned canonical conversation IDs for downstream score and summary endpoints

This works better because the conversation list response includes:

- canonical `id` as `conversation_id`
- canonical `deal_id`
- `origin_conversation_id`

That means the skill can directly call canonical score endpoints without guessing origin mappings.

## Confirmed Megaview endpoints for analytics

| Purpose | Method | Endpoint | Key field |
| --- | --- | --- | --- |
| Resolve Megaview user | `GET` | `/openapi/organization/v1/origin_users/:origin_user_id` | `origin_user_id` |
| List employee conversations | `POST` | `/openapi/conversation/v1/origin_conversations/list` | body `origin_user_id` |
| Query conversation score | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/score_result` | `conversation_id` |
| Query conversation summary | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/summary_pro` | `conversation_id` |
| Query ASR metadata | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/asr_data` | `conversation_id` |
| Query customer score | `GET` | `/openapi/crm/v1/deals/:deal_id/score_result` | `deal_id` |

## Confirmed response fields used for aggregation

### User lookup

The user query response includes:

- `open_user_id`
- `name`
- `tel`
- `email`
- `main_department_id`

### Conversation list

The conversation list response includes:

- `total_count`
- `conversations[].id`
- `conversations[].deal_id`
- `conversations[].origin_conversation_id`
- `conversations[].begin_time`
- `conversations[].salesman_percent`

The latest confirmed employee-analysis route uses `origin_user_id` directly for this batch query, so `open_user_id` is no longer required to list the employee's conversations.

### Score endpoints

Both conversation score and customer score responses include:

- `score_results[]`
- `score_results[].score`
- `score_results[].total_score`
- `score_results[].qualified`

For aggregation, the scripts use the average of `score_results[].score` per entity, then compute an employee-level mean.

### Coaching endpoints

`summary_pro` is useful for:

- customer need
- objections
- next-step commitment
- SOP / quality labels

`asr_data` is useful for:

- short transcript preview
- real wording examples for coaching
- checking whether the seller explored needs, handled objections, and closed next steps

## Time-range rules

Megaview canonical conversation list has a documented limit:

- each request window must not exceed 7 days

So for longer ranges, the script must split the full interval into 7-day slices and page through each slice.

## StarRocks side

The built-in scripts expect StarRocks to be reachable through the MySQL protocol.
They now prefer a Python driver (`PyMySQL`) and can also load it from the skill-local `.venv`.
The MySQL CLI is only a fallback when the Python driver is unavailable.

The skill now ships with a bundled default config file:

- `data/starrocks_config.json`

Current built-in defaults:

- host: `10.23.16.15`
- port: `9030`
- database: `intl_analysis`
- table: `vk_sr_intl_sa_cc_quality_monitor_da`
- join key: `staffName`
- join field: `staff_name`
- date field: `pt`
- sales field: `total_new_gmv_usd`

This reflects the verified live setup from prior testing. In normal use, the skill should use these defaults directly instead of asking the user to restate them.

Only ask for additional StarRocks details when the user wants to override the default target table, metric, or database.

Minimum override configuration if the user wants a different sales comparison:

- host
- port
- user
- password
- database
- sales table
- join field
- date field
- sales amount field or metric expression

Supported join rules:

- `employees.staffId == starrocks.staff_id`
- `employees.staffName == starrocks.staff_name`

Use `staffId` when the StarRocks table has a stable numeric identifier.
Use `staffName` when the table only stores employee names.

For the current built-in default table, use `staffName`.

## Bundled scripts

For sales comparison, prefer:

- `scripts/employee_performance.py`

For coaching sample extraction, prefer:

- `scripts/conversation_training_samples.py`

## Output expectations

For analytics tasks, prefer this summary shape:

```markdown
## Employees
- ...

## Megaview Metrics
- conversation_count: ...
- average_conversation_score: ...
- average_customer_score: ...

## StarRocks Metrics
- sales_amount: ...

## Comparison
- ...

## Performance Review Priority
- high / medium / low
- reasons: ...
- recommendation: urgent_manual_review / coach_and_recheck / stable

## Notes
- ...
```

## When to ask follow-up questions

Ask for more information when any of these are missing:

- employee name or `staffId`
- time range
- a non-default StarRocks table / field mapping the user explicitly wants
- a non-default StarRocks credential set the user explicitly wants to use

If the user only wants a plan or draft, do not execute the scripts.
If the user only wants coaching logic, StarRocks is not required.

## Common pitfalls

- `staffId` in the current `employees.json` is Megaview `origin_user_id`, not `open_user_id`
- for employee analysis, use `origin_conversations/list` with `origin_user_id` first; do not force an `open_user_id -> conversations/list` conversion if the origin batch query already satisfies the need
- conversation count depends on the selected time range
- customer score aggregation should deduplicate `deal_id` values, or one active customer with many conversations will be over-weighted
- Megaview may return unfinished analysis for some conversations; note these misses in the output instead of pretending every score exists
- training conclusions should be based on multiple representative calls, not one isolated conversation
