#!/usr/bin/env python3
"""
SMB Server connector with automatic proxy/DNS bypass.
Handles Clash Verge fake-ip, cross-platform mounting, and authentication.
Credentials are stored in ~/.vk-cowork/smb-config.json on first use.

Usage:
  python3 smb_connect.py                          # use saved config (or prompt)
  python3 smb_connect.py --share 双师智学2026      # connect to a different share
  python3 smb_connect.py --check                   # check if already mounted
  python3 smb_connect.py --list-shares             # list all shares
  python3 smb_connect.py --reconfigure             # re-enter credentials
"""

import argparse
import getpass
import json
import os
import platform
import re
import socket
import sys
import time
from pathlib import Path

from preflight import ensure_connect_prerequisites, run


CONFIG_DIR = Path.home() / ".vk-cowork"
CONFIG_FILE = CONFIG_DIR / "smb-config.json"
MOUNT_BASE_MAC = "/tmp/smb_mounts"
MOUNT_BASE_WIN = "Z:"
DEFAULT_DOMAIN = "vipkid.work"


# Config management

def load_config():
    cfg = {}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    if not cfg.get("domain"):
        cfg["domain"] = DEFAULT_DOMAIN
    return cfg


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    CONFIG_FILE.chmod(0o600)
    print(f"[config] Saved to {CONFIG_FILE}")


def prompt_config(existing=None):
    """Interactive prompt for server credentials."""
    cfg = existing or {}
    print("── SMB 服务器配置 ──")
    cfg["server"] = input(f"  服务器主机名 [{cfg.get('server', '')}]: ").strip() or cfg.get("server", "")
    cfg["domain"] = input(f"  企业域名 [{cfg.get('domain', DEFAULT_DOMAIN)}]: ").strip() or cfg.get("domain", DEFAULT_DOMAIN)
    cfg["default_share"] = input(f"  默认共享名 [{cfg.get('default_share', '')}]: ").strip() or cfg.get("default_share", "")
    cfg["user"] = input(f"  用户名(不含邮箱域名) [{cfg.get('user', '')}]: ").strip() or cfg.get("user", "")
    pwd = getpass.getpass(f"  密码 [{'****' if cfg.get('password') else ''}]: ")
    if pwd:
        cfg["password"] = pwd
    print()

    if not all(cfg.get(k) for k in ("server", "user", "password")):
        print("[error] server、user、password 为必填项")
        sys.exit(1)

    save_config(cfg)
    return cfg


def get_config(args):
    """Load config, prompt if missing, apply CLI overrides."""
    cfg = load_config()

    if args.init:
        if args.server:
            cfg["server"] = args.server
        if args.share:
            cfg["default_share"] = args.share
        if args.user:
            cfg["user"] = args.user
        if args.password:
            cfg["password"] = args.password
        if args.domain:
            cfg["domain"] = args.domain
        if not all(cfg.get(k) for k in ("server", "user", "password")):
            print("[error] --init requires --server, --user, --password")
            sys.exit(1)
        save_config(cfg)
        return cfg

    if args.reconfigure:
        if sys.stdin.isatty():
            cfg = prompt_config(cfg)
        else:
            print("[error] --reconfigure requires interactive terminal, or use --init with CLI args")
            sys.exit(1)

    if not cfg.get("server") or not cfg.get("user") or not cfg.get("password"):
        if sys.stdin.isatty():
            cfg = prompt_config(cfg)
        else:
            print("[error] No config found at", CONFIG_FILE)
            print("[hint] Run with --init --server X --user Y --password Z to create config")
            sys.exit(1)

    if args.server:
        cfg["server"] = args.server
    if args.share:
        cfg["default_share"] = args.share
    if args.user:
        cfg["user"] = args.user
    if args.password:
        cfg["password"] = args.password
    if args.domain:
        cfg["domain"] = args.domain

    return cfg


# Network helpers

def detect_dhcp_dns():
    code, out, _ = run("ipconfig getpacket en0")
    if code != 0:
        return []
    dns_servers = []
    for line in out.splitlines():
        if "domain_name_server" in line:
            ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', line)
            dns_servers.extend(ips)
    return dns_servers


def detect_clash_tun():
    code, out, _ = run("ifconfig")
    if code != 0:
        return False
    for line in out.splitlines():
        if "198.18.0." in line and "utun" in out:
            return True
    return False


def clash_api_query_dns(hostname, domain):
    sock_path = "/tmp/verge/verge-mihomo.sock"
    if not os.path.exists(sock_path):
        return None
    fqdn = f"{hostname}.{domain}" if "." not in hostname else hostname
    code, out, _ = run(
        f"curl -s --unix-socket {sock_path} "
        f"'http://localhost/dns/query?name={fqdn}&type=A'"
    )
    if code != 0:
        return None
    try:
        data = json.loads(out)
        for ans in data.get("Answer", []):
            if ans.get("type") == 1:
                return ans["data"]
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def patch_clash_dns_for_domain(domain, dns_servers):
    sock_path = "/tmp/verge/verge-mihomo.sock"
    if not os.path.exists(sock_path):
        return False

    config_path = os.path.expanduser(
        "~/Library/Application Support/"
        "io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml"
    )
    if not os.path.exists(config_path):
        return False

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    domain_pattern = f"+.{domain}"
    needs_update = False

    if "fake-ip-filter:" not in content:
        content = content.replace(
            "fake-ip-range: 198.18.0.1/16",
            f"fake-ip-range: 198.18.0.1/16\n"
            f"  fake-ip-filter:\n"
            f"  - '*.lan'\n  - '*.local'\n  - '*.arpa'\n"
            f"  - {domain_pattern}",
        )
        needs_update = True
    elif domain_pattern not in content:
        content = content.replace(
            "fake-ip-filter:\n",
            f"fake-ip-filter:\n  - {domain_pattern}\n",
        )
        needs_update = True

    if "nameserver-policy:" not in content or domain_pattern not in content:
        dns_list = "\n".join(f"    - {s}" for s in dns_servers)
        if "nameserver-policy:" not in content:
            idx = content.find("fake-ip-range:")
            line_end = content.find("\n", idx)
            content = (
                content[:line_end + 1]
                + f"  nameserver-policy:\n    '{domain_pattern}':\n{dns_list}\n"
                + content[line_end + 1:]
            )
        elif domain_pattern not in content.split("nameserver-policy")[1][:200]:
            content = content.replace(
                "nameserver-policy:\n",
                f"nameserver-policy:\n    '{domain_pattern}':\n{dns_list}\n",
            )
        needs_update = True

    if needs_update:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(content)
        code, _, _ = run(
            f"curl -s --unix-socket {sock_path} -X PUT "
            f"'http://localhost/configs?force=true' "
            f"-H 'Content-Type: application/json' "
            f'-d \'{{"path":"{config_path}"}}\''
        )
        time.sleep(2)
        return code == 0

    return True


def resolve_server(hostname, domain):
    fqdn = f"{hostname}.{domain}" if ("." not in hostname and domain) else hostname
    is_tun = detect_clash_tun()

    if is_tun and domain:
        print(f"[info] Clash TUN detected, checking DNS bypass for {domain}...")
        real_ip = clash_api_query_dns(hostname, domain)
        if real_ip and not real_ip.startswith("198.18."):
            print(f"[info] Resolved {fqdn} -> {real_ip}")
            return real_ip

        dhcp_dns = detect_dhcp_dns()
        if dhcp_dns:
            print(f"[info] Corporate DNS: {dhcp_dns}, patching Clash config...")
            patch_clash_dns_for_domain(domain, dhcp_dns)
            real_ip = clash_api_query_dns(hostname, domain)
            if real_ip and not real_ip.startswith("198.18."):
                print(f"[info] Resolved {fqdn} -> {real_ip} (after patch)")
                return real_ip

        for dns in dhcp_dns:
            code, out, _ = run(f"dig @{dns} {fqdn} +short +timeout=3 +tcp")
            if code == 0 and out and not out.startswith("198.18."):
                print(f"[info] Resolved via TCP DNS: {fqdn} -> {out}")
                return out.splitlines()[0]

    try:
        ip = socket.gethostbyname(fqdn)
        if not ip.startswith("198.18."):
            return ip
    except socket.gaierror:
        pass

    print(f"[error] Cannot resolve {fqdn}. Check VPN/network connection.")
    sys.exit(1)


def check_port(ip, port=445, timeout=5):
    try:
        sock = socket.create_connection((ip, port), timeout=timeout)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


# Mount

def mount_smb_mac(ip, share, user, password):
    mount_point = os.path.join(MOUNT_BASE_MAC, share.replace(" ", "_"))
    code, out, _ = run(f"mount | grep '{mount_point}'")
    if code == 0 and out:
        print(f"[info] Already mounted at {mount_point}")
        return mount_point

    os.makedirs(mount_point, exist_ok=True)
    pwd_escaped = password.replace("@", "%40").replace("#", "%23").replace("&", "%26")
    cmd = f"mount_smbfs -o nobrowse '//{user}:{pwd_escaped}@{ip}/{share}' '{mount_point}'"
    code, out, err = run(cmd)
    if code != 0:
        print(f"[error] Mount failed: {err or out}")
        if "Authentication" in (err + out):
            print("[hint] Run with --reconfigure to re-enter credentials")
        sys.exit(1)
    print(f"[ok] Mounted //{ip}/{share} -> {mount_point}")
    return mount_point


def mount_smb_win(ip, share, user, password, drive=MOUNT_BASE_WIN):
    code, out, _ = run(f'net use {drive}', shell=True)
    if code == 0 and ip in out:
        print(f"[info] Already mapped to {drive}")
        return drive

    cmd = f'net use {drive} \\\\{ip}\\{share} /user:{user} "{password}" /persistent:no'
    code, out, err = run(cmd)
    if code != 0:
        print(f"[error] Map failed: {err or out}")
        sys.exit(1)
    print(f"[ok] Mapped \\\\{ip}\\{share} -> {drive}")
    return drive


def list_shares(ip, user, password):
    pwd_escaped = password.replace("@", "%40").replace("#", "%23")
    code, out, err = run(f"smbutil view '//{user}:{pwd_escaped}@{ip}'")
    if code != 0:
        print(f"[error] Cannot list shares: {err}")
        return
    print(out)


def main():
    parser = argparse.ArgumentParser(description="SMB Server Connector")
    parser.add_argument("--server", help="Server hostname (override config)")
    parser.add_argument("--share", help="Share name (override config)")
    parser.add_argument("--user", help="Username (override config)")
    parser.add_argument("--password", help="Password (override config)")
    parser.add_argument("--check-tools", action="store_true", help="Check and install required command line tools if needed")
    parser.add_argument("--check", action="store_true", help="Check existing mounts")
    parser.add_argument("--list-shares", action="store_true", help="List server shares")
    parser.add_argument("--reconfigure", action="store_true", help="Re-enter and save credentials")
    parser.add_argument("--init", action="store_true", help="Create/update config from CLI args and save")
    parser.add_argument("--domain", help=f"Corporate domain for DNS (default: {DEFAULT_DOMAIN})")
    parser.add_argument("--drive", default=MOUNT_BASE_WIN, help="Windows drive letter")
    args = parser.parse_args()

    setup_status = ensure_connect_prerequisites()
    if setup_status == "pending":
        return
    if setup_status == "error":
        sys.exit(1)

    if args.check_tools:
        print("[ok] Required command line tools are available.")
        return

    if args.check:
        if platform.system() == "Darwin":
            code, out, _ = run("mount | grep smb")
            print(out if out else "No SMB mounts found.")
        else:
            code, out, _ = run("net use")
            print(out if out else "No mapped drives found.")
        return

    cfg = get_config(args)
    server = cfg["server"]
    share = cfg.get("default_share", "")
    user = cfg["user"]
    password = cfg["password"]
    domain = cfg.get("domain", "")

    ip = resolve_server(server, domain)
    print(f"[info] Server IP: {ip}")

    if not check_port(ip):
        print(f"[error] SMB port 445 not reachable on {ip}")
        sys.exit(1)

    if args.list_shares:
        list_shares(ip, user, password)
        return

    if not share:
        print("[error] No share specified. Use --share or set default_share in config.")
        print("[hint] Run --list-shares to see available shares.")
        sys.exit(1)

    if platform.system() == "Darwin":
        path = mount_smb_mac(ip, share, user, password)
    elif platform.system() == "Windows":
        path = mount_smb_win(ip, share, user, password, args.drive)
    else:
        print(f"[error] Unsupported OS: {platform.system()}")
        sys.exit(1)

    print(f"\n[ready] Mount path: {path}")
    print(f"  Browse: ls '{path}'")


if __name__ == "__main__":
    main()
