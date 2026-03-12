# Coaching Samples

Read this file when the user asks to:

- fetch representative conversation content
- prepare coaching or training samples
- analyze specific calls for feedback
- compare good and bad conversations from the same employee
- extract dialogue snippets for manager coaching

## Goal

Turn a time range plus one employee into a compact coaching pack:

1. resolve the employee from `data/employees.json`
2. use `staffId` as Megaview `origin_user_id`
3. if needed, query the user record only as a presence check or metadata supplement
4. list conversations in the requested time range with `origin_user_id`
5. pick representative low / median / high score conversations
6. fetch score details, summary, and ASR preview
7. explain what should be copied or corrected in training

## Confirmed endpoints

| Purpose | Method | Endpoint |
| --- | --- | --- |
| Resolve Megaview user | `GET` | `/openapi/organization/v1/origin_users/:origin_user_id` |
| List employee conversations | `POST` | `/openapi/conversation/v1/origin_conversations/list` |
| Query conversation score | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/score_result` |
| Query conversation summary | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/summary_pro` |
| Query ASR metadata | `GET` | `/openapi/conversation/v1/conversations/:conversation_id/asr_data` |

## Suggested sample selection

Account existence rule:

- ignore `is_enable`
- do not ignore `is_delete`
- only continue the coaching workflow when the account is not deleted
- if Megaview can return conversations for the `origin_user_id`, treat that as usable evidence of account presence

When the user wants a few training examples, prefer:

- one low-score conversation
- one median or near-average conversation
- one high-score conversation

Why:

- low score shows the failure mode
- median shows the common everyday pattern
- high score shows what good looks like

If too many conversations exist, score an evenly distributed subset first instead of only the earliest or latest chunk.

## Most useful fields for coaching

### From conversation list

- `id`
- `origin_conversation_id`
- `deal_id`
- `begin_time`
- `salesman_percent`

### From score result

- `score_results[].name`
- `score_results[].score`
- `score_results[].total_score`
- `score_results[].qualified`

### From summary

Prefer these blocks when present:

- `客户档案`
- `客户诉求`
- `客户异议`
- `下一步行动`
- `客户意向度`
- `销售SOP`
- `红线质检`

### From ASR

Keep only a short preview unless the user explicitly asks for full transcript content.
For each preview line, keep:

- speaker
- timestamp
- original utterance
- translated utterance when available

## Bundled script

Use:

`scripts/conversation_training_samples.py`

It already:

- resolves the employee
- uses `origin_user_id` directly for the conversation batch query
- samples representative conversations
- fetches score, summary, and ASR preview
- returns a compact JSON package suitable for training analysis

## Output expectations

For coaching tasks, prefer this structure:

```markdown
## Employee
- ...

## Sample 1
- score: ...
- what happened: ...
- coaching point: ...

## Sample 2
- score: ...
- what happened: ...
- coaching point: ...

## Sample 3
- score: ...
- what happened: ...
- coaching point: ...

## Repeated Issues
- ...

## Training Focus
- ...
```

## Common pitfalls

- do not assume every conversation has ready ASR content
- `summary_pro` may succeed even when some score or ASR calls fail
- do not overfit training conclusions to one single low-score call; compare at least 2 to 3 samples
- `open_user_id` is not required for the employee conversation batch query when `origin_conversations/list` already supports `origin_user_id`
