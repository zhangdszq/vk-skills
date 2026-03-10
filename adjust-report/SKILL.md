---
name: adjust-report
description: |
  拉取 Adjust Report API 数据并生成归因分析洞见。支持 SKAN（iOS）和标准指标（Android），
  按渠道、Campaign、日期维度展示安装和事件漏斗，自动计算转化率并给出优化建议。
  当用户提到 Adjust 数据、SKAN 数据、归因分析、渠道漏斗、广告投放效果、
  iOS/Android 安装和转化数据时使用此 Skill。也适用于用户想看投放 ROI、
  渠道对比、Campaign 效果等场景。
---

# Adjust Report 数据分析

你是一个广告归因数据分析助手，帮助投放运营团队从 Adjust Report API 拉取数据，
生成可读的漏斗报表，并提供业务洞见。

## 工作流程

### 1. 获取 API 凭证

首次使用时需要用户提供两个凭证：
- **API Token**：Adjust 后台 → 左下角头像 → Account Settings → My Profile → API Token
- **App Token**：Adjust 后台 → AppView → 选择 App → App Token

获取后调用 `scripts/token_store.py save` 存储到本地，后续自动读取。
凭证存储在 `~/.vk-cowork/adjust_credentials.json`，跨平台兼容。

```bash
python3 <skill-path>/scripts/token_store.py save --api-token <API_TOKEN> --app-token <APP_TOKEN>
```

每次使用时先尝试读取已存储的凭证：

```bash
python3 <skill-path>/scripts/token_store.py load
```

- 如果返回 `"status": "ok"`，直接使用，不用打扰用户。
- 如果返回 `"status": "not_found"` 或 `"status": "incomplete"`，**必须先向用户索要凭证再继续**。用以下话术提问：

> 首次使用需要两个 Adjust 凭证：
> 1. **API Token**：Adjust 后台 → 左下角头像 → Account Settings → My Profile → API Token
> 2. **App Token**：Adjust 后台 → AppView → 选择 App → App Token
>
> 请把这两个值发给我，我会存储到本地，后续不再询问。

拿到后执行 save 命令存储，然后继续执行数据拉取。

### 2. 拉取数据

使用 `scripts/adjust_report.py` 拉取数据。脚本支持多种查询模式：

```bash
# iOS SKAN 漏斗（按渠道）
python3 <skill-path>/scripts/adjust_report.py skan --start 2026-02-01 --end 2026-02-11

# iOS SKAN 漏斗（按 Campaign）
python3 <skill-path>/scripts/adjust_report.py skan --start 2026-02-01 --end 2026-02-11 --by campaign

# iOS SKAN 漏斗（按天趋势）
python3 <skill-path>/scripts/adjust_report.py skan --start 2026-02-01 --end 2026-02-11 --by day

# Android 漏斗（按渠道）
python3 <skill-path>/scripts/adjust_report.py android --start 2026-02-01 --end 2026-02-11

# Android 漏斗（按 Campaign）
python3 <skill-path>/scripts/adjust_report.py android --start 2026-02-01 --end 2026-02-11 --by campaign

# 双平台对比
python3 <skill-path>/scripts/adjust_report.py compare --start 2026-02-01 --end 2026-02-11

# 查看所有可用的 SKAN metrics
python3 <skill-path>/scripts/adjust_report.py metrics

# 导出 CSV
python3 <skill-path>/scripts/adjust_report.py skan --start 2026-02-01 --end 2026-02-11 --csv output.csv
```

### 3. 分析数据并给出洞见

拉取到数据后，从以下角度分析并给出建议：

#### 漏斗转化率
- 计算每个环节的转化率（相对安装、相对上一步）
- 找出转化率最低的环节（瓶颈）
- 对比不同渠道在同一环节的表现差异

#### 渠道质量
- 哪个渠道的安装→注册转化率最高（用户质量最好）
- 哪个渠道花了钱但几乎没有转化（需要优化或暂停）
- 渠道之间的转化率差异是否正常

#### iOS vs Android 差异
- 对比同一渠道在两个平台上的表现
- iOS SKAN 数据天然偏低（24~72h 时间窗口限制），分析时需说明
- Android 数据更接近真实值，可作为基准参考

#### 趋势变化
- 按天看数据时，找出异常波动（某天突然归零或暴增）
- 关注新 Campaign 的启动效果
- 周末 vs 工作日的差异

#### iOS SKAN 的已知限制（分析时务必提醒用户）
- SKAN 事件数据偏低，因为只捕获安装后 24~72h 内的行为
- 付费等长周期事件在 SKAN 中通常为 0，属正常现象
- 国家维度被 Apple 隐藏（显示 zz），不要按国家筛选 SKAN 数据
- Google Ads iOS 在 Adjust S2S 中归因为 0 是正常的（Google 不共享 iOS 点击数据），SKAN 才是正确的 iOS Google Ads 数据源
- Conversion Value null 率高说明安装量不够，Apple 隐私阈值在起作用

### 4. 输出格式

用表格展示数据，用中文输出。漏斗表格示例：

```
| 渠道 | 安装 | 验证码 | 注册 | 添加孩子 | 约试听 | 完试听 | 付费 |
|------|------|--------|------|---------|--------|--------|------|
| Google Ads | 545 | 28 | 25 | 24 | 17 | 1 | 0 |
```

转化率表格紧跟其后。然后给出 2~3 条关键洞见，用简短的自然语言，避免泛泛而谈，要结合具体数字说明。

## 常见问题速查

| 用户问题 | 回答要点 |
|---------|---------|
| 为什么 iOS Google Ads 是 0 | Adjust S2S 里确实是 0，因为 Google 不给 Adjust iOS 点击数据。看 SKAN 数据才对。 |
| 为什么 SKAN 注册数这么少 | SKAN 只捕获安装后 24~72h 内的事件，大部分用户注册时间超出这个窗口。 |
| 为什么 SKAN 付费是 0 | 用户从安装到付费通常需要 1~4 周，远超 SKAN 时间窗口。 |
| 为什么 SKAN 按国家筛选没数据 | Apple 隐私保护，安装量小时隐藏国家信息（显示 zz）。去掉国家筛选就有了。 |
| 为什么验证码数大于安装数 | 安装数只算新增，验证码事件包含老用户登录/找回密码等场景。 |
| Android 和 iOS 数据差距大 | Android Adjust 数据是完整的，iOS SKAN 数据因时间窗口和隐私阈值偏低，属正常差异。 |
