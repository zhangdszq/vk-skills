# API 完整参考

Base URL: `https://sa-manager.lionabc.com/rest`

枚举值见 [enums.md](enums.md)。

---

## 商品包列表

```
GET /international/api/product/list/
```

> 端点硬编码只返回 `productTypeId=3`，不可覆盖。`productName` 为精确匹配（SQL `=`），非模糊搜索。

| 参数 | 类型 | 说明 |
|------|------|------|
| start | int | 分页偏移量，默认 0 |
| limit | int | 每页数量，默认 10 |
| productId | long | 精确查询 |
| productName | string | 精确匹配名称 |
| status | byte | 0=未发布, 1=已发布, 2=已过期, 3=已删除 |
| courseType | string | 如 `MAJOR` |
| courseId | long | 课程 ID |
| discountType | byte | 折扣类型 |
| visibility | byte | 用户侧可见性 |
| adminVisibility | byte | 客服侧可见性 |
| leadsVisibility | byte | Leads 侧可见性 |
| giftable | byte | 0=普通, 1=赠品 |
| contractId | long | 合同 ID |

响应：`data.total` + `data.data[]`（含 id, name, status, originPrice, realPrice, giftable 等）

---

## 商品包详情

```
GET /international/api/product/detail?productId=<id>
```

> `type` 参数被后端忽略，无需传。

响应 `data` 主要字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id / name / showName | - | 基础信息 |
| productTypeId / saleType | int | 见枚举表 |
| originPrice / realPrice | string | 价格 |
| discount | decimal | 0-1 小数（0.8=八折） |
| discountType | byte | 见枚举表 |
| visibility / adminVisibility / leadsVisibility | byte | 可见性 |
| giftable | byte | 0=普通, 1=赠品 |
| status | byte | 只读，见枚举表 |
| expireTime | int | 有效期（天） |
| stockLimit | boolean | 是否限制库存 |
| signatureType | byte | 见枚举表 |
| detail | array | 子商品 `[{subProductId, productCount}]` |
| multiCurrencyPricingList | array | 多币种定价（⚠️ 仅出参，创建/修改请求用 `multiCurrencyPricingData`） |
| content | array | CMS 内容 |

---

## 新建商品包

```
POST /international/order-service/api/product/new
```

必填（`@NotNull`）：`name`、`productTypeId`。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | ✅ | 商品包名称 |
| productTypeId | long | ✅ | 普通课包填 `3` |
| showName | string | | JSON 格式：`{"default":"xxx"}` |
| saleType | int | | 1=课时, 2=有效期, 3=考试, 4=实物, 5=休学 |
| originPrice | decimal | | 原价 |
| realPrice | decimal | | 售卖价 |
| localeCurrencyRealPrice | decimal | ⚠️ 实际必填 | 本地币种售价，**值与 `realPrice` 相同即可**。字段已废弃但 DB NOT NULL，不传导致 `product_locale_currency_real_price_sum cannot be null` (code 500) |
| localeDiscount | int | | 1-100（80=八折） |
| discountType | byte | | 0=无折扣, 1=正常, 2=折上折 |
| visibility | byte | | 默认 0 |
| adminVisibility | byte | | |
| leadsVisibility | byte | | |
| giftable | byte | | 0=普通, 1=赠品 |
| expireTime | int | | 有效期（天） |
| stockLimit | boolean | | 是否限制库存 |
| signatureType | byte | | 0=无归属, 1=新签/补差/续费 |
| summary / thumbnail | string | | 摘要 / 封面图 URL |
| detail | array | | `[{subProductId*, productCount*}]` |
| multiCurrencyPricingData | array | ✅ 必填 | 见下方，**不传或传 `[]` 均会导致 code 500**，至少包含一条 `isEnabled: 1` 的记录。⚠️ **字段名是 `Data` 不是 `List`**——`multiCurrencyPricingList` 是详情接口的出参字段名，两者不同，不可混用 |
| content | array | | CMS 内容，传 `[]` |

**multiCurrencyPricingData 结构：**
```json
[{
  "currencyCode": "AED",
  "originalPrice": "11880.00",
  "discountPercent": 61,
  "sellingPrice": "7247.00",
  "isEnabled": 1
}]
```
> `discountPercent` 传 0-100 整数，后端自动转为小数。`isEnabled`: 0=未启用, 1=启用。
>
> ⚠️ **必须至少包含一条启用（`isEnabled: 1`）的记录**，否则后端计算 `product_locale_currency_real_price_sum` 为 null，DB 报 `Column 'product_locale_currency_real_price_sum' cannot be null` 错误（code 500）。Java 层没有 `@NotNull` 校验，此约束来自数据库。

**成功响应：** `{"code": 200, "data": <新ID>}`

**错误：**
- `MAINPRODUCT_HAVE_BEEN_RELATED`（子商品已关联）
- `PRODUCT_DUPLICATE_TAG`（标签重复）
- `code:500, Column 'product_locale_currency_real_price_sum' cannot be null` → 顶层字段 `localeCurrencyRealPrice` 未传（与 `multiCurrencyPricingData` 无关，此为后端已废弃字段但 DB NOT NULL 约束仍在）

---

## 修改商品包

```
POST /international/order-service/api/product/edit
```

请求体同新建，**必须含 `id`**。未传字段不清空（部分更新）。

---

## 优惠券使用限制

```
GET  /international/api/product/getCouponLimit/?productId=<id>
POST /international/order-service/api/product/editCouponLimit/
```

POST 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| productId | long | 必填 |
| couponLimitNum | string | 数量限制，**字符串**，范围 1-999999 |
| couponLimitRate | string | 金额比例，**字符串**，范围 (0, 100) 不含边界 |

> 两字段均为字符串类型，不传或空字符串=不限制。

---

## 库存管理

```
GET  /international/order-service/api/product/package/stock?packageId=<id>
POST /international/order-service/api/product/package/updateStock
```

GET 响应：`{stockLimit, stockNum, toBePaidNum, inRefundNum, paymentNum}`

POST 字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| packageId | long | 必填 |
| stockLimit | boolean | true=限制, false=不限制 |
| operateType | string | `"add"` 或 `"subtract"`（仅 stockLimit=true 时有效） |
| operateNum | int | 操作数量，必须 > 0 |
| productTypeId | long | 商品类型 ID（订阅包 4/5/9 不支持限制库存） |

示例：
```json
// 不限制
{"packageId": 3539, "stockLimit": false}

// 追加 100
{"packageId": 3539, "stockLimit": true, "operateType": "add", "operateNum": 100, "productTypeId": 3}
```

---

## 赠送权限配置

```
GET  /international/api/productPackage/auth/list?packageId=<id>
POST /international/api/productPackage/auth/config
```

POST: `{"packageId": 3539, "roleIds": [2397, 2398]}`

---

## 辅助查询

```bash
# 课程库存类型列表（获取 inventoryTypeId）
GET /international/api/inventory/type/course/rel/list/

# 全部角色列表（获取赠送权限 roleId）
GET /auth/api/auth/role/all

# 商品类型列表
GET /international/api/product/type/list
```

---

## 家长详情页聚合详情

```
GET /international/api/parent/v2/getParentDetailWithChildById?id=<parentId>
```

返回结构：

| 字段 | 说明 |
|------|------|
| `data.parent` | 家长基础信息 |
| `data.parentExt` | 扩展信息，如 memo / city / nationality / monthBudget / tags / referrerId / timeZone |
| `data.childs` | 学生列表 |

`vipkid-ops` 的 `parent-detail` 会把 `parent` 和 `parentExt` 合并后做摘要输出。

---

## 家长资料修改

```
POST /international/uc/api/parent/v2/updateInfo
```

前端以表单方式传参，最少包含：

| 字段 | 说明 |
|------|------|
| `id` | 家长 ID |
| 其余任一字段 | 要更新的字段 |

当前页面实际写入过的字段：

- `city`
- `hasOverseaStudyExp`
- `ethnicGroup`
- `nationality`
- `monthBudget`
- `memo`

> 接口支持的字段可能比页面更多；`vipkid-ops` 当前只显式开放上述字段，避免误写。

---

## 备注联系方式

```
POST /international/api/parent/editOtherContacts
```

表单字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `parentId` | long | 必填 |
| `otherContacts` | string | JSON 字符串，例如 `[{"data":"WhatsApp +9665..."},{"data":"Dad phone"}]` |

---

## 时区修改

```
POST /international/api/parent/updateTimeZone
```

表单字段：

| 字段 | 说明 |
|------|------|
| `parentId` | 家长 ID |
| `timeZone` | 例如 `GMT+03:00` |

页面下拉框仅提供 `GMT-12:00` 到 `GMT+12:00` 的整点值。

---

## 补填推荐码

```
POST /international/api/parent/updateReferrerInfo
```

表单字段：

| 字段 | 说明 |
|------|------|
| `parentId` | 家长 ID |
| `referrerCode` | 推荐码 |

前端额外做了一层校验：不能填写自己的邀请码。

---

## 家长解密

```
GET /international/api/parent/decrypt?id=<parentId>
```

主要返回：

- `countryCode`
- `phone`
- `contactCountryCode`
- `contactPhone`

---

## 家长是否下载 / 登录过 App

```
GET /international/uc/api/rpc/user/hasLogin?userId=<parentId>&deviceType=APP
```

常见 `deviceType`：

- `APP`
- 其他端值可按服务端支持传入

返回通常含 `hasLogin`、`lastLoginDateTime` 等字段。

---

## 课耗进度

```
GET /manager/webhub/admin/api/admin/class/progress?parentId=<parentId>
```

主要返回：

| 字段 | 说明 |
|------|------|
| `firstPaymentTime` | 首次付费时间 |
| `sessionInventories` | 课时库存详情 |
| `fixedConsumptions` | 固定课消包详情 |

---

## 固定课消明细

```
GET /international/api/minimumConsumption/schedule/detail/<id>?id=<id>
```

返回每个履约周期的：

- `cycleStartTime`
- `cycleEndTime`
- `consumedQuantity`
- `minimumConsumptionQuantity`

---

## 学习行为

批量查家长下全部学生：

```
GET /manager/webhub/admin/api/class/schedule/batchLearningBehavior?parentId=<parentId>
```

单个学生：

```
GET /manager/webhub/admin/api/class/schedule/learningBehavior?studentId=<studentId>
```

典型字段：

- `recentBookedStats`
- `monthlyConsumption`
- `monthlyCompletionDetail`
- `lastCompletion`

---

## 跟进记录聚合

家长详情页右侧跟进记录来自多路接口拼装：

```bash
# 学生列表（先拿 studentId）
GET /international/api/parent/v2/getParentDetailWithChildById?id=<parentId>

# 学生节点跟进
GET /international/api/flow/getFlowRemarkList?studentId=<studentId>&type=0

# 销售跟进
GET /international/api/sale/tracking/list?parentId=<parentId>

# 服务跟进
GET /international/leads/api/v2/leads/follow/record/getList?userId=<parentId>

# 智齿外呼记录
POST /international/leads/api/v1/leads/sobot/callRecord/search/?userId=<parentId>
```

`vipkid-ops follow-records` 会把这些结果聚合后统一输出。

---

## 海报配置与复制次数

海报配置：

```
GET /international/api/poster/config/getInfo
```

海报复制次数：

```
GET /international/api/busiclick/getTotal?action=posterCopy&parentId=<parentId>
```

> 页面中的“复制推荐语”和“复制海报到剪贴板”还依赖 CMS 配置、短链服务、二维码合成和浏览器剪贴板能力；CLI 当前只覆盖配置与计数查询。
