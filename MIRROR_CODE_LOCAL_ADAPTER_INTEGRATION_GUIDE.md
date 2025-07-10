# Mirror Code与Local Adapter集成使用指南

## 📋 概述

Mirror Code与Local Adapter的集成实现了通过Local Adapter MCP在Mac本地执行claude命令，并将执行结果实时同步到ClaudEditor的功能。这个集成避免了重复实现命令执行功能，充分利用了Local Adapter MCP的平台适配能力。

## 🏗️ 架构设计

### 核心组件

```
ClaudEditor (前端界面)
     ↓ WebSocket同步
Mirror Code (命令执行和同步层)
     ↓ 集成调用
Local Adapter MCP (平台适配层)
     ↓ 系统调用
Mac终端/WSL (系统执行层)
```

### 主要组件说明

1. **LocalAdapterIntegration** - 核心集成器
   - 通过Local Adapter MCP执行命令
   - 管理命令会话和状态
   - 提供全局回调机制

2. **ResultCapture** - 结果捕获器
   - 实时捕获命令输出
   - 支持多种格式化输出（HTML、Markdown、纯文本）
   - 提供流式输出支持

3. **ClaudeIntegration** - Claude集成管理器
   - 统一管理命令执行和结果同步
   - 提供WebSocket同步到ClaudEditor
   - 管理活跃集成会话

4. **MirrorEngine** - Mirror引擎
   - 集成所有组件的主控制器
   - 提供统一的API接口
   - 管理整个Mirror Code生命周期

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- Mac系统（支持macOS终端）
- Local Adapter MCP组件
- ClaudEditor（可选，用于结果同步）

### 2. 基本使用

#### 通过Mirror Engine执行Claude命令

```python
import asyncio
from core.mirror_code.engine.mirror_engine import MirrorEngine

async def main():
    # 创建Mirror引擎
    config = {
        "local_path": "/Users/alexchuang/Desktop/alex/tests/package",
        "claude_integration": {
            "sync_enabled": True,  # 启用ClaudEditor同步
            "local_adapter_integration": {
                "default_working_dir": "/Users/alexchuang/Desktop/alex/tests/package"
            }
        }
    }
    
    engine = MirrorEngine(config)
    
    try:
        # 启动引擎
        start_result = await engine.start()
        if not start_result.get("success"):
            print(f"启动失败: {start_result.get('error')}")
            return
        
        # 执行Claude命令
        result = await engine.execute_claude_command(
            model="claude-sonnet-4-20250514",
            working_dir="/Users/alexchuang/Desktop/alex/tests/package"
        )
        
        if result.get("success"):
            print(f"命令执行成功，集成ID: {result.get('integration_id')}")
            
            # 获取集成状态
            status = await engine.get_claude_integration_status()
            print(f"集成状态: {status}")
        else:
            print(f"命令执行失败: {result.get('error')}")
    
    finally:
        # 停止引擎
        await engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 直接使用LocalAdapterIntegration

```python
import asyncio
from core.mirror_code.command_execution.local_adapter_integration import LocalAdapterIntegration

async def main():
    # 创建集成器
    integration = LocalAdapterIntegration({
        "default_working_dir": "/Users/alexchuang/Desktop/alex/tests/package"
    })
    
    if not integration.available:
        print("Local Adapter不可用")
        return
    
    # 执行Claude命令
    result = await integration.execute_claude_command(
        model="claude-sonnet-4-20250514",
        working_dir="/Users/alexchuang/Desktop/alex/tests/package"
    )
    
    if result.get("success"):
        print(f"命令执行成功，会话ID: {result.get('session_id')}")
        print(f"输出: {result.get('stdout')}")
    else:
        print(f"命令执行失败: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### 使用ClaudeIntegration进行完整集成

```python
import asyncio
from core.mirror_code.command_execution.claude_integration import ClaudeIntegration

async def main():
    # 创建Claude集成
    config = {
        "sync_enabled": True,
        "claudeditor_websocket": "ws://localhost:8081/socket.io/",
        "local_adapter_integration": {
            "default_working_dir": "/Users/alexchuang/Desktop/alex/tests/package"
        }
    }
    
    integration = ClaudeIntegration(config)
    
    try:
        # 启动集成服务
        start_result = await integration.start()
        print(f"启动结果: {start_result}")
        
        # 执行Claude命令并同步
        result = await integration.execute_claude_with_sync(
            model="claude-sonnet-4-20250514",
            working_dir="/Users/alexchuang/Desktop/alex/tests/package"
        )
        
        if result.get("success"):
            integration_id = result.get("integration_id")
            print(f"集成ID: {integration_id}")
            
            # 获取实时输出
            async for output_chunk in integration.get_live_output(integration_id, "html"):
                if output_chunk.get("success"):
                    print(f"实时输出: {output_chunk.get('output_chunk')}")
                else:
                    break
    
    finally:
        # 停止集成服务
        await integration.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## ⚙️ 配置说明

### Mirror Engine配置

```python
config = {
    "local_path": "/path/to/local/directory",  # 本地工作目录
    "remote_endpoint": "ws://localhost:8080",  # 远程端点（可选）
    "claude_integration": {
        "sync_enabled": True,  # 是否启用ClaudEditor同步
        "claudeditor_websocket": "ws://localhost:8081/socket.io/",  # ClaudEditor WebSocket地址
        "local_adapter_integration": {
            "default_working_dir": "/path/to/working/dir",  # 默认工作目录
            "command_timeout": 300  # 命令超时时间（秒）
        },
        "result_capture": {
            "max_buffer_size": 10000,  # 最大缓冲区大小
            "auto_format": True  # 自动格式化输出
        }
    },
    "sync": {
        "auto_sync": True,  # 自动同步
        "sync_interval": 5  # 同步间隔（秒）
    },
    "communication": {
        "websocket_port": 8080,  # WebSocket端口
        "max_connections": 10  # 最大连接数
    },
    "git": {
        "auto_commit": False,  # 自动提交
        "commit_message_template": "Mirror sync: {files_count} files"
    },
    "file_monitor": {
        "ignore_patterns": [".git/*", "node_modules/*", "*.tmp"],  # 忽略模式
        "debounce_delay": 0.5  # 防抖延迟
    },
    "logging": {
        "level": "INFO"  # 日志级别
    }
}
```

### LocalAdapterIntegration配置

```python
config = {
    "default_working_dir": "/path/to/working/dir",  # 默认工作目录
    "command_timeout": 300,  # 命令超时时间（秒）
    "logging": {
        "level": "INFO"  # 日志级别
    }
}
```

### ClaudeIntegration配置

```python
config = {
    "sync_enabled": True,  # 是否启用同步
    "claudeditor_websocket": "ws://localhost:8081/socket.io/",  # ClaudEditor WebSocket地址
    "local_adapter_integration": {
        # LocalAdapterIntegration配置
    },
    "result_capture": {
        "max_buffer_size": 10000,  # 最大缓冲区大小
        "auto_format": True,  # 自动格式化
        "format_types": ["html", "markdown", "raw"]  # 支持的格式类型
    },
    "logging": {
        "level": "INFO"  # 日志级别
    }
}
```

## 🔧 API参考

### MirrorEngine

#### `execute_claude_command(model, working_dir, additional_args)`
执行Claude命令并同步到ClaudEditor

**参数:**
- `model` (str): Claude模型名称，默认"claude-sonnet-4-20250514"
- `working_dir` (str, 可选): 工作目录
- `additional_args` (List[str], 可选): 额外参数

**返回:**
- `Dict[str, Any]`: 执行结果

#### `get_claude_integration_status()`
获取Claude集成状态

**返回:**
- `Dict[str, Any]`: 集成状态信息

### LocalAdapterIntegration

#### `execute_claude_command(model, working_dir, additional_args)`
通过Local Adapter执行Claude命令

#### `execute_command(command, args, working_dir, env)`
执行任意命令

#### `get_session_status(session_id)`
获取会话状态

#### `list_sessions()`
列出所有会话

#### `add_output_callback(callback)`
添加全局输出回调

#### `add_status_callback(callback)`
添加全局状态回调

### ClaudeIntegration

#### `execute_claude_with_sync(model, working_dir, additional_args)`
执行Claude命令并同步到ClaudEditor

#### `get_integration_status(integration_id)`
获取集成状态

#### `get_live_output(integration_id, format_type)`
获取实时输出流

#### `terminate_integration(integration_id)`
终止集成

#### `cleanup_integration(integration_id)`
清理集成数据

## 🔍 故障排除

### 常见问题

#### 1. Local Adapter MCP不可用

**症状:** 日志显示"Local Adapter MCP不可用"

**解决方案:**
1. 检查Local Adapter MCP组件是否正确安装
2. 确认导入路径是否正确
3. 检查依赖组件是否完整

```bash
# 检查Local Adapter组件
python -c "from core.components.local_adapter_mcp.local_adapter_engine import LocalAdapterEngine; print('OK')"
```

#### 2. 工作目录不存在

**症状:** 错误信息"本地路径不存在"

**解决方案:**
1. 确认指定的工作目录存在
2. 检查路径权限
3. 使用绝对路径

```python
import os
working_dir = "/path/to/your/directory"
if not os.path.exists(working_dir):
    os.makedirs(working_dir)
```

#### 3. ClaudEditor连接失败

**症状:** 无法连接到ClaudEditor WebSocket

**解决方案:**
1. 确认ClaudEditor正在运行
2. 检查WebSocket地址和端口
3. 确认防火墙设置

```python
# 测试WebSocket连接
import websockets
import asyncio

async def test_connection():
    try:
        async with websockets.connect("ws://localhost:8081/socket.io/") as websocket:
            print("连接成功")
    except Exception as e:
        print(f"连接失败: {e}")

asyncio.run(test_connection())
```

#### 4. 命令执行超时

**症状:** 命令执行时间过长导致超时

**解决方案:**
1. 增加命令超时时间
2. 检查命令是否需要交互输入
3. 优化命令参数

```python
config = {
    "local_adapter_integration": {
        "command_timeout": 600  # 增加到10分钟
    }
}
```

### 调试技巧

#### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 检查组件状态

```python
# 检查平台信息
integration = LocalAdapterIntegration()
platform_info = integration.get_platform_info()
print(f"平台信息: {platform_info}")

# 检查会话列表
sessions = await integration.list_sessions()
print(f"活跃会话: {sessions}")
```

#### 3. 测试基本功能

```python
# 测试简单命令
result = await integration.execute_command("echo", ["Hello World"])
print(f"测试结果: {result}")
```

## 📦 部署指南

### 1. 开发环境部署

```bash
# 1. 克隆项目
git clone <repository_url>
cd aicore0707

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行测试
python MIRROR_CODE_LOCAL_ADAPTER_INTEGRATION_TEST.py

# 4. 启动Mirror Code
python core/mirror_code/launch_mirror.py /path/to/working/directory
```

### 2. 生产环境部署

```bash
# 1. 配置环境变量
export MIRROR_CODE_CONFIG="/path/to/config.json"
export CLAUDE_MODEL="claude-sonnet-4-20250514"
export WORKING_DIR="/path/to/working/directory"

# 2. 创建配置文件
cat > /path/to/config.json << EOF
{
    "local_path": "${WORKING_DIR}",
    "claude_integration": {
        "sync_enabled": true,
        "local_adapter_integration": {
            "default_working_dir": "${WORKING_DIR}",
            "command_timeout": 300
        }
    },
    "logging": {
        "level": "INFO"
    }
}
EOF

# 3. 启动服务
python -m core.mirror_code.engine.mirror_engine
```

### 3. Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt

EXPOSE 8080 8081

CMD ["python", "-m", "core.mirror_code.engine.mirror_engine"]
```

```bash
# 构建镜像
docker build -t mirror-code-local-adapter .

# 运行容器
docker run -d \
  -p 8080:8080 \
  -p 8081:8081 \
  -v /path/to/working/dir:/app/workspace \
  -e WORKING_DIR=/app/workspace \
  mirror-code-local-adapter
```

## 🔄 集成示例

### 与ClaudEditor集成

```javascript
// ClaudEditor前端代码示例
const socket = new WebSocket('ws://localhost:8081/socket.io/');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'command_start':
            console.log('命令开始:', data.command);
            break;
        case 'command_output':
            console.log('命令输出:', data.output);
            // 更新编辑器内容
            updateEditor(data.output);
            break;
        case 'command_complete':
            console.log('命令完成:', data.status);
            break;
    }
};

function updateEditor(output) {
    // 更新ClaudEditor界面
    const editor = document.getElementById('claude-editor');
    editor.innerHTML += output;
}
```

### 与其他系统集成

```python
# 与PowerAutomation集成示例
from core.mirror_code.command_execution.claude_integration import ClaudeIntegration

class PowerAutomationMirrorIntegration:
    def __init__(self):
        self.claude_integration = ClaudeIntegration({
            "sync_enabled": False  # 禁用ClaudEditor同步
        })
    
    async def execute_automation_task(self, task_config):
        """执行自动化任务"""
        await self.claude_integration.start()
        
        try:
            result = await self.claude_integration.execute_claude_with_sync(
                model=task_config.get("model", "claude-sonnet-4-20250514"),
                working_dir=task_config.get("working_dir"),
                additional_args=task_config.get("args", [])
            )
            
            return result
        finally:
            await self.claude_integration.stop()
```

## 📈 性能优化

### 1. 命令执行优化

- 使用异步执行避免阻塞
- 设置合理的超时时间
- 实现命令缓存机制

### 2. 内存管理

- 定期清理完成的会话
- 限制输出缓冲区大小
- 使用流式处理大量输出

### 3. 网络优化

- 使用WebSocket连接池
- 实现断线重连机制
- 压缩传输数据

## 🔒 安全考虑

### 1. 命令执行安全

- 验证命令参数
- 限制可执行的命令
- 使用沙箱环境

### 2. 网络安全

- 使用WSS加密连接
- 实现身份验证
- 限制访问来源

### 3. 数据安全

- 加密敏感数据
- 定期清理临时文件
- 审计命令执行日志

## 📚 更多资源

- [Local Adapter MCP文档](./core/components/local_adapter_mcp/README.md)
- [Mirror Code架构文档](./core/mirror_code/README.md)
- [ClaudEditor集成指南](./claudeditor/README.md)
- [PowerAutomation集成文档](./deployment/README.md)

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证，详见LICENSE文件。

