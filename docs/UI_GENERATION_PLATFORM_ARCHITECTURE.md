# ClaudEditor 4.1 AG-UI UI生成平台架构设计

## 🏗️ **整体架构**

### **核心设计理念**
- **模板驱动** - 所有UI生成都基于模板定义
- **AG-UI集成** - 完全基于AG-UI组件生成器架构
- **命令驱动** - 通过命令行和API接口操作
- **实时预览** - 支持实时预览和热更新
- **主题系统** - 统一的主题管理和切换

### **架构层次**
```
┌─────────────────────────────────────────────────────────┐
│                    用户接口层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   CLI工具    │  │   Web界面    │  │   API接口    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    生成器层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  组件生成器   │  │  布局生成器   │  │  页面生成器   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  主题生成器   │  │  样式生成器   │  │  脚本生成器   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    模板层                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  组件模板    │  │  布局模板    │  │  页面模板    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  主题模板    │  │  样式模板    │  │  配置模板    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   AG-UI核心层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │AG-UI组件生成器│  │  协议适配器   │  │  状态管理器   │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└─────────────────────────────────────────────────────────┘
```

## 📁 **详细目录结构**

### **ui/templates/ - 模板定义**
```
templates/
├── components/                 # 组件模板
│   ├── basic/                 # 基础组件
│   │   ├── button.json        # 按钮组件模板
│   │   ├── input.json         # 输入框组件模板
│   │   ├── select.json        # 选择器组件模板
│   │   └── checkbox.json      # 复选框组件模板
│   ├── form/                  # 表单组件
│   │   ├── form.json          # 表单容器模板
│   │   ├── form-field.json    # 表单字段模板
│   │   └── form-group.json    # 表单组模板
│   ├── navigation/            # 导航组件
│   │   ├── navbar.json        # 导航栏模板
│   │   ├── sidebar.json       # 侧边栏模板
│   │   └── breadcrumb.json    # 面包屑模板
│   ├── data/                  # 数据展示组件
│   │   ├── table.json         # 表格模板
│   │   ├── chart.json         # 图表模板
│   │   └── list.json          # 列表模板
│   └── feedback/              # 反馈组件
│       ├── modal.json         # 模态框模板
│       ├── toast.json         # 提示框模板
│       └── loading.json       # 加载组件模板
├── layouts/                   # 布局模板
│   ├── grid.json             # 网格布局
│   ├── flex.json             # 弹性布局
│   ├── sidebar.json          # 侧边栏布局
│   └── dashboard.json        # 仪表板布局
├── pages/                     # 页面模板
│   ├── dashboard.json        # 仪表板页面
│   ├── form.json             # 表单页面
│   ├── list.json             # 列表页面
│   └── detail.json           # 详情页面
└── patterns/                  # 设计模式模板
    ├── crud.json             # CRUD模式
    ├── wizard.json           # 向导模式
    ├── master-detail.json    # 主从模式
    └── kanban.json           # 看板模式
```

### **ui/generators/ - 生成器**
```
generators/
├── __init__.py               # 生成器包初始化
├── base_generator.py         # 基础生成器类
├── component_generator.py    # 组件生成器
├── layout_generator.py       # 布局生成器
├── page_generator.py         # 页面生成器
├── theme_generator.py        # 主题生成器
├── style_generator.py        # 样式生成器
├── script_generator.py       # 脚本生成器
├── template_engine.py        # 模板引擎
├── validation.py             # 模板验证
└── cli.py                    # 命令行接口
```

### **ui/components/ - 生成的组件**
```
components/
├── basic/                    # 基础组件
│   ├── buttons/             # 按钮组件
│   ├── inputs/              # 输入组件
│   └── displays/            # 显示组件
├── complex/                 # 复杂组件
│   ├── forms/               # 表单组件
│   ├── tables/              # 表格组件
│   └── charts/              # 图表组件
├── custom/                  # 自定义组件
│   ├── testing/             # 测试相关组件
│   ├── admin/               # 管理相关组件
│   └── user/                # 用户相关组件
└── generated/               # 动态生成的组件
    ├── temp/                # 临时组件
    └── cache/               # 缓存组件
```

### **ui/themes/ - 主题系统**
```
themes/
├── claudeditor/             # ClaudEditor主题
│   ├── dark.json           # 深色主题
│   ├── light.json          # 浅色主题
│   └── auto.json           # 自动主题
├── testing/                 # 测试主题
│   ├── focused.json        # 专注主题
│   └── colorful.json       # 彩色主题
├── custom/                  # 自定义主题
│   └── user_themes/        # 用户主题
└── base/                    # 基础主题
    ├── variables.json      # 主题变量
    ├── colors.json         # 颜色定义
    └── typography.json     # 字体定义
```

## 🔧 **核心组件设计**

### **1. 模板引擎 (Template Engine)**
```python
class TemplateEngine:
    """模板引擎 - 负责模板解析和渲染"""
    
    def __init__(self):
        self.template_cache = {}
        self.variable_resolver = VariableResolver()
        self.condition_evaluator = ConditionEvaluator()
    
    async def render_template(
        self, 
        template_path: str, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """渲染模板"""
        pass
    
    def parse_template(self, template_content: str) -> TemplateAST:
        """解析模板"""
        pass
    
    def validate_template(self, template: Dict[str, Any]) -> ValidationResult:
        """验证模板"""
        pass
```

### **2. 组件生成器 (Component Generator)**
```python
class ComponentGenerator(BaseGenerator):
    """组件生成器 - 基于模板生成UI组件"""
    
    async def generate_component(
        self,
        template_name: str,
        config: Dict[str, Any],
        theme: Optional[str] = None
    ) -> AGUIComponent:
        """生成组件"""
        pass
    
    async def generate_from_template(
        self,
        template_path: str,
        context: Dict[str, Any]
    ) -> AGUIComponent:
        """从模板生成组件"""
        pass
    
    def get_available_templates(self) -> List[str]:
        """获取可用模板列表"""
        pass
```

### **3. 主题生成器 (Theme Generator)**
```python
class ThemeGenerator:
    """主题生成器 - 生成和管理主题"""
    
    async def generate_theme(
        self,
        base_theme: str,
        customizations: Dict[str, Any]
    ) -> Theme:
        """生成主题"""
        pass
    
    async def apply_theme(
        self,
        component: AGUIComponent,
        theme: Theme
    ) -> AGUIComponent:
        """应用主题到组件"""
        pass
    
    def get_available_themes(self) -> List[str]:
        """获取可用主题列表"""
        pass
```

## 📋 **模板定义规范**

### **组件模板结构**
```json
{
  "meta": {
    "name": "button",
    "version": "1.0.0",
    "description": "基础按钮组件",
    "category": "basic",
    "tags": ["button", "interactive", "form"],
    "author": "ClaudEditor Team",
    "created": "2025-01-09",
    "updated": "2025-01-09"
  },
  "schema": {
    "type": "object",
    "properties": {
      "variant": {
        "type": "string",
        "enum": ["primary", "secondary", "success", "warning", "danger"],
        "default": "primary",
        "description": "按钮变体"
      },
      "size": {
        "type": "string", 
        "enum": ["small", "medium", "large"],
        "default": "medium",
        "description": "按钮尺寸"
      },
      "text": {
        "type": "string",
        "description": "按钮文本"
      },
      "icon": {
        "type": "string",
        "description": "按钮图标"
      },
      "disabled": {
        "type": "boolean",
        "default": false,
        "description": "是否禁用"
      },
      "loading": {
        "type": "boolean",
        "default": false,
        "description": "是否加载中"
      }
    },
    "required": ["text"]
  },
  "template": {
    "component_type": "button",
    "props": {
      "className": "btn btn-{{variant}} btn-{{size}}{{#if disabled}} btn-disabled{{/if}}{{#if loading}} btn-loading{{/if}}",
      "disabled": "{{disabled}}",
      "onClick": "{{onClick}}"
    },
    "children": [
      {
        "condition": "{{icon}}",
        "component_type": "icon",
        "props": {
          "name": "{{icon}}",
          "className": "btn-icon"
        }
      },
      {
        "component_type": "text",
        "props": {
          "content": "{{text}}"
        }
      },
      {
        "condition": "{{loading}}",
        "component_type": "spinner",
        "props": {
          "size": "small",
          "className": "btn-spinner"
        }
      }
    ]
  },
  "styles": {
    "base": {
      ".btn": {
        "display": "inline-flex",
        "align-items": "center",
        "justify-content": "center",
        "padding": "var(--btn-padding)",
        "border": "var(--btn-border)",
        "border-radius": "var(--btn-border-radius)",
        "font-family": "var(--btn-font-family)",
        "font-size": "var(--btn-font-size)",
        "font-weight": "var(--btn-font-weight)",
        "line-height": "var(--btn-line-height)",
        "text-decoration": "none",
        "cursor": "pointer",
        "transition": "all 0.2s ease-in-out"
      }
    },
    "variants": {
      "primary": {
        ".btn-primary": {
          "background-color": "var(--color-primary)",
          "color": "var(--color-primary-text)",
          "border-color": "var(--color-primary)"
        }
      },
      "secondary": {
        ".btn-secondary": {
          "background-color": "var(--color-secondary)",
          "color": "var(--color-secondary-text)",
          "border-color": "var(--color-secondary)"
        }
      }
    },
    "sizes": {
      "small": {
        ".btn-small": {
          "--btn-padding": "0.25rem 0.5rem",
          "--btn-font-size": "0.875rem"
        }
      },
      "medium": {
        ".btn-medium": {
          "--btn-padding": "0.5rem 1rem",
          "--btn-font-size": "1rem"
        }
      },
      "large": {
        ".btn-large": {
          "--btn-padding": "0.75rem 1.5rem",
          "--btn-font-size": "1.125rem"
        }
      }
    },
    "states": {
      "disabled": {
        ".btn-disabled": {
          "opacity": "0.6",
          "cursor": "not-allowed",
          "pointer-events": "none"
        }
      },
      "loading": {
        ".btn-loading": {
          "position": "relative",
          "color": "transparent"
        }
      }
    }
  },
  "events": {
    "onClick": {
      "description": "按钮点击事件",
      "parameters": {
        "event": "MouseEvent"
      }
    },
    "onFocus": {
      "description": "按钮获得焦点事件",
      "parameters": {
        "event": "FocusEvent"
      }
    },
    "onBlur": {
      "description": "按钮失去焦点事件",
      "parameters": {
        "event": "FocusEvent"
      }
    }
  },
  "examples": [
    {
      "name": "基础按钮",
      "config": {
        "text": "点击我",
        "variant": "primary"
      }
    },
    {
      "name": "带图标按钮",
      "config": {
        "text": "保存",
        "variant": "success",
        "icon": "save"
      }
    },
    {
      "name": "加载状态按钮",
      "config": {
        "text": "提交中...",
        "variant": "primary",
        "loading": true
      }
    }
  ],
  "dependencies": {
    "components": ["icon", "text", "spinner"],
    "themes": ["base", "button"],
    "assets": []
  }
}
```

### **页面模板结构**
```json
{
  "meta": {
    "name": "dashboard",
    "version": "1.0.0",
    "description": "仪表板页面模板",
    "category": "page",
    "tags": ["dashboard", "admin", "analytics"]
  },
  "schema": {
    "type": "object",
    "properties": {
      "title": {
        "type": "string",
        "description": "页面标题"
      },
      "widgets": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "type": {"type": "string"},
            "title": {"type": "string"},
            "data": {"type": "object"},
            "position": {
              "type": "object",
              "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "w": {"type": "integer"},
                "h": {"type": "integer"}
              }
            }
          }
        }
      }
    }
  },
  "template": {
    "component_type": "page",
    "props": {
      "className": "dashboard-page"
    },
    "children": [
      {
        "component_type": "header",
        "props": {
          "className": "dashboard-header"
        },
        "children": [
          {
            "component_type": "title",
            "props": {
              "level": 1,
              "content": "{{title}}"
            }
          }
        ]
      },
      {
        "component_type": "main",
        "props": {
          "className": "dashboard-main"
        },
        "children": [
          {
            "component_type": "grid",
            "props": {
              "className": "dashboard-grid",
              "columns": 12,
              "gap": "1rem"
            },
            "children": "{{#each widgets}}{{> widget this}}{{/each}}"
          }
        ]
      }
    ]
  },
  "partials": {
    "widget": {
      "component_type": "widget",
      "props": {
        "className": "dashboard-widget",
        "gridPosition": {
          "x": "{{position.x}}",
          "y": "{{position.y}}",
          "w": "{{position.w}}",
          "h": "{{position.h}}"
        }
      },
      "children": [
        {
          "component_type": "widget-header",
          "children": [
            {
              "component_type": "title",
              "props": {
                "level": 3,
                "content": "{{title}}"
              }
            }
          ]
        },
        {
          "component_type": "widget-content",
          "children": "{{> widget-content type data}}"
        }
      ]
    }
  }
}
```

## 🎨 **主题系统设计**

### **主题定义结构**
```json
{
  "meta": {
    "name": "claudeditor-dark",
    "version": "1.0.0",
    "description": "ClaudEditor深色主题",
    "category": "official",
    "extends": "base"
  },
  "variables": {
    "colors": {
      "primary": "#3498db",
      "secondary": "#2c3e50",
      "success": "#27ae60",
      "warning": "#f39c12",
      "danger": "#e74c3c",
      "background": "#1e1e1e",
      "surface": "#2d2d2d",
      "text": "#ffffff",
      "text-secondary": "#b0b0b0",
      "border": "#444444"
    },
    "typography": {
      "font-family": "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      "font-size-base": "16px",
      "line-height-base": "1.5",
      "font-weight-normal": "400",
      "font-weight-medium": "500",
      "font-weight-bold": "700"
    },
    "spacing": {
      "xs": "4px",
      "sm": "8px",
      "md": "16px",
      "lg": "24px",
      "xl": "32px",
      "xxl": "48px"
    },
    "borders": {
      "radius-sm": "4px",
      "radius-md": "8px",
      "radius-lg": "12px",
      "width-thin": "1px",
      "width-medium": "2px",
      "width-thick": "4px"
    },
    "shadows": {
      "sm": "0 1px 3px rgba(0, 0, 0, 0.12)",
      "md": "0 4px 6px rgba(0, 0, 0, 0.16)",
      "lg": "0 10px 25px rgba(0, 0, 0, 0.20)"
    },
    "animations": {
      "duration-fast": "0.15s",
      "duration-normal": "0.3s",
      "duration-slow": "0.5s",
      "easing-ease": "ease",
      "easing-ease-in": "ease-in",
      "easing-ease-out": "ease-out",
      "easing-ease-in-out": "ease-in-out"
    }
  },
  "component_overrides": {
    "button": {
      "variants": {
        "primary": {
          "background-color": "var(--color-primary)",
          "color": "var(--color-text)",
          "border-color": "var(--color-primary)"
        }
      }
    },
    "input": {
      "base": {
        "background-color": "var(--color-surface)",
        "border-color": "var(--color-border)",
        "color": "var(--color-text)"
      }
    }
  }
}
```

## 🔧 **命令行工具设计**

### **CLI命令结构**
```bash
# 组件生成
claudeditor ui generate component <template> [options]
claudeditor ui generate layout <template> [options]
claudeditor ui generate page <template> [options]

# 模板管理
claudeditor ui template list [category]
claudeditor ui template create <name> [options]
claudeditor ui template validate <path>
claudeditor ui template install <source>

# 主题管理
claudeditor ui theme list
claudeditor ui theme apply <theme>
claudeditor ui theme create <name> [options]
claudeditor ui theme export <theme> <path>

# 项目管理
claudeditor ui init [options]
claudeditor ui build [options]
claudeditor ui preview [options]
claudeditor ui deploy [options]
```

### **配置文件**
```json
{
  "ui_config": {
    "version": "1.0.0",
    "default_theme": "claudeditor-dark",
    "output_directory": "ui/components/generated",
    "template_directories": [
      "ui/templates",
      "~/.claudeditor/templates"
    ],
    "theme_directories": [
      "ui/themes",
      "~/.claudeditor/themes"
    ],
    "build": {
      "minify": true,
      "source_maps": true,
      "target": "es2020"
    },
    "preview": {
      "port": 3000,
      "hot_reload": true,
      "open_browser": true
    }
  }
}
```

## 🚀 **集成流程**

### **1. 初始化项目**
```bash
# 初始化UI生成平台
claudeditor ui init --template basic

# 安装默认模板
claudeditor ui template install official

# 设置默认主题
claudeditor ui theme apply claudeditor-dark
```

### **2. 生成组件**
```bash
# 生成按钮组件
claudeditor ui generate component button \
  --name primary-button \
  --config '{"variant": "primary", "size": "large"}' \
  --output ui/components/basic/

# 生成表单页面
claudeditor ui generate page form \
  --name user-form \
  --config form-config.json \
  --theme claudeditor-light
```

### **3. 预览和构建**
```bash
# 启动预览服务器
claudeditor ui preview --port 3000

# 构建生产版本
claudeditor ui build --minify --output dist/
```

## 📊 **性能优化**

### **1. 模板缓存**
- 模板解析结果缓存
- 组件生成结果缓存
- 主题计算结果缓存

### **2. 增量生成**
- 只重新生成变更的组件
- 依赖关系追踪
- 智能缓存失效

### **3. 并行处理**
- 多组件并行生成
- 异步模板解析
- 并发主题应用

这个架构设计为ClaudEditor 4.1提供了完整的UI生成平台基础，支持模板驱动的AG-UI组件动态生成。

