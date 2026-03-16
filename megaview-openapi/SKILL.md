---
name: megaview-openapi
description: Use this skill whenever the user wants sales-centric analysis driven by the `intl_analysis` StarRocks database, especially from a Saudi `leads-to-order` conversion perspective, and enriched by Megaview conversation evidence. Use it for seller performance comparison, session score and customer score analysis, conversation count analysis, GMV comparison, training samples, coaching calls, transcript snippets, manager coaching material, or to identify who should enter performance review first. Use it when the user wants to start from the growth chain in `intl_analysis` - channel, marketing, sales team, LP, trial completion, post-trial follow-up, TCC, and order conversion - then use Megaview to explain seller quality, fetch representative conversations, or build a review-priority list for underperformers. This skill is specifically for sales and growth-chain analysis built on `intl_analysis` plus Megaview, not for general-purpose Megaview API documentation, request drafting, or ad-hoc endpoint execution.
---

# 销售能力分析

## What this skill does

Use this skill to turn a natural-language sales analysis request into one of two outcomes:

1. Start from the growth chain in `intl_analysis`, especially Saudi `leads-to-order` conversion plus trial-completion / post-trial follow-up analysis, then enrich it with Megaview quality evidence.
2. Fetch representative conversation samples for coaching or training after a seller, team, or conversion stage has been identified.

This skill is designed to reduce these common failure modes:

- confusing Megaview employee IDs with the built-in `employees.json` mapping
- using the wrong StarRocks join rule or wrong GMV table defaults
- mixing database-inactive sellers into the default active performance-review scope
- drawing coaching conclusions from isolated calls instead of representative samples

## Scope boundary

This skill is only for:

- employee performance analysis
- sales comparison driven by `intl_analysis` and enriched by Megaview
- Saudi `leads-to-order` conversion analysis
- sales team / channel / marketing / LP / trial completion / TCC growth-chain analysis
- representative conversation selection
- coaching and training analysis
- performance risk review and underperformer prioritization
- StarRocks analysis scoped to the bundled `intl_analysis` database

Do not present this skill as able to:

- write generic API requests
- provide curl / Python / TypeScript request templates
- act as a general Megaview API assistant
- offer ad-hoc endpoint invocation as a primary workflow

If the user asks for generic API drafting, explain briefly that this skill focuses on sales analysis and coaching, then steer back to analysis workflows.

Do not turn this skill into an automatic firing tool.
If the user asks "谁该被淘汰", translate that into:

- who should enter performance review first
- who needs urgent coaching
- who should be manually reviewed before any HR decision

## Introduction style

When this skill first responds, keep the intro narrow.

Good intro scope:

- 先看沙特 `leads-to-order` 或其他增长链路在 `intl_analysis` 里的业务表现
- 再看销售团队、渠道、投放、LP、试听是否完课、完课后是否及时跟进、TCC 哪一段有问题
- 再补会话评分、客户评分、GMV 和通话证据
- 按条件筛选样本通话
- 做培训样例和带教分析
- 输出绩效风险预警和复核优先级

Do not proactively offer:

- 帮你写接口请求
- curl / Python / TS 示例
- 直接调任意 Megaview 接口
- 其他问题

## Read order

Always read these files in order:

1. `references/auth-common.md`
2. `references/analytics.md` or `references/coaching.md`
3. Read `data/data_warehouse_metric_manual.md` when the task touches order metrics, course metrics, Saudi `leads-to-order`, trial completion, LP, TCC, marketing, or executable SQL metric definitions.
4. Read `references/starrocks-routing.md` when the task touches StarRocks metric selection, non-default StarRocks tables, or the warehouse metric-definition document.
5. Read `references/org.md`, `references/crm.md`, or `references/conversation.md` only when you need to verify the underlying analytics chain or debug a metric source.

This skill is no longer a general Megaview API router. Read only the files needed for analysis or coaching.

## Intent routing

Route the task before writing anything.

### 1. Employee analytics

Use this path when the user wants:

- employee or staff performance
- seller-centric analysis anchored on `intl_analysis`
- Saudi `leads-to-order` conversion
- sales team / channel / marketing / LP / trial completion / TCC chain analysis
- session score and customer score by employee
- conversation count by employee
- Megaview vs StarRocks sales comparison
- ranking or comparing multiple employees
- who looks most at risk among a selected peer group
- who should enter performance review first

Deliver:

- the growth-chain stage being analyzed
- the resolved employees and IDs
- the StarRocks table and metric used
- the seller metrics used to define the business conclusion
- the Megaview metrics used to explain the seller's quality or coaching context
- a comparison summary and the relevant built-in analysis workflow
- a performance review priority list when the user asks who is underperforming

### 2. Coaching samples

Use this path when the user wants:

- representative conversations for training
- good / bad call examples
- transcript snippets for manager coaching
- examples to teach a seller how to improve

Deliver:

- the resolved employee and Megaview mapping
- which conversations were selected and why
- summary / score / ASR highlights
- concrete coaching takeaways

## Analysis routing rules

### Prefer analytics when:

- the user asks for employee performance or sales comparison
- the user wants to start from sales, GMV, order, or calling performance in `intl_analysis`
- the user asks about Saudi conversion, channels, marketing, LP, trial completion, TCC, or team performance
- the user gives employee names rather than direct API identifiers
- the task mixes Megaview metrics with StarRocks sales data
- the user asks who is weakest, who is bottom-ranked, or who should be reviewed first

### Prefer coaching when:

- the user wants representative conversations
- the user wants good / bad / typical call examples
- the user wants transcript snippets or manager coaching material

## Analysis discipline

Do not turn this skill into a generic API explainer.

Instead:

1. identify whether the request is analytics or coaching
2. anchor the task on the growth-chain question inside `intl_analysis`
3. when the question is broad, prefer the Saudi `leads-to-order` conversion perspective first, and explicitly check the trial-completed / post-trial follow-up slice when conversion analysis is in scope
4. for employee performance analysis, check the employee scope in `vk_gl_leads_staff_team_assignment_relation` first and prefer `termination_date is null` rows
5. resolve employees from the built-in mapping only after the seller or team scope is clear
6. use Megaview to explain seller quality, conversation evidence, and coaching direction
7. if the user asks for marketing, channel, LP, trial completion, TCC, order, class, learning, or region metrics, route through `data/data_warehouse_metric_manual.md` and `references/starrocks-routing.md`
8. ask only for business information that is actually missing for analysis, such as time range, channel scope, team scope, or employee identity

Important identifier rules:

- `open_user_id` and `origin_user_id` are not interchangeable
- `conversation_id` and `origin_conversation_id` are not interchangeable
- in this skill's built-in analytics flow, `data/employees.json` is the Megaview mapping layer, not the primary active-employee scope:
  - for employee performance review, prefer `vk_gl_leads_staff_team_assignment_relation`
  - treat `termination_date is null` as active and `termination_date is not null` as inactive
  - if the user explicitly asks for a departed seller, keep the analysis as a historical review rather than mixing that seller into the default active review pool
- `data/employees.json` uses `staffId` as the shared key:
  - treat it as Megaview `origin_user_id`
  - prefer `POST /openapi/conversation/v1/origin_conversations/list` with `origin_user_id` for employee conversation listing
  - prefer `staffName` for StarRocks joins unless the user provides a separate numeric `staff_id` mapping
  - do not reinterpret it as `uniq_token` unless the user explicitly says their data uses that scheme
- account existence rule for analytics and coaching:
  - ignore `is_enable`
  - do not ignore `is_delete`
  - if `is_delete` indicates the account is deleted, do not keep it in scope
  - only treat the account as usable when it exists and is not deleted

Time values should follow one of the documented formats:

- `YYYY-MM-DD HH:MM:SS`
- `YYYY-MM-DDTHH:MM:SS+08:00`

## Runtime rules

When running the built-in analysis workflows:

1. Prefer credentials from explicit user input.
2. If the user says credentials are already in environment variables, use:
   - `MEGAVIEW_APP_KEY`
   - `MEGAVIEW_APP_SECRET`
3. If explicit values and environment variables are missing, load:
   - `~/.vk-cowork/megaview_credentials.json`
   - or the bundled `data/megaview_credentials.json`
   - expected shape: `{"app_key":"...","app_secret":"..."}`
4. Never print raw secrets back to the user.
5. If the task is employee analytics, verify that you have:
   - employee names or staff IDs
   - a time range
   - default to the database-active employee scope from `vk_gl_leads_staff_team_assignment_relation`
   - if a requested employee is already inactive in that table, label the result as historical review / inactive instead of treating it as a normal active performance-review target
   - if the user wants the built-in sales comparison, use the bundled StarRocks defaults first
   - only ask about StarRocks table mapping or metric selection within `intl_analysis`
   - do not switch to another StarRocks database unless the skill is explicitly expanded later
6. If the task is coaching or training, verify that you have:
   - exactly which employee to analyze
   - a time range
   - whether the user wants summary only or transcript snippets too

## Driver model

The default reasoning order of this skill should be:

1. use `intl_analysis` to define the growth-chain stage, seller scope, business metric, and ranking context
2. when broad, start from Saudi `leads-to-order` conversion
3. move along the chain: channel -> marketing -> sales team / individual -> LP -> trial completion / post-trial follow-up -> TCC -> order
4. decide which sellers or periods deserve deeper explanation
5. resolve those sellers into Megaview `origin_user_id`
6. use Megaview to explain call quality, customer quality, and coaching evidence

In other words:

- `intl_analysis` is the business driver
- Megaview is the conversation-evidence and coaching layer at the individual level
- active employee scope comes from StarRocks first, not from `employees.json`

Do not default to a Megaview-first story when the user is clearly asking a sales-performance question.

For employee analytics, use:

```bash
python3 "/Users/zhang/.claude/skills/megaview-openapi/scripts/employee_performance.py" \
  --employee-name "Mohammad Qasem" \
  --begin-time "2026-03-01 00:00:00" \
  --end-time "2026-03-08 00:00:00"
```

The script reads `data/employees.json` by default and auto-loads the built-in StarRocks config unless the user explicitly overrides it.

For the default sales comparison setup, the script also auto-loads:

- `data/starrocks_config.json`

That file already contains the currently verified StarRocks connection and default mapping:

- database: `intl_analysis`
- table: `vk_sr_intl_sa_cc_quality_monitor_da`
- join key: `staffName`
- join field: `staff_name`
- date field: `pt`
- GMV field: `total_new_gmv_usd`

Interpret the default table carefully:

- `vk_sr_intl_sa_cc_quality_monitor_da` is the default snapshot anchor for seller-level quality review
- prefer `vk_sr_intl_sa_cc_quality_monitor_lv`, `vk_sr_intl_sa_cc_quality_monitor_today_lv`, or `vk_sr_intl_sa_cc_quality_monitor_all_lv` when the user clearly wants a more real-time or wider live view

So under the normal workflow, do not stop to ask for StarRocks config again unless the user wants to override these defaults.

Default order-metric reminders:

- by default, explain that GMV is discussed as total GMV and should be labeled as including refunded amount unless the user explicitly asks for refund-separated logic
- for Saudi conversion timing, prefer the `_jordan` time fields exposed by the conversion tables when they are available

For coaching samples, use:

```bash
python3 "/Users/zhang/.claude/skills/megaview-openapi/scripts/conversation_training_samples.py" \
  --employee-name "Abdelrahman Al-Hamdan" \
  --begin-time "2026-02-01 00:00:00" \
  --end-time "2026-03-01 00:00:00"
```

## StarRocks routing

Treat the bundled StarRocks materials as two layers:

1. `data/国际站全部物化视图_指标字段口径梳理_2026-03-11.md` is the warehouse metric-definition reference.
2. The live verified query layer in the current environment is mainly `intl_analysis` tables named `vk_sr_intl_*_lv` and `vk_sr_intl_*_da`.

Important rule:

- for now, keep the StarRocks scope limited to the bundled `intl_analysis` database
- do not assume a documented `vk_intl_dw_*_mv` name from the warehouse document is directly queryable in the current live database
- if the user references one of those names, verify it first and then map it to the closest live reporting table when needed

Current routing defaults:

- Saudi `leads-to-order` conversion backbone:
  - prefer `vk_sr_intl_sa_leads_to_order_details_lv`
- Saudi trial-completion / post-trial follow-up slice:
  - prefer `vk_sr_intl_sa_leads_to_order_details_lv`
- sales team / seller quality snapshot:
  - use `vk_sr_intl_sa_cc_quality_monitor_da`
- sales team / seller quality live view:
  - prefer `vk_sr_intl_sa_cc_quality_monitor_lv`, `vk_sr_intl_sa_cc_quality_monitor_today_lv`, or `vk_sr_intl_sa_cc_quality_monitor_all_lv`
- channel and follow-record analysis:
  - prefer `vk_sr_intl_gl_leads_channel_analysis_follow_record_lv`
- LP performance:
  - prefer `vk_sr_intl_sa_lp_performance_evaluation_details_mtd_lv`
- trial-completion / trial-contact / TCC analysis:
  - prefer `vk_sr_intl_sa_leads_to_order_details_lv`, `global_tcc_to_new_conversion_aging_lv`, and `vk_sr_intl_sa_trial_contact_summary_lv`
- marketing and ROAS:
  - prefer `vk_sr_intl_sa_marketing_spend_daily_lv`, `vk_sr_intl_sa_marketing_spend_7d_roas_lv`, `vk_sr_intl_sa_marketing_spend_mtd_roas_lv`, and `vk_sr_intl_sa_marketing_spend_ytd_roas_lv`
- order-detail revenue / refund / inventory analysis:
  - consult `references/starrocks-routing.md`
  - likely use live order-detail tables such as `vk_sr_intl_ae_order_detail_lv` or `vk_sr_intl_kr_order_detail_lv`
- class consumption / attendance / parent-feedback analysis:
  - consult `references/starrocks-routing.md`
  - likely use live class-consumption tables such as `vk_sr_intl_ae_class_consumption_detail_lv`
- learning-performance analysis:
  - consult `references/starrocks-routing.md`
  - likely use live learning tables such as `vk_sr_intl_sa_student_learning_performance_lv`
- region or business-line GMV target achievement:
  - consult `references/starrocks-routing.md`
  - likely use `vk_sr_intl_gl_gmv_achievement_lv`

When the task is non-default StarRocks exploration or verification, prefer:

```bash
python3 "/Users/zhang/.claude/skills/megaview-openapi/scripts/starrocks_query.py" --sql "..."
```

## Response format

For employee analytics tasks, use this structure:

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

## Notes
- ...
```

For coaching tasks, use this structure:

```markdown
## Employee
- ...

## Sample Calls
- low-score: ...
- median: ...
- high-score: ...

## Coaching Findings
- ...

## Recommended Training Focus
- ...
```

## Known doc caveats

The bundled references include a few Megaview doc inconsistencies. When one of them applies, mention it briefly instead of acting overconfident:

- some docs have a missing leading slash in the path
- at least one "solution update" page appears to point to the wrong conversation-label endpoint
- some solution query docs reuse canonical conversation paths instead of `origin_conversation_id`

If a doc looks inconsistent, prefer to:

1. warn the user
2. use the canonical module reference to cross-check
3. keep the final analysis chain conservative and explicit

## Examples

### Example 1

User: "帮我看 Mohammad Qasem 最近 30 天的会话评分、客户评分、会话数量，再和 StarRocks 销售额对比。"

Good behavior:

- route to `references/auth-common.md` and `references/analytics.md`
- start from the relevant `intl_analysis` business table first
- check whether `Mohammad Qasem` is still active in `vk_gl_leads_staff_team_assignment_relation` before default performance-review ranking
- resolve `Mohammad Qasem` from `data/employees.json`
- treat `staffId` as Megaview `origin_user_id`
- use `scripts/employee_performance.py`
- if the user wants the built-in sales comparison, do not ask them to restate the known default StarRocks config
- use Megaview metrics as explanatory evidence for the seller result rather than as the primary business anchor

### Example 4

User: "先按沙特 leads-to-order 转化视角，看渠道、销售团队、LP、试听完课、TCC 哪一段掉得最明显。"

Good behavior:

- route to `data/data_warehouse_metric_manual.md`, `references/analytics.md`, and `references/starrocks-routing.md`
- start from `vk_sr_intl_sa_leads_to_order_details_lv`
- expand to `vk_sr_intl_sa_lp_performance_evaluation_details_mtd_lv`, `global_tcc_to_new_conversion_aging_lv`, and the Saudi marketing / ROAS tables only when needed
- treat Megaview as the personal drill-down layer after the weak team, seller, or stage has been identified

### Example 3

User: "我不只想看 GMV，我还想看订单实付、退款和库存消耗。你会查哪张 StarRocks 表？"

Good behavior:

- route to `references/analytics.md` and `references/starrocks-routing.md`
- do not force the request into `vk_sr_intl_sa_cc_quality_monitor_da` just because it is the default sales table
- explain that the warehouse metric-definition document and the live reporting tables are not always one-to-one by table name
- choose the live order-detail route and name the verified join fields and time fields before executing
- keep the analysis anchored on `intl_analysis`, then decide whether Megaview evidence is needed

### Example 2

User: "抓 Abdelrahman 2 月几个代表性会话，给我做培训样例。"

Good behavior:

- if this request came from a seller identified in `intl_analysis`, keep that seller as the coaching subject
- route to `references/auth-common.md`, `references/conversation.md`, and `references/coaching.md`
- resolve the employee from `data/employees.json`
- use `origin_user_id -> origin_conversations/list`
- use `scripts/conversation_training_samples.py`
- summarize the chosen low / median / high samples into coaching takeaways
