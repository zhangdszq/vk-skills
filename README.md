# vk-skills

Agent Skills 技能库。

## 技能列表

| 技能 | 说明 |
|------|------|
| [vipkid-ops](vipkid-ops/) | VIPKID 国际化运营后台助理，支持商品包查询/新建/修改、库存、优惠券、赠送权限配置 |
| [dingtalk-task-stats](dingtalk-task-stats/) | 钉钉 AI 表格任务统计与需求看板分析，全量拉取记录后按字段过滤、聚合统计 |
| [curriculum-outline-editor](curriculum-outline-editor/) | 4-6 岁儿童英语课程大纲审校工具，修复中式英语、优化词汇复现结构，输出修订版 Excel 及中文变更摘要 |
| [minimax-tts](minimax-tts/) | 使用 MiniMax API 将文本转成语音并自动播放，支持情绪与语速参数 |
| [smb-file-browser](smb-file-browser/) | 企业 SMB 文件服务器检索工具，供**教研团队**使用，支持共享浏览、快速搜索与文件下载 |
| [aliyun-sms-bulk](aliyun-sms-bulk/) | 阿里云短信群发工具，供**市场部**使用，支持单发与批量群发（单次最多 100 个号码），适用于营销通知、活动推送等场景 |
| [adjust-report](adjust-report/) | Adjust 归因数据分析工具，供**投放运营**使用，拉取 Report API 数据生成 SKAN（iOS）和标准（Android）漏斗报表，自动计算转化率并给出优化建议 |

## 安装

```bash
# macOS / Linux
ln -s ~/git-repos/vk-skills/<skill-name> ~/.claude/skills/<skill-name>
ln -s ~/git-repos/vk-skills/<skill-name> ~/.cursor/skills/<skill-name>

# Windows (PowerShell 管理员)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\skills\<skill-name>" -Target "D:\git-repos\vk-skills\<skill-name>"
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.cursor\skills\<skill-name>" -Target "D:\git-repos\vk-skills\<skill-name>"
```
