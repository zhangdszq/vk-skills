#!/usr/bin/env python3
"""Resolve employees, query Megaview metrics, and compare with StarRocks sales."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from megaview_request import (
    DEFAULT_BASE_URL,
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_TIMEOUT,
    request_token,
    resolve_credentials,
)
from starrocks_query import (
    DEFAULT_STARROCKS_CONFIG_PATH,
    build_sales_query,
    load_starrocks_config,
    run_query,
)


USER_ENDPOINT = "/openapi/organization/v1/origin_users/:origin_user_id"
CONVERSATION_LIST_ENDPOINT = "/openapi/conversation/v1/origin_conversations/list"
CONVERSATION_SCORE_ENDPOINT = "/openapi/conversation/v1/conversations/:conversation_id/score_result"
DEAL_SCORE_ENDPOINT = "/openapi/crm/v1/deals/:deal_id/score_result"
DEFAULT_EMPLOYEES_FILE = Path(__file__).resolve().parent.parent / "data" / "employees.json"
MAX_WINDOW_DAYS = 7


def load_json_value(raw: str | None) -> Any:
    """Load JSON from inline JSON or @file."""
    if not raw:
        return None
    if raw.startswith("@"):
        return json.loads(Path(raw[1:]).read_text())
    return json.loads(raw)


def parse_datetime(value: str) -> datetime:
    """Parse common datetime formats used by the scripts."""
    normalized = value.strip().replace("Z", "+00:00")
    if "T" not in normalized and " " in normalized:
        normalized = normalized.replace(" ", "T", 1)
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)
    return dt


def format_api_time(value: datetime) -> str:
    """Render datetime in a Megaview-friendly format."""
    return value.strftime("%Y-%m-%d %H:%M:%S")


def iter_time_windows(begin_time: str, end_time: str) -> list[tuple[str, str]]:
    """Split a longer range into <=7-day windows."""
    start = parse_datetime(begin_time)
    end = parse_datetime(end_time)
    if end <= start:
        raise ValueError("end_time must be later than begin_time")

    windows: list[tuple[str, str]] = []
    cursor = start
    while cursor < end:
        next_cursor = min(cursor + timedelta(days=MAX_WINDOW_DAYS), end)
        windows.append((format_api_time(cursor), format_api_time(next_cursor)))
        cursor = next_cursor
    return windows


def load_employees(path: Path) -> list[dict[str, Any]]:
    """Load built-in employee mappings."""
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError("employees file must be a JSON array")
    return data


def normalize_name(value: str) -> str:
    """Normalize names for matching."""
    return " ".join(value.strip().lower().split())


def resolve_requested_employees(
    employees: list[dict[str, Any]],
    names: list[str],
    staff_ids: list[str],
) -> list[dict[str, Any]]:
    """Resolve employees by exact name, loose name, or staff id."""
    by_staff_id = {str(item["staffId"]): item for item in employees if "staffId" in item}
    by_exact_name = {
        normalize_name(str(item["staffName"])): item
        for item in employees
        if "staffName" in item
    }

    resolved: list[dict[str, Any]] = []
    seen_staff_ids: set[str] = set()

    for staff_id in staff_ids:
        item = by_staff_id.get(str(staff_id))
        if not item:
            raise ValueError(f"staffId not found in employees.json: {staff_id}")
        key = str(item["staffId"])
        if key not in seen_staff_ids:
            resolved.append(item)
            seen_staff_ids.add(key)

    for name in names:
        normalized = normalize_name(name)
        item = by_exact_name.get(normalized)
        if not item:
            candidates = [
                employee
                for employee in employees
                if normalized in normalize_name(str(employee.get("staffName", "")))
            ]
            if len(candidates) == 1:
                item = candidates[0]
            elif len(candidates) > 1:
                raise ValueError(f"Ambiguous employee name: {name}")
            else:
                raise ValueError(f"Employee name not found in employees.json: {name}")
        key = str(item["staffId"])
        if key not in seen_staff_ids:
            resolved.append(item)
            seen_staff_ids.add(key)

    if not resolved:
        raise ValueError("Provide at least one --employee-name or --staff-id")
    return resolved


def api_get(
    token: str,
    endpoint: str,
    path_params: dict[str, Any] | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Call a GET Megaview endpoint."""
    path_params = path_params or {}
    for key, value in path_params.items():
        endpoint = endpoint.replace(f":{key}", str(value))
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    response = requests.get(
        base_url.rstrip("/") + endpoint,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def api_post(
    token: str,
    endpoint: str,
    body: dict[str, Any],
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Call a POST Megaview endpoint."""
    response = requests.post(
        base_url.rstrip("/") + endpoint,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        json=body,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def extract_rule_average(payload: dict[str, Any]) -> float | None:
    """Average score_results[].score from a Megaview score payload."""
    results = payload.get("data", {}).get("score_results", [])
    scores = [item.get("score") for item in results if isinstance(item.get("score"), (int, float))]
    if not scores:
        return None
    return round(statistics.mean(scores), 4)


def fetch_user_info(token: str, origin_user_id: str) -> dict[str, Any]:
    """Fetch Megaview user info for an origin_user_id."""
    return api_get(token, USER_ENDPOINT, {"origin_user_id": origin_user_id})


def list_employee_conversations(
    token: str,
    origin_user_id: str,
    begin_time: str,
    end_time: str,
) -> list[dict[str, Any]]:
    """List all conversations for an employee across chunked windows and pages."""
    conversations: dict[str, dict[str, Any]] = {}
    for window_begin, window_end in iter_time_windows(begin_time, end_time):
        page_token = ""
        while True:
            body: dict[str, Any] = {
                "origin_user_id": origin_user_id,
                "begin_time": window_begin,
                "end_time": window_end,
                "page_size": 100,
            }
            if page_token:
                body["page_token"] = page_token
            payload = api_post(token, CONVERSATION_LIST_ENDPOINT, body)
            data = payload.get("data", {})
            for item in data.get("conversations", []):
                conv_id = str(item.get("id"))
                if conv_id and conv_id != "None":
                    conversations[conv_id] = item
            if not data.get("has_more"):
                break
            page_token = data.get("page_token", "")
            if not page_token:
                break
    return list(conversations.values())


def fetch_conversation_score(token: str, conversation_id: Any) -> float | None:
    """Fetch canonical conversation score."""
    payload = api_get(token, CONVERSATION_SCORE_ENDPOINT, {"conversation_id": conversation_id})
    return extract_rule_average(payload)


def fetch_deal_score(token: str, deal_id: Any) -> float | None:
    """Fetch canonical deal score."""
    payload = api_get(token, DEAL_SCORE_ENDPOINT, {"deal_id": deal_id})
    return extract_rule_average(payload)


def build_sales_lookup(
    join_values: list[Any],
    begin_time: str,
    end_time: str,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    table: str,
    join_field: str,
    date_field: str,
    amount_field: str | None,
    metric_expr: str | None,
    extra_where: str,
    driver: str,
) -> tuple[dict[str, float], str, str]:
    """Query StarRocks and return staff_id -> sales_amount lookup."""
    expr = (metric_expr or "").strip()
    if not expr:
        if not amount_field:
            raise ValueError("Provide sales amount field or metric expression for StarRocks")
        expr = f"SUM({amount_field})"

    sql = build_sales_query(
        staff_ids=join_values,
        table=table,
        staff_id_field=join_field,
        date_field=date_field,
        metric_expr=expr,
        begin_time=begin_time,
        end_time=end_time,
        extra_where=extra_where,
    )
    rows, driver_used = run_query(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        sql=sql,
        driver=driver,
    )
    lookup: dict[str, float] = {}
    for row in rows:
        key = str(row.get("staff_id"))
        try:
            lookup[key] = float(row.get("sales_amount", 0))
        except (TypeError, ValueError):
            lookup[key] = 0.0
    return lookup, sql, driver_used


def mean_or_none(values: list[float]) -> float | None:
    """Return rounded mean or None."""
    if not values:
        return None
    return round(statistics.mean(values), 4)


def get_metric_value(employee: dict[str, Any], path: tuple[str, str]) -> float | None:
    """Read a nested numeric metric."""
    section = employee.get(path[0], {})
    value = section.get(path[1]) if isinstance(section, dict) else None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def build_review_rankings(employees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build peer-relative review priority, suitable for manager review."""
    metrics = [
        {
            "path": ("starrocks_metrics", "sales_amount"),
            "label": "sales_amount",
            "reason": "sales_amount is near the bottom of the selected peer group",
            "weight": 0.4,
        },
        {
            "path": ("megaview_metrics", "average_conversation_score"),
            "label": "average_conversation_score",
            "reason": "average_conversation_score is near the bottom of the selected peer group",
            "weight": 0.25,
        },
        {
            "path": ("megaview_metrics", "average_customer_score"),
            "label": "average_customer_score",
            "reason": "average_customer_score is near the bottom of the selected peer group",
            "weight": 0.25,
        },
        {
            "path": ("megaview_metrics", "conversation_count"),
            "label": "conversation_count",
            "reason": "conversation_count is near the bottom of the selected peer group",
            "weight": 0.1,
        },
    ]

    review_map: dict[str, dict[str, Any]] = {
        str(employee["staffId"]): {
            "staffName": employee["staffName"],
            "staffId": employee["staffId"],
            "risk_score": 0.0,
            "reasons": [],
            "evaluated_metrics": [],
        }
        for employee in employees
    }

    for metric in metrics:
        comparable = []
        for employee in employees:
            value = get_metric_value(employee, metric["path"])
            if value is not None:
                comparable.append((employee, value))
        if len(comparable) < 2:
            continue

        comparable.sort(key=lambda item: item[1])
        denominator = max(len(comparable) - 1, 1)
        bottom_cutoff = max(1, len(comparable) // 3)

        for index, (employee, value) in enumerate(comparable):
            risk_component = 1 - (index / denominator)
            review = review_map[str(employee["staffId"])]
            review["risk_score"] += metric["weight"] * risk_component
            review["evaluated_metrics"].append(metric["label"])
            if index < bottom_cutoff:
                review["reasons"].append(f"{metric['reason']} ({value})")

    rankings: list[dict[str, Any]] = []
    for employee in employees:
        review = review_map[str(employee["staffId"])]
        conversation_count = get_metric_value(employee, ("megaview_metrics", "conversation_count")) or 0.0
        scored_conversation_count = get_metric_value(employee, ("megaview_metrics", "scored_conversation_count")) or 0.0
        if conversation_count >= 20 and scored_conversation_count >= 10 and not review["reasons"]:
            review["reasons"].append("No bottom-tier metric detected in the selected peer group")
        if len(review["evaluated_metrics"]) < 2:
            priority = "insufficient_context"
            recommendation = "manual_review_needed"
            review["reasons"].append("Too few comparable peer metrics for a reliable review priority")
        else:
            review["risk_score"] = round(review["risk_score"], 4)
            if review["risk_score"] >= 0.67:
                priority = "high"
                recommendation = "urgent_manual_review"
            elif review["risk_score"] >= 0.4:
                priority = "medium"
                recommendation = "coach_and_recheck"
            else:
                priority = "low"
                recommendation = "stable"
        rankings.append(
            {
                "staffName": review["staffName"],
                "staffId": review["staffId"],
                "priority": priority,
                "risk_score": review["risk_score"],
                "recommendation": recommendation,
                "reasons": review["reasons"][:4],
                "guardrail": "Use for human performance review only, not automatic elimination.",
            }
        )

    def sort_key(item: dict[str, Any]) -> tuple[int, float]:
        priority_order = {
            "high": 0,
            "medium": 1,
            "low": 2,
            "insufficient_context": 3,
        }
        return (priority_order.get(item["priority"], 9), -item["risk_score"])

    return sorted(rankings, key=sort_key)


def compare_employees(employees: list[dict[str, Any]]) -> list[str]:
    """Generate lightweight comparison notes across employees."""
    notes: list[str] = []
    if len(employees) < 2:
        return notes

    by_sales = sorted(
        employees,
        key=lambda item: item.get("starrocks_metrics", {}).get("sales_amount", 0.0),
        reverse=True,
    )
    top_sales = by_sales[0]
    notes.append(
        f"Top sales_amount: {top_sales['staffName']} ({top_sales.get('starrocks_metrics', {}).get('sales_amount', 0.0)})"
    )

    scored = [
        item for item in employees
        if item.get("megaview_metrics", {}).get("average_conversation_score") is not None
    ]
    if scored:
        best_conv = sorted(
            scored,
            key=lambda item: item["megaview_metrics"]["average_conversation_score"],
            reverse=True,
        )[0]
        notes.append(
            "Highest average_conversation_score: "
            f"{best_conv['staffName']} ({best_conv['megaview_metrics']['average_conversation_score']})"
        )
    return notes


def write_output(payload: dict[str, Any], output_path: str | None) -> None:
    """Write JSON result to stdout and optional file."""
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output_path:
        Path(output_path).write_text(text + "\n")
    print(text)


def apply_starrocks_defaults(args: argparse.Namespace) -> tuple[argparse.Namespace, str]:
    """Fill missing StarRocks args from the bundled config file."""
    config_path = Path(args.starrocks_config_file).expanduser()
    config = load_starrocks_config(config_path)
    field_map = {
        "starrocks_host": "host",
        "starrocks_port": "port",
        "starrocks_user": "user",
        "starrocks_password": "password",
        "starrocks_database": "database",
        "sales_table": "sales_table",
        "sales_join_key": "sales_join_key",
        "sales_join_field": "sales_join_field",
        "sales_date_field": "sales_date_field",
        "sales_amount_field": "sales_amount_field",
        "sales_metric_expr": "sales_metric_expr",
        "sales_extra_where": "sales_extra_where",
        "starrocks_driver": "driver",
    }
    for arg_name, config_name in field_map.items():
        current_value = getattr(args, arg_name, None)
        if current_value in (None, ""):
            config_value = config.get(config_name)
            if config_value not in (None, ""):
                setattr(args, arg_name, config_value)
    return args, str(config_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Megaview employee metrics with StarRocks sales.")
    parser.add_argument("--employees-file", default=str(DEFAULT_EMPLOYEES_FILE))
    parser.add_argument("--employee-name", action="append", default=[])
    parser.add_argument("--staff-id", action="append", default=[])
    parser.add_argument("--begin-time", required=True)
    parser.add_argument("--end-time", required=True)
    parser.add_argument("--app-key", default=os.getenv("MEGAVIEW_APP_KEY"))
    parser.add_argument("--app-secret", default=os.getenv("MEGAVIEW_APP_SECRET"))
    parser.add_argument(
        "--megaview-credentials-file",
        default=os.getenv("MEGAVIEW_CREDENTIALS_FILE", str(DEFAULT_CREDENTIALS_PATH)),
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument(
        "--max-score-fetches",
        type=int,
        default=int(os.getenv("MEGAVIEW_ANALYTICS_MAX_SCORE_FETCHES", "200")),
    )
    parser.add_argument("--starrocks-host", default=os.getenv("STARROCKS_HOST"))
    parser.add_argument("--starrocks-port", type=int, default=int(os.getenv("STARROCKS_PORT", "9030")))
    parser.add_argument("--starrocks-user", default=os.getenv("STARROCKS_USER"))
    parser.add_argument("--starrocks-password", default=os.getenv("STARROCKS_PASSWORD"))
    parser.add_argument("--starrocks-database", default=os.getenv("STARROCKS_DATABASE"))
    parser.add_argument(
        "--starrocks-config-file",
        default=os.getenv("STARROCKS_CONFIG_FILE", str(DEFAULT_STARROCKS_CONFIG_PATH)),
    )
    parser.add_argument("--sales-table", default=os.getenv("STARROCKS_SALES_TABLE"))
    parser.add_argument(
        "--sales-join-key",
        choices=["staffId", "staffName"],
        default=os.getenv("STARROCKS_JOIN_KEY", "staffName"),
    )
    parser.add_argument(
        "--sales-join-field",
        default=os.getenv("STARROCKS_JOIN_FIELD"),
    )
    parser.add_argument("--sales-date-field", default=os.getenv("STARROCKS_SALES_DATE_FIELD"))
    parser.add_argument("--sales-amount-field", default=os.getenv("STARROCKS_SALES_AMOUNT_FIELD"))
    parser.add_argument("--sales-metric-expr", default=os.getenv("STARROCKS_SALES_METRIC_EXPR"))
    parser.add_argument("--sales-extra-where", default=os.getenv("STARROCKS_SALES_EXTRA_WHERE", ""))
    parser.add_argument(
        "--starrocks-driver",
        choices=["auto", "pymysql", "cli"],
        default=os.getenv("STARROCKS_DRIVER", "auto"),
    )
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()
    args, resolved_starrocks_config_file = apply_starrocks_defaults(args)

    app_key, app_secret, megaview_credentials_file = resolve_credentials(
        args.app_key,
        args.app_secret,
        args.megaview_credentials_file,
    )
    if not args.sales_join_field:
        args.sales_join_field = (
            "staff_name"
            if args.sales_join_key == "staffName"
            else os.getenv("STARROCKS_STAFF_ID_FIELD", "staff_id")
        )
    missing_megaview = [key for key, value in {"app_key": app_key, "app_secret": app_secret}.items() if not value]
    missing_starrocks = [
        key
        for key, value in {
            "starrocks_host": args.starrocks_host,
            "starrocks_user": args.starrocks_user,
            "starrocks_password": args.starrocks_password,
            "starrocks_database": args.starrocks_database,
            "sales_table": args.sales_table,
            "sales_date_field": args.sales_date_field,
        }.items()
        if not value
    ]
    if missing_megaview or missing_starrocks:
        write_output(
            {
                "ok": False,
                "stage": "config",
                "missing_megaview": missing_megaview,
                "missing_starrocks": missing_starrocks,
                "starrocks_config_file": resolved_starrocks_config_file,
            },
            args.out,
        )
        return 2

    try:
        employees = load_employees(Path(args.employees_file))
        selected = resolve_requested_employees(employees, args.employee_name, args.staff_id)
        auth_json = request_token(args.base_url, app_key, app_secret, args.timeout)
        token = auth_json.get("data", {}).get("app_access_token", "")
        if auth_json.get("code") != 0 or not token:
            raise RuntimeError("Megaview token request failed")

        sales_join_values = [
            item["staffId"] if args.sales_join_key == "staffId" else item["staffName"] for item in selected
        ]
        sales_lookup, sales_sql, sales_driver = build_sales_lookup(
            join_values=sales_join_values,
            begin_time=args.begin_time,
            end_time=args.end_time,
            host=args.starrocks_host,
            port=args.starrocks_port,
            user=args.starrocks_user,
            password=args.starrocks_password,
            database=args.starrocks_database,
            table=args.sales_table,
            join_field=args.sales_join_field,
            date_field=args.sales_date_field,
            amount_field=args.sales_amount_field,
            metric_expr=args.sales_metric_expr,
            extra_where=args.sales_extra_where,
            driver=args.starrocks_driver,
        )

        employee_outputs: list[dict[str, Any]] = []
        for employee in selected:
            staff_name = employee["staffName"]
            staff_id = employee["staffId"]
            sales_lookup_key = str(staff_id if args.sales_join_key == "staffId" else staff_name)
            notes: list[str] = []
            user_info: dict[str, Any] = {}
            open_user_id = None
            try:
                user_payload = fetch_user_info(token, str(staff_id))
                user_info = user_payload.get("data", {}).get("user", {})
                open_user_id = user_info.get("open_user_id")
                if not open_user_id:
                    notes.append("Megaview user lookup returned no open_user_id, but conversation listing can continue with origin_user_id.")
            except Exception as exc:  # noqa: BLE001
                notes.append(f"Megaview user lookup failed, continue with origin_user_id conversation query: {exc}")

            conversations = list_employee_conversations(
                token=token,
                origin_user_id=str(staff_id),
                begin_time=args.begin_time,
                end_time=args.end_time,
            )
            conversation_count = len(conversations)

            conversation_scores: list[float] = []
            skipped_conversation_scores = 0
            for item in conversations[: args.max_score_fetches]:
                try:
                    score = fetch_conversation_score(token, item.get("id"))
                    if score is None:
                        skipped_conversation_scores += 1
                    else:
                        conversation_scores.append(score)
                except Exception:  # noqa: BLE001
                    skipped_conversation_scores += 1
            if conversation_count > args.max_score_fetches:
                notes.append(
                    f"Conversation score fetch capped at {args.max_score_fetches} items for performance."
                )

            deal_ids = []
            seen_deals: set[str] = set()
            for item in conversations:
                deal_id = item.get("deal_id")
                if deal_id is None:
                    continue
                deal_key = str(deal_id)
                if deal_key not in seen_deals:
                    seen_deals.add(deal_key)
                    deal_ids.append(deal_id)

            customer_scores: list[float] = []
            skipped_customer_scores = 0
            for deal_id in deal_ids[: args.max_score_fetches]:
                try:
                    score = fetch_deal_score(token, deal_id)
                    if score is None:
                        skipped_customer_scores += 1
                    else:
                        customer_scores.append(score)
                except Exception:  # noqa: BLE001
                    skipped_customer_scores += 1
            if len(deal_ids) > args.max_score_fetches:
                notes.append(
                    f"Customer score fetch capped at {args.max_score_fetches} unique deals for performance."
                )

            employee_outputs.append(
                {
                    "staffName": staff_name,
                    "staffId": staff_id,
                    "megaview_mapping": {
                        "origin_user_id": str(staff_id),
                        "open_user_id": str(open_user_id),
                    },
                    "megaview_user": user_info,
                    "megaview_metrics": {
                        "conversation_count": conversation_count,
                        "average_conversation_score": mean_or_none(conversation_scores),
                        "scored_conversation_count": len(conversation_scores),
                        "skipped_conversation_scores": skipped_conversation_scores,
                        "unique_deal_count": len(deal_ids),
                        "average_customer_score": mean_or_none(customer_scores),
                        "scored_customer_count": len(customer_scores),
                        "skipped_customer_scores": skipped_customer_scores,
                    },
                    "starrocks_metrics": {
                        "sales_amount": sales_lookup.get(sales_lookup_key, 0.0),
                    },
                    "notes": notes,
                }
            )

        review_rankings = build_review_rankings(employee_outputs)
        review_lookup = {str(item["staffId"]): item for item in review_rankings}
        for employee in employee_outputs:
            employee["performance_review"] = review_lookup.get(
                str(employee["staffId"]),
                {
                    "priority": "insufficient_context",
                    "risk_score": 0.0,
                    "recommendation": "manual_review_needed",
                    "reasons": ["Too few peer metrics for a reliable review priority"],
                    "guardrail": "Use for human performance review only, not automatic elimination.",
                },
            )

        payload = {
            "ok": True,
            "request": {
                "employee_names": args.employee_name,
                "staff_ids": args.staff_id,
                "begin_time": args.begin_time,
                "end_time": args.end_time,
                "employees_file": str(Path(args.employees_file).resolve()),
                "megaview_credentials_file": megaview_credentials_file,
                "starrocks_config_file": resolved_starrocks_config_file,
            },
            "megaview": {
                "user_endpoint": USER_ENDPOINT,
                "conversation_list_endpoint": CONVERSATION_LIST_ENDPOINT,
                "conversation_score_endpoint": CONVERSATION_SCORE_ENDPOINT,
                "deal_score_endpoint": DEAL_SCORE_ENDPOINT,
            },
            "starrocks": {
                "host": args.starrocks_host,
                "port": args.starrocks_port,
                "database": args.starrocks_database,
                "join_key": args.sales_join_key,
                "join_field": args.sales_join_field,
                "driver": sales_driver,
                "sales_sql": sales_sql,
                "config_file": resolved_starrocks_config_file,
            },
            "employees": employee_outputs,
            "comparison": {
                "notes": compare_employees(employee_outputs),
                "review_priority_ranking": review_rankings,
                "guardrail": "Use this ranking for manager review, coaching prioritization, and manual performance review only. Do not treat it as an automatic firing decision.",
            },
        }
        write_output(payload, args.out)
        return 0
    except Exception as exc:  # noqa: BLE001
        write_output(
            {
                "ok": False,
                "stage": "runtime",
                "error": str(exc),
            },
            args.out,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
