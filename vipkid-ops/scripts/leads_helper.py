#!/usr/bin/env python3
"""
leads_helper.py - VIPKID Leads 线索库辅助工具

用法：
  python3 scripts/leads_helper.py auth
  python3 scripts/leads_helper.py list --status public --page-num 1 --page-size 20
  python3 scripts/leads_helper.py list --status public --user-id 123456 --country-code 966
  python3 scripts/leads_helper.py channels
  python3 scripts/leads_helper.py tags
  python3 scripts/leads_helper.py flow-reasons
  python3 scripts/leads_helper.py nodes
  python3 scripts/leads_helper.py staff --role gcc --query Alice
  python3 scripts/leads_helper.py decrypt-user 123456
  python3 scripts/leads_helper.py add-tag 123456 18 --yes
  python3 scripts/leads_helper.py delete-tag 123456 18 --yes
  python3 scripts/leads_helper.py allot gcc 9988 123456 234567 --yes
  python3 scripts/leads_helper.py flow froze 123456 234567 --yes
  python3 scripts/leads_helper.py upload leads ./leads.xlsx --yes
  python3 scripts/leads_helper.py upload equity ./equity.xlsx --yes
  python3 scripts/leads_helper.py upload frozen ./batch_frozen.xlsx --yes
  python3 scripts/leads_helper.py batch-allot-upload gcc ./batch_allot.xlsx --yes
"""

import argparse
import json
import mimetypes
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

CONFIG_PATH = Path.home() / ".vipkid-ops" / "config.json"
DEFAULT_MANAGER_BASE_URL = "https://sa-manager.lionabc.com"
DEFAULT_CR_CODE = "sa"

STATUS_MAP = {"public": 0, "private": 1, "froze": 2}
ROLE_MAP = {"gcc": 0, "gcs": 1, "tmk": 3}
RUN_STATUS_MAP = {0: "禁用", 1: "启用"}

UPLOAD_TYPE_MAP = {
    "leads": "/api/v1/leads/user/upload",
    "equity": "/api/v1/leads/user/equity/upload",
    "frozen": "/api/v1/leads/user/batchFrozenByUpload",
}

SORT_FIELD_MAP = {
    "time:asc": ("sortByTime", 0),
    "time:desc": ("sortByTime", 1),
    "remaining:asc": ("sortByRemainingTime", 0),
    "remaining:desc": ("sortByRemainingTime", 1),
    "allot:asc": ("sortByAllotTime", 0),
    "allot:desc": ("sortByAllotTime", 1),
}


def load_config(required=False):
    if not CONFIG_PATH.exists():
        if required:
            print(f"[ERROR] 配置文件不存在：{CONFIG_PATH}")
            print("请先创建 ~/.vipkid-ops/config.json 并写入 token。")
            sys.exit(1)
        return {"base_url": DEFAULT_MANAGER_BASE_URL, "cr_code": DEFAULT_CR_CODE}

    with open(CONFIG_PATH, encoding="utf-8") as file_obj:
        config = json.load(file_obj)

    config.setdefault("base_url", DEFAULT_MANAGER_BASE_URL)
    config.setdefault("cr_code", DEFAULT_CR_CODE)
    return config


def require_auth_config():
    config = load_config(required=True)
    token = str(config.get("token", "")).strip()
    if token:
        return config

    print(f"[ERROR] 配置文件缺少 token：{CONFIG_PATH}")
    print("请先运行商品包 helper 里的 refresh-token 或手动填入 intlAuthToken。")
    sys.exit(1)


def resolve_leads_base_url(config):
    explicit = str(config.get("leads_base_url", "")).strip()
    if explicit:
        return explicit.rstrip("/")

    base_url = str(config.get("base_url", DEFAULT_MANAGER_BASE_URL)).strip().rstrip("/")
    if "manager" in base_url:
        return base_url.replace("manager", "leads").replace("//dev-", "//test-")

    cr_code = str(config.get("cr_code", DEFAULT_CR_CODE)).strip() or DEFAULT_CR_CODE
    return f"https://{cr_code}-leads.lionabc.com"


def build_headers(content_type="application/json"):
    config = require_auth_config()
    token = str(config["token"]).strip()
    cr_code = str(config.get("cr_code", DEFAULT_CR_CODE)).strip() or DEFAULT_CR_CODE
    leads_base_url = resolve_leads_base_url(config)
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Authorization": token,
        "intlAuthToken": token,
        "Cookie": f"intlAuthToken={token}; biz-line={cr_code}; sidebarStatus=0",
        "Origin": leads_base_url,
        "Referer": f"{leads_base_url}/leadsPublic/list",
        "Connection": "keep-alive",
        "vk-cr-code": cr_code,
        "vk-language-code": "zh-CN",
        "app-Code": "leads-management",
        "biz-line": cr_code,
        "web-site": cr_code,
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        ),
    }
    if content_type:
        headers["Content-Type"] = content_type
    return leads_base_url, headers


def run_curl_json(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except FileNotFoundError:
        return {"network_error": "curl 命令不存在"}
    except subprocess.TimeoutExpired:
        return {"network_error": "curl 请求超时"}

    if result.returncode != 0:
        error_message = (result.stderr or result.stdout or "").strip()
        return {"network_error": error_message or f"curl exit code {result.returncode}"}

    raw = (result.stdout or "").strip()
    if not raw:
        return {"network_error": "接口返回为空"}

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_response": raw}


def api_get(path, params=None):
    base_url, headers = build_headers(content_type=None)
    url = f"{base_url}/rest/leadsgw{path}"
    if params:
        url = f"{url}?{urlencode(params, doseq=True)}"
    command = ["curl", "-ks", url]
    for key, value in headers.items():
        command.extend(["-H", f"{key}: {value}"])
    return run_curl_json(command)


def api_auth_get(path, params=None):
    base_url, headers = build_headers(content_type=None)
    url = f"{base_url}/rest/auth{path}"
    if params:
        url = f"{url}?{urlencode(params, doseq=True)}"
    command = ["curl", "-ks", url]
    for key, value in headers.items():
        command.extend(["-H", f"{key}: {value}"])
    return run_curl_json(command)


def api_post(path, data):
    base_url, headers = build_headers()
    command = ["curl", "-ks", f"{base_url}/rest/leadsgw{path}", "-X", "POST"]
    for key, value in headers.items():
        command.extend(["-H", f"{key}: {value}"])
    command.extend(["--data-raw", json.dumps(data, ensure_ascii=False)])
    return run_curl_json(command)


def encode_multipart_formdata(fields, files):
    boundary = f"----vipkidops{uuid.uuid4().hex}"
    body_parts = []

    for key, value in fields.items():
        body_parts.append(f"--{boundary}".encode("utf-8"))
        body_parts.append(f'Content-Disposition: form-data; name="{key}"'.encode("utf-8"))
        body_parts.append(b"")
        body_parts.append(str(value).encode("utf-8"))

    for key, file_path in files.items():
        path_obj = Path(file_path)
        filename = path_obj.name
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        body_parts.append(f"--{boundary}".encode("utf-8"))
        body_parts.append(
            f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode("utf-8")
        )
        body_parts.append(f"Content-Type: {content_type}".encode("utf-8"))
        body_parts.append(b"")
        body_parts.append(path_obj.read_bytes())

    body_parts.append(f"--{boundary}--".encode("utf-8"))
    body_parts.append(b"")
    return b"\r\n".join(body_parts), f"multipart/form-data; boundary={boundary}"


def api_post_multipart(path, fields, files):
    base_url, headers = build_headers(content_type=None)
    command = ["curl", "-ks", f"{base_url}/rest/leadsgw{path}", "-X", "POST"]
    for key, value in headers.items():
        command.extend(["-H", f"{key}: {value}"])
    for key, value in fields.items():
        command.extend(["-F", f"{key}={value}"])
    for key, file_path in files.items():
        command.extend(["-F", f"{key}=@{Path(file_path).expanduser()}"])
    return run_curl_json(command)


def parse_time(value):
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if raw.isdigit():
        return int(raw)

    formats = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d")
    for fmt in formats:
        try:
            return int(datetime.strptime(raw, fmt).timestamp() * 1000)
        except ValueError:
            continue

    raise ValueError(f"无法解析时间：{value}")


def split_csv(value, cast=None):
    if not value:
        return None
    items = [item.strip() for item in str(value).split(",") if item.strip()]
    if cast is None:
        return items
    return [cast(item) for item in items]


def truncate(value, width):
    text = "" if value is None else str(value)
    if len(text) <= width:
        return text
    return text[: max(0, width - 3)] + "..."


def confirm_action(summary, auto_yes=False):
    print(summary)
    if auto_yes:
        return True
    answer = input("确认执行？输入 y 继续: ").strip().lower()
    return answer == "y"


def ensure_success(resp):
    if resp.get("network_error"):
        print(f"[ERROR] 网络错误：{resp['network_error']}")
        return False
    if resp.get("http_error"):
        print(f"[ERROR] HTTP 错误：{resp['http_error']} {resp.get('reason', '')}")
        return False
    if resp.get("code") not in (0, 200):
        print(f"[ERROR] code={resp.get('code')} msg={resp.get('msg') or resp}")
        return False
    return True


def check_auth():
    resp = api_auth_get("/api/auth/userAuthInfo")
    if ensure_success(resp) and resp.get("data"):
        role_list = resp["data"].get("roleList", [])
        print(f"✅ Leads 认证有效，角色：{role_list}")
        return True
    print("❌ Leads token 无效或已过期。")
    return False


def list_channels():
    resp = api_get("/api/v1/leads/business/channel/all")
    if not ensure_success(resp):
        return
    data = resp.get("data") or []
    print(f"共 {len(data)} 个渠道节点")
    for item in data[:200]:
        print(json.dumps(item, ensure_ascii=False))


def list_tags():
    resp = api_get("/api/v1/leads/tag/all")
    if not ensure_success(resp):
        return
    data = resp.get("data") or []
    print(f"{'ID':<8} {'名称':<30}")
    print("-" * 40)
    for item in data:
        print(f"{str(item.get('id', '')):<8} {truncate(item.get('name', ''), 30)}")


def list_flow_reasons():
    resp = api_get("/api/v1/leads/flow/reason/all")
    if not ensure_success(resp):
        return
    data = resp.get("data") or []
    print(f"{'ID':<8} {'名称':<32}")
    print("-" * 44)
    for item in data:
        print(f"{str(item.get('id', '')):<8} {truncate(item.get('name', ''), 32)}")


def list_nodes():
    resp = api_get("/api/v1/leads/flow/manage/node/all")
    if not ensure_success(resp):
        return
    data = resp.get("data") or []
    print(f"{'Code':<18} {'名称':<24}")
    print("-" * 44)
    for item in data:
        print(f"{truncate(item.get('nodeCode', ''), 18):<18} {truncate(item.get('nodeName', ''), 24)}")


def list_staff(args):
    role = ROLE_MAP[args.role]
    payload = {
        "pageSize": args.page_size,
        "currentPage": args.page_num,
        "staffRole": role,
    }
    if args.query:
        payload["staffName"] = args.query
    if args.staff_no:
        payload["staffNo"] = args.staff_no

    resp = api_post("/api/v1/leads/staff/getList", payload)
    if not ensure_success(resp):
        return

    data = resp.get("data") or []
    total = resp.get("totalCount", len(data))
    print(f"共 {total} 个员工，本页 {len(data)} 个")
    print(f"{'staffId':<10} {'姓名':<24} {'工号':<12} {'角色':<6} {'状态':<6}")
    print("-" * 70)
    for item in data:
        print(
            f"{str(item.get('staffId', '')):<10} "
            f"{truncate(item.get('staffName', ''), 24):<24} "
            f"{truncate(item.get('staffNo', ''), 12):<12} "
            f"{str(item.get('staffRole', '')):<6} "
            f"{RUN_STATUS_MAP.get(item.get('status'), item.get('status', '-')):<6}"
        )


def build_list_payload(args):
    payload = {
        "status": STATUS_MAP[args.status],
        "currentPage": args.page_num,
        "pageSize": args.page_size,
    }

    direct_fields = {
        "user_id": "userId",
        "student_id": "studentId",
        "mobile": "mobile",
        "country_code": "countryCode",
        "gcs_name": "gcsName",
        "staff_id": "staffId",
        "tmk_name": "tmkName",
        "last_follow_result_type": "lastFollowResultType",
        "channel_code": "channelCode",
        "channel_level_id": "channelLevelId",
    }
    for arg_name, field_name in direct_fields.items():
        value = getattr(args, arg_name)
        if value not in (None, "", []):
            payload[field_name] = value

    flow_reason_ids = split_csv(args.flow_reason_ids, int)
    if flow_reason_ids:
        payload["flowReasonIdList"] = flow_reason_ids

    flow_node_list = split_csv(args.flow_node_list)
    if flow_node_list:
        payload["flowNodeList"] = flow_node_list

    time_pairs = [
        ("last_follow_start", "lastFollowFilterTimeStart"),
        ("last_follow_end", "lastFollowFilterTimeEnd"),
        ("last_unfollow_start", "lastUnFollowFilterTimeStart"),
        ("last_unfollow_end", "lastUnFollowFilterTimeEnd"),
        ("register_start", "registerTimeStart"),
        ("register_end", "registerTimeEnd"),
        ("last_login_start", "lastLoginTimeStart"),
        ("last_login_end", "lastLoginTimeEnd"),
        ("node_time_start", "lastFlowTimeStart"),
        ("node_time_end", "lastFlowTimeEnd"),
    ]
    for arg_name, field_name in time_pairs:
        value = getattr(args, arg_name)
        if value:
            payload[field_name] = parse_time(value)

    if args.sort:
        column_name, order_value = SORT_FIELD_MAP[args.sort]
        payload[column_name] = order_value

    return payload


def list_leads(args):
    payload = build_list_payload(args)
    endpoint = (
        "/api/v1/leads/user/manage/getList"
        if args.status == "private"
        else "/api/v1/leads/user/pub/getList"
    )
    resp = api_post(endpoint, payload)
    if not ensure_success(resp):
        return

    data = resp.get("data") or []
    total = resp.get("totalCount", len(data))
    print(f"共 {total} 条线索，本页 {len(data)} 条")
    print(
        f"{'userId':<12} {'渠道':<18} {'手机号':<18} "
        f"{'节点':<12} {'GCS':<18} {'流转标记':<18}"
    )
    print("-" * 110)
    for item in data:
        flow_info = item.get("flowNodeInfo") or {}
        flow_reason_desc = flow_info.get("flowReasonDesc") or ""
        flow_node_name = flow_info.get("nodeName") or item.get("flowNodeName") or item.get("flowNode") or ""
        phone_text = item.get("showMobile") or "-"
        if item.get("countryCode"):
            phone_text = f"{item['countryCode']}-{phone_text}"
        print(
            f"{str(item.get('userId', '')):<12} "
            f"{truncate(item.get('channelName', ''), 18):<18} "
            f"{truncate(phone_text, 18):<18} "
            f"{truncate(flow_node_name, 12):<12} "
            f"{truncate(item.get('gcsName', ''), 18):<18} "
            f"{truncate(flow_reason_desc, 18):<18}"
        )


def decrypt_user(user_id):
    resp = api_get("/api/v1/leads/user/decrypt", {"userId": user_id})
    if not ensure_success(resp):
        return
    data = resp.get("data") or {}
    mobile = data.get("mobile") or "-"
    if data.get("countryCode"):
        mobile = f"{data['countryCode']}-{mobile}"
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"\n手机号: {mobile}")
    print(f"邮箱: {data.get('email', '-')}")


def add_tag(user_id, tag_id, auto_yes=False):
    summary = f"准备给 userId={user_id} 添加标签 tagId={tag_id}"
    if not confirm_action(summary, auto_yes=auto_yes):
        print("已取消")
        return
    resp = api_post("/api/v1/leads/user/addTag", {"userId": user_id, "tagId": tag_id})
    if ensure_success(resp):
        print("✅ 添加标签成功")


def delete_tag(user_id, tag_id, auto_yes=False):
    summary = f"准备给 userId={user_id} 删除标签 tagId={tag_id}"
    if not confirm_action(summary, auto_yes=auto_yes):
        print("已取消")
        return
    resp = api_post("/api/v1/leads/user/deleteTag", {"userId": user_id, "tagId": tag_id})
    if ensure_success(resp):
        print("✅ 删除标签成功")


def allot_leads(role_name, staff_id, user_ids, auto_yes=False):
    payload = {
        "userIdList": user_ids,
        "staffId": staff_id,
        "staffRole": ROLE_MAP[role_name],
    }
    summary = (
        f"准备把 {len(user_ids)} 条线索分配给 {role_name.upper()}，"
        f"staffId={staff_id}，userIds={','.join(user_ids)}"
    )
    if not confirm_action(summary, auto_yes=auto_yes):
        print("已取消")
        return
    resp = api_post("/api/v1/leads/user/manage/allot", payload)
    if ensure_success(resp):
        print("✅ 分配成功")


def flow_leads(target, user_ids, auto_yes=False):
    if target not in ("public", "froze"):
        print("[ERROR] flow 仅支持 public 或 froze")
        return
    payload = {"userIdList": user_ids, "type": STATUS_MAP[target]}
    summary = f"准备把 {len(user_ids)} 条线索流转到 {target}，userIds={','.join(user_ids)}"
    if not confirm_action(summary, auto_yes=auto_yes):
        print("已取消")
        return
    resp = api_post("/api/v1/leads/user/manage/flow", payload)
    if ensure_success(resp):
        print("✅ 流转成功")


def upload_file(upload_type, file_path, auto_yes=False):
    path_obj = Path(file_path).expanduser()
    if not path_obj.exists():
        print(f"[ERROR] 文件不存在：{path_obj}")
        return
    endpoint = UPLOAD_TYPE_MAP[upload_type]
    summary = f"准备上传 {upload_type} 文件：{path_obj}"
    if not confirm_action(summary, auto_yes=auto_yes):
        print("已取消")
        return
    resp = api_post_multipart(endpoint, {}, {"file": path_obj})
    if ensure_success(resp):
        print("✅ 上传成功")
        if resp.get("data") is not None:
            print(json.dumps(resp.get("data"), ensure_ascii=False, indent=2))


def batch_allot_upload(role_name, file_path, auto_yes=False):
    if role_name not in ("gcc", "tmk"):
        print("[ERROR] batch-allot-upload 仅支持 gcc 或 tmk")
        return
    path_obj = Path(file_path).expanduser()
    if not path_obj.exists():
        print(f"[ERROR] 文件不存在：{path_obj}")
        return
    fields = {"allotType": ROLE_MAP[role_name]}
    summary = f"准备上传批量分配文件到 {role_name.upper()}：{path_obj}"
    if not confirm_action(summary, auto_yes=auto_yes):
        print("已取消")
        return
    resp = api_post_multipart("/api/v1/leads/user/manage/allot/upload", fields, {"file": path_obj})
    if ensure_success(resp):
        print("✅ 批量分配上传成功")
        if resp.get("data") is not None:
            print(json.dumps(resp.get("data"), ensure_ascii=False, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description="VIPKID Leads 线索库辅助工具")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("auth")
    subparsers.add_parser("channels")
    subparsers.add_parser("tags")
    subparsers.add_parser("flow-reasons")
    subparsers.add_parser("nodes")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--status", choices=tuple(STATUS_MAP.keys()), default="public")
    list_parser.add_argument("--page-num", type=int, default=1)
    list_parser.add_argument("--page-size", type=int, default=20)
    list_parser.add_argument("--user-id")
    list_parser.add_argument("--student-id")
    list_parser.add_argument("--mobile")
    list_parser.add_argument("--country-code")
    list_parser.add_argument("--gcs-name")
    list_parser.add_argument("--staff-id")
    list_parser.add_argument("--tmk-name")
    list_parser.add_argument("--last-follow-result-type")
    list_parser.add_argument("--channel-code")
    list_parser.add_argument("--channel-level-id")
    list_parser.add_argument("--flow-reason-ids", help="逗号分隔，如 1,2,3")
    list_parser.add_argument("--flow-node-list", help="逗号分隔，如 FIRST_CONTACT,TRIAL")
    list_parser.add_argument("--last-follow-start")
    list_parser.add_argument("--last-follow-end")
    list_parser.add_argument("--last-unfollow-start")
    list_parser.add_argument("--last-unfollow-end")
    list_parser.add_argument("--register-start")
    list_parser.add_argument("--register-end")
    list_parser.add_argument("--last-login-start")
    list_parser.add_argument("--last-login-end")
    list_parser.add_argument("--node-time-start")
    list_parser.add_argument("--node-time-end")
    list_parser.add_argument("--sort", choices=tuple(SORT_FIELD_MAP.keys()))

    staff_parser = subparsers.add_parser("staff")
    staff_parser.add_argument("--role", required=True, choices=tuple(ROLE_MAP.keys()))
    staff_parser.add_argument("--query")
    staff_parser.add_argument("--staff-no")
    staff_parser.add_argument("--page-num", type=int, default=1)
    staff_parser.add_argument("--page-size", type=int, default=20)

    decrypt_parser = subparsers.add_parser("decrypt-user")
    decrypt_parser.add_argument("user_id")

    add_tag_parser = subparsers.add_parser("add-tag")
    add_tag_parser.add_argument("user_id")
    add_tag_parser.add_argument("tag_id", type=int)
    add_tag_parser.add_argument("--yes", action="store_true")

    delete_tag_parser = subparsers.add_parser("delete-tag")
    delete_tag_parser.add_argument("user_id")
    delete_tag_parser.add_argument("tag_id", type=int)
    delete_tag_parser.add_argument("--yes", action="store_true")

    allot_parser = subparsers.add_parser("allot")
    allot_parser.add_argument("role", choices=tuple(ROLE_MAP.keys()))
    allot_parser.add_argument("staff_id")
    allot_parser.add_argument("user_ids", nargs="+")
    allot_parser.add_argument("--yes", action="store_true")

    flow_parser = subparsers.add_parser("flow")
    flow_parser.add_argument("target", choices=("public", "froze"))
    flow_parser.add_argument("user_ids", nargs="+")
    flow_parser.add_argument("--yes", action="store_true")

    upload_parser = subparsers.add_parser("upload")
    upload_parser.add_argument("upload_type", choices=tuple(UPLOAD_TYPE_MAP.keys()))
    upload_parser.add_argument("file_path")
    upload_parser.add_argument("--yes", action="store_true")

    batch_upload_parser = subparsers.add_parser("batch-allot-upload")
    batch_upload_parser.add_argument("role", choices=("gcc", "tmk"))
    batch_upload_parser.add_argument("file_path")
    batch_upload_parser.add_argument("--yes", action="store_true")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "auth":
        check_auth()
    elif args.command == "channels":
        list_channels()
    elif args.command == "tags":
        list_tags()
    elif args.command == "flow-reasons":
        list_flow_reasons()
    elif args.command == "nodes":
        list_nodes()
    elif args.command == "list":
        list_leads(args)
    elif args.command == "staff":
        list_staff(args)
    elif args.command == "decrypt-user":
        decrypt_user(args.user_id)
    elif args.command == "add-tag":
        add_tag(args.user_id, args.tag_id, auto_yes=args.yes)
    elif args.command == "delete-tag":
        delete_tag(args.user_id, args.tag_id, auto_yes=args.yes)
    elif args.command == "allot":
        allot_leads(args.role, args.staff_id, args.user_ids, auto_yes=args.yes)
    elif args.command == "flow":
        flow_leads(args.target, args.user_ids, auto_yes=args.yes)
    elif args.command == "upload":
        upload_file(args.upload_type, args.file_path, auto_yes=args.yes)
    elif args.command == "batch-allot-upload":
        batch_allot_upload(args.role, args.file_path, auto_yes=args.yes)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
