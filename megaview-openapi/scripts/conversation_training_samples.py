#!/usr/bin/env python3
"""Fetch representative Megaview conversations for coaching and training."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from pathlib import Path
from typing import Any

import requests

from employee_performance import (
    DEFAULT_EMPLOYMENT_TABLE,
    DEFAULT_EMPLOYEES_FILE,
    api_get,
    build_database_employee_lookup,
    extract_rule_average,
    fetch_user_info,
    list_employee_conversations,
    load_employees,
    resolve_requested_employees,
)
from megaview_request import (
    DEFAULT_BASE_URL,
    DEFAULT_CREDENTIALS_PATH,
    DEFAULT_TIMEOUT,
    request_token,
    resolve_credentials,
)
from starrocks_query import DEFAULT_STARROCKS_CONFIG_PATH, load_starrocks_config


DEFAULT_SCORE_SCAN_LIMIT = 120
DEFAULT_ASR_PREVIEW_LINES = 12
IGNORED_SUMMARY_CONTENT = {"", "未提及"}


def default_database_employee_status() -> dict[str, Any]:
    """Return a stable fallback for database employee scope."""
    return {
        "status": "unknown",
        "active_first_applied": True,
        "matched_row_count": 0,
        "active_row_count": 0,
        "preferred_record": None,
    }


def apply_optional_starrocks_defaults(args: argparse.Namespace) -> tuple[argparse.Namespace, str]:
    """Fill optional StarRocks args from the bundled config when available."""
    config_path = Path(args.starrocks_config_file).expanduser()
    if not config_path.exists():
        return args, str(config_path)

    config = load_starrocks_config(config_path)
    field_map = {
        "starrocks_host": "host",
        "starrocks_port": "port",
        "starrocks_user": "user",
        "starrocks_password": "password",
        "starrocks_database": "database",
        "starrocks_driver": "driver",
    }
    for arg_name, config_name in field_map.items():
        current_value = getattr(args, arg_name, None)
        if current_value in (None, ""):
            config_value = config.get(config_name)
            if config_value not in (None, ""):
                setattr(args, arg_name, config_value)
    return args, str(config_path)


def evenly_sample(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Pick evenly distributed items from a longer list."""
    if limit <= 0 or len(items) <= limit:
        return items

    if limit == 1:
        return [items[len(items) // 2]]

    chosen_indices: list[int] = []
    for index in range(limit):
        ratio = index / (limit - 1)
        selected = round(ratio * (len(items) - 1))
        if selected not in chosen_indices:
            chosen_indices.append(selected)

    return [items[idx] for idx in chosen_indices]


def summarize_score_result(payload: dict[str, Any]) -> dict[str, Any]:
    """Keep the most useful score details for training."""
    score_results = payload.get("data", {}).get("score_results", [])
    return {
        "average_score": extract_rule_average(payload),
        "score_results": [
            {
                "name": item.get("name"),
                "score": item.get("score"),
                "total_score": item.get("total_score"),
                "qualified": item.get("qualified"),
            }
            for item in score_results
        ],
    }


def summarize_summary_result(payload: dict[str, Any], max_items: int = 8) -> dict[str, Any]:
    """Extract compact highlights from Megaview summary results."""
    result = payload.get("data", {})
    highlights: list[dict[str, Any]] = []
    for block in result.get("summary_result", []):
        answers = block.get("answers", [])
        if not answers:
            continue
        first_answer = answers[0]
        content = str(first_answer.get("content", "")).strip()
        if content in IGNORED_SUMMARY_CONTENT:
            continue
        highlights.append(
            {
                "name": block.get("name"),
                "question_name": block.get("question_name"),
                "content": content,
                "contexts": [
                    {
                        "speaker_type": ctx.get("speaker_type"),
                        "speaker_name": ctx.get("speaker_name"),
                        "content": ctx.get("content"),
                    }
                    for ctx in first_answer.get("context", [])[:3]
                ],
            }
        )
        if len(highlights) >= max_items:
            break

    return {
        "summary_status": result.get("summary_status"),
        "highlights": highlights,
    }


def safe_api_get(token: str, endpoint: str) -> tuple[dict[str, Any], str | None]:
    """Fetch a Megaview resource without aborting the whole script."""
    try:
        return api_get(token, endpoint), None
    except Exception as exc:  # noqa: BLE001
        return {}, str(exc)


def summarize_asr_data(payload: dict[str, Any], preview_lines: int) -> dict[str, Any]:
    """Download ASR content and keep a short preview."""
    meta = payload.get("data", {})
    asr_file_url = meta.get("asr_file_url")
    if not asr_file_url:
        return {
            "conversation_type": meta.get("conversation_type"),
            "preview": [],
            "note": "No asr_file_url returned.",
        }

    try:
        transcript = requests.get(asr_file_url, timeout=30).json()
    except Exception as exc:  # noqa: BLE001
        return {
            "conversation_type": meta.get("conversation_type"),
            "preview": [],
            "note": f"Failed to load ASR transcript: {exc}",
        }

    preview: list[dict[str, Any]] = []
    if isinstance(transcript, list):
        for item in transcript[:preview_lines]:
            preview.append(
                {
                    "begin_time": item.get("begin_time"),
                    "speaker_type": item.get("entity_type"),
                    "speaker_name": item.get("name"),
                    "content": item.get("content"),
                    "content_en": item.get("content_en"),
                }
            )

    return {
        "conversation_type": meta.get("conversation_type"),
        "preview": preview,
    }


def select_representative_samples(
    scored_conversations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Choose low / median / high score conversations."""
    if not scored_conversations:
        return []

    ordered = sorted(scored_conversations, key=lambda item: item["average_score"])
    target_median = statistics.median(item["average_score"] for item in ordered)

    selections = [
        ("low", ordered[0]),
        ("median", min(ordered, key=lambda item: abs(item["average_score"] - target_median))),
        ("high", ordered[-1]),
    ]

    unique: list[dict[str, Any]] = []
    seen_ids: set[Any] = set()
    for bucket, item in selections:
        if item["conversation_id"] in seen_ids:
            continue
        unique.append({"bucket": bucket, **item})
        seen_ids.add(item["conversation_id"])
    return unique


def write_output(payload: dict[str, Any], output_path: str | None) -> None:
    """Write JSON result to stdout and optional file."""
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output_path:
        Path(output_path).write_text(text + "\n")
    print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch representative Megaview conversation samples.")
    parser.add_argument("--employees-file", default=str(DEFAULT_EMPLOYEES_FILE))
    parser.add_argument("--employee-name", action="append", default=[])
    parser.add_argument("--staff-id", action="append", default=[])
    parser.add_argument("--begin-time", required=True)
    parser.add_argument("--end-time", required=True)
    parser.add_argument("--app-key")
    parser.add_argument("--app-secret")
    parser.add_argument(
        "--megaview-credentials-file",
        default=str(DEFAULT_CREDENTIALS_PATH),
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--score-scan-limit", type=int, default=DEFAULT_SCORE_SCAN_LIMIT)
    parser.add_argument("--asr-preview-lines", type=int, default=DEFAULT_ASR_PREVIEW_LINES)
    parser.add_argument(
        "--starrocks-config-file",
        default=os.getenv("STARROCKS_CONFIG_FILE", str(DEFAULT_STARROCKS_CONFIG_PATH)),
    )
    parser.add_argument("--starrocks-host", default=os.getenv("STARROCKS_HOST"))
    parser.add_argument("--starrocks-port", type=int, default=int(os.getenv("STARROCKS_PORT", "9030")))
    parser.add_argument("--starrocks-user", default=os.getenv("STARROCKS_USER"))
    parser.add_argument("--starrocks-password", default=os.getenv("STARROCKS_PASSWORD"))
    parser.add_argument("--starrocks-database", default=os.getenv("STARROCKS_DATABASE"))
    parser.add_argument(
        "--starrocks-driver",
        choices=["auto", "pymysql", "cli"],
        default=os.getenv("STARROCKS_DRIVER", "auto"),
    )
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()
    args, resolved_starrocks_config_file = apply_optional_starrocks_defaults(args)

    try:
        app_key, app_secret, credentials_file = resolve_credentials(
            args.app_key,
            args.app_secret,
            args.megaview_credentials_file,
        )
        if not app_key or not app_secret:
            raise ValueError("Missing Megaview credentials")

        employees = load_employees(Path(args.employees_file))
        selected = resolve_requested_employees(employees, args.employee_name, args.staff_id)
        if len(selected) != 1:
            raise ValueError("Training sample extraction requires exactly one employee")

        auth_json = request_token(args.base_url, app_key, app_secret, args.timeout)
        token = auth_json.get("data", {}).get("app_access_token", "")
        if auth_json.get("code") != 0 or not token:
            raise RuntimeError("Megaview token request failed")

        employee = selected[0]
        origin_user_id = str(employee["staffId"])
        notes: list[str] = []
        database_employee = default_database_employee_status()
        database_employee_sql = None
        database_employee_driver = None
        missing_starrocks = [
            key
            for key, value in {
                "starrocks_host": args.starrocks_host,
                "starrocks_user": args.starrocks_user,
                "starrocks_password": args.starrocks_password,
                "starrocks_database": args.starrocks_database,
            }.items()
            if not value
        ]
        if missing_starrocks:
            notes.append(
                "Database employee status check skipped because optional StarRocks connection info is incomplete."
            )
        else:
            try:
                database_lookup, database_employee_sql, database_employee_driver = build_database_employee_lookup(
                    employees=[employee],
                    host=args.starrocks_host,
                    port=args.starrocks_port,
                    user=args.starrocks_user,
                    password=args.starrocks_password,
                    database=args.starrocks_database,
                    driver=args.starrocks_driver,
                )
                database_employee = database_lookup.get(origin_user_id, default_database_employee_status())
                if database_employee["status"] == "active":
                    notes.append("Database employee status: active.")
                elif database_employee["status"] == "inactive":
                    notes.append(
                        "Database employee status: inactive. Keep this coaching pack as historical review because the employee was explicitly requested."
                    )
                else:
                    notes.append(
                        "Database employee status: unknown. Continue with Megaview evidence, but treat historical employment context carefully."
                    )
            except Exception as exc:  # noqa: BLE001
                notes.append(f"Database employee status check failed and was skipped: {exc}")

        user_info: dict[str, Any] = {}
        open_user_id = None
        try:
            user_payload = fetch_user_info(token, origin_user_id)
            user_info = user_payload.get("data", {}).get("user", {})
            open_user_id = user_info.get("open_user_id")
        except Exception as exc:  # noqa: BLE001
            user_info = {}
            open_user_id = None
            notes.append(f"Megaview user lookup failed, continue with origin_user_id conversation query: {exc}")

        conversations = list_employee_conversations(
            token=token,
            origin_user_id=origin_user_id,
            begin_time=args.begin_time,
            end_time=args.end_time,
        )
        sampled_candidates = evenly_sample(conversations, args.score_scan_limit)

        scored_candidates: list[dict[str, Any]] = []
        for conversation in sampled_candidates:
            conversation_id = conversation.get("id")
            if conversation_id is None:
                continue
            try:
                score_payload = api_get(
                    token,
                    f"/openapi/conversation/v1/conversations/{conversation_id}/score_result",
                )
                average_score = extract_rule_average(score_payload)
                if average_score is None:
                    continue
                scored_candidates.append(
                    {
                        "conversation_id": conversation_id,
                        "origin_conversation_id": conversation.get("origin_conversation_id"),
                        "deal_id": conversation.get("deal_id"),
                        "begin_time": conversation.get("begin_time"),
                        "salesman_percent": conversation.get("salesman_percent"),
                        "average_score": average_score,
                    }
                )
            except Exception:
                continue

        representative = select_representative_samples(scored_candidates)
        training_samples: list[dict[str, Any]] = []
        for sample in representative:
            conversation_id = sample["conversation_id"]
            score_payload, score_error = safe_api_get(
                token,
                f"/openapi/conversation/v1/conversations/{conversation_id}/score_result",
            )
            summary_payload, summary_error = safe_api_get(
                token,
                f"/openapi/conversation/v1/conversations/{conversation_id}/summary_pro",
            )
            asr_payload, asr_error = safe_api_get(
                token,
                f"/openapi/conversation/v1/conversations/{conversation_id}/asr_data",
            )

            training_samples.append(
                {
                    "bucket": sample["bucket"],
                    "conversation_id": conversation_id,
                    "origin_conversation_id": sample.get("origin_conversation_id"),
                    "deal_id": sample.get("deal_id"),
                    "begin_time": sample.get("begin_time"),
                    "salesman_percent": sample.get("salesman_percent"),
                    "score": summarize_score_result(score_payload),
                    "score_error": score_error,
                    "summary": summarize_summary_result(summary_payload),
                    "summary_error": summary_error,
                    "asr": summarize_asr_data(asr_payload, args.asr_preview_lines),
                    "asr_error": asr_error,
                }
            )

        payload = {
            "ok": True,
            "request": {
                "employee_name": employee["staffName"],
                "staff_id": employee["staffId"],
                "begin_time": args.begin_time,
                "end_time": args.end_time,
                "score_scan_limit": args.score_scan_limit,
                "asr_preview_lines": args.asr_preview_lines,
                "employees_file": str(Path(args.employees_file).resolve()),
                "megaview_credentials_file": credentials_file,
                "starrocks_config_file": resolved_starrocks_config_file,
            },
            "employee": {
                "staffName": employee["staffName"],
                "staffId": employee["staffId"],
                "origin_user_id": origin_user_id,
                "open_user_id": open_user_id,
                "database_employee": database_employee,
            },
            "starrocks": {
                "database": args.starrocks_database,
                "database_employee_table": DEFAULT_EMPLOYMENT_TABLE,
                "database_employee_driver": database_employee_driver,
                "database_employee_sql": database_employee_sql,
                "config_file": resolved_starrocks_config_file,
            },
            "selection": {
                "conversation_count": len(conversations),
                "score_candidate_count": len(sampled_candidates),
                "scored_candidate_count": len(scored_candidates),
            },
            "samples": training_samples,
            "notes": notes,
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
