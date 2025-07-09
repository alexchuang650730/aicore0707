# Cloud MCP AG-UI Dashboard 部署指南

## 📍 项目位置

本项目位于 aicore0707 仓库的 `core/components/cloud_mcp_agui_dashboard/` 目录下。

## 🚀 快速部署

### 本地开发环境

```bash
# 进入项目目录
cd core/components/cloud_mcp_agui_dashboard/

# 安装依赖
pnpm install

# 启动开发服务器
pnpm run dev

# 访问 http://localhost:5173
```

### 生产环境构建

```bash
# 构建生产版本
pnpm run build

# 预览构建结果
pnpm run preview
```

## 🌐 在线演示

**Live Demo**: [https://mennfpem.manus.space](https://mennfpem.manus.space)

## 📦 项目结构

```
core/components/cloud_mcp_agui_dashboard/
├── src/
│   ├── components/ui/          # shadcn/ui 组件库
│   ├── hooks/                  # React Hooks
│   ├── lib/                    # 工具函数
│   ├── App.jsx                 # 主应用组件
│   ├── main.jsx               # 应用入口
│   └── index.css              # 全局样式
├── public/                     # 静态资源
├── dist/                       # 构建输出 (生产环境)
├── README.md                   # 项目文档
├── CHANGELOG.md               # 变更日志
├── DEPLOYMENT.md              # 部署指南
├── package.json               # 项目配置
├── vite.config.js             # Vite 配置
└── components.json            # shadcn/ui 配置
```

## 🔧 技术栈

- **React 19**: 最新的React框架
- **AG-UI Protocol**: 标准化AI代理交互协议
- **CopilotKit**: 企业级AI应用框架
- **Tailwind CSS**: 原子化CSS框架
- **shadcn/ui**: 高质量UI组件库
- **Framer Motion**: 专业动画库
- **Vite**: 现代化构建工具

## 🌟 核心特性

### AG-UI 协议集成
- 遵循 Agent User Interaction Protocol 标准
- CopilotKit 框架集成
- 标准化的AI代理交互接口

### AI 增强功能
- 智能搜索和自然语言查询
- AI 洞察和优化建议
- 智能活动分析和评分
- 内置AI助手对话

### 现代化界面
- 响应式设计，支持移动端
- 深色/浅色主题切换
- 流畅的动画和过渡效果
- 直观的用户体验

## 🔗 相关链接

- **GitHub仓库**: [https://github.com/alexchuang650730/aicore0707](https://github.com/alexchuang650730/aicore0707)
- **项目路径**: `core/components/cloud_mcp_agui_dashboard/`
- **在线演示**: [https://mennfpem.manus.space](https://mennfpem.manus.space)

## 📚 文档

- [README.md](./README.md) - 项目概述和使用指南
- [CHANGELOG.md](./CHANGELOG.md) - 版本变更记录
- [AG-UI Protocol Documentation](https://docs.ag-ui.com/)
- [CopilotKit Documentation](https://docs.copilotkit.ai/)

## 🤝 贡献

本项目是 aicore0707 生态系统的一部分，欢迎贡献代码和建议。

## 📄 许可证

本项目遵循 aicore0707 仓库的许可证条款。

---

**Cloud MCP AG-UI Dashboard** - AI驱动的下一代端云管理界面 🚀

