# Cloud MCP AG-UI Dashboard

🚀 **智能端云部署系统控制台** - 基于AG-UI协议的现代化Web管理界面

[![Deploy Status](https://img.shields.io/badge/Deploy-Live-brightgreen)](https://mennfpem.manus.space)
[![AG-UI](https://img.shields.io/badge/AG--UI-Protocol-blue)](https://docs.ag-ui.com/)
[![CopilotKit](https://img.shields.io/badge/CopilotKit-Powered-purple)](https://www.copilotkit.ai/)
[![React](https://img.shields.io/badge/React-19-61dafb)](https://react.dev/)

## 🌟 项目概述

Cloud MCP AG-UI Dashboard是一个基于AG-UI协议的智能端云部署系统管理界面，集成了最新的AI代理交互技术，为用户提供直观、智能的系统管理体验。

### 🎯 核心特性

- **🤖 AG-UI协议集成**: 遵循Agent User Interaction Protocol标准
- **🧠 AI智能助手**: 集成CopilotKit框架，提供智能对话和建议
- **📊 实时监控**: AI增强的系统性能监控和分析
- **🎨 现代化UI**: 响应式设计，支持深色/浅色主题
- **⚡ 高性能**: 基于Vite构建，快速加载和热更新
- **🔧 模块化**: 组件化架构，易于扩展和维护

## 🏗️ 技术架构

### 前端技术栈
- **React 19**: 最新的React框架
- **AG-UI Protocol**: 标准化AI代理交互协议
- **CopilotKit**: 企业级AI应用框架
- **Tailwind CSS**: 原子化CSS框架
- **shadcn/ui**: 高质量UI组件库
- **Framer Motion**: 专业动画库
- **Vite**: 现代化构建工具

### AG-UI集成
```javascript
import { CopilotKit, CopilotSidebar } from '@copilotkit/react-core'
import { CopilotChat } from '@copilotkit/react-ui'

// AG-UI协议集成示例
<CopilotKit publicApiKey="demo-key">
  <CopilotSidebar>
    <CopilotChat
      labels={{
        title: "Cloud MCP AI助手",
        initial: "你好！我是Cloud MCP的AI助手..."
      }}
    />
  </CopilotSidebar>
</CopilotKit>
```

## 🚀 快速开始

### 环境要求
- Node.js 18+
- pnpm 8+

### 安装依赖
```bash
# 克隆项目
git clone <repository-url>
cd cloud-mcp-agui-dashboard

# 安装依赖
pnpm install
```

### 开发模式
```bash
# 启动开发服务器
pnpm run dev

# 访问 http://localhost:5173
```

### 生产构建
```bash
# 构建生产版本
pnpm run build

# 预览构建结果
pnpm run preview
```

## 📱 功能模块

### 🏠 智能仪表板
- **系统概览**: 环境总数、活跃部署、系统健康度
- **AI洞察**: 智能分析和优化建议
- **性能监控**: 实时CPU、内存、网络监控
- **活动分析**: AI评分的系统活动记录

### 🔧 管理功能
- **环境管理**: AI辅助环境配置和优化
- **智能部署**: 自动化部署管理和预测
- **AI监控**: 智能告警和性能预测
- **安全防护**: AI驱动的安全分析
- **性能优化**: AI性能调优建议
- **用户管理**: 智能权限管理
- **系统设置**: AI配置助手

## 🎨 界面特色

### AI增强体验
- **智能搜索**: 支持自然语言查询
- **AI洞察横幅**: 实时显示系统优化建议
- **智能状态卡片**: 每个指标包含AI分析
- **AI助手入口**: 一键启动智能对话

### 视觉设计
- **现代化布局**: 清晰的信息层次和视觉引导
- **动态交互**: 流畅的动画和过渡效果
- **响应式设计**: 完美适配各种设备尺寸
- **主题支持**: 深色/浅色主题切换

## 🔗 在线演示

**Live Demo**: [https://mennfpem.manus.space](https://mennfpem.manus.space)

## 📚 相关文档

- [AG-UI Protocol Documentation](https://docs.ag-ui.com/)
- [CopilotKit Documentation](https://docs.copilotkit.ai/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [AG-UI Protocol](https://docs.ag-ui.com/) - 标准化AI代理交互协议
- [CopilotKit](https://www.copilotkit.ai/) - 强大的AI应用框架
- [shadcn/ui](https://ui.shadcn.com/) - 优秀的UI组件库
- [Tailwind CSS](https://tailwindcss.com/) - 实用的CSS框架

---

**Cloud MCP AG-UI Dashboard** - 让AI驱动的端云管理变得简单而强大 🚀

