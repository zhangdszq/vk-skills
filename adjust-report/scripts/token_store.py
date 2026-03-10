"""
Adjust API 凭证存储和读取
存储位置: ~/.vk-cowork/adjust_credentials.json（跨平台兼容）

用法:
  python token_store.py save --api-token <API_TOKEN> --app-token <APP_TOKEN>
  python token_store.py load
"""

import argparse
import json
import os
import sys
from pathlib import Path


def get_config_dir():
    """获取配置目录，跨平台兼容"""
    home = Path.home()
    config_dir = home / ".vk-cowork"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_credentials_path():
    return get_config_dir() / "adjust_credentials.json"


def save_credentials(api_token, app_token):
    path = get_credentials_path()
    data = {"api_token": api_token, "app_token": app_token}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.chmod(path, 0o600)
    print(json.dumps({"status": "saved", "path": str(path)}))


def load_credentials():
    path = get_credentials_path()
    if not path.exists():
        print(json.dumps({"status": "not_found", "path": str(path)}))
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data.get("api_token") or not data.get("app_token"):
        print(json.dumps({"status": "incomplete", "path": str(path)}))
        sys.exit(1)

    print(json.dumps({"status": "ok", **data}))


def main():
    parser = argparse.ArgumentParser(description="Adjust 凭证管理")
    sub = parser.add_subparsers(dest="command")

    save_cmd = sub.add_parser("save")
    save_cmd.add_argument("--api-token", required=True)
    save_cmd.add_argument("--app-token", required=True)

    sub.add_parser("load")

    args = parser.parse_args()

    if args.command == "save":
        save_credentials(args.api_token, args.app_token)
    elif args.command == "load":
        load_credentials()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
