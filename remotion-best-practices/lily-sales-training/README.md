# 销冠Lily的销售心法 - 培训视频

基于《销冠Lily的销售心法》VIPKID绘本馆销售赋能内部手册制作的 Remotion 培训视频。

## 📹 视频内容

本视频涵盖了销售全流程的核心技巧：

1. **封面** - 销冠Lily的销售心法
2. **开篇** - 为什么是Lily？（18个月销冠记录）
3. **第一章 - 邀约篇**
   - 电话前准备工作
   - 黄金前30秒话术
4. **第二章 - 诊脉篇**
   - 三诊三问法
   - 挖掘真实需求
5. **第三章 - 理念渗透篇**
   - FAB法则（特征-优势-利益）
   - 三明治法则
6. **第四章 - 异议处理篇**
   - 价格异议处理
   - "再考虑考虑"应对
   - 家人决策应对
7. **第五章 - 逼单篇**
   - 逼单四步法
8. **结尾** - 销售是科学与艺术的结合

## 🚀 快速开始

### 安装依赖

```bash
cd lily-sales-training
npm install
```

### 启动开发服务器

```bash
npm start
```

这将启动 Remotion Studio，你可以在浏览器中预览视频。

### 渲染视频

```bash
npm run build
```

视频将渲染到 `out/video.mp4`

## 🎨 视频规格

- **分辨率**: 1920x1080 (Full HD)
- **帧率**: 30 FPS
- **总时长**: 约 100 秒
- **总帧数**: 3000 帧

## 📁 项目结构

```
lily-sales-training/
├── src/
│   ├── components/          # 可复用组件
│   │   ├── Cover.tsx       # 封面组件
│   │   ├── ChapterTitle.tsx  # 章节标题组件
│   │   ├── ContentSlide.tsx  # 内容幻灯片组件
│   │   ├── FormulaCard.tsx   # 公式卡片组件
│   │   └── DialogueSlide.tsx # 对话幻灯片组件
│   ├── compositions/        # 视频合成
│   │   └── LilySalesTraining.tsx
│   ├── Root.tsx            # 根组件
│   ├── index.ts            # 入口文件
│   └── remotion.config.ts  # Remotion 配置
├── package.json
├── tsconfig.json
└── README.md
```

## 🎯 自定义内容

### 修改场景

在 `src/compositions/LilySalesTraining.tsx` 中的 `SCENES` 数组里定义所有场景。每个场景包含：

- `duration`: 持续帧数
- `component`: 使用的组件
- `props`: 传递给组件的属性

### 修改样式

每个组件都支持自定义颜色、字体大小等样式属性。例如：

```tsx
<ContentSlide
  title="我的标题"
  points={["要点1", "要点2"]}
  backgroundColor="linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"
/>
```

### 添加新组件

在 `src/components/` 目录下创建新组件，然后在 `LilySalesTraining.tsx` 中导入并使用。

## 🎬 Remotion 最佳实践

遵循以下 Remotion 开发原则：

1. **使用 useCurrentFrame()** 获取当前帧号来驱动动画
2. **使用 interpolate()** 创建平滑的数值过渡
3. **使用 spring()** 实现弹性动画效果
4. **使用 Sequence** 组织时间轴上的多个场景
5. **避免外部副作用** - 组件应该是纯函数
6. **性能优化** - 避免在组件内部创建新对象/函数

## 📝 扩展建议

1. **添加背景音乐**: 使用 `<Audio>` 组件添加背景音乐
2. **添加配音**: 为每个场景添加配音旁白
3. **添加字幕**: 使用 `<Subtitles>` 组件添加字幕
4. **导出不同格式**: 修改配置导出 GIF、不同分辨率等
5. **添加互动元素**: 使用 `<input>` 等组件创建可交互视频

## 🔗 相关资源

- [Remotion 官方文档](https://www.remotion.dev/docs/)
- [Remotion GitHub](https://github.com/remotion-dev/remotion)
- 原始PDF: 《销冠Lily的销售心法》VIPKID绘本馆销售赋能内部手册

## 📜 许可证

MIT
