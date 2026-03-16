# CRM Module

Read this file when the task is about customer remark names, contacts, deals, customer summaries, or scores.

## Entity vocabulary

Megaview CRM docs distinguish three common entity types:

- `account`: customer remark name / customer alias entity
- `contact`: person
- `deal`: customer / opportunity entity

## Routing rule

- If the user already has `account_id`, `contact_id`, or `deal_id`, use canonical CRM endpoints.
- If the user only has `origin_account_id`, `origin_contact_id`, or `origin_deal_id`, prefer the solution or origin endpoints.

## Canonical account endpoints


| Task                        | Method | Endpoint                                            |
| --------------------------- | ------ | --------------------------------------------------- |
| Create account              | `POST` | `/openapi/crm/v1/accounts`                          |
| Query account custom fields | `GET`  | `/openapi/crm/v1/accounts/customer_fields`          |
| Query single account        | `GET`  | `/openapi/crm/v1/accounts/:account_id`              |
| Update account              | `PUT`  | `/openapi/crm/v1/accounts/:account_id`              |
| Bind contact to account     | `PUT`  | `/openapi/crm/v1/accounts/:account_id/bind_contact` |
| List account contacts       | `POST` | `/openapi/crm/v1/accounts/:account_id/contacts`     |


### Create account: confirmed core fields

- `uniq_token` required
- `name` required
- `follow_up_by` required, expects Megaview `open_user_id`
- `customize_fields` optional

## Canonical contact endpoints


| Task                        | Method | Endpoint                                   |
| --------------------------- | ------ | ------------------------------------------ |
| Create contact              | `POST` | `/openapi/crm/v1/contacts`                 |
| Query single contact        | `GET`  | `/openapi/crm/v1/contacts/:contact_id`     |
| Query contact custom fields | `GET`  | `/openapi/crm/v1/contacts/customer_fields` |
| Update contact              | `PUT`  | `/openapi/crm/v1/contacts/:contact_id`     |


### Create contact: confirmed core fields

- `uniq_token` required
- `name` required
- `tel` optional
- `email` optional
- `position` optional
- `account_id` optional
- `customize_fields` optional

## Canonical deal endpoints


| Task                     | Method | Endpoint                                      |
| ------------------------ | ------ | --------------------------------------------- |
| Create deal              | `POST` | `/openapi/crm/v1/deals`                       |
| Update deal              | `PUT`  | `/openapi/crm/v1/deals/:deal_id`              |
| Query single deal        | `GET`  | `/openapi/crm/v1/deals/:deal_id`              |
| Batch query deals        | `POST` | `/openapi/crm/v1/deals/list`                  |
| Bind contact to deal     | `PUT`  | `/openapi/crm/v1/deals/:deal_id/bind_contact` |
| Query deal custom fields | `GET`  | `/openapi/crm/v1/deals/customer_fields`       |
| Query deal summary       | `GET`  | `/openapi/crm/v1/deals/:deal_id/summary_pro`  |
| Query deal score         | `GET`  | `/openapi/crm/v1/deals/:deal_id/score_result` |


### Create deal: confirmed core fields

- `uniq_token` required
- `name` required
- `type` required, docs say current valid value is `1`
- `owner` required, expects Megaview `open_user_id`
- `amount` required
- `plan_to_deal_at` required
- `deal_stage` optional

## Origin or solution CRM endpoints

Use these when the task starts from third-party business IDs.


| Task                                    | Method | Endpoint                                                          |
| --------------------------------------- | ------ | ----------------------------------------------------------------- |
| Query account by third-party ID         | `GET`  | `/openapi/crm/v1/origin_accounts/:origin_account_id`              |
| List contacts under third-party account | `POST` | `/openapi/crm/v1/origin_accounts/:origin_account_id/contacts`     |
| Bind contact to third-party account     | `PUT`  | `/openapi/crm/v1/origin_accounts/:origin_account_id/bind_contact` |
| Query contact by third-party ID         | `GET`  | `/openapi/crm/v1/origin_contacts/:origin_contact_id`              |
| Update contact by third-party ID        | `PUT`  | `/openapi/crm/v1/origin_contacts/:origin_contact_id`              |
| Query deal by third-party ID            | `GET`  | `/openapi/crm/v1/origin_deals/:origin_deal_id`                    |
| Update deal by third-party ID           | `PUT`  | `/openapi/crm/v1/origin_deals/:origin_deal_id`                    |
| Bind contact to third-party deal        | `PUT`  | `/openapi/crm/v1/origin_deals/:origin_deal_id/bind_contact`       |
| Query third-party deal summary          | `GET`  | `/openapi/crm/v1/origin_deals/:origin_deal_id/summary_pro`        |
| Query third-party deal score            | `GET`  | `/openapi/crm/v1/origin_deals/:origin_deal_id/score_result`       |


## What to ask for

### If the user wants to create a deal

Ask for:

- customer name
- owner identity, and whether they have `open_user_id` or only `origin_user_id`
- transaction amount
- planned close time
- whether they want canonical create or solution create

### If the user wants to query score or summary

Ask only for:

- `deal_id` or `origin_deal_id`
- whether they want score, summary, or both

### If the user wants to bind a contact

Ask for:

- which parent entity is the source of truth: account or deal
- Megaview IDs or origin IDs
- target contact identifier

## Common pitfalls

- `follow_up_by` and `owner` require Megaview `open_user_id`, not `origin_user_id`
- account, contact, and deal custom fields are different endpoints; do not mix them
- the CRM account update doc has a missing leading slash; use `/openapi/crm/v1/accounts/:account_id`

