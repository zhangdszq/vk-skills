#!/usr/bin/env python3
"""
auth_helper.py - 权限系统辅助工具

用法：
  python3 auth_helper.py auth-check
  python3 auth_helper.py refresh-token [--timeout 300] [--headless]                # 通过 Playwright 独立登录并自动刷新 token
  python3 auth_helper.py refresh-token --mode cdp --port 9222                      # 可选：通过已开启 CDP 的 Chrome 读取 token
  python3 auth_helper.py role-list --app-id 1 [--start 0] [--limit 10] [--menu-code CODE]
  python3 auth_helper.py role-detail <roleId>
  python3 auth_helper.py user-search-email <keyword>
  python3 auth_helper.py user-search-name <name>
  python3 auth_helper.py user-basic <userId>
  python3 auth_helper.py user-detail <userId>
  python3 auth_helper.py user-login-strategy <userId>
  python3 auth_helper.py user-orgs <userId>
  python3 auth_helper.py user-role-list <userId> --app-id 2 [--owned-only] [--vk-cr-code hk]
  python3 auth_helper.py role-permissions <roleId>
  python3 auth_helper.py user-permissions <userId> --app-id 1 [--vk-cr-code hk] [--cr-codes hk,ts,k2] [--include-unowned]
  python3 auth_helper.py org-tree
  python3 auth_helper.py org-detail <orgId>
  python3 auth_helper.py app-list [--name leads] [--code leads-management]
  python3 auth_helper.py app-detail <appId>
  python3 auth_helper.py business-list [--code ae]
  python3 auth_helper.py menu-tree --app-id 1
  python3 auth_helper.py permission-check /api/parent/list
  python3 auth_helper.py user-role-add --app-id 4 --user-id 32383527 --role-ids 1,2 [--role-codes A,B] [--confirm]
  python3 auth_helper.py user-role-delete --id 2646 [--confirm]
  python3 auth_helper.py user-role-delete --user-id 18054465 --role-codes SUPER_ADMIN [--confirm]
  python3 auth_helper.py role-menu-add --role-id 2446 --menu-ids 9657,9658 [--confirm]
  python3 auth_helper.py role-menu-add --app-id 1 --role-code ROLE_CODE --menu-codes MENU_A,MENU_B [--confirm]
  python3 auth_helper.py role-menu-delete --role-id 2335 --menu-ids 9433 [--confirm]
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


CONFIG_PATH = Path.home() / ".vipkid-auth" / "config.json"
CURRENT_SCRIPT_PATH = Path(__file__).resolve()
DEFAULT_AUTH_BASE_URL = "https://power.lionabc.com/"
DEFAULT_CDP_PORT = 9222
DEFAULT_REFRESH_MODE = "playwright"
DEFAULT_LOGIN_TIMEOUT_SECONDS = 300
DEFAULT_PLAYWRIGHT_PROFILE_DIR = CONFIG_PATH.parent / "playwright-profile"
LOGIN_TYPE_LABELS = {
    0: "密码登录",
    1: "验证码登录",
}


def load_config(required=False):
    if not CONFIG_PATH.exists():
        if required:
            print(f"[ERROR] 配置文件不存在：{CONFIG_PATH}")
            print("请先创建配置文件，并补齐权限系统配置。")
            sys.exit(1)
        return {"auth_base_url": DEFAULT_AUTH_BASE_URL}

    with open(CONFIG_PATH, encoding="utf-8") as file_obj:
        config = json.load(file_obj)

    config.setdefault("auth_base_url", DEFAULT_AUTH_BASE_URL)
    config.setdefault("auth_app_code", "")
    config.setdefault("auth_vk_cr_code", "")
    config.setdefault("auth_cookie", "")
    config.setdefault("auth_authorization", "")
    config.setdefault("auth_intl_auth_token", "")
    return config


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as file_obj:
        json.dump(config, file_obj, indent=2, ensure_ascii=False)
        file_obj.write("\n")


def require_auth_config():
    config = load_config(required=True)
    app_code = str(config.get("auth_app_code", "")).strip()
    cr_code = str(config.get("auth_vk_cr_code", "")).strip()
    cookie = str(config.get("auth_cookie", "")).strip()
    authorization = str(config.get("auth_authorization", "")).strip()
    intl_auth_token = str(config.get("auth_intl_auth_token", "")).strip()

    missing_fields = []
    if not app_code:
        missing_fields.append("auth_app_code")
    if not cr_code:
        missing_fields.append("auth_vk_cr_code")
    if not any([cookie, authorization, intl_auth_token]):
        missing_fields.append("auth_cookie / auth_authorization / auth_intl_auth_token（至少一个）")

    if missing_fields:
        print("[ERROR] 权限系统配置不完整：")
        for field_name in missing_fields:
            print(f"  - {field_name}")
        print("建议先在 ~/.vipkid-auth/config.json 中补齐上述字段。")
        print("若只缺少登录态，优先运行以下命令自动获取 token：")
        print(f"  python3 {CURRENT_SCRIPT_PATH} refresh-token")
        sys.exit(1)

    return config


def upsert_cookie_value(cookie_header, cookie_name, cookie_value):
    items = []
    for part in str(cookie_header or "").split(";"):
        segment = part.strip()
        if not segment:
            continue
        key, sep, value = segment.partition("=")
        if key.strip() == cookie_name:
            continue
        items.append(f"{key.strip()}{sep}{value.strip()}" if sep else key.strip())
    items.append(f"{cookie_name}={cookie_value}")
    return "; ".join(items)


def build_headers_from_values(
    app_code,
    cr_code,
    auth_cookie="",
    auth_authorization="",
    auth_intl_auth_token="",
):
    headers = {
        "app-code": str(app_code).strip(),
        "vk-cr-code": str(cr_code).strip(),
        "Accept": "application/json",
    }
    auth_cookie = str(auth_cookie).strip()
    auth_authorization = str(auth_authorization).strip()
    auth_intl_auth_token = str(auth_intl_auth_token).strip()
    if auth_cookie:
        headers["Cookie"] = auth_cookie
    elif auth_intl_auth_token:
        headers["Cookie"] = f"intlAuthToken={auth_intl_auth_token}"
    if auth_authorization:
        headers["Authorization"] = auth_authorization
    if auth_intl_auth_token:
        headers["intlAuthToken"] = auth_intl_auth_token
    return headers


def build_headers_from_config(config):
    return build_headers_from_values(
        config.get("auth_app_code", ""),
        config.get("auth_vk_cr_code", ""),
        auth_cookie=config.get("auth_cookie", ""),
        auth_authorization=config.get("auth_authorization", ""),
        auth_intl_auth_token=config.get("auth_intl_auth_token", ""),
    )


def build_headers():
    config = require_auth_config()
    return config, build_headers_from_config(config)


def build_url(base_url, path, params=None):
    normalized_base = normalize_auth_base_url(base_url)
    normalized_path = path if path.startswith("/") else f"/{path}"
    url = f"{normalized_base}{normalized_path}"
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        url = f"{url}?{query}"
    return url


def normalize_auth_base_url(base_url):
    normalized_base = str(base_url).rstrip("/")
    if normalized_base.endswith("/rest/auth"):
        return normalized_base
    return f"{normalized_base}/rest/auth"


def get_auth_browser_url(base_url):
    normalized_base = str(base_url).rstrip("/")
    if normalized_base.endswith("/rest/auth"):
        normalized_base = normalized_base[: -len("/rest/auth")]
    return normalized_base or DEFAULT_AUTH_BASE_URL.rstrip("/")


def api_request_with_headers(base_url, headers, method, path, params=None, data=None):
    payload = None
    if method.upper() == "POST":
        headers = dict(headers)
        headers["Content-Type"] = "application/json"
        payload = json.dumps(data or {}, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        build_url(base_url, path, params),
        headers=headers,
        data=payload,
        method=method.upper(),
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8")
            return parse_response_body(body)
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        parsed = parse_response_body(body)
        if isinstance(parsed, dict):
            parsed.setdefault("http_error", error.code)
            return parsed
        return {"http_error": error.code, "body": parsed}
    except urllib.error.URLError as error:
        return {"network_error": str(error.reason)}


def api_request(method, path, params=None, data=None):
    config, headers = build_headers()
    return api_request_with_headers(config["auth_base_url"], headers, method, path, params=params, data=data)


def api_request_for_vk_cr_code(vk_cr_code, method, path, params=None, data=None):
    config = require_auth_config()
    headers = build_headers_from_values(
        config.get("auth_app_code", ""),
        vk_cr_code,
        auth_cookie=config.get("auth_cookie", ""),
        auth_authorization=config.get("auth_authorization", ""),
        auth_intl_auth_token=config.get("auth_intl_auth_token", ""),
    )
    return api_request_with_headers(config["auth_base_url"], headers, method, path, params=params, data=data)


def parse_response_body(body):
    try:
        return json.loads(body)
    except Exception:
        return {"raw_body": body}


def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


def run_refresh_command(command, timeout_seconds):
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError as error:
        print(f"[ERROR] 未检测到命令：{error.filename}")
        return None
    except subprocess.TimeoutExpired:
        print("❌ 自动获取 token 超时。")
        return None


def can_validate_login_state(config):
    return bool(str(config.get("auth_app_code", "")).strip() and str(config.get("auth_vk_cr_code", "")).strip())


def validate_login_state(config, token):
    auth_base_url = config.get("auth_base_url", DEFAULT_AUTH_BASE_URL)
    headers = build_headers_from_values(
        config.get("auth_app_code", ""),
        config.get("auth_vk_cr_code", ""),
        auth_cookie=upsert_cookie_value("", "intlAuthToken", token),
        auth_authorization=token,
        auth_intl_auth_token=token,
    )
    resp = api_request_with_headers(auth_base_url, headers, "POST", "/api/auth/isLogin", data={})
    is_valid = isinstance(resp, dict) and resp.get("code") == 200 and resp.get("data")
    return bool(is_valid), resp


def refresh_token(
    mode=DEFAULT_REFRESH_MODE,
    port=DEFAULT_CDP_PORT,
    timeout_seconds=DEFAULT_LOGIN_TIMEOUT_SECONDS,
    profile_dir=DEFAULT_PLAYWRIGHT_PROFILE_DIR,
    headless=False,
):
    config = load_config(required=False)
    auth_base_url = config.get("auth_base_url", DEFAULT_AUTH_BASE_URL)
    browser_url = get_auth_browser_url(auth_base_url)
    profile_dir = Path(profile_dir).expanduser()

    if mode == "playwright":
        script_path = Path(__file__).with_name("get_token_via_playwright.py")
        if not script_path.exists():
            print(f"[ERROR] 未找到 Playwright 脚本：{script_path}")
            return False

        command = [
            sys.executable,
            str(script_path),
            "--url",
            browser_url,
            "--cookie",
            "intlAuthToken",
            "--timeout",
            str(timeout_seconds),
            "--profile-dir",
            str(profile_dir),
        ]
        if headless:
            command.append("--headless")

        print(f"正在打开独立 Chrome 窗口，使用专用登录目录：{profile_dir}")
        print("请在弹出的浏览器里完成登录，脚本会在检测到 intlAuthToken 后自动关闭窗口。")
        result = run_refresh_command(command, timeout_seconds + 90)
        failure_hints = [
            "  1. 是否已在弹出的独立 Chrome 窗口中完成登录",
            "  2. 登录成功后 Cookie 中是否存在 intlAuthToken",
            f"  3. 如需重置专用登录态，可删除目录：{profile_dir}",
        ]
        success_message = f"✅ 已通过 Playwright 读取 intlAuthToken，并写入 {CONFIG_PATH}"
    else:
        script_path = Path(__file__).with_name("get_token_via_cdp.js")
        if not script_path.exists():
            print(f"[ERROR] 未找到 CDP 脚本：{script_path}")
            return False

        command = [
            "node",
            str(script_path),
            "--port",
            str(port),
            "--url",
            browser_url,
            "--cookie",
            "intlAuthToken",
        ]
        result = run_refresh_command(command, 30)
        failure_hints = [
            f"  1. Chrome 是否已使用 --remote-debugging-port={port} 启动",
            f"  2. 是否已在 Chrome 中登录 {get_auth_browser_url(browser_url)}",
            "  3. Cookie 中是否存在 intlAuthToken",
        ]
        success_message = f"✅ 已通过 Chrome CDP 读取 intlAuthToken，并写入 {CONFIG_PATH}"

    if result is None:
        return False

    token = result.stdout.strip()
    error_output = result.stderr.strip()
    if result.returncode != 0 or not token:
        print("❌ 自动获取 token 失败。")
        if error_output:
            print(error_output)
        print("可检查：")
        for hint in failure_hints:
            print(hint)
        return False

    validation_skipped = False
    if can_validate_login_state(config):
        is_valid, validation_resp = validate_login_state(config, token)
        if not is_valid:
            print("❌ 自动获取 token 失败：检测到的 intlAuthToken 登录态无效。")
            print("登录态校验响应：")
            print_json(validation_resp)
            print("可检查：")
            for hint in failure_hints:
                print(hint)
            return False
    else:
        validation_skipped = True

    config["auth_base_url"] = auth_base_url
    config["auth_cookie"] = upsert_cookie_value(config.get("auth_cookie", ""), "intlAuthToken", token)
    config["auth_intl_auth_token"] = token
    save_config(config)
    print(success_message)
    if validation_skipped:
        print("⚠️ 当前缺少 auth_app_code 或 auth_vk_cr_code，暂时跳过了自动登录态校验。")
    return True


def with_login_type_label(user_data):
    if not isinstance(user_data, dict):
        return user_data
    login_type = user_data.get("loginType")
    if login_type in LOGIN_TYPE_LABELS:
        user_data = dict(user_data)
        user_data["loginTypeLabel"] = LOGIN_TYPE_LABELS[login_type]
    return user_data


def parse_int_list(raw_value):
    items = []
    for part in str(raw_value).split(","):
        value = part.strip()
        if value:
            try:
                items.append(int(value))
            except ValueError:
                print(f"[ERROR] 需要传入整数列表，检测到非法值：{value}")
                sys.exit(1)
    return items


def parse_str_list(raw_value):
    items = []
    for part in str(raw_value).split(","):
        value = part.strip()
        if value:
            items.append(value)
    return items


def resolve_vk_cr_codes(vk_cr_code=None, cr_codes=None):
    single_code = str(vk_cr_code or "").strip()
    multi_codes = parse_str_list(cr_codes or "")
    if single_code and multi_codes:
        print("[ERROR] --vk-cr-code 与 --cr-codes 不能同时传。")
        sys.exit(1)
    if multi_codes:
        return multi_codes
    if single_code:
        return [single_code]

    config = require_auth_config()
    default_code = str(config.get("auth_vk_cr_code", "")).strip()
    if not default_code:
        print("[ERROR] 当前未配置 auth_vk_cr_code，请显式传入 --vk-cr-code 或 --cr-codes。")
        sys.exit(1)
    return [default_code]


def preview_write_action(action_name, path, payload, confirm):
    print(f"即将执行写操作：{action_name}")
    print(f"接口：{path}")
    print("请求体预览：")
    print_json(payload)
    if not confirm:
        print("当前仅预览，未实际调用。若确认执行，请追加 --confirm。")
        return False
    return True


def summarize_menu_items(menu_items):
    pages = []
    buttons = []
    for item in menu_items or []:
        entry = {
            "id": item.get("id"),
            "code": item.get("code"),
            "name": item.get("name"),
            "url": item.get("url"),
            "parentId": item.get("parentId"),
        }
        if item.get("type") == 0:
            pages.append(entry)
        elif item.get("type") == 1:
            buttons.append(entry)
    return pages, buttons


def build_menu_item_key(item):
    item_id = item.get("id")
    if item_id is not None:
        return f"id:{item_id}"

    item_code = item.get("code")
    if item_code:
        return f"code:{item_code}"

    return "fallback:{parent_id}:{name}:{url}".format(
        parent_id=item.get("parentId"),
        name=item.get("name") or "",
        url=item.get("url") or "",
    )


def build_role_summary(role_data):
    if not isinstance(role_data, dict):
        return {}
    return {
        "roleId": role_data.get("id") if role_data.get("id") is not None else role_data.get("roleId"),
        "roleCode": role_data.get("code") if role_data.get("code") is not None else role_data.get("roleCode"),
        "roleName": role_data.get("name") if role_data.get("name") is not None else role_data.get("roleName"),
        "businessId": role_data.get("businessId"),
        "authStatus": role_data.get("authStatus"),
        "owned": role_data.get("authStatus") == 1,
    }


def role_is_owned(role_data):
    return bool(isinstance(role_data, dict) and role_data.get("authStatus") == 1)


def command_refresh_token(args):
    ok = refresh_token(
        mode=args.mode,
        port=args.port,
        timeout_seconds=args.timeout,
        profile_dir=args.profile_dir,
        headless=args.headless,
    )
    if not ok:
        sys.exit(1)


def command_auth_check(_args):
    resp = api_request("POST", "/api/auth/isLogin", data={})
    print_json(resp)


def command_role_list(args):
    params = {
        "appId": args.app_id,
        "page.start": args.start,
        "page.limit": args.limit,
    }
    if args.name:
        params["name"] = args.name
    if args.code:
        params["code"] = args.code
    if args.menu_code:
        params["menuCode"] = args.menu_code
    resp = api_request("GET", "/api/role/list", params=params)
    print_json(resp)


def command_role_detail(args):
    resp = api_request("GET", "/api/role/detail", params={"id": args.role_id})
    print_json(resp)


def command_user_search_email(args):
    resp = api_request("GET", "/api/auth/user/searchByEmail", params={"email": args.keyword})
    print_json(resp)


def command_user_search_name(args):
    resp = api_request("GET", "/api/user/getUserList", params={"name": args.name})
    print_json(resp)


def command_user_basic(args):
    resp = api_request("GET", "/api/user/getById", params={"id": args.user_id})
    if isinstance(resp, dict) and resp.get("data"):
        resp = dict(resp)
        resp["data"] = with_login_type_label(resp["data"])
    print_json(resp)


def command_user_detail(args):
    resp = api_request("GET", "/api/user/getById", params={"id": args.user_id})
    if isinstance(resp, dict) and resp.get("data"):
        resp = dict(resp)
        resp["data"] = with_login_type_label(resp["data"])
    print_json(resp)


def command_user_login_strategy(args):
    resp = api_request("GET", "/api/user/getById", params={"id": args.user_id})
    if not isinstance(resp, dict) or resp.get("code") != 200 or not resp.get("data"):
        print_json(resp)
        return
    data = resp["data"]
    result = {
        "id": data.get("id"),
        "name": data.get("name"),
        "email": data.get("email"),
        "loginType": data.get("loginType"),
        "loginTypeLabel": LOGIN_TYPE_LABELS.get(data.get("loginType"), "未知"),
        "status": data.get("status"),
        "lastLoginDateTime": data.get("lastLoginDateTime"),
    }
    print_json(result)


def command_user_orgs(args):
    resp = api_request("GET", "/api/user/getUserOrgList", params={"id": args.user_id})
    print_json(resp)


def command_user_role_list(args):
    request_func = api_request_for_vk_cr_code if args.vk_cr_code else api_request
    request_args = (
        args.vk_cr_code,
        "GET",
        "/api/role/userRole/list",
    ) if args.vk_cr_code else (
        "GET",
        "/api/role/userRole/list",
    )
    resp = request_func(
        *request_args,
        params={"userId": args.user_id, "appId": args.app_id},
    )
    if not isinstance(resp, dict) or resp.get("code") != 200 or not isinstance(resp.get("data"), list):
        print_json(resp)
        return

    roles = resp.get("data") or []
    result = dict(resp)
    result["returnedRoleCount"] = len(roles)
    result["ownedRoleCount"] = sum(1 for role in roles if role_is_owned(role))
    if args.vk_cr_code:
        result["vkCrCode"] = args.vk_cr_code
    if args.owned_only:
        result["data"] = [role for role in roles if role_is_owned(role)]
        result["warning"] = "原始接口会返回当前应用在该业务线下的全部角色；这里只保留 authStatus=1 的真实拥有角色。"
    print_json(result)


def command_org_tree(_args):
    resp = api_request("GET", "/api/org/getOrgTrees")
    print_json(resp)


def command_org_detail(args):
    resp = api_request("GET", "/api/org/getDetail", params={"orgId": args.org_id})
    print_json(resp)


def command_app_list(args):
    params = {}
    if args.name:
        params["name"] = args.name
    if args.code:
        params["code"] = args.code
    if args.status is not None:
        params["status"] = args.status
    resp = api_request("GET", "/api/app/getAppList", params=params or None)
    print_json(resp)


def command_app_detail(args):
    resp = api_request("GET", "/api/app/getById", params={"id": args.app_id})
    print_json(resp)


def command_business_list(args):
    params = {}
    if args.code:
        params["code"] = args.code
    if args.status is not None:
        params["status"] = args.status
    resp = api_request("GET", "/api/business/getList", params=params or None)
    print_json(resp)


def command_menu_tree(args):
    resp = api_request("GET", "/api/menuTree/getAllTreeMenus", params={"appId": args.app_id})
    print_json(resp)


def command_role_permissions(args):
    resp = api_request("GET", "/api/role/detail", params={"id": args.role_id})
    if not isinstance(resp, dict) or resp.get("code") != 200 or not resp.get("data"):
        print_json(resp)
        return
    role_detail = resp["data"]
    pages, buttons = summarize_menu_items(role_detail.get("menuTreeList") or [])
    result = {
        "roleId": role_detail.get("id"),
        "roleCode": role_detail.get("code"),
        "roleName": role_detail.get("name"),
        "menuCount": len(role_detail.get("menuTreeList") or []),
        "pageCount": len(pages),
        "buttonCount": len(buttons),
        "pages": pages,
        "buttons": buttons,
    }
    print_json(result)


def command_user_permissions(args):
    requested_cr_codes = resolve_vk_cr_codes(args.vk_cr_code, args.cr_codes)
    role_summaries = []
    unique_pages = {}
    unique_buttons = {}
    failed_roles = []
    skipped_roles = []
    per_cr = []
    returned_role_count = 0
    owned_role_count = 0

    for vk_cr_code in requested_cr_codes:
        roles_resp = api_request_for_vk_cr_code(
            vk_cr_code,
            "GET",
            "/api/role/userRole/list",
            params={"userId": args.user_id, "appId": args.app_id},
        )
        if not isinstance(roles_resp, dict) or roles_resp.get("code") != 200:
            failed_roles.append({
                "vkCrCode": vk_cr_code,
                "reason": "员工角色查询失败",
                "detailResponse": roles_resp,
            })
            continue

        roles = roles_resp.get("data") or []
        returned_role_count += len(roles)
        current_owned_roles = [role for role in roles if role_is_owned(role)]
        owned_role_count += len(current_owned_roles)
        included_roles = roles if args.include_unowned else current_owned_roles

        per_cr_item = {
            "vkCrCode": vk_cr_code,
            "returnedRoleCount": len(roles),
            "ownedRoleCount": len(current_owned_roles),
            "includedRoleCount": len(included_roles),
        }
        if not args.include_unowned:
            current_skipped_roles = [
                {
                    **build_role_summary(role),
                    "vkCrCode": vk_cr_code,
                    "reason": "authStatus != 1，当前用户并未拥有该角色",
                }
                for role in roles
                if not role_is_owned(role)
            ]
            skipped_roles.extend(current_skipped_roles)
            per_cr_item["skippedRoleCount"] = len(current_skipped_roles)
        per_cr.append(per_cr_item)

        for role in included_roles:
            role_summary = build_role_summary(role)
            role_id = role_summary.get("roleId")
            if role_id is None:
                failed_roles.append({
                    **role_summary,
                    "vkCrCode": vk_cr_code,
                    "reason": "缺少角色 ID，无法继续查询角色详情",
                })
                continue

            detail_resp = api_request_for_vk_cr_code(vk_cr_code, "GET", "/api/role/detail", params={"id": role_id})
            if not isinstance(detail_resp, dict) or detail_resp.get("code") != 200 or not detail_resp.get("data"):
                failed_roles.append({
                    **role_summary,
                    "vkCrCode": vk_cr_code,
                    "reason": "角色详情查询失败",
                    "detailResponse": detail_resp,
                })
                continue
            detail = detail_resp["data"]
            pages, buttons = summarize_menu_items(detail.get("menuTreeList") or [])
            for item in pages:
                unique_pages[build_menu_item_key(item)] = item
            for item in buttons:
                unique_buttons[build_menu_item_key(item)] = item
            role_summaries.append({
                "vkCrCode": vk_cr_code,
                "businessId": detail.get("businessId"),
                "authStatus": role.get("authStatus"),
                "owned": role_is_owned(role),
                "roleId": detail.get("id"),
                "roleCode": detail.get("code"),
                "roleName": detail.get("name"),
                "pageCount": len(pages),
                "buttonCount": len(buttons),
                "pages": pages,
                "buttons": buttons,
            })

    result = {
        "userId": args.user_id,
        "appId": args.app_id,
        "requestedCrCodes": requested_cr_codes,
        "includeUnowned": bool(args.include_unowned),
        "returnedRoleCount": returned_role_count,
        "ownedRoleCount": owned_role_count,
        "roleCount": len(role_summaries),
        "skippedRoleCount": len(skipped_roles),
        "failedRoleCount": len(failed_roles),
        "uniquePageCount": len(unique_pages),
        "uniqueButtonCount": len(unique_buttons),
        "uniquePages": list(unique_pages.values()),
        "uniqueButtons": list(unique_buttons.values()),
        "roles": role_summaries,
        "perCr": per_cr,
    }
    if skipped_roles:
        result["skippedRoles"] = skipped_roles
        result["warning"] = "GET /api/role/userRole/list 会返回当前应用在该业务线下的全部角色；默认只统计 authStatus=1 的真实拥有角色。"
    if failed_roles:
        result["failedRoles"] = failed_roles
        failure_warning = "部分角色详情查询失败，当前结果不是完整权限视图，不能直接按“无权限”解读。"
        if result.get("warning"):
            result["warning"] = f"{result['warning']} {failure_warning}"
        else:
            result["warning"] = failure_warning
    print_json(result)


def command_permission_check(args):
    resp = api_request("GET", "/api/auth/permission/function/check", params={"url": args.url})
    print_json(resp)


def command_user_role_add(args):
    role_id_list = parse_int_list(args.role_ids)
    if not role_id_list:
        print("[ERROR] 添加员工角色时，必须提供至少一个 roleId。")
        sys.exit(1)

    payload = {
        "appId": args.app_id,
        "userId": args.user_id,
        "roleIdList": role_id_list,
    }
    if args.role_codes:
        payload["roleCodeList"] = parse_str_list(args.role_codes)
    if not preview_write_action("添加员工角色", "/api/role/userRole/add", payload, args.confirm):
        return
    resp = api_request("POST", "/api/role/userRole/add", data=payload)
    print_json(resp)


def command_user_role_delete(args):
    if args.id is not None and (args.user_id is not None or args.role_codes):
        print("[ERROR] 删除员工角色时，--id 与 --user-id/--role-codes 不能同时传。")
        sys.exit(1)

    if args.id is not None:
        path = "/api/role/userRole/delete"
        payload = {"id": args.id}
        if not preview_write_action("删除员工角色", path, payload, args.confirm):
            return
        resp = api_request("GET", path, params=payload)
        print_json(resp)
        return

    role_codes = parse_str_list(args.role_codes or "")
    if not args.user_id or not role_codes:
        print("[ERROR] 删除员工角色时，必须提供 --id，或同时提供 --user-id 与 --role-codes。")
        sys.exit(1)

    path = "/api/role/userRole/deleteByRoleCode"
    payload = {"userId": args.user_id, "roleCodes": ",".join(role_codes)}
    if not preview_write_action("按角色码删除员工角色", path, payload, args.confirm):
        return
    resp = api_request("GET", path, params=payload)
    print_json(resp)


def command_role_menu_add(args):
    use_role_id_mode = args.role_id is not None or args.menu_ids is not None
    use_role_code_mode = args.app_id is not None or bool(args.role_code) or bool(args.menu_codes)

    if use_role_id_mode and use_role_code_mode:
        print("[ERROR] 添加角色菜单时，--role-id/--menu-ids 与 --app-id/--role-code/--menu-codes 不能同时传。")
        sys.exit(1)

    if use_role_id_mode:
        if args.role_id is None:
            print("[ERROR] 使用 roleId 方式添加角色菜单时，必须提供 --role-id。")
            sys.exit(1)
        payload = {
            "roleId": args.role_id,
            "menuIds": parse_int_list(args.menu_ids or ""),
        }
        if not payload["menuIds"]:
            print("[ERROR] 使用 roleId 方式添加角色菜单时，必须提供 --menu-ids。")
            sys.exit(1)
        path = "/api/roleMenu/add"
        if not preview_write_action("添加角色菜单", path, payload, args.confirm):
            return
        resp = api_request("POST", path, data=payload)
        print_json(resp)
        return

    menu_codes = parse_str_list(args.menu_codes or "")
    if args.app_id is None or not args.role_code or not menu_codes:
        print("[ERROR] 使用角色码方式添加角色菜单时，必须提供 --app-id、--role-code、--menu-codes。")
        sys.exit(1)

    path = "/api/roleMenu/addByCode"
    payload = {
        "appId": args.app_id,
        "roleCode": args.role_code,
        "menuCodes": menu_codes,
    }
    if not preview_write_action("按角色码添加角色菜单", path, payload, args.confirm):
        return
    resp = api_request("POST", path, data=payload)
    print_json(resp)


def command_role_menu_delete(args):
    payload = {
        "roleId": args.role_id,
        "menuIds": parse_int_list(args.menu_ids),
    }
    if not payload["menuIds"]:
        print("[ERROR] 删除角色菜单时必须提供至少一个 menuId。")
        sys.exit(1)
    if not preview_write_action("删除角色菜单", "/api/roleMenu/delete", payload, args.confirm):
        return
    resp = api_request("POST", "/api/roleMenu/delete", data=payload)
    print_json(resp)


def build_parser():
    parser = argparse.ArgumentParser(description="权限系统辅助工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh_token_parser = subparsers.add_parser("refresh-token", help="自动刷新权限系统 token")
    refresh_token_parser.add_argument(
        "--mode",
        choices=("playwright", "cdp"),
        default=os.environ.get("VIPKID_TOKEN_REFRESH_MODE", DEFAULT_REFRESH_MODE),
        help="取 token 方式，默认使用 Playwright。",
    )
    refresh_token_parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("VIPKID_CHROME_CDP_PORT", DEFAULT_CDP_PORT)),
        help="CDP 模式下的远程调试端口。",
    )
    refresh_token_parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("VIPKID_TOKEN_WAIT_TIMEOUT", DEFAULT_LOGIN_TIMEOUT_SECONDS)),
        help="Playwright 模式下等待登录的秒数。",
    )
    refresh_token_parser.add_argument(
        "--profile-dir",
        default=str(DEFAULT_PLAYWRIGHT_PROFILE_DIR),
        help="Playwright 独立浏览器配置目录。",
    )
    refresh_token_parser.add_argument(
        "--headless",
        action="store_true",
        help="以无头模式运行 Playwright，主要用于自动化验证。",
    )
    refresh_token_parser.set_defaults(func=command_refresh_token)

    auth_check_parser = subparsers.add_parser("auth-check", help="验证权限系统登录态")
    auth_check_parser.set_defaults(func=command_auth_check)

    role_list_parser = subparsers.add_parser("role-list", help="查询角色列表")
    role_list_parser.add_argument("--app-id", type=int, required=True)
    role_list_parser.add_argument("--start", type=int, default=0)
    role_list_parser.add_argument("--limit", type=int, default=10)
    role_list_parser.add_argument("--name")
    role_list_parser.add_argument("--code")
    role_list_parser.add_argument("--menu-code")
    role_list_parser.set_defaults(func=command_role_list)

    role_detail_parser = subparsers.add_parser("role-detail", help="查询角色详情")
    role_detail_parser.add_argument("role_id", type=int)
    role_detail_parser.set_defaults(func=command_role_detail)

    user_search_parser = subparsers.add_parser("user-search-email", help="按邮箱搜索员工")
    user_search_parser.add_argument("keyword")
    user_search_parser.set_defaults(func=command_user_search_email)

    user_search_name_parser = subparsers.add_parser("user-search-name", help="按姓名搜索员工")
    user_search_name_parser.add_argument("name")
    user_search_name_parser.set_defaults(func=command_user_search_name)

    user_basic_parser = subparsers.add_parser("user-basic", help="查询员工基础信息")
    user_basic_parser.add_argument("user_id", type=int)
    user_basic_parser.set_defaults(func=command_user_basic)

    user_detail_parser = subparsers.add_parser("user-detail", help="查询员工详情")
    user_detail_parser.add_argument("user_id", type=int)
    user_detail_parser.set_defaults(func=command_user_detail)

    user_login_strategy_parser = subparsers.add_parser("user-login-strategy", help="查询员工登录策略")
    user_login_strategy_parser.add_argument("user_id", type=int)
    user_login_strategy_parser.set_defaults(func=command_user_login_strategy)

    user_orgs_parser = subparsers.add_parser("user-orgs", help="查询员工组织归属")
    user_orgs_parser.add_argument("user_id", type=int)
    user_orgs_parser.set_defaults(func=command_user_orgs)

    user_role_list_parser = subparsers.add_parser("user-role-list", help="查询员工角色")
    user_role_list_parser.add_argument("user_id", type=int)
    user_role_list_parser.add_argument("--app-id", type=int, required=True)
    user_role_list_parser.add_argument("--owned-only", action="store_true")
    user_role_list_parser.add_argument("--vk-cr-code")
    user_role_list_parser.set_defaults(func=command_user_role_list)

    org_tree_parser = subparsers.add_parser("org-tree", help="查询组织树")
    org_tree_parser.set_defaults(func=command_org_tree)

    org_detail_parser = subparsers.add_parser("org-detail", help="查询组织详情")
    org_detail_parser.add_argument("org_id", type=int)
    org_detail_parser.set_defaults(func=command_org_detail)

    app_list_parser = subparsers.add_parser("app-list", help="查询应用列表")
    app_list_parser.add_argument("--name")
    app_list_parser.add_argument("--code")
    app_list_parser.add_argument("--status", type=int)
    app_list_parser.set_defaults(func=command_app_list)

    app_detail_parser = subparsers.add_parser("app-detail", help="查询应用详情")
    app_detail_parser.add_argument("app_id", type=int)
    app_detail_parser.set_defaults(func=command_app_detail)

    business_list_parser = subparsers.add_parser("business-list", help="查询业务线列表")
    business_list_parser.add_argument("--code")
    business_list_parser.add_argument("--status", type=int)
    business_list_parser.set_defaults(func=command_business_list)

    menu_tree_parser = subparsers.add_parser("menu-tree", help="查询菜单树")
    menu_tree_parser.add_argument("--app-id", type=int, required=True)
    menu_tree_parser.set_defaults(func=command_menu_tree)

    role_permissions_parser = subparsers.add_parser("role-permissions", help="查询角色对应的页面和按钮权限")
    role_permissions_parser.add_argument("role_id", type=int)
    role_permissions_parser.set_defaults(func=command_role_permissions)

    user_permissions_parser = subparsers.add_parser("user-permissions", help="汇总员工在某应用下的页面和按钮权限")
    user_permissions_parser.add_argument("user_id", type=int)
    user_permissions_parser.add_argument("--app-id", type=int, required=True)
    user_permissions_parser.add_argument("--vk-cr-code")
    user_permissions_parser.add_argument("--cr-codes")
    user_permissions_parser.add_argument("--include-unowned", action="store_true")
    user_permissions_parser.set_defaults(func=command_user_permissions)

    permission_check_parser = subparsers.add_parser("permission-check", help="校验功能权限")
    permission_check_parser.add_argument("url")
    permission_check_parser.set_defaults(func=command_permission_check)

    user_role_add_parser = subparsers.add_parser("user-role-add", help="添加员工角色")
    user_role_add_parser.add_argument("--app-id", type=int, required=True)
    user_role_add_parser.add_argument("--user-id", type=int, required=True)
    user_role_add_parser.add_argument("--role-ids", required=True)
    user_role_add_parser.add_argument("--role-codes")
    user_role_add_parser.add_argument("--confirm", action="store_true")
    user_role_add_parser.set_defaults(func=command_user_role_add)

    user_role_delete_parser = subparsers.add_parser("user-role-delete", help="删除员工角色")
    user_role_delete_parser.add_argument("--id", type=int)
    user_role_delete_parser.add_argument("--user-id", type=int)
    user_role_delete_parser.add_argument("--role-codes")
    user_role_delete_parser.add_argument("--confirm", action="store_true")
    user_role_delete_parser.set_defaults(func=command_user_role_delete)

    role_menu_add_parser = subparsers.add_parser("role-menu-add", help="添加角色菜单")
    role_menu_add_parser.add_argument("--role-id", type=int)
    role_menu_add_parser.add_argument("--menu-ids")
    role_menu_add_parser.add_argument("--app-id", type=int)
    role_menu_add_parser.add_argument("--role-code")
    role_menu_add_parser.add_argument("--menu-codes")
    role_menu_add_parser.add_argument("--confirm", action="store_true")
    role_menu_add_parser.set_defaults(func=command_role_menu_add)

    role_menu_delete_parser = subparsers.add_parser("role-menu-delete", help="删除角色菜单")
    role_menu_delete_parser.add_argument("--role-id", type=int, required=True)
    role_menu_delete_parser.add_argument("--menu-ids", required=True)
    role_menu_delete_parser.add_argument("--confirm", action="store_true")
    role_menu_delete_parser.set_defaults(func=command_role_menu_delete)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
