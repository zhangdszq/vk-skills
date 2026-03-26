# DinoClaw SkillHub

从 `DinoClaw/website/` 迁入的独立静态站点，包含：

- `skillhub.html`：技能社区主页
- `skills-browse.html`：按部门浏览全部技能（卡片 / 列表切换，`?dept=` 与首页部门筛选一致）
- `skills-data.js`：首页与浏览页共享的技能数据、部门映射与图标定义
- `login.html`：钉钉扫码登录页
- `cases.html`：使用案例页
- `auth/dingtalk-callback.html`：钉钉 OAuth 回调页
- `assets/`：SkillHub 与案例页所需图片

## 目录结构

```text
dinoclaw-skillhub/
  skillhub.html
  skills-browse.html
  skills-data.js
  login.html
  cases.html
  auth/
    dingtalk-callback.html
  assets/
    dinoclaw-login-bg.png
    dinoclaw-splash-connect.png
    dinoclaw-splash-memory.png
    dinoclaw-splash-autonomy.png
    dinoclaw-ai-mascot.png.png
```

## 部署前需要替换的占位地址

本目录里的页面不再与 DinoClaw 官网 `index.html` 同目录，因此已把相关链接改成绝对地址占位：

- `https://dinoclaw.example.com`

部署前请把 `skillhub.html` 和 `cases.html` 中的这个占位地址统一替换成你实际的 DinoClaw 官网基址，例如：

```text
https://your-domain.example.com/dinoclaw
```

## 钉钉登录配置

`login.html` 的登录链路参考 `DinoClaw/src/electron/libs/dingtalk-auth.ts`，但网页端只负责发起 OAuth 授权，不能在前端保存 `clientSecret`。

使用方式：

1. 打开 `login.html?client_id=你的钉钉应用ClientId`
2. 或先在浏览器控制台执行：

```js
localStorage.setItem("dingtalk_oauth_client_id", "你的ClientId");
```

3. 在钉钉开放平台登记回调地址：

```text
https://<你的域名>/<部署路径>/auth/dingtalk-callback.html
```

4. 在服务端使用 `authCode` 调用钉钉 `userAccessToken` 接口换取 token

## 本地预览

这是纯静态页面，可直接用任意静态文件服务预览，例如在本目录启动一个简单 HTTP 服务后访问：

- `skillhub.html`
- `login.html`
- `cases.html`

## 备注

- `cases.html` 已新增返回 `skillhub.html` 的「技能社区」入口。
- `login.html` 背景图加载失败时会自动隐藏，不影响登录流程。
