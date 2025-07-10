# 🎨 PowerAutomation 4.1 SmartUI MCP 集成指南

## 📋 **概述**

SmartUI MCP是PowerAutomation 4.1的核心UI生成和管理组件，提供智能化的UI开发体验。通过模板驱动、AI优化和AG-UI深度集成，为开发者提供前所未有的UI开发效率。

## 🏗️ **架构概览**

### **核心组件**
```
core/components/smartui_mcp/
├── __init__.py                 # 组件入口
├── services/                   # 核心服务
│   ├── smartui_service.py     # 主服务
│   ├── ai_optimization_service.py
│   ├── theme_service.py
│   └── component_registry_service.py
├── generators/                 # 生成器引擎
│   ├── smartui_generator.py   # 智能生成器
│   ├── base_generator.py      # 基础生成器
│   ├── template_engine.py     # 模板引擎
│   └── ui_generator.py        # UI生成器
├── templates/                  # 模板系统
│   ├── components/            # 组件模板
│   ├── layouts/               # 布局模板
│   ├── pages/                 # 页面模板
│   └── themes/                # 主题模板
├── cli/                       # 命令行接口
│   └── smartui_cli.py         # CLI工具
├── config/                    # 配置管理
│   └── smartui_config.json    # 主配置文件
├── generated/                 # 生成输出
├── assets/                    # 静态资源
├── examples/                  # 示例代码
└── docs/                      # 文档
```

## 🚀 **快速开始**

### **1. 安装依赖**
```bash
# 安装Python依赖
pip install click jinja2 pyyaml

# 安装Node.js依赖（可选，用于前端框架支持）
npm install react vue
```

### **2. 初始化SmartUI MCP**
```python
from core.components.smartui_mcp import SmartUIService, SmartUIGenerator

# 启动服务
service = await SmartUIService().start()

# 创建生成器
generator = SmartUIGenerator(smartui_service=service)
```

### **3. 生成第一个组件**
```bash
# 使用CLI生成按钮组件
python -m core.components.smartui_mcp.cli.smartui_cli component generate button MyButton \
  --context '{"variant": "primary", "size": "lg", "text": "点击我"}'

# 生成表单输入组件
python -m core.components.smartui_mcp.cli.smartui_cli component generate input EmailInput \
  --context '{"type": "email", "label": "邮箱地址", "required": true}'
```

## 🎨 **模板系统**

### **组件模板结构**
```json
{
  "meta": {
    "name": "Button",
    "description": "可定制的按钮组件",
    "version": "1.0.0",
    "category": "basic",
    "author": "SmartUI MCP",
    "tags": ["button", "interactive", "form"]
  },
  "schema": {
    "type": "object",
    "properties": {
      "variant": {
        "type": "string",
        "enum": ["primary", "secondary", "success", "warning", "danger"],
        "default": "primary",
        "description": "按钮样式变体"
      },
      "size": {
        "type": "string", 
        "enum": ["sm", "md", "lg", "xl"],
        "default": "md",
        "description": "按钮尺寸"
      },
      "text": {
        "type": "string",
        "default": "Button",
        "description": "按钮文本"
      }
    }
  },
  "template": {
    "react": "templates/react/button.hbs",
    "vue": "templates/vue/button.hbs", 
    "html": "templates/html/button.hbs"
  },
  "styles": {
    "css": "styles/button.css",
    "scss": "styles/button.scss"
  },
  "examples": [
    {
      "name": "主要按钮",
      "description": "标准的主要操作按钮",
      "context": {
        "variant": "primary",
        "size": "md",
        "text": "提交"
      }
    }
  ]
}
```

### **模板引擎特性**
- **Handlebars语法** - 强大的模板语法支持
- **条件渲染** - `{{#if}}` `{{#unless}}` 条件控制
- **循环渲染** - `{{#each}}` 列表渲染
- **辅助函数** - 内置丰富的辅助函数
- **模板继承** - 支持模板继承和组合

## 🤖 **AI优化功能**

### **智能上下文优化**
```python
# AI自动优化组件上下文
optimized_context = await service.optimize_component_context(
    context={"text": "按钮", "color": "蓝色"},
    template="button",
    framework="react"
)
# 输出: {"text": "按钮", "variant": "primary", "size": "md", "accessibility": {...}}
```

### **代码质量优化**
- **性能优化** - 自动优化组件性能
- **可访问性增强** - 自动添加ARIA标签和语义化HTML
- **SEO优化** - 自动优化SEO相关属性
- **最佳实践** - 遵循框架最佳实践

## 🎭 **主题系统**

### **内置主题**
- **default** - 默认主题，现代简洁风格
- **dark** - 深色主题，适合夜间使用
- **light** - 浅色主题，简洁明亮
- **corporate** - 企业主题，专业商务风格
- **creative** - 创意主题，活泼有趣
- **minimal** - 极简主题，纯净简约

### **主题应用**
```bash
# 生成深色主题的组件
python -m core.components.smartui_mcp.cli.smartui_cli component generate button DarkButton \
  --theme dark --context '{"text": "深色按钮"}'

# 生成多主题变体
python -m core.components.smartui_mcp.cli.smartui_cli component generate-themes button MyButton \
  --themes dark,light,corporate
```

### **自定义主题**
```json
{
  "name": "custom-theme",
  "description": "我的自定义主题",
  "variables": {
    "primary-color": "#007bff",
    "secondary-color": "#6c757d",
    "success-color": "#28a745",
    "warning-color": "#ffc107",
    "danger-color": "#dc3545",
    "font-family": "'Helvetica Neue', Arial, sans-serif",
    "border-radius": "4px",
    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
  },
  "components": {
    "button": {
      "padding": "8px 16px",
      "font-weight": "500"
    }
  }
}
```

## 🔧 **AG-UI集成**

### **自动生成AG-UI定义**
SmartUI MCP自动为每个生成的组件创建AG-UI定义文件：

```json
{
  "meta": {
    "name": "MyButton",
    "version": "1.0.0",
    "framework": "react",
    "generated_by": "SmartUI MCP"
  },
  "component": {
    "type": "button",
    "props": {
      "variant": "primary",
      "size": "md",
      "text": "点击我"
    },
    "events": {
      "onClick": "handleClick"
    },
    "styles": {
      "className": "btn btn-primary"
    }
  },
  "agui_protocol": {
    "version": "4.1.0",
    "compatible": true,
    "features": ["reactive", "themeable", "accessible"]
  }
}
```

### **ClaudEditor集成**
```python
# 在ClaudEditor中使用SmartUI MCP
from core.components.smartui_mcp import SmartUIService
from core.components.ag_ui_mcp import AGUIComponentGenerator

# 集成到ClaudEditor
claudeditor_ui.register_component_generator(SmartUIService())
```

## 📊 **CLI命令参考**

### **组件管理**
```bash
# 生成组件
smartui component generate <template> <name> [options]

# 列出模板
smartui component list-templates [--category <category>]

# 查看模板信息
smartui component template-info <template> [--category <category>]

# 生成组件套件
smartui component generate-suite <suite-name> <config-file>
```

### **主题管理**
```bash
# 列出主题
smartui theme list

# 应用主题
smartui theme apply <theme-name> <component-path>

# 创建自定义主题
smartui theme create <theme-name> <config-file>
```

### **服务管理**
```bash
# 查看服务状态
smartui service status

# 健康检查
smartui service health

# 重启服务
smartui service restart
```

## 🔌 **编程接口**

### **基础使用**
```python
from core.components.smartui_mcp import SmartUIGenerator, SmartUIGenerationRequest

# 创建生成器
generator = SmartUIGenerator()

# 创建生成请求
request = SmartUIGenerationRequest(
    type="component",
    template="button",
    context={"name": "MyButton", "variant": "primary"},
    output_dir="./generated",
    framework="react",
    agui_integration=True,
    ai_optimization=True
)

# 生成组件
result = await generator.generate_smart(request)

if result.success:
    print(f"生成成功: {result.output_files}")
else:
    print(f"生成失败: {result.errors}")
```

### **批量生成**
```python
# 生成组件套件
components = [
    SmartUIGenerationRequest(type="component", template="button", context={"name": "PrimaryButton"}),
    SmartUIGenerationRequest(type="component", template="input", context={"name": "EmailInput"}),
    SmartUIGenerationRequest(type="component", template="select", context={"name": "CountrySelect"})
]

results = await generator.generate_component_suite("form-components", components)
```

### **主题变体生成**
```python
# 生成多主题变体
base_request = SmartUIGenerationRequest(
    type="component",
    template="button", 
    context={"name": "ThemedButton"}
)

theme_results = await generator.generate_theme_variations(
    base_request, 
    themes=["default", "dark", "light"]
)
```

## 📈 **性能优化**

### **缓存机制**
- **模板缓存** - 自动缓存已解析的模板
- **上下文缓存** - 缓存AI优化结果
- **组件缓存** - 缓存生成的组件代码
- **主题缓存** - 缓存主题计算结果

### **并行处理**
- **并行生成** - 支持多组件并行生成
- **异步处理** - 全异步架构，高性能
- **增量生成** - 只生成变更的部分
- **智能依赖** - 自动解析和管理依赖关系

## 🛡️ **错误处理**

### **常见错误**
```python
# 模板不存在
if not result.success and "template not found" in result.errors[0]:
    print("请检查模板名称是否正确")

# 上下文验证失败
if not result.success and "validation failed" in result.errors[0]:
    print("请检查上下文数据格式")

# AI服务不可用
if "ai service unavailable" in result.warnings:
    print("AI优化服务暂时不可用，使用默认配置")
```

### **调试模式**
```bash
# 启用详细输出
smartui --verbose component generate button MyButton

# 启用调试模式
export SMARTUI_DEBUG=true
smartui component generate button MyButton
```

## 🔄 **与其他MCP集成**

### **与Stagewise MCP集成**
```python
# 在测试中使用SmartUI生成的组件
from core.components.stagewise_mcp import StagewiseService
from core.components.smartui_mcp import SmartUIGenerator

# 生成测试组件
test_component = await smartui_generator.generate_smart(test_request)

# 在Stagewise测试中使用
await stagewise_service.test_component(test_component.output_files[0])
```

### **与MemoryOS MCP集成**
```python
# 使用MemoryOS记忆用户的UI偏好
from core.components.memoryos_mcp import MemoryOSService

# 获取用户UI偏好
user_preferences = await memoryos.get_user_preferences("ui_design")

# 应用到SmartUI生成
request.context.update(user_preferences)
result = await smartui_generator.generate_smart(request)
```

## 📚 **最佳实践**

### **模板设计**
1. **保持简洁** - 模板应该专注于单一职责
2. **参数化设计** - 通过参数控制组件行为
3. **可扩展性** - 预留扩展点和自定义选项
4. **文档完善** - 提供详细的使用说明和示例

### **组件生成**
1. **语义化命名** - 使用有意义的组件名称
2. **一致性** - 保持命名和结构的一致性
3. **可访问性** - 始终考虑可访问性要求
4. **性能优化** - 避免不必要的重复渲染

### **主题管理**
1. **变量驱动** - 使用CSS变量实现主题切换
2. **层次结构** - 建立清晰的主题层次结构
3. **向后兼容** - 确保主题更新的向后兼容性
4. **测试覆盖** - 对所有主题进行充分测试

## 🎯 **使用场景**

### **快速原型开发**
```bash
# 快速生成登录页面原型
smartui page generate login LoginPage \
  --context '{"title": "用户登录", "fields": ["email", "password"]}'
```

### **设计系统构建**
```bash
# 生成完整的设计系统组件库
smartui component generate-suite design-system design-system-config.json
```

### **多品牌支持**
```bash
# 为不同品牌生成主题变体
smartui component generate-themes button BrandButton \
  --themes brand-a,brand-b,brand-c
```

### **A/B测试支持**
```bash
# 生成A/B测试变体
smartui component generate button ButtonA --context '{"style": "variant-a"}'
smartui component generate button ButtonB --context '{"style": "variant-b"}'
```

## 🔮 **未来规划**

### **即将推出的功能**
- **可视化编辑器** - 拖拽式组件设计界面
- **实时预览** - 实时预览组件效果
- **组件市场** - 社区组件分享平台
- **AI设计助手** - 更智能的设计建议
- **多语言支持** - 国际化组件生成
- **移动端优化** - 专门的移动端组件

### **技术演进**
- **WebAssembly集成** - 提升生成性能
- **GraphQL支持** - 更灵活的数据查询
- **微前端支持** - 支持微前端架构
- **云端协作** - 团队协作功能

---

## 📞 **支持与反馈**

如有问题或建议，请联系PowerAutomation 4.1团队：
- 📧 Email: support@powerautomation.com
- 📱 GitHub: https://github.com/powerautomation/smartui-mcp
- 📖 文档: https://docs.powerautomation.com/smartui-mcp

**SmartUI MCP - 让UI开发更智能、更高效！** 🚀

