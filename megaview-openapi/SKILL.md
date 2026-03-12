---
name: megaview-openapi
description: Use this skill whenever the user wants Megaview-based sales analysis, employee performance comparison, session score and customer score analysis, conversation count analysis, StarRocks GMV comparison, training samples, coaching calls, transcript snippets, manager coaching material, or wants to know who is most at risk and should enter performance review first. Use it when the user wants to compare employee quality with GMV, analyze one or more sellers, fetch representative conversations for coaching, or build a review-priority list for underperformers. This skill is specifically for sales performance analysis and coaching workflows built on Megaview plus StarRocks, not for general-purpose Megaview API documentation, request drafting, or ad-hoc endpoint execution.
---

# 销售能力分析

## What this skill does

Use this skill to turn a natural-language sales analysis request into one of two outcomes:

1. Analyze employee performance by combining Megaview metrics with StarRocks sales data.
2. Fetch representative conversation samples for coaching or training.

This skill is designed to reduce these common failure modes:

- confusing Megaview employee IDs with the built-in `employees.json` mapping
- using the wrong StarRocks join rule or wrong GMV table defaults
- drawing coaching conclusions from isolated calls instead of representative samples

## Scope boundary

This skill is only for:

- employee performance analysis
- sales comparison with Megaview and StarRocks
- representative conversation selection
- coaching and training analysis
- performance risk review and underperformer prioritization

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

- 查某个销售/员工的数据表现
- 对比会话评分、客户评分、GMV
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
3. Read `references/org.md`, `references/crm.md`, or `references/conversation.md` only when you need to verify the underlying analytics chain or debug a metric source.

This skill is no longer a general Megaview API router. Read only the files needed for analysis or coaching.

## Intent routing

Route the task before writing anything.

### 1. Employee analytics

Use this path when the user wants:

- employee or staff performance
- session score and customer score by employee
- conversation count by employee
- Megaview vs StarRocks sales comparison
- ranking or comparing multiple employees
- who looks most at risk among a selected peer group
- who should enter performance review first

Deliver:

- the resolved employees and IDs
- the Megaview metrics used
- the StarRocks sales metric used
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
2. resolve employees from the built-in mapping
3. use the bundled default StarRocks config when sales comparison is requested
4. ask only for business information that is actually missing for analysis, such as employee identity or time range

Important identifier rules:

- `open_user_id` and `origin_user_id` are not interchangeable
- `conversation_id` and `origin_conversation_id` are not interchangeable
- in this skill's built-in analytics flow, `data/employees.json` uses `staffId` as the shared key:
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
   - if the user wants the built-in sales comparison, use the bundled StarRocks defaults first
   - only ask about StarRocks connection info or table mapping when the user explicitly wants a different table / metric / database
6. If the task is coaching or training, verify that you have:
   - exactly which employee to analyze
   - a time range
   - whether the user wants summary only or transcript snippets too

For employee analytics, use:

```bash
python3 "/Users/zhang/.claude/skills/megaview-openapi/scripts/employee_performance.py" \
  --employee-name "王志全" \
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

So under the normal workflow, do not stop to ask for StarRocks config again unless the user wants to override these defaults.

For coaching samples, use:

```bash
python3 "/Users/zhang/.claude/skills/megaview-openapi/scripts/conversation_training_samples.py" \
  --employee-name "Abdelrahman Al-Hamdan" \
  --begin-time "2026-02-01 00:00:00" \
  --end-time "2026-03-01 00:00:00"
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

User: "帮我看王志全最近 30 天的会话评分、客户评分、会话数量，再和 StarRocks 销售额对比。"

Good behavior:

- route to `references/auth-common.md` and `references/analytics.md`
- resolve `王志全` from `data/employees.json`
- treat `staffId` as Megaview `origin_user_id`
- use `scripts/employee_performance.py`
- if the user wants the built-in sales comparison, do not ask them to restate the known default StarRocks config

### Example 2

User: "抓 Abdelrahman 2 月几个代表性会话，给我做培训样例。"

Good behavior:

- route to `references/auth-common.md`, `references/conversation.md`, and `references/coaching.md`
- resolve the employee from `data/employees.json`
- use `origin_user_id -> origin_conversations/list`
- use `scripts/conversation_training_samples.py`
- summarize the chosen low / median / high samples into coaching takeaways
