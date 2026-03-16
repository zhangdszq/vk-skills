# Employee Analytics

Read this file when the user asks about employee performance, seller comparison, Saudi `leads-to-order` conversion, sales team or channel performance, LP, trial-completion, or TCC effectiveness, session score, customer score, conversation count, sales amount, wants to compare Megaview metrics with StarRocks sales data, wants to know who is weakest or should be reviewed first, or wants to pull representative call samples for coaching.

If the request touches non-default StarRocks tables or the warehouse metric-definition document, also read `references/starrocks-routing.md`.

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

## Database employee scope

For employee performance analysis, use StarRocks to define the active review scope before using Megaview mappings:

- primary employee master table: `vk_gl_leads_staff_team_assignment_relation`
- active rule: `termination_date is null`
- inactive rule: `termination_date is not null`
- default review behavior: prioritize database-active employees first
- `data/employees.json` is the Megaview mapping layer used after the seller scope is clear
- if the user explicitly asks for a departed seller, keep the analysis as historical review and label that seller as inactive instead of mixing them into the default active review ranking

Existence rule for Megaview accounts:

- ignore `is_enable`
- do not ignore `is_delete`
- if the account can be found by `origin_user_id` and is not deleted, treat it as an existing account for analysis

## Main analysis flow

When the user asks for employee performance analysis, follow this chain:

1. Start from `intl_analysis` and decide which growth-chain stage answers the business question.
2. When the question is broad, prefer the Saudi `leads-to-order` perspective first:
   - `vk_sr_intl_sa_leads_to_order_details_lv`
   - then expand to channel, LP, trial-completion / post-trial follow-up, TCC, and marketing tables when needed
3. For employee review, check the requested or derived seller scope in `vk_gl_leads_staff_team_assignment_relation` first and prefer active employees where `termination_date is null`.
4. Resolve employee names from `data/employees.json` only after the seller or team scope is clear.
5. Query StarRocks first:
   - prefer `staffName`
   - use `staffId` only when the table really stores that identifier
   - use the seller metric from `intl_analysis` as the main business anchor
6. Query Megaview user info with:
   - `GET /openapi/organization/v1/origin_users/:origin_user_id`
   - only use it to confirm the account exists or enrich user metadata
   - do not exclude the employee just because `is_enable` suggests a non-active status
   - exclude the employee if `is_delete` indicates the account has been deleted
7. Query Megaview conversations with:
   - `POST /openapi/conversation/v1/origin_conversations/list`
   - filter by `origin_user_id`
8. Aggregate Megaview explanation metrics:
   - conversation count from `total_count` / returned conversations
   - conversation score from `GET /openapi/conversation/v1/conversations/:conversation_id/score_result`
   - customer score from `GET /openapi/crm/v1/deals/:deal_id/score_result`
9. Merge the `intl_analysis` growth-chain result with Megaview explanation metrics into one summary

## Driver principle

For this skill, the preferred reasoning order is:

1. `intl_analysis` defines the seller scope and business conclusion
2. Megaview explains quality, call evidence, and coaching direction

Use this framing especially when the user asks questions like:

- 哪个销售表现最好或最差
- 沙特从渠道到订单的转化卡在哪一段
- 哪个销售团队、LP、试听完课或 TCC 承接最差
- 哪些销售值得优先复核
- 哪些销售需要带教
- 这组销售的业务结果和会话质量是否一致

Do not default to a Megaview-first narrative for seller-performance work.

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
- default review scope should exclude database-inactive employees unless the user explicitly asks for a historical review

Current script logic uses peer-relative signals from:

- `sales_amount`
- `average_conversation_score`
- `average_customer_score`
- `conversation_count`

Interpretation guidance:

- `sales_amount` is the primary business anchor
- Megaview metrics explain whether the seller's conversation quality supports or conflicts with the business result

The output should be described as:

- `performance_review`
- `review_priority_ranking`
- `urgent_manual_review` / `coach_and_recheck` / `stable`

Do not phrase the result as an automatic termination decision.

## Coaching sample flow

When the user wants representative conversations for training, follow this chain:

1. Usually start from a seller already identified by `intl_analysis`
2. Resolve one employee from `data/employees.json`
3. Optionally query Megaview user info with:
   - `GET /openapi/organization/v1/origin_users/:origin_user_id`
4. List conversations with:
   - `POST /openapi/conversation/v1/origin_conversations/list`
5. Score an evenly distributed subset of conversations with:
   - `GET /openapi/conversation/v1/conversations/:conversation_id/score_result`
6. Pick representative low / median / high conversations
7. Pull supporting evidence with:
   - `GET /openapi/conversation/v1/conversations/:conversation_id/summary_pro`
   - `GET /openapi/conversation/v1/conversations/:conversation_id/asr_data`
8. Summarize coaching takeaways from the selected samples

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

Treat StarRocks references as two layers:

1. metric-definition layer:
   - `data/国际站全部物化视图_指标字段口径梳理_2026-03-11.md`
   - this explains warehouse-source business meaning and field definitions
2. live-query layer:
   - the current verified database is `intl_analysis`
   - the currently visible live reporting objects are mainly `vk_sr_intl_*_lv` and `vk_sr_intl_*_da`

Current skill scope:

- only use the bundled `intl_analysis` database
- do not expand analysis to other StarRocks databases unless the skill is updated on purpose

Do not assume every documented `vk_intl_dw_*_mv` table name can be queried directly in the current live database.
When that distinction matters, read `references/starrocks-routing.md` and explicitly separate:

- documented metric-definition table names
- verified live reporting table names

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

For seller-performance analysis, this default table is the first business anchor.
Megaview should be layered on top of it as explanation, not treated as the primary driver of the workflow.

But for broader Saudi growth questions, prefer these table families before falling back to the seller-quality snapshot:

- Saudi leads-to-order: `vk_sr_intl_sa_leads_to_order_details_lv`
- Saudi LP performance: `vk_sr_intl_sa_lp_performance_evaluation_details_mtd_lv`
- Saudi trial contact: `vk_sr_intl_sa_trial_contact_summary_lv`
- Saudi marketing / ROAS: `vk_sr_intl_sa_marketing_spend_daily_lv`, `vk_sr_intl_sa_marketing_spend_7d_roas_lv`, `vk_sr_intl_sa_marketing_spend_mtd_roas_lv`, `vk_sr_intl_sa_marketing_spend_ytd_roas_lv`
- TCC aging: `global_tcc_to_new_conversion_aging_lv`

Verified useful fields on the default table include:

- `staff_name`
- `business_line`
- `pt`
- `total_new_gmv_usd`
- `total_new_order`
- `total_calls`
- `connected_calls`
- `no_answer_calls`
- `total_duration`
- `avg_duration_sec`
- `avg_duration_min`
- `connect_rate`

For multi-day analysis, prefer summing the base count / amount fields and recomputing ratios from numerators when possible.
Do not blindly sum or average already-derived rates such as `connect_rate` across days without checking the math.

Only ask for additional StarRocks details when the user wants to override the default target table, field mapping, or metric inside `intl_analysis`.

Minimum override configuration if the user wants a different sales comparison inside `intl_analysis`:

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

## Sales-centric interpretation rule

When both sides are available:

1. use `intl_analysis` to decide the seller ranking, GMV context, and business priority
2. use Megaview to explain why that seller looks strong, weak, risky, or coachable

Good framing:

- `Sales result first, conversation evidence second`
- `Business ranking first, Megaview explanation second`

Avoid framing like:

- `Megaview first, then maybe compare to sales later`

## Saudi growth-chain interpretation rule

For broad growth questions, prefer this order:

1. channel and marketing
2. leads-to-order conversion
3. seller team and individual handoff
4. LP and trial completion
5. trial contact and TCC aging
6. Megaview individual drill-down

## Non-default StarRocks routing

Do not reuse the default seller-performance table for every StarRocks request.

When the user asks for:

- order revenue / refund / inventory metrics
- class consumption / attendance metrics
- student learning-performance metrics
- region or product-line GMV achievement

read `references/starrocks-routing.md` and choose the table by business theme.

Examples of verified live reporting tables:

- seller quality + GMV: `vk_sr_intl_sa_cc_quality_monitor_da`
- order detail: `vk_sr_intl_ae_order_detail_lv`, `vk_sr_intl_kr_order_detail_lv`
- class consumption: `vk_sr_intl_ae_class_consumption_detail_lv`, `vk_sr_intl_kr_class_consumption_detail_lv`
- learning performance: `vk_sr_intl_sa_student_learning_performance_lv`
- region GMV achievement: `vk_sr_intl_gl_gmv_achievement_lv`

When the request is primarily StarRocks exploration rather than the bundled employee workflow, prefer:

- `scripts/starrocks_query.py`

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
- a non-default StarRocks credential set for the same `intl_analysis` database the user explicitly wants to use

If the user only wants a plan or draft, do not execute the scripts.
If the user only wants coaching logic, StarRocks is not required.

## Common pitfalls

- `staffId` in the current `employees.json` is Megaview `origin_user_id`, not `open_user_id`
- for employee analysis, use `origin_conversations/list` with `origin_user_id` first; do not force an `open_user_id -> conversations/list` conversion if the origin batch query already satisfies the need
- conversation count depends on the selected time range
- customer score aggregation should deduplicate `deal_id` values, or one active customer with many conversations will be over-weighted
- Megaview may return unfinished analysis for some conversations; note these misses in the output instead of pretending every score exists
- training conclusions should be based on multiple representative calls, not one isolated conversation
