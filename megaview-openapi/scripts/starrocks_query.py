#!/usr/bin/env python3
"""Query StarRocks and return JSON.

Prefer PyMySQL when available, including the skill-local `.venv`.
Fall back to a MySQL-compatible CLI only when the Python driver is unavailable.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any


DEFAULT_PORT = 9030
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_.]+$")
DEFAULT_STARROCKS_CONFIG_PATH = Path(__file__).resolve().parent.parent / "data" / "starrocks_config.json"


def load_json_value(raw: str | None) -> Any:
    """Load JSON from inline content or @file."""
    if not raw:
        return None
    if raw.startswith("@"):
        return json.loads(Path(raw[1:]).read_text())
    return json.loads(raw)


def load_starrocks_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load default StarRocks config from the bundled JSON file."""
    config_path = Path(path or DEFAULT_STARROCKS_CONFIG_PATH).expanduser()
    if not config_path.exists():
        return {}
    payload = json.loads(config_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("StarRocks config file must be a JSON object")
    return payload


def resolve_starrocks_config(
    args: argparse.Namespace,
    config_file: str | Path | None = None,
) -> tuple[argparse.Namespace, str]:
    """Resolve StarRocks config from args/env first, then bundled defaults."""
    config_path = str(Path(config_file or DEFAULT_STARROCKS_CONFIG_PATH).expanduser())
    config = load_starrocks_config(config_path)

    field_map = {
        "host": "host",
        "port": "port",
        "user": "user",
        "password": "password",
        "database": "database",
        "table": "sales_table",
        "staff_id_field": "sales_join_field",
        "date_field": "sales_date_field",
        "amount_field": "sales_amount_field",
        "metric_expr": "sales_metric_expr",
        "extra_where": "sales_extra_where",
        "driver": "driver",
    }
    for arg_name, config_name in field_map.items():
        current_value = getattr(args, arg_name, None)
        if current_value in (None, ""):
            config_value = config.get(config_name)
            if config_value not in (None, ""):
                setattr(args, arg_name, config_value)
    return args, config_path


def locate_mysql_client() -> str:
    """Find a MySQL-compatible CLI binary."""
    for candidate in ("mysql", "/opt/homebrew/opt/mysql-client/bin/mysql"):
        path = shutil.which(candidate) if "/" not in candidate else candidate
        if path and Path(path).exists():
            return str(path)
    raise FileNotFoundError(
        "MySQL CLI not found. Install mysql-client or provide a reachable mysql binary."
    )


def load_pymysql():
    """Load PyMySQL from the current environment or the skill-local venv."""
    try:
        return importlib.import_module("pymysql")
    except ModuleNotFoundError:
        skill_root = Path(__file__).resolve().parent.parent
        candidates = sorted((skill_root / ".venv" / "lib").glob("python*/site-packages"))
        for candidate in candidates:
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
        try:
            return importlib.import_module("pymysql")
        except ModuleNotFoundError:
            return None


def validate_identifier(value: str, label: str) -> str:
    """Allow simple SQL identifiers only."""
    if not value or not IDENTIFIER_RE.match(value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


def sql_literal(value: Any) -> str:
    """Render a safe SQL literal for simple values."""
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return f"'{text}'"


def build_sales_query(
    staff_ids: list[Any],
    table: str,
    staff_id_field: str,
    date_field: str,
    metric_expr: str,
    begin_time: str,
    end_time: str,
    extra_where: str = "",
) -> str:
    """Build a grouped sales query."""
    if not staff_ids:
        raise ValueError("staff_ids cannot be empty")

    validate_identifier(table, "table")
    validate_identifier(staff_id_field, "staff_id_field")
    validate_identifier(date_field, "date_field")

    if not metric_expr.strip():
        raise ValueError("metric_expr cannot be empty")

    staff_list = ", ".join(sql_literal(item) for item in staff_ids)
    where_parts = [
        f"{staff_id_field} IN ({staff_list})",
        f"{date_field} >= {sql_literal(begin_time)}",
        f"{date_field} < {sql_literal(end_time)}",
    ]
    if extra_where.strip():
        where_parts.append(f"({extra_where})")

    where_sql = " AND ".join(where_parts)
    return (
        f"SELECT {staff_id_field} AS staff_id, {metric_expr} AS sales_amount "
        f"FROM {table} "
        f"WHERE {where_sql} "
        f"GROUP BY {staff_id_field} "
        f"ORDER BY {staff_id_field}"
    )


def parse_tsv_rows(output: str) -> list[dict[str, Any]]:
    """Parse mysql CLI TSV output into rows."""
    if not output.strip():
        return []
    lines = output.strip().splitlines()
    headers = lines[0].split("\t")
    rows: list[dict[str, Any]] = []
    for line in lines[1:]:
        values = line.split("\t")
        row = {header: values[idx] if idx < len(values) else "" for idx, header in enumerate(headers)}
        if "sales_amount" in row:
            try:
                row["sales_amount"] = float(row["sales_amount"])
            except ValueError:
                pass
        rows.append(row)
    return rows


def run_query_cli(
    mysql_bin: str,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    sql: str,
) -> list[dict[str, Any]]:
    """Execute SQL through mysql CLI and parse TSV output."""
    cmd = [
        mysql_bin,
        "--host",
        host,
        "--port",
        str(port),
        "--user",
        user,
        "--database",
        database,
        "--batch",
        "--raw",
        "--execute",
        sql,
    ]
    env = os.environ.copy()
    env["MYSQL_PWD"] = password

    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "mysql query failed")
    return parse_tsv_rows(result.stdout)


def run_query_python(
    pymysql,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    sql: str,
) -> list[dict[str, Any]]:
    """Execute SQL through PyMySQL and return rows."""
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connect_timeout=10,
        read_timeout=30,
        write_timeout=30,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
    finally:
        connection.close()

    parsed: list[dict[str, Any]] = []
    for row in rows:
        normalized = dict(row)
        if "sales_amount" in normalized:
            try:
                normalized["sales_amount"] = float(normalized["sales_amount"])
            except (TypeError, ValueError):
                pass
        parsed.append(normalized)
    return parsed


def run_query(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    sql: str,
    driver: str = "auto",
) -> tuple[list[dict[str, Any]], str]:
    """Execute SQL with PyMySQL first, then CLI if needed."""
    pymysql = load_pymysql() if driver in {"auto", "pymysql"} else None
    cli_error = None
    pymysql_error = None

    if pymysql is not None:
        try:
            return (
                run_query_python(
                    pymysql=pymysql,
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    sql=sql,
                ),
                "pymysql",
            )
        except Exception as exc:  # noqa: BLE001
            pymysql_error = str(exc)
            if driver == "pymysql":
                raise RuntimeError(pymysql_error) from exc

    if driver in {"auto", "cli"}:
        try:
            mysql_bin = locate_mysql_client()
            return (
                run_query_cli(
                    mysql_bin=mysql_bin,
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database=database,
                    sql=sql,
                ),
                "cli",
            )
        except Exception as exc:  # noqa: BLE001
            cli_error = str(exc)
            if driver == "cli":
                raise RuntimeError(cli_error) from exc

    details = {
        "pymysql_error": pymysql_error,
        "cli_error": cli_error,
    }
    raise RuntimeError(json.dumps(details, ensure_ascii=False))


def write_output(payload: dict[str, Any], output_path: str | None) -> None:
    """Write JSON result to stdout and optional file."""
    def to_json_safe(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: to_json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [to_json_safe(item) for item in value]
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat(sep=" ")
        return value

    text = json.dumps(to_json_safe(payload), ensure_ascii=False, indent=2)
    if output_path:
        Path(output_path).write_text(text + "\n")
    print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Query StarRocks sales data.")
    parser.add_argument(
        "--config-file",
        default=os.getenv("STARROCKS_CONFIG_FILE", str(DEFAULT_STARROCKS_CONFIG_PATH)),
        help="Bundled StarRocks config JSON file",
    )
    parser.add_argument("--host", default=os.getenv("STARROCKS_HOST"))
    parser.add_argument("--port", type=int, default=int(os.getenv("STARROCKS_PORT", DEFAULT_PORT)))
    parser.add_argument("--user", default=os.getenv("STARROCKS_USER"))
    parser.add_argument("--password", default=os.getenv("STARROCKS_PASSWORD"))
    parser.add_argument("--database", default=os.getenv("STARROCKS_DATABASE"))
    parser.add_argument("--sql", help="Raw SQL string")
    parser.add_argument("--sql-file", help="Path to a SQL file")
    parser.add_argument("--staff-ids", help="JSON array or @file")
    parser.add_argument("--table", default=os.getenv("STARROCKS_SALES_TABLE"))
    parser.add_argument("--staff-id-field", default=os.getenv("STARROCKS_STAFF_ID_FIELD", "staff_id"))
    parser.add_argument("--date-field", default=os.getenv("STARROCKS_SALES_DATE_FIELD"))
    parser.add_argument("--amount-field", default=os.getenv("STARROCKS_SALES_AMOUNT_FIELD"))
    parser.add_argument("--metric-expr", default=os.getenv("STARROCKS_SALES_METRIC_EXPR"))
    parser.add_argument("--begin-time")
    parser.add_argument("--end-time")
    parser.add_argument("--extra-where", default=os.getenv("STARROCKS_SALES_EXTRA_WHERE", ""))
    parser.add_argument(
        "--driver",
        choices=["auto", "pymysql", "cli"],
        default=os.getenv("STARROCKS_DRIVER", "auto"),
        help="Preferred StarRocks query driver",
    )
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()
    args, resolved_config_path = resolve_starrocks_config(args, args.config_file)

    required = {
        "host": args.host,
        "user": args.user,
        "password": args.password,
        "database": args.database,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        write_output(
            {
                "ok": False,
                "stage": "config",
                "error": f"Missing StarRocks config: {', '.join(missing)}",
                "config_file": resolved_config_path,
            },
            args.out,
        )
        return 2

    try:
        sql = args.sql or ""
        if args.sql_file:
            sql = Path(args.sql_file).read_text()

        if not sql:
            staff_ids = load_json_value(args.staff_ids)
            if not isinstance(staff_ids, list):
                raise ValueError("staff_ids must be a JSON array when sql is not provided")
            metric_expr = args.metric_expr.strip() if args.metric_expr else ""
            if not metric_expr:
                if not args.amount_field:
                    raise ValueError("Provide --metric-expr or --amount-field")
                metric_expr = f"SUM({validate_identifier(args.amount_field, 'amount_field')})"
            if not args.table or not args.date_field or not args.begin_time or not args.end_time:
                raise ValueError(
                    "Structured mode requires --table, --date-field, --begin-time, --end-time, and --staff-ids"
                )
            sql = build_sales_query(
                staff_ids=staff_ids,
                table=args.table,
                staff_id_field=args.staff_id_field,
                date_field=args.date_field,
                metric_expr=metric_expr,
                begin_time=args.begin_time,
                end_time=args.end_time,
                extra_where=args.extra_where,
            )

        rows, driver_used = run_query(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database,
            sql=sql,
            driver=args.driver,
        )
        write_output(
            {
                "ok": True,
                "request": {
                    "host": args.host,
                    "port": args.port,
                    "database": args.database,
                    "sql": sql,
                    "driver": driver_used,
                    "config_file": resolved_config_path,
                },
                "rows": rows,
            },
            args.out,
        )
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
