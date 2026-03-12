#!/usr/bin/env python3
"""Megaview OpenAPI request helper.

This script obtains an app access token and then calls a Megaview API with a
structured JSON result. It is intentionally generic so the skill can reuse it
for many endpoints.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests


DEFAULT_BASE_URL = "https://open.megaview.com"
DEFAULT_TIMEOUT = 30
AUTH_ENDPOINT = "/openapi/auth/v1/app_access_token/internal"
DEFAULT_CREDENTIALS_PATH = Path.home() / ".vk-cowork" / "megaview_credentials.json"
DEFAULT_BUNDLED_CREDENTIALS_PATH = Path(__file__).resolve().parent.parent / "data" / "megaview_credentials.json"


def load_json_value(raw: str | None) -> dict[str, Any]:
    """Load a JSON object from inline JSON or from @file."""
    if not raw:
        return {}

    if raw.startswith("@"):
        path = Path(raw[1:])
        return json.loads(path.read_text())

    return json.loads(raw)


def load_credentials_file(path: str | Path | None) -> dict[str, Any]:
    """Load Megaview credentials from a JSON file."""
    if not path:
        return {}

    credentials_path = Path(path).expanduser()
    if not credentials_path.exists():
        return {}

    payload = json.loads(credentials_path.read_text())
    if not isinstance(payload, dict):
        raise ValueError("Megaview credentials file must be a JSON object")
    return payload


def resolve_credentials(
    app_key: str | None,
    app_secret: str | None,
    credentials_file: str | Path | None = None,
) -> tuple[str | None, str | None, str | None]:
    """Resolve credentials from args/env first, then shared or bundled files."""
    requested_path = Path(
        credentials_file
        or os.getenv("MEGAVIEW_CREDENTIALS_FILE")
        or DEFAULT_CREDENTIALS_PATH
    ).expanduser()

    resolved_key = app_key or os.getenv("MEGAVIEW_APP_KEY")
    resolved_secret = app_secret or os.getenv("MEGAVIEW_APP_SECRET")

    if resolved_key and resolved_secret:
        return resolved_key, resolved_secret, str(requested_path)

    candidate_paths = [requested_path]
    if requested_path != DEFAULT_BUNDLED_CREDENTIALS_PATH:
        candidate_paths.append(DEFAULT_BUNDLED_CREDENTIALS_PATH)

    for candidate_path in candidate_paths:
        file_credentials = load_credentials_file(candidate_path)
        resolved_key = resolved_key or file_credentials.get("app_key")
        resolved_secret = resolved_secret or file_credentials.get("app_secret")
        if resolved_key and resolved_secret:
            return resolved_key, resolved_secret, str(candidate_path)

    return resolved_key, resolved_secret, str(requested_path)


def normalize_endpoint(endpoint: str, path_params: dict[str, Any]) -> str:
    """Replace :path_param placeholders and ensure a leading slash."""
    resolved = endpoint.strip()
    if not resolved.startswith("/"):
        resolved = "/" + resolved

    for key, value in path_params.items():
        resolved = resolved.replace(f":{key}", str(value))

    return resolved


def request_token(
    base_url: str,
    app_key: str,
    app_secret: str,
    timeout: int,
) -> dict[str, Any]:
    """Fetch Megaview app access token."""
    url = base_url.rstrip("/") + AUTH_ENDPOINT
    response = requests.post(
        url,
        json={"app_key": app_key, "app_secret": app_secret},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def safe_headers(token: str) -> dict[str, str]:
    """Return redacted headers for output."""
    if not token:
        auth = ""
    elif len(token) <= 8:
        auth = "Bearer ***"
    else:
        auth = f"Bearer {token[:4]}***{token[-4:]}"

    return {
        "Content-Type": "application/json",
        "Authorization": auth,
    }


def write_output(payload: dict[str, Any], output_path: str | None) -> None:
    """Write JSON result to stdout and optionally to a file."""
    text = json.dumps(payload, ensure_ascii=False, indent=2)

    if output_path:
        Path(output_path).write_text(text + "\n")

    print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="Call Megaview OpenAPI.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--endpoint", required=True, help="Megaview API path")
    parser.add_argument("--method", default="GET", help="HTTP method")
    parser.add_argument("--app-key", default=os.getenv("MEGAVIEW_APP_KEY"))
    parser.add_argument("--app-secret", default=os.getenv("MEGAVIEW_APP_SECRET"))
    parser.add_argument(
        "--credentials-file",
        default=os.getenv("MEGAVIEW_CREDENTIALS_FILE", str(DEFAULT_CREDENTIALS_PATH)),
        help="Megaview credentials JSON file",
    )
    parser.add_argument("--path-params", help="JSON object or @file")
    parser.add_argument("--query", help="JSON object or @file")
    parser.add_argument("--body", help="JSON object or @file")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--out", help="Optional file path for JSON output")
    parser.add_argument(
        "--show-token",
        action="store_true",
        help="Include raw token in output. Use only when the user explicitly asks.",
    )
    args = parser.parse_args()

    app_key, app_secret, credentials_file = resolve_credentials(
        args.app_key,
        args.app_secret,
        args.credentials_file,
    )
    if not app_key or not app_secret:
        error_payload = {
            "ok": False,
            "stage": "config",
            "error": (
                "Missing credentials. Provide --app-key/--app-secret, "
                "set MEGAVIEW_APP_KEY/MEGAVIEW_APP_SECRET, "
                f"or store app_key/app_secret in {credentials_file}."
            ),
        }
        write_output(error_payload, args.out)
        return 2

    try:
        path_params = load_json_value(args.path_params)
        query = load_json_value(args.query)
        body = load_json_value(args.body)
    except Exception as exc:  # noqa: BLE001
        error_payload = {
            "ok": False,
            "stage": "argument_parse",
            "error": str(exc),
        }
        write_output(error_payload, args.out)
        return 2

    try:
        auth_json = request_token(args.base_url, app_key, app_secret, args.timeout)
        token_data = auth_json.get("data") or {}
        token = token_data.get("app_access_token", "")
        if auth_json.get("code") != 0 or not token:
            payload = {
                "ok": False,
                "stage": "auth",
                "auth_response": auth_json,
                "error": "Megaview token request failed.",
            }
            write_output(payload, args.out)
            return 1

        endpoint = normalize_endpoint(args.endpoint, path_params)
        url = args.base_url.rstrip("/") + endpoint
        response = requests.request(
            method=args.method.upper(),
            url=url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            params=query or None,
            json=body or None,
            timeout=args.timeout,
        )

        try:
            response_payload: Any = response.json()
        except Exception:  # noqa: BLE001
            response_payload = response.text

        auth_output = {
            "code": auth_json.get("code"),
            "msg": auth_json.get("msg"),
            "expire": token_data.get("expire"),
        }
        if args.show_token:
            auth_output["app_access_token"] = token

        payload = {
            "ok": response.ok and (
                not isinstance(response_payload, dict)
                or response_payload.get("code", 0) == 0
            ),
            "request": {
                "method": args.method.upper(),
                "url": url,
                "path_params": path_params,
                "query": query,
                "body": body,
                "headers": safe_headers(token),
            },
            "auth": auth_output,
            "response": {
                "status_code": response.status_code,
                "payload": response_payload,
            },
        }
        write_output(payload, args.out)
        return 0 if payload["ok"] else 1

    except requests.HTTPError as exc:
        response_text = ""
        if exc.response is not None:
            try:
                response_text = exc.response.text
            except Exception:  # noqa: BLE001
                response_text = ""
        payload = {
            "ok": False,
            "stage": "http",
            "error": str(exc),
            "response_text": response_text,
        }
        write_output(payload, args.out)
        return 1
    except Exception as exc:  # noqa: BLE001
        payload = {
            "ok": False,
            "stage": "runtime",
            "error": str(exc),
        }
        write_output(payload, args.out)
        return 1


if __name__ == "__main__":
    sys.exit(main())
