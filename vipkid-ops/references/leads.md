# Leads 管理页参考

Base URL：`https://sa-leads.lionabc.com`

REST Base：`/rest/leadsgw`

---

## 真实请求头（直调接口时）

Leads 列表接口与商品包接口不共用同一套请求头。实测直连 `sa-leads` 时，至少应带这些头：

- `authorization: <intlAuthToken>`
- `vk-cr-code: sa`
- `app-code: leads-management`
- `biz-line: sa`
- `web-site: sa`
- `Referer: https://sa-leads.lionabc.com/leadsGCC/list`

补充说明：

- 直接复用商品包那套 `intlAuthToken + Cookie + app-code: international-mgt` 模板，容易返回 `Forwarding error`
- 列表接口成功响应实测为 `code=0`，不要按商品包接口的 `code=200` 判断

---

## 页面定位

- 路由：`/leadsGCC/list`
- 路由名：`leadsGCCList`
- 一级权限码：`LEADS_MANAGEMENT_LEADS_MANAGE`
- 页面模式：私池 Leads，对应查询参数 `status=1`
- 首页 `/` 默认跳转到该页
- 进入页面后会切到业务线时区

---

## 页面核心能力

### 顶部筛选

| 页面字段 | 请求参数 | 说明 |
|------|------|------|
| 渠道 | `channelCode` / `channelLevelId` | 来自渠道级联选择器 |
| 节点 | `flowNodeList` | 多选 |
| 节点生成时间 | `lastFlowTimeStart` / `lastFlowTimeEnd` | 毫秒时间戳 |
| 家长 ID | `userId` | 精确查家长 |
| 学生 ID | `studentId` | 精确查学生 |
| 地区 | `countryCode` | 只填区号不填手机号时前端会报错 |
| 手机号 | `mobile` | 前端会过滤成纯数字 |
| 归属 GCC | `staffId` | 远程搜索员工 |
| 归属 GCS | `gcsName` | 私池页通常展示 GCC / TMK，GCS 更常见于公海 |
| 归属 TMK | `tmkName` | 主题开启时显示 |
| 最后一次沟通状态 | `lastFollowResultType` | 对应跟进结果枚举 |
| 最后一次人工 Follow 时间 | `lastFollowFilterTimeStart` / `lastFollowFilterTimeEnd` | 时间范围 |
| 最近未人工 Follow 时间 | `lastUnFollowFilterTimeStart` / `lastUnFollowFilterTimeEnd` | 时间范围 |
| 注册时间 | `registerTimeStart` / `registerTimeEnd` | 时间范围 |
| 最后登录时间 | `lastLoginTimeStart` / `lastLoginTimeEnd` | 时间范围 |
| 冷藏标记 | `suspendTag` | `1=是`、`0=否` |
| 节点是否有人工 Follow | `nodeHasFollow` | `1=是`、`0=否` |
| 节点创建到人工 Follow 时长 | `durationBetweenCreateAndFollow` | 小时，常见值 `2/12/24/48/72/168` |
| 今日是否会掉库 | `willFlowToday` | `1=是`、`0=否` |
| 跟进意向 | `buyingIntention` | 对应意向枚举 |
| 试听课 SNS 时间范围 | `trialSNSTime` | 当前代码只内置 `36` 小时 |

### URL 预置筛选

页面支持从 URL query 预置部分筛选条件，常见键：

- `flowNodeList`
- `trialSNSTime`
- `nodeHasFollow`
- `willFlowToday`
- `durationBetweenCreateAndFollow`
- `lastFollowTime`
- `lastUnFollowTime`
- `registerTimeRange`
- `lastLoginTimeRange`
- `flowTimeLimit`
- `lastFlowTime`
- `lastThirtyDays`

---

## 查询接口

### 私池 Leads 列表

```bash
POST /api/v1/leads/user/manage/getList
```

最小请求示例：

```json
{
  "status": 1,
  "currentPage": 1,
  "pageSize": 10
}
```

补充说明：

- `status`：`0=公海`、`1=私池`、`2=冻结库`
- 当前页面固定传 `1`
- 支持排序字段：
  - `sortByTime`
  - `sortByRemainingTime`
  - `sortByAllotTime`

### 节点与渠道辅助接口

```bash
GET /api/v1/leads/flow/manage/node/all
GET /api/v1/leads/business/channel/all
```

实测节点枚举值：

- `WAIT_FOLLOW`：待 Follow 跟进
- `WAIT_TRIAL`：待约试听课
- `WAIT_TRIAL_COMPLETE`：待试听课完课
- `WAIT_PAY`：待付费
- `PAID`：已付费

渠道接口返回的是多级渠道树，不是一个小的固定平铺枚举：

- `channelCode`：末级渠道编码，适合精确筛选
- `channelLevelId`：渠道树级联选择器里的层级 ID
- 一级渠道实测包含：`测试渠道`、`n_Digital`、`n_Recommendation`、`n_Offline`、`n_B2B`、`n_Organic`、`n_distributor`、`n_dino_book_club`、`n_dino_AI`

### 查询列表接口参数分类

> 页面默认请求体会带很多空数组字段，例如 `lastNodeTime`、`registerTime`、`lastLoginTime`。
> 实测在“直接调用接口”场景下，更稳定生效的是 `xxxStart` / `xxxEnd` 这一类开始结束字段。

| 参数 | 类型 / 来源 | 是否自由输入 | 说明 |
|------|------|------|------|
| `status` | 固定枚举 | 否 | `0=公海`、`1=私池`、`2=冻结库` |
| `currentPage` / `pageSize` | 数字 | 是 | 分页参数 |
| `userId` / `studentId` | 精确 ID | 是 | 精确查家长 / 学生 |
| `channelCode` | 渠道树末级编码 | 否 | 来自 `channel/all` 返回值，不是自由文本 |
| `channelLevelId` | 渠道层级 ID | 否 | 来自 `channel/all` 返回值，通常和 `channelCode` 配合 |
| `flowNodeList` | 节点枚举数组 | 否 | 来自 `node/all`，如 `WAIT_PAY`、`PAID` |
| `countryCode` | 区号 | 半固定 | 来自区号选择器，不建议手填随意值 |
| `mobile` | 数字字符串 | 是 | 前端会过滤成纯数字 |
| `staffId` | 员工 ID | 否 | 通常来自 `POST /api/v1/leads/staff/getList` |
| `staffName` / `gcsName` / `tmkName` | 文本 | 是 | 员工姓名或关键词筛选 |
| `lastFlowTimeStart` / `lastFlowTimeEnd` | 毫秒时间戳 | 是 | 节点生成时间，实测生效 |
| `registerTimeStart` / `registerTimeEnd` | 毫秒时间戳 | 是 | 注册时间，实测生效 |
| `lastLoginTimeStart` / `lastLoginTimeEnd` | 毫秒时间戳 | 是 | 最后登录时间，实测生效 |
| `lastFollowFilterTimeStart` / `lastFollowFilterTimeEnd` | 毫秒时间戳 | 是 | 最后一次人工 Follow 时间 |
| `lastUnFollowFilterTimeStart` / `lastUnFollowFilterTimeEnd` | 毫秒时间戳 | 是 | 最近未人工 Follow 时间 |
| `lastFollowResultType` | 页面枚举值 | 否 | 来自页面下拉，不建议自由编造 |
| `suspendTag` | 固定枚举 | 否 | `1=是`、`0=否` |
| `nodeHasFollow` | 固定枚举 | 否 | `1=是`、`0=否` |
| `durationBetweenCreateAndFollow` | 固定枚举 | 否 | 常见值 `2/12/24/48/72/168` |
| `willFlowToday` | 固定枚举 | 否 | `1=是`、`0=否` |
| `buyingIntention` | 页面枚举值 | 否 | 来自页面下拉，不建议自由编造 |
| `trialSNSTime` | 固定枚举 | 否 | 当前页面常见值 `36` |
| `flowReasonIdList` | 页面 ID 列表 | 否 | 页面默认常传空数组，本轮未展开来源接口 |
| `kpFlag` / `registerToday` | 页面内部筛选字段 | 否 | 页面默认空字符串 / 空值，直接调用时通常保持默认 |

### 员工搜索

```bash
POST /api/v1/leads/staff/getList
```

请求示例：

```json
{
  "pageSize": 100,
  "staffName": "Tom",
  "staffRole": 0
}
```

角色值：

- `0=GCC`
- `1=GCS`
- `3=TMK`

---

## 批量操作

### 手动分配

```bash
POST /api/v1/leads/user/manage/allot
```

请求示例：

```json
{
  "userIdList": [10001, 10002],
  "staffId": 90001,
  "staffRole": 0
}
```

说明：

- `staffRole`：`0=GCC`、`1=GCS`、`3=TMK`
- 页面里会先弹员工选择框，再提交分配

### 手动流转

```bash
POST /api/v1/leads/user/manage/flow
```

请求示例：

```json
{
  "userIdList": [10001, 10002],
  "type": 2
}
```

说明：

- `type`：`0=流转到公海`、`2=流转到冻结库`

### 批量导入分配

```bash
POST /api/v1/leads/user/manage/allot/upload
```

请求方式：`multipart/form-data`

字段：

- `file`：Excel 文件
- `allotType`：`0=GCC`、`3=TMK`

---

## 标签管理

### 添加标签

```bash
POST /api/v1/leads/user/addTag
```

```json
{
  "userId": 10001,
  "tagId": 12
}
```

### 删除标签

```bash
POST /api/v1/leads/user/deleteTag
```

```json
{
  "userId": 10001,
  "tagId": 12
}
```

---

## 行内操作与跳转页

这些操作大多不是直接在当前页发 API，而是打开后台其他页面或 iframe。

| 功能 | 路径模板 | 关键参数 | 说明 |
|------|------|------|------|
| 家长详情 | `/user/parent/detail/<parentId>` | `falcon_country_code`、`falcon_lang_code` | 右侧抽屉打开 |
| 添加 Follow | `/omnicenter/leads/leadsFollow/` | `parentId`、`lang` | 新窗口打开 |
| 流转记录 | `/omnicenter/leads/transferRecord/` | `userid`、`headless=1` | 新窗口打开 |
| 下单 | `/hobbit/user/createorder/` | `parentId`、`orderSource=12`、`falcon_lang_code` | 弹窗 iframe |
| 选课包 | `/hobbit/product/package/` | `mode=select`、`parentId`、`orderSource=12` | 下单子流程 |
| 预约试听课 | `/hobbit/user/bookingTrial` | `parentId`、`childId`、`type=1`、`isIframe=1` | 弹窗 iframe |
| 预约线下课 | `/omnicenter/offlineClass/bookOfflineClass/` | `studentId`、`parentId`、`headless=1`、`from=international-mgt` | 需先选学生 |
| 修改定级 | `/hobbit/user/modifyGrading` | `parentId`、`isIframe=1`、`type=1` | 弹窗 iframe |
| 添加孩子 | `/hobbit/user/registerchild` | `parentId`、`falcon_lang_code` | 弹窗 iframe |
| 重置密码 | `/hobbit/user/resetPassword` | `parentId`、`phone`、`email`、`type=1`、`isIframe=1` | 操作前前端会二次确认 |
| 绑定/解绑微信 | `/hobbit/user/bindwx` | `parentId`、`status`、`falcon_lang_code` | `status=0` 表示当前未绑定 |
| 创建用户 | `/hobbit/user/createuser` | `bizLine`、`falcon_lang_code` | 页顶按钮 |
| 呼叫中心拨号 | `/omnicenter/sobotCallCenter` | `staffId`、`parentId`、`lang`、`origin=leadsList` | 需要呼叫中心能力 |

---

## 页面上的批量按钮

当前 `/leadsGCC/list` 私池页会根据权限显示这些批量按钮：

- 分配给 GCC
- 分配给 GCS
- 分配给 TMK
- 冻结到冻结库
- 流转到公海
- 批量导入分配 GCC
- 批量导入分配 TMK

---

## 当前页面不属于私池页的功能

下面这些能力也在通用 `leadsList` 组件里，但不是 `/leadsGCC/list` 当前页面的实际功能：

- 上传 Leads
- 上传权益
- 批量冻结导入
- 解密用户

这些分别属于公海页或冻结库页。

---

## 操作建议

- 查询类操作可优先走 `POST /api/v1/leads/user/manage/getList`
- 直接调接口时，优先使用 `sa-leads` 域名与 `authorization + app-code: leads-management + biz-line/web-site` 请求头
- 时间筛选优先使用 `lastFlowTimeStart/End`、`registerTimeStart/End`、`lastLoginTimeStart/End` 这类开始结束字段
- 涉及批量改动时，先向用户确认 `userIdList`、目标员工或目标流向
- 涉及 iframe 页面操作时，优先用浏览器自动化而不是盲猜接口
- 重置密码、绑定微信、下单、预约等动作都属于强副作用操作，必须二次确认
