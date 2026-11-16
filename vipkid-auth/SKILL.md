---
name: vipkid-auth
description: >
  VIPKID 权限系统后台助理。适用于角色、员工、组织、应用、业务线、菜单树、功能权限、
  登录校验、登录策略、页面权限、按钮权限等场景，统一走 `power.lionabc.com/rest/auth`。
  用户说“角色列表”“员工角色”“登录策略”“页面权限”“按钮权限”“验证是否登录”
  “菜单树”“应用列表”“组织树”时触发。任何添加角色、删除角色、角色菜单变更、菜单删除、
  同步、批量登出、改密前都必须二次确认。
---

# VIPKID 权限系统后台

## 首次初始化

先准备配置文件：

```bash
mkdir -p ~/.vipkid-auth
cat > ~/.vipkid-auth/config.json <<'EOF'
{
  "auth_base_url": "https://power.lionabc.com/",
  "auth_app_code": "international-auth",
  "auth_vk_cr_code": "sa",
  "auth_cookie": "",
  "auth_authorization": "",
  "auth_intl_auth_token": ""
}
EOF
```

常用初始化命令：

```bash
AUTH_HELPER="python3 <vipkid-auth/scripts/auth_helper.py 的实际路径>"

$AUTH_HELPER refresh-token
$AUTH_HELPER auth-check
```

补充规则：
- `auth_base_url` 固定填 `https://power.lionabc.com/`，脚本会自动补成 `/rest/auth`
- 推荐先运行 `refresh-token` 自动写入 `auth_cookie` 与 `auth_intl_auth_token`
- 默认优先使用 `Cookie`
- 某些接口要求更严格时，再补 `Authorization` 或 `intlAuthToken`

## 自动获取 token

推荐优先使用和 `vipkid-ops` 一致的自动获取方式：

```bash
AUTH_HELPER="python3 <vipkid-auth/scripts/auth_helper.py 的实际路径>"

$AUTH_HELPER refresh-token
```

说明：
- 该命令会打开一个独立 Chrome 窗口，不影响你当前正在使用的浏览器
- 登录完成后会自动读取 `intlAuthToken`
- 脚本会把 token 同时写入 `auth_cookie` 和 `auth_intl_auth_token`

如需复用一个已经开启远程调试端口的 Chrome，可使用：

```bash
$AUTH_HELPER refresh-token --mode cdp --port 9222
```

## 默认执行策略

### 1. 先确认目标

如果用户说得含糊，先反查目标对象：
- 角色：角色列表、角色详情、角色菜单、角色权限
- 员工：基础信息、角色归属、组织归属、登录策略、页面按钮权限
- 组织：组织树、组织详情、组织成员
- 应用：应用列表、应用详情、业务线、菜单树

### 2. 优先使用脚本

优先级固定为：

1. `scripts/auth_helper.py`
2. `references/auth.md`
3. 最后才手写 `curl`

### 3. 输出方式

默认按下面的顺序回答：

1. 这是哪类权限对象
2. 会走哪个命令或接口
3. 关键参数 / 关键字段是什么
4. 如果是写操作，先展示预览并要求二次确认

## 核心命令

```bash
AUTH_HELPER="python3 <vipkid-auth/scripts/auth_helper.py 的实际路径>"

$AUTH_HELPER refresh-token
$AUTH_HELPER auth-check
$AUTH_HELPER role-list --app-id 1
$AUTH_HELPER role-detail 2318
$AUTH_HELPER user-search-name 许梦月
$AUTH_HELPER user-basic 57775188
$AUTH_HELPER user-login-strategy 57775188
$AUTH_HELPER user-orgs 57775188
$AUTH_HELPER user-role-list 600000000 --app-id 2
$AUTH_HELPER user-role-list 600000000 --app-id 1 --owned-only --vk-cr-code hk
$AUTH_HELPER app-list
$AUTH_HELPER app-detail 1
$AUTH_HELPER business-list
$AUTH_HELPER menu-tree --app-id 1
$AUTH_HELPER role-permissions 2397
$AUTH_HELPER user-permissions 60172103 --app-id 1
$AUTH_HELPER user-permissions 60172103 --app-id 1 --cr-codes hk,ts,k2
$AUTH_HELPER permission-check /api/parent/list
```

## 高频判断要点

- 角色列表：`GET /api/role/list`
- 员工角色：`GET /api/role/userRole/list`
- 角色详情：`GET /api/role/detail`
- 员工列表：`GET /api/user/getUserList`
- 员工基础信息：`GET /api/user/getById`
- 功能权限校验：`GET /api/auth/permission/function/check`
- 登录校验：`POST /api/auth/isLogin`

两个关键字段必须记住：
- `loginType`：`0=密码登录`，`1=验证码登录`
- `menuTreeList[].type`：`0=页面/菜单权限`，`1=按钮/操作权限`
- `authStatus`：`1=当前用户真实拥有该角色`，`0=当前业务线下存在这个角色，但当前用户并未拥有`
- `vk-cr-code`：当前请求命中的业务线范围；不切换它，就不是“所有业务线”

如果用户问“某个人在某个应用下有哪些页面权限和按钮权限”，默认链路是：

1. 先查 `user-role-list`
2. 先按 `authStatus=1` 过滤出真实拥有角色
3. 再查 `role-detail`
4. 从 `menuTreeList` 里按 `type` 分类
5. 或直接用 `user-permissions`

`user-permissions` 默认只统计 `authStatus=1` 的真实拥有角色，并输出按角色拆分的权限，以及去重后的 `uniquePages`、`uniqueButtons` 汇总结果。

如果用户问“国际化管理端所有业务线的权限 / 角色”，默认链路是：

1. 先查 `app-detail`，确认该应用挂了哪些业务线
2. 不要只看配置里的单个 `auth_vk_cr_code`
3. 用 `user-role-list --owned-only --vk-cr-code <业务线>` 或 `user-permissions --cr-codes hk,ts,k2`
4. 逐个业务线汇总，再做差异比对
5. 如果要写入角色，必须按业务线拆分预览和执行

补充要求：
- 如果某个角色的 `role-detail` 查询失败，必须把失败角色单独列出
- 不能把“查询失败”直接当成“这个人没有该角色权限”
- 不能把 `user-role-list` 返回的全部角色直接当成“用户已有角色”；必须先看 `authStatus`

## 安全约束

### 必须二次确认后才允许执行

- 添加员工角色
- 删除员工角色
- 添加角色菜单
- 删除角色菜单
- 菜单删除
- 权限同步接口
- 批量登出接口
- 修改密码或重置密码

确认前必须先展示：
- 目标对象
- 关键 ID
- 请求体或参数预览
- 影响范围

### 明确排除

- `POST /api/mysql/backdoor/update`

## 常见异常

| 情况 | 处理 |
|------|------|
| 权限系统未登录 / 403 | 先运行 `refresh-token` 刷新登录态，再检查 `auth_app_code`、`auth_vk_cr_code` |
| 权限系统 HTTP 正常但结果异常 | 先打印完整响应，再按 `code`、`msg`、`data` 判断 |
| 登录策略不一致 | 先查 `user-login-strategy`，确认 `loginType` 是否匹配 |
| 查“所有业务线”却只看到一部分角色 | 大概率只用了单个 `vk-cr-code`，先看 `app-detail` 的 `appBusinessList`，再按业务线逐个查询 |
| 角色列表很多但实际页面没权限 | 先看 `authStatus`，只有 `authStatus=1` 才代表当前用户真实拥有该角色 |

## 按需阅读的参考文档

- 权限系统接口、请求头、风险分级：`references/auth.md`
