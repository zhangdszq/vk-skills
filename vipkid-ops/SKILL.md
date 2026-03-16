---
name: vipkid-ops
description: >
  VIPKID 国际化运营后台助理。商品包等国际化管理能力操作 sa-manager.lionabc.com；
  Leads 管理页、私池/公海/冻结库列表查询与相关接口操作 sa-leads.lionabc.com。
  支持商品包查询、新建、修改、库存、优惠券限制、赠送权限；
  也支持 Leads 列表筛选查询、节点统计、标签管理、解密用户、批量分配/流转、上传 Leads/权益、家长详情与关联页面入口说明。
  用户说「查商品包」「新建课包」「修改价格」「配置库存」「优惠券限制」「赠送配置」「查 leads」「Leads管理」「分配 GCC/GCS/TMK」「冻结 leads」「流转公海」「跟进 leads」「线索库」「解密用户」「上传 leads」时触发。
  ⛔ 绝不执行上架、下架、删除操作；任何批量分配、冻结、流转、上传、改密前必须二次确认。
---

# VIPKID 运营后台

优先使用现成脚本：

- 商品包能力：`scripts/ops_helper.py`
- Leads 能力：`scripts/leads_helper.py`

只有当脚本不覆盖某个只读场景时，才直接拼 `curl`。

## 初始化

共享配置文件是 `~/.vipkid-ops/config.json`：

```json
{
  "base_url": "https://sa-manager.lionabc.com",
  "leads_base_url": "https://sa-leads.lionabc.com",
  "token": "",
  "cr_code": "sa"
}
```

说明：

- `base_url` 默认是商品包/运营后台域名
- `leads_base_url` 默认是 Leads 域名
- `token` 是 `intlAuthToken`
- `cr_code` 常见值：`sa`、`ae`、`k2`、`hk`、`tw`、`kr`、`vn`、`jp`、`ts`

获取 token：

```bash
python3 scripts/ops_helper.py refresh-token
python3 scripts/ops_helper.py auth
python3 scripts/leads_helper.py auth
```

## 回答风格

面对业务用户时：

- 先给结论，再补充关键数字或链接
- 默认少讲技术术语、少讲接口名、少讲代码细节
- 用户只问结果时，不主动展开请求头、返回结构、报错栈
- 用户问“通话记录链接”“还有多少课时”“有没有跟进记录”“有多少个”时，直接给业务结果

只有在用户明确要求排查原因、修 skill、修脚本、看接口时，才展开技术细节。

## 快速分流

### 商品包

用在：

- 查商品包
- 新建课包
- 改价格
- 查库存 / 改库存
- 配优惠券限制
- 配赠送权限

常用命令：

```bash
python3 scripts/ops_helper.py list "商品包名"
python3 scripts/ops_helper.py detail 3537
python3 scripts/ops_helper.py inventory 3537
python3 scripts/ops_helper.py coupon-limit 3537
python3 scripts/ops_helper.py update-stock 3537 add 100
```

细节看：

- [references/api.md](references/api.md)
- [references/enums.md](references/enums.md)

### Leads

用在：

- 查私池 / 公海 / 冻结库列表
- 查节点数量、注册时间口径、节点生成时间口径
- 查标签、流转标记、节点、员工
- 解密用户
- 给线索加标签 / 删标签
- 分配 GCC / GCS / TMK
- 流转到冻结库或公海
- 上传 Leads / 上传权益 / 批量冻结
- 批量分配 GCC / TMK

常用命令：

```bash
python3 scripts/leads_helper.py list --status private --page-num 1 --page-size 20
python3 scripts/leads_helper.py list --status private --user-id 123456
python3 scripts/leads_helper.py list --status public --register-start "2026-03-16 00:00:00" --register-end "2026-03-16 23:59:59" --page-size 1
python3 scripts/leads_helper.py nodes
python3 scripts/leads_helper.py tags
python3 scripts/leads_helper.py flow-reasons
python3 scripts/leads_helper.py staff --role gcc --query Alice
python3 scripts/leads_helper.py decrypt-user 123456
```

写操作命令：

```bash
python3 scripts/leads_helper.py add-tag 123456 18 --yes
python3 scripts/leads_helper.py delete-tag 123456 18 --yes
python3 scripts/leads_helper.py allot gcc 9988 123456 234567 --yes
python3 scripts/leads_helper.py flow froze 123456 234567 --yes
python3 scripts/leads_helper.py upload leads ./leads.xlsx --yes
python3 scripts/leads_helper.py upload equity ./equity.xlsx --yes
python3 scripts/leads_helper.py upload frozen ./batch_frozen.xlsx --yes
python3 scripts/leads_helper.py batch-allot-upload gcc ./batch_allot.xlsx --yes
```

完整字段、权限、接口、模板链接见：

- [references/leads-public.md](references/leads-public.md)

## 业务优先流程

遇到业务同学的提问，优先按这个顺序处理：

1. 先识别问题类型
   - 商品包
   - 家长详情
   - 跟进/通话
   - Leads 节点列表/数量
2. 先给结果
   - 数量问题先给数字
   - 家长问题先给结论和关键字段
   - 通话问题直接给录音链接
3. 只在用户追问时再展开
   - 明细列表
   - 时间范围
   - 原因排查
   - 接口或脚本细节

如果用户表达很口语化，也不要要求他改成技术说法。像下面这些都应直接理解：

- “未完课节点” = `待试听课完课` = `WAIT_TRIAL_COMPLETE`
- “待付费” = `WAIT_PAY`
- “2.1 到现在” = 当年 `2月1日` 到今天
- “抓给我” = 查出结果并直接整理给用户

## 标准执行流程

### 只读查询

1. 先确认地区码 `cr_code` 和目标域名
2. 确认 `~/.vipkid-ops/config.json` 中 token 可用
3. 优先跑只读命令拿到 ID、tagId、staffId、flowReasonId
4. 汇总关键结果给用户，不要直接贴一大段原始 JSON，除非用户明确要

### 写操作

1. 先做一次只读查询，确认目标对象存在
2. 明确告诉用户将修改哪些对象、数量是多少、参数是什么
3. 如果是批量操作，必须展示清单或摘要并等待确认
4. 执行一次写入
5. 返回成功数、失败数、失败原因；必要时再做一次查询验证

## 边界与安全

这些能力适合自动化：

- 商品包查询/新建/修改
- Leads 列表查询
- 标签增删
- 解密用户
- 手动分配
- 流转到冻结库 / 公海
- 上传 Excel
- 读字典数据

这些更适合浏览器或仅作说明：

- 流转记录弹窗
- 跟进记录页面跳转
- 家长详情页跳转
- 依赖 iframe 的表单页

⛔ 禁止：

- `POST .../product/release/`
- `POST .../product/unrelease/`
- 任何含 `delete`、`remove`、`destroy` 的商品包接口
- 未经确认的批量标签、分配、流转、上传

✅ 必须：

- 批量写入前展示影响范围
- 写入后汇总结果
- token 或地区码异常时先排查配置，不要盲试多次

## 错误处理

| 情况 | 处理 |
|------|------|
| HTTP 401 / auth 失败 | 先运行 `python3 scripts/ops_helper.py refresh-token`，再重新校验 |
| `country or region` 错误 | 检查 `cr_code` 或 `leads_base_url` |
| SSL 证书链问题 | `leads_helper.py` 已通过 `curl -ks` 规避 |
| 接口可在浏览器里成功但脚本失败 | 优先检查 `Authorization` / `app-Code: leads-management` / `biz-line` / `web-site` 是否齐全 |
| Leads 接口 `code != 0` | 原样保留 `code` 和 `msg` 给用户 |
| Excel 上传失败 | 先确认模板是否正确，再检查文件类型、地区和权限 |
| 批量部分失败 | 不重试整批，先汇总失败项给用户确认 |

## 测试样例

草稿测试提示保存在：

- [evals/evals.json](evals/evals.json)
