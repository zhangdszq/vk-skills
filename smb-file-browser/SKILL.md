---
name: smb-file-browser
description: >
  连接 VIPKID 教研 SMB 文件服务器（HT-FILE2），浏览和下载课件文件。
  自动处理 Clash Verge fake-ip DNS 劫持、跨平台（macOS/Windows）挂载、
  大文件低带宽下载。首次扫描建立本地索引后搜索秒出。
  当用户提到"教研服务器"、"SMB"、"HT-FILE2"、"DMFile"、"双师智学"、
  "课件文件"、"文件服务器"、"共享文件夹"、"课件搜索"时触发。
---

# 教研 SMB Server 文件检索

## 首次连接

配置文件：`~/.vk-cowork/smb-config.json`

如果配置不存在，**必须先向用户询问以下信息**（不要猜测或编造）：
1. 服务器主机名（如 HT-FILE2）
2. 企业域名（如 vipkid.work）
3. 默认共享名（如 DMFile）
4. 用户名（不含邮箱域名部分）
5. 密码

收集完毕后通过 CLI 参数初始化配置并连接：

```bash
python3 scripts/smb_connect.py \
  --server <主机名> --share <共享名> --user <用户名> --password '<密码>' \
  --init --domain <企业域名>
```

配置存在后直接连接：

```bash
python3 scripts/smb_connect.py                         # 用已存配置连接
python3 scripts/smb_connect.py --share 双师智学2026      # 连不同共享
python3 scripts/smb_connect.py --list-shares            # 列出所有共享
python3 scripts/smb_connect.py --reconfigure            # 重新输入凭据（同样先问用户）
```

自动执行：加载配置 → 检测 Clash TUN → 获取企业 DNS → 修补 fake-ip → 解析真实 IP → 挂载。

## 文件搜索（带本地缓存）

首次搜索会建立本地索引（~70s），之后搜索 <0.1s。索引缓存在 `~/.cache/smb-file-index/`。

```bash
# 目录树（直接读 SMB，不用索引）
python3 scripts/smb_search.py /tmp/smb_mounts/DMFile/双师智学2026 --tree --max-depth 2

# 按文件类型搜索（自动建索引/用缓存）
python3 scripts/smb_search.py /tmp/smb_mounts/DMFile/双师智学2026 --ext pptx --sort size --top 10

# 按路径+类型搜索
python3 scripts/smb_search.py /tmp/smb_mounts/DMFile/双师智学2026 --ext xlsx --path-contains "level 1"

# 按文件名模式
python3 scripts/smb_search.py /tmp/smb_mounts/DMFile/双师智学2026 --name "*U1*"

# 大文件排查
python3 scripts/smb_search.py /tmp/smb_mounts/DMFile/双师智学2026 --size-gt 100M --sort size

# 索引统计（文件总数、大小、类型分布）
python3 scripts/smb_search.py /tmp/smb_mounts/DMFile/双师智学2026 --stats

# 强制重建索引
python3 scripts/smb_search.py /tmp/smb_mounts/DMFile/双师智学2026 --rebuild --ext pptx
```

## 文件下载

```bash
# 下载单个文件
python3 scripts/smb_download.py /tmp/smb_mounts/DMFile/双师智学2026/培训物料/xxx.pptx ./downloads/

# 下载目录中的 pptx，限速 5MB/s
python3 scripts/smb_download.py /tmp/smb_mounts/DMFile/双师智学2026/level\ 1/ ./downloads/ --ext pptx --bw-limit 5M

# 仅预览不下载
python3 scripts/smb_download.py /tmp/smb_mounts/DMFile/双师智学2026/ ./downloads/ --dry-run
```

支持 `.partial` 断点续传——中断后重跑同一命令自动继续。

## 低带宽策略

- `--tree --max-depth 2` 快速概览结构（只读顶层目录）
- 搜索优先用缓存索引，避免重复扫描 SMB
- `--dry-run` 预览再下载
- `--bw-limit 5M` 防止占满带宽
- `--ext` / `--name` 缩小范围后再下载
- 索引超过 24h 提示刷新，`--rebuild` 强制重建

## 参考

- 服务器信息与目录结构: [references/server-info.md](references/server-info.md)
- 故障排查指南: [references/troubleshooting.md](references/troubleshooting.md)
