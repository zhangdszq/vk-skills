# Organization Module

Read this file when the task is about departments or users.

## When to use this module

Use this module when the user is working with:

- departments
- sales users
- organization sync
- `department_id`, `open_user_id`
- `origin_department_id`, `origin_user_id`

## Routing rule

- If the user already has Megaview IDs, use canonical organization endpoints.
- If the user only has third-party IDs, prefer solution or origin endpoints.

## Canonical department endpoints

| Task | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| Create department | `POST` | `/openapi/organization/v1/departments` | Uses `uniq_token` semantics through the department object, not `origin_department_id` |
| List departments | `GET` | `/openapi/organization/v1/departments/list` | Returns the department tree / org info list |
| Query single department | `GET` | `/openapi/organization/v1/departments/:department_id` | Requires Megaview `department_id` |
| Update department | `PUT` | `/openapi/organization/v1/departments/:department_id` | Requires Megaview `department_id` |

### Create department: confirmed core fields

- `name` required
- `parent_department_id` required
- `lead_open_user_id` optional
- `uniq_token` required

## Canonical user endpoints

| Task | Method | Endpoint | Notes |
| --- | --- | --- | --- |
| Create user | `POST` | `/openapi/organization/v1/users` | Creates a Megaview sales user |
| Batch query users | `POST` | `/openapi/organization/v1/users/list` | Query by `tels` or `emails`, max 100 items |
| Map uniq token to uid | `POST` | `/openapi/organization/v1/users/uniq_token_to_uid` | Useful when the caller only has third-party unique IDs; body uses `uniq_tokens` |
| Query single user | `GET` | `/openapi/organization/v1/users/:open_user_id` | Requires Megaview `open_user_id` |
| Update user | `PUT` | `/openapi/organization/v1/users/:open_user_id` | Requires Megaview `open_user_id` |
| Dimission user | `POST` | `/openapi/organization/v1/users/dimission/:open_user_id` | Offboards a Megaview user |

### Create user: confirmed core fields

- `uniq_token` required
- `name` required
- `login_method` required, one of `tel`, `email`, `off-limits`
- `tel` required when `login_method == "tel"`
- `email` required when `login_method == "email"`
- `main_workspace_id` optional
- `main_department_id` optional

### Map uniq token to uid: confirmed fields

- request body uses `uniq_tokens`
- response includes `users[].uniq_token`
- response includes `users[].open_user_id`

## Origin or solution organization endpoints

Use these when the task is keyed by the user's own system IDs.

| Task | Method | Endpoint |
| --- | --- | --- |
| Query department by third-party ID | `GET` | `/openapi/organization/v1/origin_departments/:origin_department_id` |
| Update department by third-party ID | `PUT` | `/openapi/organization/v1/origin_departments/:origin_department_id` |
| Query user by third-party ID | `GET` | `/openapi/organization/v1/origin_users/:origin_user_id` |
| Update user by third-party ID | `PUT` | `/openapi/organization/v1/origin_users/:origin_user_id` |
| Dimission user by third-party ID | `POST` | `/openapi/organization/v1/origin_users/dimission/:origin_user_id` |

## Asking strategy

If the user wants a live request, ask only for the smallest missing set:

### For department create

- department name
- parent department identifier
- whether a department owner already exists in Megaview
- unique token from the user's system

### For user create

- user name
- login method
- login value (`tel` or `email` if needed)
- main department if they care about org placement
- unique token from the user's system

### For origin-based org queries

- exact third-party ID value
- whether they want read-only query or actual mutation

## Common pitfalls

- `open_user_id` is a Megaview identifier, not a phone number and not an `origin_user_id`
- in this workspace's built-in employee mapping, `data/employees.json.staffId` is already the exact `origin_user_id` string to use against `/origin_users/:origin_user_id`
- batch query users requires at least one non-empty list among `tels` or `emails`
- dimission is a state-changing call; do not draft it if the user only asked to inspect data
- for this workspace's employee analytics and coaching flows, ignore `is_enable` but do not ignore `is_delete`; only keep the account in scope when it exists and is not deleted
