"""
Adjust Report API 数据拉取脚本

用法:
  python adjust_report.py skan --start 2026-02-01 --end 2026-02-11
  python adjust_report.py skan --start 2026-02-01 --end 2026-02-11 --by campaign
  python adjust_report.py skan --start 2026-02-01 --end 2026-02-11 --by day
  python adjust_report.py android --start 2026-02-01 --end 2026-02-11
  python adjust_report.py android --start 2026-02-01 --end 2026-02-11 --by campaign
  python adjust_report.py compare --start 2026-02-01 --end 2026-02-11
  python adjust_report.py metrics
  python adjust_report.py skan --start 2026-02-01 --end 2026-02-11 --csv output.csv
"""

import argparse
import csv
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

REPORT_URL = "https://automate.adjust.com/reports-service/report"
FILTERS_URL = "https://automate.adjust.com/reports-service/filters_data"

SKAN_EVENT_METRICS = [
    "skad_installs",
    "注册（发送验证码）_events_est",
    "注册_events_est",
    "添加孩子_events_est",
    "约试听课_events_est",
    "试听完课_events_est",
    "付费_events_est",
]

ANDROID_EVENT_METRICS = [
    "installs",
    "注册（发送验证码）_events",
    "注册_events",
    "添加孩子_events",
    "约试听课_events",
    "试听完课_events",
    "付费_events",
]

DISPLAY_NAMES = {
    "skad_installs": "安装(SKAN)",
    "installs": "安装",
    "注册（发送验证码）_events_est": "验证码",
    "注册_events_est": "注册",
    "添加孩子_events_est": "添加孩子",
    "约试听课_events_est": "约试听",
    "试听完课_events_est": "完试听",
    "付费_events_est": "付费",
    "注册（发送验证码）_events": "验证码",
    "注册_events": "注册",
    "添加孩子_events": "添加孩子",
    "约试听课_events": "约试听",
    "试听完课_events": "完试听",
    "付费_events": "付费",
}


def load_credentials():
    config_path = Path.home() / ".vk-cowork" / "adjust_credentials.json"
    if not config_path.exists():
        print("错误: 未找到 Adjust 凭证。请先运行:")
        print(f"  python {Path(__file__).parent / 'token_store.py'} save --api-token <TOKEN> --app-token <TOKEN>")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def api_request(url, params, api_token):
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    full_url = f"{url}?{query}"
    req = urllib.request.Request(full_url, headers={"Authorization": f"Bearer {api_token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {body[:500]}")
        sys.exit(1)


def get_dimensions(by):
    if by == "campaign":
        return "network,campaign,campaign_id_network"
    elif by == "day":
        return "day,network"
    else:
        return "network"


def get_group_key(row, by):
    if by == "campaign":
        network = row.get("network", "unknown")
        campaign = row.get("campaign", "") or row.get("campaign_network", "") or "unknown"
        return f"{network} / {campaign}"
    elif by == "day":
        return f"{row.get('day', '')} | {row.get('network', 'unknown')}"
    else:
        return row.get("network", "unknown")


def print_funnel(title, rows, metrics, by, install_key):
    print()
    print(f"{'=' * 100}")
    print(title)
    print(f"{'=' * 100}")
    print()

    # 按 group 聚合
    groups = {}
    for row in rows:
        key = get_group_key(row, by)
        if key not in groups:
            groups[key] = {}
        for m in metrics:
            val = float(row.get(m, 0) or 0)
            groups[key][m] = groups[key].get(m, 0) + val

    # 过滤全零行
    groups = {k: v for k, v in groups.items() if any(v.get(m, 0) > 0 for m in metrics)}

    if not groups:
        print("  无数据")
        return groups

    # 漏斗绝对值
    col_width = max(8, max(len(DISPLAY_NAMES.get(m, m)) for m in metrics) + 2)
    label_width = min(50, max(len(k) for k in groups) + 2) if groups else 30

    header = f"{'名称':<{label_width}}"
    for m in metrics:
        header += f" {DISPLAY_NAMES.get(m, m):>{col_width}}"
    print(header)
    print("-" * len(header.encode("gbk", errors="replace")))

    sorted_keys = sorted(groups.keys(), key=lambda x: -groups[x].get(install_key, 0))
    for key in sorted_keys:
        data = groups[key]
        line = f"{key:<{label_width}}"
        for m in metrics:
            val = int(data.get(m, 0))
            line += f" {val:>{col_width}}" if val else f" {'—':>{col_width}}"
        print(line)

    # 转化率（相对安装）
    print()
    header2 = f"{'名称':<{label_width}}"
    for m in metrics[1:]:
        header2 += f" {'→' + DISPLAY_NAMES.get(m, m):>{col_width}}"
    print(header2)
    print("-" * len(header2.encode("gbk", errors="replace")))

    for key in sorted_keys:
        data = groups[key]
        installs = data.get(install_key, 0)
        if installs == 0:
            continue
        line = f"{key:<{label_width}}"
        for m in metrics[1:]:
            val = data.get(m, 0)
            pct = f"{val / installs * 100:.1f}%" if val else "—"
            line += f" {pct:>{col_width}}"
        print(line)

    # 环节间转化率
    print()
    step_labels = []
    for i in range(1, len(metrics)):
        prev_name = DISPLAY_NAMES.get(metrics[i - 1], metrics[i - 1])[:3]
        curr_name = DISPLAY_NAMES.get(metrics[i], metrics[i])[:3]
        step_labels.append(f"{prev_name}→{curr_name}")

    header3 = f"{'名称':<{label_width}}"
    for label in step_labels:
        header3 += f" {label:>{col_width}}"
    print(header3)
    print("-" * len(header3.encode("gbk", errors="replace")))

    for key in sorted_keys:
        data = groups[key]
        if data.get(install_key, 0) == 0:
            continue
        line = f"{key:<{label_width}}"
        for i in range(1, len(metrics)):
            prev_val = data.get(metrics[i - 1], 0)
            curr_val = data.get(metrics[i], 0)
            if prev_val > 0:
                pct = f"{curr_val / prev_val * 100:.0f}%"
            else:
                pct = "—"
            line += f" {pct:>{col_width}}"
        print(line)

    return groups


def export_csv(groups, metrics, output_path):
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        header = ["名称"] + [DISPLAY_NAMES.get(m, m) for m in metrics]
        writer.writerow(header)
        for key in sorted(groups.keys()):
            row = [key] + [int(groups[key].get(m, 0)) for m in metrics]
            writer.writerow(row)
    print(f"\n已导出: {output_path}")


def cmd_skan(args, creds):
    params = {
        "app_token__in": creds["app_token"],
        "date_period": f"{args.start}:{args.end}",
        "dimensions": get_dimensions(args.by),
        "metrics": ",".join(SKAN_EVENT_METRICS),
        "os_names": "ios",
    }
    data = api_request(REPORT_URL, params, creds["api_token"])
    rows = data.get("rows", [])
    groups = print_funnel(
        f"iOS SKAN 漏斗 ({args.start} ~ {args.end}, 按{args.by})",
        rows, SKAN_EVENT_METRICS, args.by, "skad_installs"
    )
    if args.csv and groups:
        export_csv(groups, SKAN_EVENT_METRICS, args.csv)

    # JSON 输出供上层解析
    print(f"\n__JSON_DATA__")
    print(json.dumps({"platform": "ios_skan", "period": f"{args.start}:{args.end}",
                       "by": args.by, "rows": rows, "totals": data.get("totals", {})},
                      ensure_ascii=False))


def cmd_android(args, creds):
    params = {
        "app_token__in": creds["app_token"],
        "date_period": f"{args.start}:{args.end}",
        "dimensions": get_dimensions(args.by),
        "metrics": ",".join(ANDROID_EVENT_METRICS),
        "os_names": "android",
    }
    data = api_request(REPORT_URL, params, creds["api_token"])
    rows = data.get("rows", [])
    groups = print_funnel(
        f"Android 漏斗 ({args.start} ~ {args.end}, 按{args.by})",
        rows, ANDROID_EVENT_METRICS, args.by, "installs"
    )
    if args.csv and groups:
        export_csv(groups, ANDROID_EVENT_METRICS, args.csv)

    print(f"\n__JSON_DATA__")
    print(json.dumps({"platform": "android", "period": f"{args.start}:{args.end}",
                       "by": args.by, "rows": rows, "totals": data.get("totals", {})},
                      ensure_ascii=False))


def cmd_compare(args, creds):
    # iOS SKAN
    skan_data = api_request(REPORT_URL, {
        "app_token__in": creds["app_token"],
        "date_period": f"{args.start}:{args.end}",
        "dimensions": "network",
        "metrics": ",".join(SKAN_EVENT_METRICS),
        "os_names": "ios",
    }, creds["api_token"])

    # Android
    android_data = api_request(REPORT_URL, {
        "app_token__in": creds["app_token"],
        "date_period": f"{args.start}:{args.end}",
        "dimensions": "network",
        "metrics": ",".join(ANDROID_EVENT_METRICS),
        "os_names": "android",
    }, creds["api_token"])

    print_funnel(
        f"iOS SKAN 漏斗 ({args.start} ~ {args.end})",
        skan_data.get("rows", []), SKAN_EVENT_METRICS, "network", "skad_installs"
    )
    print_funnel(
        f"Android 漏斗 ({args.start} ~ {args.end})",
        android_data.get("rows", []), ANDROID_EVENT_METRICS, "network", "installs"
    )


def cmd_metrics(args, creds):
    data = api_request(FILTERS_URL, {"required_filters": "skad_metrics"}, creds["api_token"])
    metrics = data.get("skad_metrics", [])
    print(f"共 {len(metrics)} 个 SKAN metrics\n")
    for item in metrics:
        if isinstance(item, dict):
            print(f"  {item.get('id', ''):<50} {item.get('name', '')}")


def main():
    parser = argparse.ArgumentParser(description="Adjust Report 数据拉取")
    sub = parser.add_subparsers(dest="command")

    default_end = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    default_start = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

    for name, func in [("skan", cmd_skan), ("android", cmd_android)]:
        cmd = sub.add_parser(name)
        cmd.add_argument("--start", default=default_start, help="开始日期")
        cmd.add_argument("--end", default=default_end, help="结束日期")
        cmd.add_argument("--by", default="network", choices=["network", "campaign", "day"], help="维度")
        cmd.add_argument("--csv", default=None, help="导出 CSV 路径")

    compare_cmd = sub.add_parser("compare")
    compare_cmd.add_argument("--start", default=default_start)
    compare_cmd.add_argument("--end", default=default_end)

    sub.add_parser("metrics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    creds = load_credentials()

    if args.command == "skan":
        cmd_skan(args, creds)
    elif args.command == "android":
        cmd_android(args, creds)
    elif args.command == "compare":
        cmd_compare(args, creds)
    elif args.command == "metrics":
        cmd_metrics(args, creds)


if __name__ == "__main__":
    main()
