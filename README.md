# vk-skills

Agent Skills 技能库。

## 技能列表

<table>
<tr>
  <th>部门</th><th>技能</th><th>说明</th>
</tr>
<tr>
  <td>运营</td>
  <td><a href="vipkid-ops/">vipkid-ops</a></td>
  <td>国际化运营后台助理，支持商品包查询/新建/修改、库存、优惠券、赠送权限配置</td>
</tr>
<tr>
  <td rowspan="2">教研</td>
  <td><a href="curriculum-outline-editor/">curriculum-outline-editor</a></td>
  <td>4-6 岁儿童英语课程大纲审校工具，修复中式英语、优化词汇复现结构，输出修订版 Excel 及中文变更摘要</td>
</tr>
<tr>
  <td><a href="smb-file-browser/">smb-file-browser</a></td>
  <td>企业 SMB 文件服务器检索工具，支持默认域名、自检、共享浏览、快速搜索与低带宽下载</td>
</tr>
<tr>
  <td rowspan="2">市场</td>
  <td><a href="aliyun-sms-bulk/">aliyun-sms-bulk</a></td>
  <td>阿里云短信群发工具，支持单发与批量群发（单次最多 100 个号码），适用于营销通知、活动推送等场景</td>
</tr>
<tr>
  <td><a href="adjust-report/">adjust-report</a></td>
  <td>Adjust 归因数据分析工具，拉取 Report API 数据生成 SKAN（iOS）和标准（Android）漏斗报表，自动计算转化率并给出优化建议</td>
</tr>
<tr>
  <td rowspan="2">其它</td>
  <td><a href="dingtalk-task-stats/">dingtalk-task-stats</a></td>
  <td>钉钉 AI 表格任务统计与需求看板分析，全量拉取记录后按字段过滤、聚合统计</td>
</tr>
<tr>
  <td><a href="minimax-tts/">minimax-tts</a></td>
  <td>使用 MiniMax API 将文本转成语音并自动播放，支持情绪与语速参数</td>
</tr>
</table>

## 安装

```bash
# macOS / Linux
ln -s ~/git-repos/vk-skills/<skill-name> ~/.claude/skills/<skill-name>
ln -s ~/git-repos/vk-skills/<skill-name> ~/.cursor/skills/<skill-name>

# Windows (PowerShell 管理员)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\skills\<skill-name>" -Target "D:\git-repos\vk-skills\<skill-name>"
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.cursor\skills\<skill-name>" -Target "D:\git-repos\vk-skills\<skill-name>"
```
