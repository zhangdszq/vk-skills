---
name: vipkid-ops
description: >
  VIPKID 国际化运营后台助理。商品包等国际化管理能力操作 sa-manager.lionabc.com；
  Leads 管理页 `/leadsGCC/list` 与列表查询接口操作 sa-leads.lionabc.com。
  支持商品包查询、新建、修改，配置优惠券使用限制、库存（追加/扣减/不限制）、赠送权限；
  也支持 Leads 管理页 `/leadsGCC/list` 的筛选查询、批量分配/流转、标签管理、家长详情、跟进、下单、预约试听课/线下课、添加孩子、重置密码、绑定微信等操作指引。
  用户说「查商品包」「新建课包」「修改价格」「配置库存」「优惠券限制」「赠送配置」「查 leads」「Leads管理」「分配 GCC/GCS/TMK」「冻结 leads」「流转公海」「跟进 leads」时触发。
  ⛔ 绝不执行上架、下架、删除操作；任何批量分配、冻结、流转、改密前必须二次确认。
---

# VIPKID 运营后台

通过 `scripts/ops_helper.py` 或直接 `curl` 调用 REST API 操作运营后台。
商品包相关接口走 `sa-manager.lionabc.com`，Leads 列表与筛选接口走 `sa-leads.lionabc.com`。

当前覆盖两类业务：
- **商品包运营**：商品包查询、新建、编辑、库存、优惠券限制、赠送权限
- **Leads 管理**：`/leadsGCC/list` 私池页的查询、批量操作、行内操作与关联后台页面跳转

## 初始化（首次使用）

```bash
# 1. 创建配置文件
mkdir -p ~/.vipkid-ops
cat > ~/.vipkid-ops/config.json << 'EOF'
{
  "base_url": "https://sa-manager.lionabc.com",
  "leads_base_url": "https://sa-leads.lionabc.com",
  "token": "",
  "cr_code": "sa"
}
EOF

# 2. 自动获取 token（推荐）
python3 ~/.claude/skills/vipkid-ops/scripts/ops_helper.py refresh-token

# 3. 验证
python3 ~/.claude/skills/vipkid-ops/scripts/ops_helper.py auth
```

**自动获取 token（推荐）**：
- `refresh-token` 会打开一个独立的 Chrome 窗口，不影响你当前正在使用的浏览器
- 第一次运行时，在这个独立窗口中手动登录 `sa-manager.lionabc.com`
- 登录成功后脚本会自动读取 `intlAuthToken` 并写入 `~/.vipkid-ops/config.json`
- 独立窗口使用专用登录目录：`~/.vipkid-ops/playwright-profile`

**可选高级模式**：如果你本来就有一个带 `--remote-debugging-port` 的 Chrome，也可以运行：
```bash
python3 ~/.claude/skills/vipkid-ops/scripts/ops_helper.py refresh-token --mode cdp --port 9222
```

**手动获取 token（兜底）**：Chrome 打开后台 → F12 → Application → Cookies → `intlAuthToken` → 复制 Value。

**`cr_code` 地区码**：`sa`=沙特 · `ae`=阿联酋 · `k2`=海湾 · `hk`=香港 · `tw`=台湾 · `kr`=韩国 · `vn`=越南 · `jp`=日本 · `ts`=Tiger

**token 过期**：优先自动刷新：
```bash
python3 ~/.claude/skills/vipkid-ops/scripts/ops_helper.py refresh-token
python3 ~/.claude/skills/vipkid-ops/scripts/ops_helper.py auth
```

手动更新时也可运行：
```bash
python3 -c "
import json; from pathlib import Path
cfg = Path.home() / '.vipkid-ops/config.json'
d = json.loads(cfg.read_text()); d['token'] = input('新token: ')
cfg.write_text(json.dumps(d, indent=2, ensure_ascii=False))"
```

---

## 请求模板

```bash
CONFIG=$(cat ~/.vipkid-ops/config.json)
TOKEN=$(echo $CONFIG | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")
MANAGER_BASE_URL=$(echo $CONFIG | python3 -c "import json,sys; print(json.load(sys.stdin)['base_url'])")
LEADS_BASE_URL=$(echo $CONFIG | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('leads_base_url','https://sa-leads.lionabc.com'))")
CR_CODE=$(echo $CONFIG | python3 -c "import json,sys; print(json.load(sys.stdin).get('cr_code','sa'))")
PRODUCT_REFERER="$MANAGER_BASE_URL/hobbit/product/productpackagemanage/"
LEADS_REFERER="$LEADS_BASE_URL/leadsGCC/list"

api_get() {
  curl -s -H "intlAuthToken: $TOKEN" -H "Cookie: intlAuthToken=$TOKEN" \
    -H "vk-cr-code: $CR_CODE" -H "vk-language-code: zh-cn" \
    -H "app-code: international-mgt" \
    -H "Referer: $PRODUCT_REFERER" \
    -H "Accept: application/json" "$MANAGER_BASE_URL/rest$1"
}
api_post() {
  curl -s -X POST -H "intlAuthToken: $TOKEN" -H "Cookie: intlAuthToken=$TOKEN" \
    -H "vk-cr-code: $CR_CODE" -H "vk-language-code: zh-cn" \
    -H "app-code: international-mgt" \
    -H "Referer: $PRODUCT_REFERER" \
    -H "Content-Type: application/json" -H "Accept: application/json" \
    -d "$2" "$MANAGER_BASE_URL/rest$1"
}
leads_get() {
  curl -s -H "authorization: $TOKEN" \
    -H "vk-cr-code: $CR_CODE" \
    -H "biz-line: $CR_CODE" \
    -H "web-site: $CR_CODE" \
    -H "app-code: leads-management" \
    -H "Referer: $LEADS_REFERER" \
    -H "Accept: application/json" "$LEADS_BASE_URL/rest/leadsgw$1"
}
leads_post() {
  curl -s -X POST -H "authorization: $TOKEN" \
    -H "vk-cr-code: $CR_CODE" \
    -H "biz-line: $CR_CODE" \
    -H "web-site: $CR_CODE" \
    -H "app-code: leads-management" \
    -H "Referer: $LEADS_REFERER" \
    -H "Content-Type: application/json" -H "Accept: application/json" \
    -d "$2" "$LEADS_BASE_URL/rest/leadsgw$1"
}
```

> 商品包接口可继续沿用 `intlAuthToken + Cookie + app-code: international-mgt`。
> Leads 列表接口实测必须走 `sa-leads` 域名，并带 `authorization`、`app-code: leads-management`、`biz-line`、`web-site` 等请求头；如果直接复用商品包那套模板，容易返回 `Forwarding error`。

或使用辅助脚本（推荐批量/复杂场景）：
```bash
HELPER="python3 ~/.claude/skills/vipkid-ops/scripts/ops_helper.py"
$HELPER list [名称]              # 列表
$HELPER detail <id>              # 详情
$HELPER inventory <id>           # 库存
$HELPER refresh-token            # 打开独立 Chrome 窗口登录并自动刷新 token
$HELPER refresh-token --mode cdp --port 9222 # 可选：从已开启 CDP 的 Chrome 读取 token
$HELPER update-stock <id> add 100        # 追加库存
$HELPER update-stock <id> subtract 10   # 扣减库存
$HELPER update-stock <id> infinity       # 不限制库存
$HELPER coupon-limit <id>        # 优惠券限制
$HELPER from-excel <file.xlsx>   # 解析 Excel
$HELPER batch-create <file.json> # 批量新建（需确认）
```

> 当前辅助脚本主要封装了商品包能力。Leads 相关操作优先使用上面的 `leads_get` / `leads_post`，或直接在后台页面中执行。

---

## 常用工作流

### 商品包

**查找商品包**
```bash
api_get "/international/api/product/list/?start=0&limit=10&productName=精确名称"
api_get "/international/api/product/detail?productId=<ID>"
```

**新建商品包**（必填：`name` + `productTypeId=3` + `multiCurrencyPricingData` 至少一条）
```bash
api_post "/international/order-service/api/product/new" '{
  "name": "AIKID-36class-Test", "productTypeId": 3, "saleType": 1,
  "originPrice": "11880.00", "realPrice": "7247.00", "localeCurrencyRealPrice": "7247.00", "localeDiscount": 61,
  "discountType": 1, "visibility": 0, "adminVisibility": 1,
  "giftable": 0, "expireTime": 180, "stockLimit": false, "signatureType": 1,
  "detail": [{"subProductId": 100, "productCount": 36}],
  "multiCurrencyPricingData": [
    {"currencyCode": "AED", "originalPrice": "11880.00", "discountPercent": 61, "sellingPrice": "7247.00", "isEnabled": 1}
  ], "content": []
}'
```

**修改商品包**（必须带 `id`，未传字段不清空）
```bash
api_post "/international/order-service/api/product/edit" '{"id": 3537, "realPrice": "6500.00"}'
```

**库存 / 优惠券 / 赠送** → 见 [references/api.md](references/api.md)

### Leads 管理

**打开 Leads 管理页**
- 页面路由：`https://sa-leads.lionabc.com/leadsGCC/list`
- 首页 `/` 默认会跳到这个页面
- 一级权限码：`LEADS_MANAGEMENT_LEADS_MANAGE`
- 页面模式：私池 Leads，查询接口固定使用 `status=1`

**查询私池 Leads**
```bash
leads_post "/api/v1/leads/user/manage/getList" '{
  "flowNodeList": [],
  "flowReasonIdList": [],
  "status": 1,
  "currentPage": 1,
  "pageSize": 10,
  "userId": "",
  "studentId": "",
  "countryCode": null,
  "mobile": "",
  "staffId": "",
  "staffName": "",
  "gcsName": "",
  "tmkName": "",
  "kpFlag": "",
  "lastFollowTime": [],
  "lastUnFollowTime": [],
  "lastNodeTime": [],
  "registerTime": [],
  "lastLoginTime": [],
  "lastFollowResultType": "",
  "suspendTag": null,
  "registerToday": null,
  "nodeHasFollow": null,
  "durationBetweenCreateAndFollow": null,
  "willFlowToday": null,
  "buyingIntention": null,
  "trialSNSTime": null,
  "channelCode": "",
  "channelLevelId": ""
}'
```

补充说明：
- `flowNodeList` 的真实枚举值可先查 `GET /api/v1/leads/flow/manage/node/all`
- 渠道级联筛选的 `channelCode` / `channelLevelId` 可先查 `GET /api/v1/leads/business/channel/all`
- 直接调接口筛时间时，实测以 `lastFlowTimeStart` / `lastFlowTimeEnd`、`registerTimeStart` / `registerTimeEnd`、`lastLoginTimeStart` / `lastLoginTimeEnd` 这类开始/结束字段生效，不能只依赖数组字段
- 成功响应实测为 `code=0`，不要沿用商品包接口的 `code=200` 经验判断

**查询可分配员工（GCC/GCS/TMK）**
```bash
# 0=GCC, 1=GCS, 3=TMK
leads_post "/api/v1/leads/staff/getList" '{
  "pageSize": 100,
  "staffName": "员工名关键词",
  "staffRole": 0
}'
```

**手动分配 Leads**
```bash
leads_post "/api/v1/leads/user/manage/allot" '{
  "userIdList": [10001, 10002],
  "staffId": 90001,
  "staffRole": 0
}'
```

**手动流转到公海或冻结库**
```bash
# type: 0=公海, 2=冻结库
leads_post "/api/v1/leads/user/manage/flow" '{
  "userIdList": [10001, 10002],
  "type": 2
}'
```

**标签管理**
```bash
# 添加标签
leads_post "/api/v1/leads/user/addTag" '{"userId": 10001, "tagId": 12}'

# 删除标签
leads_post "/api/v1/leads/user/deleteTag" '{"userId": 10001, "tagId": 12}'
```

**更多筛选字段、批量导入、行内跳转页面** → 见 [references/leads.md](references/leads.md)

---

## 参考文档

- **完整 API 列表、请求/响应结构**：[references/api.md](references/api.md)
- **所有枚举值**（productTypeId / saleType / visibility / giftable 等）：[references/enums.md](references/enums.md)
- **Leads 管理页功能、筛选参数、批量操作、行内跳转页**：[references/leads.md](references/leads.md)

---

## 安全约束

⛔ **禁止调用：**
- `POST .../product/release/` — 上架
- `POST .../product/unrelease/` — 下架
- 任何含 `delete`、`remove`、`destroy` 的接口

✅ 批量写入前**必须展示清单并等待用户二次确认**。
✅ Leads 的批量分配、批量流转、批量导入、重置密码、绑定/解绑微信前，必须先向用户确认目标对象、目标状态和影响范围。

## 错误处理

| 情况 | 处理 |
|------|------|
| HTTP 401 | Token 过期，先运行 `refresh-token` 打开独立 Chrome 登录，失败再手动复制 Cookie |
| Playwright 打开的独立窗口里未检测到 `intlAuthToken` | 先确认已在独立窗口中完成登录，再重试自动刷新 |
| 想复用一个已开启远程调试端口的 Chrome | 改用 `refresh-token --mode cdp --port 9222` |
| code=400 含 "country or region" | `cr_code` 错误，检查 config.json |
| Leads 列表查询返回 `code=500` 且 `msg=Forwarding error` | 多半是把请求打到了 `sa-manager`，或错误复用了商品包那套请求头；改用 `sa-leads` + `authorization` + `app-code: leads-management` + `biz-line/web-site` |
| `MAINPRODUCT_HAVE_BEEN_RELATED` | 子商品已被其他商品包关联 |
| `PRODUCT_DUPLICATE_TAG` | 标签重复 |
| 批量部分失败 | 继续执行，最终汇总失败列表 |
