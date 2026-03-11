# 故障排查指南

## 1. Clash Verge Fake-IP DNS 劫持

**症状**: DNS 解析返回 198.18.0.x，SMB 连接超时或 "socket was closed"。

**原因**: Clash Verge TUN 模式拦截所有 DNS（`dns-hijack: any:53`），返回 fake-ip。公共 DNS 查不到 `HT-FILE2.vipkid.work`（NXDOMAIN），但 fake-ip 仍分配假 IP。

**诊断**:
```bash
ifconfig | grep "198.18.0"        # 存在 utun 接口则 TUN 模式活跃
dig HT-FILE2.vipkid.work +short   # 返回 198.18.0.x 则被劫持
ipconfig getpacket en0             # 获取 DHCP 分配的企业 DNS
```

**解决**: `smb_connect.py` 自动处理，手动方式如下：

1. 修改 `~/Library/Application Support/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml`
2. 在 `dns:` 段添加 `fake-ip-filter: [+.vipkid.work]`
3. 添加 `nameserver-policy: {'+.vipkid.work': ['172.24.101.3', '172.24.101.2']}`
4. 通过 unix socket 重载：
   ```bash
   curl -s --unix-socket /tmp/verge/verge-mihomo.sock \
     -X PUT 'http://localhost/configs?force=true' \
     -H 'Content-Type: application/json' \
     -d '{"path":"<config_path>"}'
   ```

## 2. 缺少 Command Line Tools

**症状**: 脚本提示缺少 `mount_smbfs`、`smbutil`、`dig` 等命令，或首次运行前要求安装工具。

**诊断**:
```bash
python3 smb_connect.py --check-tools
xcode-select -p
```

**解决**:
1. macOS 下若缺少 Xcode Command Line Tools，脚本会自动触发：
   ```bash
   xcode-select --install
   ```
2. 完成安装后，重新运行：
   ```bash
   python3 smb_connect.py --check-tools
   python3 smb_connect.py
   ```
3. 若仍提示缺少命令，检查当前 shell 的 `PATH` 是否包含系统命令目录。

## 3. 认证失败

**症状**: `smbutil: server rejected the authentication`

**原因**: 用户名格式错误。SMB 认证使用不含邮箱域名的用户名。

**解决**: 运行 `python3 smb_connect.py --reconfigure` 重新输入凭据。密码中的 `@` 由脚本自动处理。

## 4. mount_smbfs 静默失败 (exit 1, 无输出)

**症状**: `mount_smbfs` 返回退出码 1，无任何错误信息。

**原因**: 挂载点目录已被占用或不干净。

**解决**:
```bash
umount /tmp/smb_mounts/<share> 2>/dev/null
rmdir /tmp/smb_mounts/<share>
python3 smb_connect.py
```

## 5. 大文件下载中断

**症状**: 复制大文件时网络中断。

**解决**: 使用 `smb_download.py`，支持 `.partial` 文件断点续传：
```bash
python3 smb_download.py /path/to/source ./local/ --bw-limit 5M
```
中断后重新运行同一命令即可自动续传。

## 6. Windows 系统连接

```cmd
python3 smb_connect.py
```

脚本会自动使用 `net use` 映射驱动器。如果主机名无法解析，可用 `--server <IP>` 直接指定 IP。
