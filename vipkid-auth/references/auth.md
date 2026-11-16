# 权限系统接口参考

Base URL：`https://power.lionabc.com/`

实际接口基址：`https://power.lionabc.com/rest/auth`

---

## 推荐配置

建议把权限系统配置写进 `~/.vipkid-auth/config.json`：

```json
{
  "auth_base_url": "https://power.lionabc.com/",
  "auth_app_code": "",
  "auth_vk_cr_code": "",
  "auth_cookie": "",
  "auth_authorization": "",
  "auth_intl_auth_token": ""
}
```

字段说明：

- `auth_base_url`：统一配置为 `https://power.lionabc.com/`
- helper 会自动补成实际接口基址 `https://power.lionabc.com/rest/auth`
- `auth_app_code`：当前应用编码，请按实际系统填写
- `auth_vk_cr_code`：地区码，请按实际环境填写
- `auth_cookie`：可手填浏览器里复制出的完整 `Cookie`，也可通过 `refresh-token` 自动写入
- `auth_authorization`：部分接口需要时再补
- `auth_intl_auth_token`：可通过 `refresh-token` 自动写入，部分接口需要时会直接带上

---

## 自动获取 token

`vipkid-auth` 现在和 `vipkid-ops` 使用同一套获取 token 的方式，推荐优先自动获取：

```bash
AUTH_HELPER="python3 <vipkid-auth/scripts/auth_helper.py 的实际路径>"

$AUTH_HELPER refresh-token
```

说明：

- 会打开一个独立 Chrome 窗口，使用单独的浏览器目录
- 你登录完成后，脚本会自动读取 `intlAuthToken`
- 读取成功后会写回 `~/.vipkid-auth/config.json`
- 同时更新 `auth_cookie` 和 `auth_intl_auth_token`
- 如果配置里已提供 `auth_app_code` 与 `auth_vk_cr_code`，helper 还会额外调用 `isLogin` 自动校验登录态，避免把失效 token 当成刷新成功

如果你已经手动启动了带远程调试端口的 Chrome，也可以直接走 CDP：

```bash
$AUTH_HELPER refresh-token --mode cdp --port 9222
```

---

## 推荐请求头

这套权限系统在 Postman 集合里同时出现了 `Cookie`、`Authorization`、`intlAuthToken` 三种鉴权方式，但并不是每个接口都稳定需要三者。

建议顺序：

1. 必带：`app-code`、`vk-cr-code`
2. 默认优先：`Cookie`
3. 某些接口要求更严格时，再补：`Authorization` 或 `intlAuthToken`

推荐模板：

```bash
curl -s \
  -H "app-code: <auth_app_code>" \
  -H "vk-cr-code: <auth_vk_cr_code>" \
  -H "Cookie: <auth_cookie>" \
  -H "Accept: application/json" \
  "https://power.lionabc.com/rest/auth/api/role/list?appId=1&page.start=0&page.limit=10"
```

补充说明：

- 这不是 OpenAPI 文档，集合里大多没有响应示例
- 不要假定所有接口都返回 `code=200`
- 遇到 HTTP 正常但业务结果不符合预期时，先打印完整响应，再看 `code`、`msg`、`data`

---

## 角色

### 查询

| 能力 | 方法 | 路径 | 关键参数 |
|------|------|------|------|
| 获取角色列表 | `GET` | `/api/role/list` | `appId`、`page.start`、`page.limit`、可选 `menuCode` |
| 获取角色详情 | `GET` | `/api/role/detail` | `id` |
| 获取员工角色列表 | `GET` | `/api/role/userRole/list` | `userId`、`appId` |

示例：

```bash
GET /api/role/list?appId=1&page.start=0&page.limit=10
GET /api/role/detail?id=2318
GET /api/role/userRole/list?userId=600000000&appId=2
```

### 写操作

| 能力 | 方法 | 路径 | 关键字段 |
|------|------|------|------|
| 添加角色 | `POST` | `/api/role/add` | `code`、`name`、`appId`、`businessId`、`type` |
| 修改角色 | `POST` | `/api/role/edit` | `id`、其余修改字段 |
| 添加员工角色 | `POST` | `/api/role/userRole/add` | `appId`、`userId`、`roleIdList`，可选 `roleCodeList` |
| 删除员工角色 | `GET` | `/api/role/userRole/delete` | `id` |
| 按角色码删除员工角色 | `GET` | `/api/role/userRole/deleteByRoleCode` | `userId`、`roleCodes` |

注意：

- `添加员工角色` 虽然是常见操作，也必须先展示 `userId`、`appId`、目标角色清单再确认
- 两个删除接口都属于高风险操作，默认只给预览，不直接执行
- `GET /api/role/userRole/list` 返回的是“当前应用 + 当前 `vk-cr-code` 下的角色列表”，不是“当前用户已经拥有的角色列表”
- 必须结合 `authStatus` 解读：`authStatus=1` 才代表当前用户真实拥有该角色，`authStatus=0` 只是该业务线下存在这个角色
- 如果要查“国际化管理端所有业务线”，不能只打一条请求；要按不同 `vk-cr-code` 逐个查

---

## 角色菜单

| 能力 | 方法 | 路径 | 关键字段 |
|------|------|------|------|
| 添加角色菜单 | `POST` | `/api/roleMenu/add` | `roleId`、`menuIds` |
| 按角色码添加角色菜单 | `POST` | `/api/roleMenu/addByCode` | `appId`、`roleCode`、`menuCodes` |
| 删除角色菜单 | `POST` | `/api/roleMenu/delete` | `roleId`、`menuIds` |

示例：

```bash
POST /api/roleMenu/add
POST /api/roleMenu/addByCode
POST /api/roleMenu/delete
```

注意：

- `addByCode` 适合“我知道角色码和菜单码，但不知道 ID”的场景
- `delete` 属于高风险操作，必须二次确认

---

## 应用 / 业务线

### 查询

| 能力 | 方法 | 路径 | 关键参数 |
|------|------|------|------|
| 获取应用列表 | `GET` | `/api/app/getAppList` | 可选 `name`、`code`、`status` |
| 根据应用 ID 获取应用信息 | `GET` | `/api/app/getById` | `id` |
| 获取业务线列表 | `GET` | `/api/business/getList` | 可选 `code`、`status` |
| 获取当前用户业务线列表 | `GET` | `/api/business/getCurrList` | 无 |
| 获取业务线信息 | `GET` | `/api/business/getById` | `id` |

### 写操作

| 能力 | 方法 | 路径 | 关键字段 |
|------|------|------|------|
| 添加业务线 | `POST` | `/api/business/add` | `code`、`name` |
| 编辑业务线 | `POST` | `/api/business/edit` | `id`、`code`、`name` |
| 添加应用 | `POST` | `/api/app/add` | `code`、`name`、`appBusinessList` |
| 编辑应用 | `POST` | `/api/app/edit` | `id`、`code`、`name`、`appBusinessList` |
| 添加应用业务线 | `POST` | `/api/app/business/add` | `appId`、`businessId`、`dataPermissionStatus` |

注意：

- `appBusinessList` 里通常要带 `businessId` 和数据权限开关
- `GET /api/app/getById` 的返回里会直接带 `appBusinessList`，可据此看到“这个应用当前挂了哪些业务线”
- `appBusinessList[].dataPermissionStatus`：`1=已开启数据权限`、`0=未开启`
- 这类接口会影响应用与业务线映射，属于普通写操作，执行前仍需展示目标列表
- 对国际化管理端这类多业务线应用，`appBusinessList` 也是判断要不要切换 `vk-cr-code` 的第一手依据

---

## 员工

### 查询

| 能力 | 方法 | 路径 | 关键参数 |
|------|------|------|------|
| 根据姓名查询员工信息 | `GET` | `/api/user/getUserList` | `name` |
| 根据邮箱模糊查询员工信息 | `GET` | `/api/user/staff/searchByEmail` | `email` |
| 根据邮箱模糊查询权限系统员工信息 | `GET` | `/api/auth/user/searchByEmail` | `email` |
| 获取员工列表 | `GET` | `/api/user/getUserList` | 可选 `name`、`email`、`status`、`roleId`、`orgIds` |
| 根据员工 ID 获取员工信息 | `GET` | `/api/user/getById` | `id` |
| 根据员工 ID 获取基础认证信息 | `GET` | `/api/auth/user/getUserById` | `userId` |
| 根据员工 ID 获取部门列表 | `GET` | `/api/user/getUserOrgList` | `id` |
| 员工权限信息 | `GET` | `/api/auth/userAuthInfo` | 无 |
| 获取用户数据权限 | `GET` | `/api/auth/permission/data/info` | 无 |

### 写操作

| 能力 | 方法 | 路径 | 关键字段 |
|------|------|------|------|
| 添加已有员工 | `POST` | `/api/user/addByStaffId` | `staffId` |
| 添加员工 | `POST` | `/api/user/add` | 基础信息、`userOrgList` |
| 根据 ID 添加员工 | `POST` | `/api/user/addById` | `id`、基础信息、`userOrgList` |
| 编辑员工 | `POST` | `/api/user/edit` | `id`、变更字段 |
| 修改员工状态 | `POST` | `/api/user/changeStatus` | `id`、`status` |
| 授权员工数据权限 | `POST` | `/api/user/addDataPermissions` | `id`、`orgId` |
| 取消授权员工数据权限 | `POST` | `/api/user/cancelDataPermissions` | `id`、`orgId` |
| 修改员工密码 | `POST` | `/api/user/editPassword` | `id`、`password`、`newPassword` |
| 重置员工密码 | `POST` | `/api/user/resetPassword` | `id`、`newPassword` |

注意：

- 加员工、改状态、改密码都属于高副作用操作
- 如果用户只说“帮我处理员工权限”，优先反问是角色、组织归属还是数据权限
- 当前 provider 代码里默认使用 `GET /api/user/getById` 作为员工详情查询入口，它会返回 `loginType`、`userOrgList`
- 历史文档里出现过 `GET /api/user/getDetail` 与 `GET /api/user/staff/searchByStaffId`，但当前仓库中的 provider 控制器未检索到这两个路由，不建议继续作为默认能力引用
- 按姓名找人时，优先使用 `GET /api/user/getUserList?name=...`

### 登录策略

员工基础信息里的 `loginType` 就是登录策略：

| loginType | 含义 |
|------|------|
| `0` | 密码登录 |
| `1` | 验证码登录 |

补充说明：

- 后端登录时会校验“用户配置的登录策略”和“前端提交的登录方式”是否一致
- 如果不一致，会触发“登录策略不一致”错误，而不是自动兜底切换
- 因此排查“明明密码对但登录失败”时，要一起看用户的 `loginType`

---

## 组织

| 能力 | 方法 | 路径 | 关键字段 |
|------|------|------|------|
| 获取组织结构树 | `GET` | `/api/org/getOrgTrees` | 无 |
| 获取组织结构详情 | `GET` | `/api/org/getDetail` | `orgId` |
| 添加组织 | `POST` | `/api/org/add` | `parentId`、`name`、`status`、`sort` |
| 编辑组织 | `POST` | `/api/org/edit` | `id`、`name`、`status`、`sort` |
| 添加组织架构用户 | `POST` | `/api/org/addOrgUsers` | `id`、`orgRoleType`、`userIdList` |

适用场景：

- 查组织树、查组织详情
- 把某批员工加入某个组织节点
- 调整组织名称、排序、启停状态

---

## 菜单与认证

| 能力 | 方法 | 路径 | 关键参数 / 字段 |
|------|------|------|------|
| 添加菜单 | `POST` | `/api/menuTree/add` | `appId`、`code`、`name`、`type`、`parentId` |
| 删除菜单 | `GET` | `/api/menuTree/deleteById` | `id` |
| 获取所有菜单树 | `GET` | `/api/menuTree/getAllTreeMenus` | `appId` |
| 员工菜单信息 | `GET` | `/api/auth/user/getTreeMenus` | 无 |
| 校验功能权限 | `GET` | `/api/auth/permission/function/check` | `url` |
| 验证是否登录 | `POST` | `/api/auth/isLogin` | 无 |
| 员工登录 | `POST` | `/api/auth/login` | `userName`、`password` |
| 员工登出 | `GET` | `/api/auth/logout` | 无 |
| 批量登出员工 | `POST` | `/api/auth/logoutByUserIds` | `userIdList` |

注意：

- `deleteById`、`logoutByUserIds` 都属于高风险操作
- `check` 常用于判断某个后端接口地址当前用户是否有权限
- `getTreeMenus` 适合排查“为什么页面没显示菜单”

### `authStatus` 与 `vk-cr-code`

这是这套权限系统里最容易误判的两个点：

- `authStatus=1`：当前用户真实拥有该角色
- `authStatus=0`：当前业务线下存在这个角色，但当前用户并未拥有
- `vk-cr-code`：请求命中的业务线范围；同一个 `appId` 在不同 `vk-cr-code` 下，角色集合可能完全不同

实战建议：

1. 查单个业务线：先确认 `vk-cr-code`，再看 `authStatus`
2. 查“所有业务线”：先看 `GET /api/app/getById` 的 `appBusinessList`，再按业务线逐个请求
3. 做“权限复制 / 权限对齐”：先按业务线算出真实拥有角色，再按业务线分批调用 `POST /api/role/userRole/add`

### 角色详情中的页面 / 按钮权限

`GET /api/role/detail` 的返回里通常有 `menuTreeList`，可以直接拿来判断这个角色具体拥有哪些页面和按钮权限。

实测规则：

- `type=0`：页面 / 菜单权限
- `type=1`：按钮 / 操作权限

常见例子：

- 页面：`Parent management`、`Student management`、`Order management`
- 按钮：`用户管理-查询`、`用户重置密码`、`退款管理-退款审批`

补充说明：

- 有些“超级管理员 / 数据管理员”角色的 `menuTreeList` 可能是空数组，不代表完全没权限，可能是系统内置特殊角色
- 如果要查“某个人在某个应用下到底能看到哪些页面、能点哪些按钮”，推荐先查 `/api/role/userRole/list`，再逐个查 `/api/role/detail`
- 如果某个角色的 `/api/role/detail` 查询失败，必须把失败角色单独标出来，不能按“无权限”直接下结论

---

## 测试与高风险接口

下面这些接口允许纳入技能识别范围，但默认只给方案和预览：

| 接口 | 风险说明 |
|------|------|
| `/api/role/userRole/delete` | 删除用户角色 |
| `/api/role/userRole/deleteByRoleCode` | 按角色码删除用户角色 |
| `/api/roleMenu/delete` | 删除角色菜单 |
| `/api/menuTree/deleteById` | 删除菜单节点 |
| `/api/app/userOrgLevel/deleteByIds` | 删除用户授权记录 |
| `/api/test/syncMenu` | 菜单同步，可能影响系统配置 |
| `/api/test/syncRole` | 角色同步，可能影响系统配置 |
| `/api/auth/logoutByUserIds` | 批量登出用户 |

明确排除：

- `/api/mysql/backdoor/update`

---

## helper 命令映射

推荐优先使用 `scripts/auth_helper.py`：

| 命令 | 对应接口 | 说明 |
|------|------|------|
| `auth-check` | `POST /api/auth/isLogin` | 验证登录态 |
| `role-list` | `GET /api/role/list` | 角色列表 |
| `role-detail` | `GET /api/role/detail` | 角色详情 |
| `user-search-email` | `GET /api/auth/user/searchByEmail` | 按邮箱查员工 |
| `user-search-name` | `GET /api/user/getUserList` | 按姓名查员工 |
| `user-basic` | `GET /api/user/getById` | 员工基础信息 |
| `user-detail` | `GET /api/user/getById` | 员工详情 |
| `user-login-strategy` | `GET /api/user/getById` | 登录策略 |
| `user-orgs` | `GET /api/user/getUserOrgList` | 组织归属 |
| `user-role-list` | `GET /api/role/userRole/list` | 员工角色；`--owned-only` 只保留 `authStatus=1` 的真实拥有角色，`--vk-cr-code` 可切换业务线 |
| `org-tree` | `GET /api/org/getOrgTrees` | 组织树 |
| `org-detail` | `GET /api/org/getDetail` | 组织详情 |
| `app-list` | `GET /api/app/getAppList` | 应用列表 |
| `app-detail` | `GET /api/app/getById` | 应用详情 |
| `business-list` | `GET /api/business/getList` | 业务线列表 |
| `menu-tree` | `GET /api/menuTree/getAllTreeMenus` | 菜单树 |
| `role-permissions` | `GET /api/role/detail` | 角色页面 / 按钮权限 |
| `user-permissions` | `GET /api/role/userRole/list` + `GET /api/role/detail` | 员工在某应用下的页面 / 按钮权限汇总，默认只统计 `authStatus=1` 的真实拥有角色；支持 `--cr-codes` 跨业务线汇总 |
| `permission-check` | `GET /api/auth/permission/function/check` | 功能权限校验 |
| `user-role-add` | `POST /api/role/userRole/add` | 添加员工角色 |
| `user-role-delete` | `GET /api/role/userRole/delete` 或 `deleteByRoleCode` | 删除员工角色，两套参数互斥：`--id` 不能与 `--user-id/--role-codes` 同时传 |
| `role-menu-add` | `POST /api/roleMenu/add` 或 `addByCode` | 添加角色菜单，两套参数互斥：`--role-id/--menu-ids` 不能与 `--app-id/--role-code/--menu-codes` 同时传 |
| `role-menu-delete` | `POST /api/roleMenu/delete` | 删除角色菜单 |

---

## 使用建议

- 查询类优先用 helper 或 `GET` 接口直接查
- 写操作先展示目标对象、请求体和影响范围
- 如果用户只提供“邮箱关键词”“角色码”“菜单码”这类半结构化信息，先补齐必要主键，再给执行方案
- 如果用户只给中文姓名，先用 `user-search-name` 定位，再继续查角色、组织或登录策略
- 如果用户问“这个人能看到哪些页面 / 能点哪些按钮”，优先用 `user-permissions`
- 如果用户问“这个人实际拥有哪些角色”，优先用 `user-role-list --owned-only`
- 如果用户问“所有业务线 / 国际化管理端全部业务线”，先用 `app-detail` 确认业务线，再用 `user-permissions --cr-codes ...`
- 如果要把国际化管理端权限从 A 复制给 B，不要一次性按一个 `appId` 粗暴添加；要先按业务线比对真实拥有角色，再按每个 `vk-cr-code` 分批写入
- 删除、同步、批量登出、改密一律先做二次确认
- 删除员工角色接口当前是 `GET`，不要分享带完整参数的 URL 或日志截图，避免暴露目标对象信息
