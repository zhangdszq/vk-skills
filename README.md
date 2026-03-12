# vk-skills

Agent Skills 技能库。

## 核心技能（P0）

业务运营、教研、数据分析等核心场景专用技能。

| 技能 | 说明 |
|------|------|
| [smb-file-browser](smb-file-browser/) | 连接企业 SMB 文件服务器，浏览和下载教研课件，自动处理 DNS 劫持、跨平台挂载 |
| [curriculum-outline-editor](curriculum-outline-editor/) | 4-6 岁儿童英语课程大纲审校，修复中式英语、优化词汇复现，输出修订版 Excel |
| [teaching-outline-writer](teaching-outline-writer/) | 根据课程目标、学段和知识点，智能生成结构化教学大纲 |
| [picturebook-planner](picturebook-planner/) | 绘本馆选书策略、主题书单、阅读活动和馆藏建设方案 |
| [adjust-report](adjust-report/) | Adjust 归因分析，SKAN/Android 标准指标，渠道漏斗与转化率优化建议 |
| [megaview-openapi](megaview-openapi/) | Megaview + StarRocks 销售分析，员工绩效、会话评分、GMV 对比、辅导材料 |
| [aliyun-sms-bulk](aliyun-sms-bulk/) | 阿里云 MCP 批量短信，单发/群发（最多 100 号码/次） |
| [vipkid-ops](vipkid-ops/) | VIPKID 运营后台助理，商品包查询/新建/修改、库存、优惠券、赠送权限 |
| [dingtalk-task-stats](dingtalk-task-stats/) | 钉钉 AI 表格任务统计与需求看板分析，全量拉取记录后按字段过滤、聚合统计 |
| [sales-coach-lily](sales-coach-lily/) | 基于销冠 Lily 实战心法的销售通话分析，邀约/诊脉/异议处理/逼单维度反馈 |
| [hr-resume-screener](hr-resume-screener/) | HR 简历批量筛选评分，五维度 100 分制打分，结合 JD 输出适配建议 |
| [niuma-help](niuma-help/) | 牛马 AI 产品使用引导与帮助 |

## 通用技能（非 P0）

效率工具、图像生成、文档处理、开发辅助等通用场景技能。

### 效率工具

| 技能 | 说明 |
|------|------|
| [agent-reach](agent-reach/) | 一键配置 12+ 平台上游工具（Twitter/X、Reddit、YouTube、Bilibili 等） |
| [minimax](minimax/) | MiniMax API 工具集，AI 对话、文字转语音、视频生成 |
| [minimax-tts](minimax-tts/) | MiniMax 语音合成，多音色、语速调节、情绪控制 |
| [feishu-card](feishu-card/) | 向飞书用户或群组发送富交互卡片（Markdown、按钮） |
| [feishu-doc-reader](feishu-doc-reader/) | 使用飞书开放 API 读取和提取飞书文档内容 |
| [baoyu-url-to-markdown](baoyu-url-to-markdown/) | Chrome CDP 获取任意 URL 转 Markdown |
| [find-skills](find-skills/) | 帮助发现和安装 Agent 技能 |
| [long-term-plan](long-term-plan/) | 结构化多轮对话制定长期项目计划 |
| [daily-review](daily-review/) | 每日工作回顾与洞察分析 |
| [deep-review](deep-review/) | 深度工作分析与项目洞察 |
| [data-analysis](data-analysis/) | 全链路数据分析，CSV/Excel/PDF/图像处理 |
| [brand-guidelines](brand-guidelines/) | Anthropic 品牌颜色和字体应用 |
| [claude-skills-zh-cn](claude-skills-zh-cn/) | Anthropic Skills 中文翻译版 |

### 视频处理

| 技能 | 说明 |
|------|------|
| [remotion-video](remotion-video/) | Remotion 框架编程式创建视频（React 组件） |
| [ffmpeg-usage](ffmpeg-usage/) | FFmpeg 音视频处理，格式转换、拼接、压缩、字幕等 |

### 图像生成

| 技能 | 说明 |
|------|------|
| [baoyu-image-gen](baoyu-image-gen/) | AI 图像生成（OpenAI、Google、DashScope） |
| [gemini-image](gemini-image/) | Gemini 文生图和图生图 |
| [baoyu-cover-image](baoyu-cover-image/) | 文章封面图，5 维度组合 × 9 色彩方案 × 6 渲染风格 |
| [baoyu-compress-image](baoyu-compress-image/) | 图片压缩为 WebP/PNG |
| [imagemagick-conversion](imagemagick-conversion/) | ImageMagick 图像转换、调整、批量处理 |
| [algorithmic-art](algorithmic-art/) | p5.js 算法艺术，流场、粒子系统 |
| [canvas-design](canvas-design/) | Canvas 视觉设计，海报、艺术品 |
| [slack-gif-creator](slack-gif-creator/) | Slack 优化 GIF 动图制作 |
| [baoyu-danger-gemini-web](baoyu-danger-gemini-web/) | Gemini Web 逆向 API 图文生成 |

### 写作内容

| 技能 | 说明 |
|------|------|
| [baoyu-format-markdown](baoyu-format-markdown/) | Markdown 格式化，添加前置信息、标题层级 |
| [baoyu-article-illustrator](baoyu-article-illustrator/) | 文章配图，类型×风格二维方法 |
| [doc-coauthoring](doc-coauthoring/) | 结构化工作流文档协作撰写 |
| [internal-comms](internal-comms/) | 内部沟通材料写作（状态报告、FAQ 等） |
| [baoyu-comic](baoyu-comic/) | 知识漫画创作，多艺术风格 |

### 社交媒体

| 技能 | 说明 |
|------|------|
| [baoyu-post-to-wechat](baoyu-post-to-wechat/) | 发布微信公众号文章/图文 |
| [baoyu-post-to-x](baoyu-post-to-x/) | 发布 X/Twitter 帖子和长文 |
| [baoyu-xhs-images](baoyu-xhs-images/) | 小红书信息图系列，10 风格 × 8 布局 |
| [baoyu-danger-x-to-markdown](baoyu-danger-x-to-markdown/) | X 推文转 Markdown（逆向 API） |

### 文档工具

| 技能 | 说明 |
|------|------|
| [baoyu-markdown-to-html](baoyu-markdown-to-html/) | Markdown 转 HTML，兼容微信公众号 |
| [pdf](pdf/) | PDF 读取/合并/拆分/水印/OCR/加密 |
| [docx](docx/) | Word 文档创建/编辑/格式化 |
| [pptx](pptx/) | PPT 演示文稿处理 |
| [xlsx](xlsx/) | Excel 表格处理 |
| [ppocrv5](ppocrv5/) | 图片文字识别 OCR |
| [deepl](deepl/) | DeepL 翻译（文本/文档/XLIFF） |
| [baoyu-slide-deck](baoyu-slide-deck/) | 从内容生成幻灯片图像 |

### 信息图表

| 技能 | 说明 |
|------|------|
| [baoyu-infographic](baoyu-infographic/) | 专业信息图，20 布局 × 17 风格 |
| [infographic-creator](infographic-creator/) | 文本内容创建信息图 |
| [infographic-item-creator](infographic-item-creator/) | 信息图 Item 组件（TSX） |
| [infographic-structure-creator](infographic-structure-creator/) | 信息图 Structure 组件（TSX） |
| [infographic-syntax-creator](infographic-syntax-creator/) | AntV 信息图 DSL 语法输出 |
| [infographic-template-updater](infographic-template-updater/) | 信息图模板目录和 UI 更新 |
| [theme-factory](theme-factory/) | 主题样式工厂，10 种预设主题 |

### 开发工具

| 技能 | 说明 |
|------|------|
| [mcp-builder](mcp-builder/) | MCP 服务器构建指南（Python/Node） |
| [webapp-testing](webapp-testing/) | Playwright Web 应用测试 |
| [frontend-design](frontend-design/) | 高设计质量前端界面 |
| [web-artifacts-builder](web-artifacts-builder/) | React/Tailwind/shadcn 组件套件 |
| [remotion-best-practices](remotion-best-practices/) | Remotion 最佳实践指南 |
| [debugging](debugging/) | 万能调试引擎，防止 AI 放弃/推诿/磨洋工 |

## 安装

```bash
# macOS / Linux
ln -s ~/git-repos/vk-skills/<skill-name> ~/.claude/skills/<skill-name>
ln -s ~/git-repos/vk-skills/<skill-name> ~/.cursor/skills/<skill-name>

# Windows (PowerShell 管理员)
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\skills\<skill-name>" -Target "D:\git-repos\vk-skills\<skill-name>"
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.cursor\skills\<skill-name>" -Target "D:\git-repos\vk-skills\<skill-name>"
```
