# 教研 SMB Server 信息

## 配置

首次运行 `smb_connect.py` 时会交互式询问以下信息并保存到 `~/.vk-cowork/smb-config.json`。如果用户未特别说明，`domain` 默认使用 `vipkid.work`。

| 字段 | 说明 | 示例 |
|------|------|------|
| server | 服务器主机名 | HT-FILE2 |
| domain | 企业域名（用于 DNS 解析，默认预设） | vipkid.work |
| default_share | 默认共享名 | DMFile |
| user | 用户名（不含邮箱域名） | panxiaoying |
| password | 密码 | — |

配置文件权限设为 600（仅本人可读）。重新配置：`python3 smb_connect.py --reconfigure`

注意：SMB 认证用户名通常不含邮箱域名部分（如用 `panxiaoying` 而非 `panxiaoying@vipkid.com.cn`）。

## 典型目录结构

以「双师智学2026」共享为例：

```text
双师智学2026/
├── 00 S&S/              (课程结构表、Language Map)
├── level 1/ ~ level 6/  (各 U1~U12 课件)
├── 双师智学社群Trial课/  (Level 0~6 Trial 课)
├── 培训物料/             (课件修改指南、培训录屏、字体包)
└── 待支持修改课程/       (原课件、修改后、Final)
```
