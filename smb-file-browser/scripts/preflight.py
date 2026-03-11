#!/usr/bin/env python3
"""
Shared preflight checks for SMB helper scripts.
"""

import os
import platform
import shutil
import subprocess


REQUIRED_MAC_COMMANDS = ["mount_smbfs", "smbutil", "curl", "dig", "ifconfig", "ipconfig"]
REQUIRED_WIN_COMMANDS = ["net"]


def run(cmd, timeout=15, shell=True):
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as exc:
        return -1, "", str(exc)


def command_exists(cmd):
    return shutil.which(cmd) is not None


def has_xcode_command_line_tools():
    code, out, _ = run("xcode-select -p")
    return code == 0 and bool(out)


def trigger_xcode_command_line_tools_install():
    print("[setup] Xcode Command Line Tools not found, launching installer...")
    code, out, err = run("xcode-select --install")
    message = f"{out}\n{err}".strip().lower()
    if "already installed" in message:
        print("[info] Xcode Command Line Tools already installed.")
        return "installed"
    if code != 0:
        print(f"[error] Failed to launch installer: {err or out}")
        print("[hint] Run `xcode-select --install` manually, then rerun this command.")
        return "error"
    print("[action] Complete the installation in the popup window, then rerun this command.")
    return "pending"


def ensure_connect_prerequisites():
    system = platform.system()

    if system == "Darwin":
        if not has_xcode_command_line_tools():
            status = trigger_xcode_command_line_tools_install()
            if status == "pending":
                return "pending"
            if status == "error":
                return "error"

        missing = [cmd for cmd in REQUIRED_MAC_COMMANDS if not command_exists(cmd)]
        if missing:
            print(f"[error] Missing required command line tools: {', '.join(missing)}")
            print("[hint] Verify Xcode Command Line Tools are installed and PATH is correct.")
            return "error"

    elif system == "Windows":
        missing = [cmd for cmd in REQUIRED_WIN_COMMANDS if not command_exists(cmd)]
        if missing:
            print(f"[error] Missing required system commands: {', '.join(missing)}")
            print("[hint] Open Command Prompt / PowerShell with standard Windows system PATH.")
            return "error"

    return "ok"


def ensure_cache_dir(cache_dir):
    try:
        os.makedirs(cache_dir, exist_ok=True)
    except OSError as exc:
        print(f"[error] Cannot create cache dir {cache_dir}: {exc}")
        return False

    if not os.access(cache_dir, os.W_OK):
        print(f"[error] Cache dir is not writable: {cache_dir}")
        return False

    print(f"[ok] Cache dir ready: {cache_dir}")
    return True


def ensure_existing_path(path, label="Path", should_be_dir=None, mount_hint=False):
    if not path:
        return True

    if not os.path.exists(path):
        print(f"[error] {label} not found: {path}")
        if mount_hint:
            print("[hint] Mount the SMB share first with `python3 scripts/smb_connect.py`.")
        return False

    if should_be_dir is True and not os.path.isdir(path):
        print(f"[error] {label} is not a directory: {path}")
        return False

    if should_be_dir is False and not os.path.isfile(path):
        print(f"[error] {label} is not a file: {path}")
        return False

    print(f"[ok] {label} ready: {os.path.abspath(path)}")
    return True


def ensure_writable_dir(path, label="Directory"):
    if not path:
        return True

    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        print(f"[error] Cannot create {label.lower()} {path}: {exc}")
        return False

    if not os.access(path, os.W_OK):
        print(f"[error] {label} is not writable: {path}")
        return False

    print(f"[ok] {label} ready: {os.path.abspath(path)}")
    return True
