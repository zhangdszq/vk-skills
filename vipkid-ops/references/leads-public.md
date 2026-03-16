# Leads 线索库页参考

目标页面：`/omnicenter/leads/leadsPublic/`

这份文档覆盖旧系统 `leadsPublic/list` 在 `flowtype=PUBLIC` 下暴露出的可自动化能力。

## 当前可用请求约定

线索库接口已验证可通过下面这组请求上下文稳定访问：

- Base URL:
  `https://sa-leads.lionabc.com/rest/leadsgw`
- 认证头：
  - `Authorization: <intlAuthToken>`
  - `intlAuthToken: <intlAuthToken>`
- 业务头：
  - `app-Code: leads-management`
  - `biz-line: sa`
  - `web-site: sa`
  - `vk-cr-code: sa`
- 常用来源头：
  - `Origin: https://sa-leads.lionabc.com`
  - `Referer: https://sa-leads.lionabc.com/leadsPublic/list`
- Cookie 至少保留：
  - `intlAuthToken=<token>`
  - `biz-line=sa`

说明：
- `scripts/leads_helper.py` 已改为走 `curl -ks`，避免本机 SSL 证书链导致的失败。
- 不要沿用商品包接口那套 `app-Code: international-mgt` 头部去调用 leads 列表接口。

## 页面范围

线索库页核心能力分 4 类：
- 列表查询与筛选
- 行级操作：标签、解密、流转记录
- 批量操作：分配、冻结
- 上传类操作：上传 Leads、上传权益、批量分配

不在本 skill 自动化范围内的 UI-only 功能：
- 流转记录弹窗与详情页浏览
- 家长详情页
- 跟进记录页

## 查询筛选项

| 页面字段 | 请求参数 |
|------|------|
| 渠道 | `channelCode` / `channelLevelId` |
| 流转标记 | `flowReasonIdList` |
| Parent ID | `userId` |
| Student ID | `studentId` |
| 区域 | `countryCode` |
| 手机号 | `mobile` |
| 最后一次沟通状态 | `lastFollowResultType` |
| 最后人工 Follow 时间 | `lastFollowFilterTimeStart` / `lastFollowFilterTimeEnd` |
| 最近未人工 Follow 时间 | `lastUnFollowFilterTimeStart` / `lastUnFollowFilterTimeEnd` |
| 注册时间 | `registerTimeStart` / `registerTimeEnd` |
| 最后登录时间 | `lastLoginTimeStart` / `lastLoginTimeEnd` |
| 节点生成时间 | `lastFlowTimeStart` / `lastFlowTimeEnd` |
| 归属 GCS | `gcsName` |
| 分页 | `currentPage` / `pageSize` |
| 状态 | `status`，`0=public`，`1=private`，`2=froze` |

排序字段：
- `sortByTime`
- `sortByRemainingTime`
- `sortByAllotTime`

排序值：
- `0` 升序
- `1` 降序

## 列表字段

线索库页主要列：
- Parent ID
- Channel Name
- Phone
- Student Name En
- Buying Intention
- Follow Record
- Connected State
- KET/PET Buy State
- Register Time
- Last Login Time
- Create Node Time
- Flow Marker
- Node
- Belong GCS
- Operation

## 行级操作

### 解密用户

- 接口：`GET /api/v1/leads/user/decrypt`
- 参数：`userId`
- 返回：邮箱、手机号、国家区号

### 标签增删

- 接口：
  - `POST /api/v1/leads/user/addTag`
  - `POST /api/v1/leads/user/deleteTag`
- 参数：`{"userId": "...", "tagId": 18}`
- 注意：
  - 不同地区可用标签和权限不同
  - 写入前要先确认 `tagId`

### 流转记录

- 页面是跳转，不是稳定 REST：
  - `/omnicenter/leads/transferRecord/?userid=<userId>&headless=1`

## 批量操作

### 手动分配

- 接口：`POST /api/v1/leads/user/manage/allot`
- 参数：

```json
{
  "userIdList": ["123456", "234567"],
  "staffId": "9988",
  "staffRole": 0
}
```

`staffRole`：
- `0` = GCC
- `1` = GCS
- `3` = TMK

### 手动流转

- 接口：`POST /api/v1/leads/user/manage/flow`
- 参数：

```json
{
  "userIdList": ["123456", "234567"],
  "type": 2
}
```

`type`：
- `0` = 流转到公海
- `2` = 流转到冻结库

## 上传类操作

### 上传 Leads / 权益 / 批量冻结

- 接口：
  - `POST /api/v1/leads/user/upload`
  - `POST /api/v1/leads/user/equity/upload`
  - `POST /api/v1/leads/user/batchFrozenByUpload`
- 方式：`multipart/form-data`
- 文件字段：`file`

模板链接：
- Leads 导入模板：
  `https://s.vipkidstatic.com/fe-static/int/asset/pub/leads%E5%AF%BC%E5%85%A5%E6%A8%A1%E6%9D%BFv5.xlsx`
- 权益导入模板：
  - PID:
    `https://s.vipkidstatic.com/int/asset/pub/%E6%9D%83%E7%9B%8A%E5%AF%BC%E5%85%A5%E6%A8%A1%E6%9D%BFv3.3.xlsx?v=1`
  - SID:
    `https://s.vipkidstatic.com/fe-static/int/asset/pub/%E6%9D%83%E7%9B%8A%E5%AF%BC%E5%85%A5%E6%A8%A1%E6%9D%BFv4.xlsx`
- 批量冻结模板：
  `https://s.vipkidstatic.com/fe-static/int/asset/pub/%E6%89%B9%E9%87%8F%E5%86%BB%E7%BB%93%E6%A8%A1%E6%9D%BF.xlsx?v=1`

### 批量分配上传

- 接口：`POST /api/v1/leads/user/manage/allot/upload`
- 方式：`multipart/form-data`
- 表单字段：
  - `file`
  - `allotType`

`allotType`：
- `0` = GCC
- `3` = TMK

模板链接：
- GCC：
  `https://s.vipkidstatic.com/fe-static/int/asset/pub/%E6%89%B9%E9%87%8F%E5%88%86%E9%85%8D%E5%AF%BC%E5%85%A5%E6%A8%A1%E6%9D%BFv4.xlsx?a=1`
- TMK：
  `https://s.vipkidstatic.com/fe-static/int/asset/pub/%E6%89%B9%E9%87%8F%E5%88%86%E9%85%8DTMK_V1.xlsx?a=1`

## 读字典接口

- `GET /api/v1/leads/business/channel/all`
- `GET /api/v1/leads/flow/reason/all`
- `GET /api/v1/leads/flow/manage/node/all`
- `GET /api/v1/leads/tag/all`
- `POST /api/v1/leads/staff/getList`
- `GET /rest/auth/api/auth/userAuthInfo` 用于认证校验

## 成功请求示例

### 按 userId 查询

```bash
curl -ks 'https://sa-leads.lionabc.com/rest/leadsgw/api/v1/leads/user/pub/getList' \
  -H 'Authorization: <token>' \
  -H 'intlAuthToken: <token>' \
  -H 'app-Code: leads-management' \
  -H 'biz-line: sa' \
  -H 'web-site: sa' \
  -H 'vk-cr-code: sa' \
  -H 'Origin: https://sa-leads.lionabc.com' \
  -H 'Referer: https://sa-leads.lionabc.com/leadsPublic/list' \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -H 'Cookie: intlAuthToken=<token>; biz-line=sa; sidebarStatus=0' \
  --data-raw '{"userId":"12699201","status":0,"currentPage":1,"pageSize":10,"flowNodeList":[],"flowReasonIdList":[]}'
```

### 查询今天注册数量

```bash
curl -ks 'https://sa-leads.lionabc.com/rest/leadsgw/api/v1/leads/user/pub/getList' \
  -H 'Authorization: <token>' \
  -H 'app-Code: leads-management' \
  -H 'biz-line: sa' \
  -H 'web-site: sa' \
  -H 'vk-cr-code: sa' \
  -H 'Origin: https://sa-leads.lionabc.com' \
  -H 'Referer: https://sa-leads.lionabc.com/leadsPublic/list' \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -H 'Cookie: intlAuthToken=<token>; biz-line=sa; sidebarStatus=0' \
  --data-raw '{"status":0,"currentPage":1,"pageSize":1,"registerTimeStart":1773608400000,"registerTimeEnd":1773694799999,"flowNodeList":[],"flowReasonIdList":[]}'
```

从响应中读取：
- `totalCount` = 今天注册总数

## 权限点

路由级：
- `LEADS_MANAGEMENT_LEADS_PUBLIC`

查询与按钮：
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_SELECT`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_RESET`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_UPLOAD_LEADS`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_UPLOAD_LEADS_EQUITY`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_USER_DECRYPT`

标签：
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_ADD_TAG_FREEZE`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_ADD_TAG_REFRIGERATE`

批量与流转：
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_ALLOT_GCC`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_ALLOT_GCS`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_ALLOT_TMK`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_FREEZE`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_LEADS_TO_PUBLIC`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_BATCH_ALLOT_GCC`
- `ALLOW_LEADS_MANAGEMENT_LEADS_PUBLIC_BATCH_ALLOT_TMK`

辅助：
- `ALLOW_LEADS_MANAGEMENT_LEADS_TRANSFER_RECORD`

## 建议执行顺序

### 只读

1. 先 `auth`
2. 再查 `tags` / `flow-reasons` / `nodes` / `staff`
3. 最后 `list`

### 写入

1. 先 `list` 确认用户集合
2. 再展示要操作的 userId / staffId / tagId / 上传文件
3. 明确得到确认
4. 最后执行写入
