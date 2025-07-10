# Stagewise测试框架输入输出结构分析

## 📊 **框架概览**

Stagewise测试框架是一个多层次的测试系统，包含以下核心组件：
- **StagewiseService** - 核心服务层
- **TestRunner** - 测试运行器
- **EnhancedTestingFramework** - 增强测试框架
- **RecordAsTestOrchestrator** - 录制即测试编排器
- **ActionRecognitionEngine** - 动作识别引擎
- **TestNodeGenerator** - 测试节点生成器
- **AGUIAutoGenerator** - AG-UI组件生成器
- **PlaybackVerificationEngine** - 回放验证引擎

## 🔄 **输入输出数据流分析**

### **1. StagewiseService (核心服务层)**

#### **输入 (Input)**
```python
# 会话创建输入
{
    "user_id": "string",
    "project_id": "string", 
    "browser_context": {
        "url": "string",
        "viewport": {"width": int, "height": int},
        "user_agent": "string"
    }
}

# 元素选择输入
{
    "element_id": "string",
    "selector": "string",
    "tag_name": "string",
    "attributes": {"key": "value"},
    "text_content": "string",
    "position": {"x": int, "y": int}
}
```

#### **输出 (Output)**
```python
# 会话信息输出
StagewiseSession {
    "session_id": "string",
    "user_id": "string",
    "project_id": "string",
    "browser_context": dict,
    "created_at": datetime,
    "last_activity": datetime,
    "status": "active|inactive|completed",
    "generated_code": [GeneratedCode]
}

# 生成代码输出
GeneratedCode {
    "code_id": "string",
    "session_id": "string",
    "element_selection": ElementSelection,
    "code_type": "click|input|extract|wait",
    "generated_code": "string",
    "language": "python|javascript",
    "framework": "selenium|playwright",
    "confidence": float,
    "created_at": datetime
}
```

### **2. TestRunner (测试运行器)**

#### **输入 (Input)**
```bash
# 命令行输入
python test_runner.py [command] [options]

# 命令类型
- p0                    # P0核心功能测试
- mcp                   # MCP组件测试
- ui                    # UI功能测试
- performance           # 性能测试
- all                   # 全部测试
- suite [suite_name]    # 指定测试套件
- case [case_name]      # 指定测试用例

# 选项参数
--output FILE           # 输出报告文件
--config FILE           # 配置文件
--parallel              # 并行执行
--timeout SECONDS       # 超时时间
--retry COUNT           # 重试次数
```

#### **输出 (Output)**
```python
# 测试会话输出
TestSession {
    "session_id": "string",
    "start_time": datetime,
    "end_time": datetime,
    "total_tests": int,
    "passed_tests": int,
    "failed_tests": int,
    "skipped_tests": int,
    "error_tests": int,
    "test_results": [TestResult],
    "system_metrics": {
        "memory_usage": float,
        "cpu_usage": float,
        "execution_time": float
    },
    "environment": {
        "python_version": "string",
        "os": "string",
        "hostname": "string"
    }
}

# 测试结果输出
TestResult {
    "test_id": "string",
    "test_name": "string",
    "status": "passed|failed|skipped|error",
    "start_time": datetime,
    "end_time": datetime,
    "duration": float,
    "error_message": "string",
    "stack_trace": "string",
    "output": "string",
    "metrics": {
        "memory_delta": float,
        "response_time": float,
        "assertions_count": int
    },
    "artifacts": ["screenshot.png", "log.txt"]
}
```

### **3. RecordAsTestOrchestrator (录制即测试编排器)**

#### **输入 (Input)**
```python
# 录制配置输入
RecordAsTestConfig {
    # 录制配置
    "auto_start_recording": bool,
    "recording_timeout": float,
    "min_actions_required": int,
    
    # 生成配置
    "generate_react_components": bool,
    "generate_vue_components": bool,
    "generate_html_components": bool,
    "component_prefix": "string",
    
    # 验证配置
    "auto_playback_verification": bool,
    "continue_on_verification_failure": bool,
    "verification_timeout": float,
    
    # 输出配置
    "output_directory": "string",
    "export_components": bool,
    "export_test_suite": bool,
    "export_playback_report": bool
}

# 会话启动输入
{
    "name": "string",
    "description": "string",
    "config": RecordAsTestConfig
}
```

#### **输出 (Output)**
```python
# 录制会话输出
RecordAsTestSession {
    "session_id": "string",
    "name": "string",
    "description": "string",
    "config": RecordAsTestConfig,
    
    # 状态信息
    "status": "idle|recording|processing|generating|testing|completed|failed",
    "current_phase": "setup|recording|analysis|generation|verification|export|cleanup",
    "start_time": datetime,
    "end_time": datetime,
    
    # 数据存储
    "recorded_actions": [UserAction],
    "generated_test_flow": TestFlow,
    "generated_components": AGUITestSuite,
    "playback_session": PlaybackSession,
    
    # 输出文件
    "output_directory": "string",
    "component_files": ["Component1.jsx", "Component2.vue"],
    "test_files": ["test1.spec.js", "test2.test.py"],
    "report_files": ["report.html", "summary.json"],
    
    # 统计信息
    "total_actions": int,
    "total_nodes": int,
    "total_components": int,
    "success_rate": float,
    
    # 元数据和错误
    "metadata": dict,
    "errors": ["error1", "error2"]
}
```

### **4. ActionRecognitionEngine (动作识别引擎)**

#### **输入 (Input)**
```python
# 监控配置输入
{
    "monitor_mouse": bool,
    "monitor_keyboard": bool,
    "monitor_screen": bool,
    "capture_screenshots": bool,
    "screenshot_interval": float,
    "action_buffer_size": int
}

# 实时动作数据 (系统自动捕获)
- 鼠标事件: 点击、移动、滚轮
- 键盘事件: 按键、组合键
- 屏幕变化: 截图、区域变化
```

#### **输出 (Output)**
```python
# 用户动作输出
UserAction {
    "action_id": "string",
    "action_type": "click|input|scroll|hover|drag|key_press|wait|navigate|screenshot",
    "timestamp": float,
    "coordinates": {"x": int, "y": int},
    "element_info": {
        "tag": "string",
        "id": "string",
        "class": "string",
        "text": "string"
    },
    "input_data": "string",
    "screenshot_path": "string",
    "confidence": float,
    "metadata": dict
}

# 动作历史输出
{
    "total_actions": int,
    "actions_by_type": {"click": int, "input": int, ...},
    "session_duration": float,
    "action_sequence": [UserAction]
}
```

### **5. TestNodeGenerator (测试节点生成器)**

#### **输入 (Input)**
```python
# 动作序列输入
[UserAction] - 来自ActionRecognitionEngine的动作列表

# 生成配置输入
{
    "auto_generate_assertions": bool,
    "insert_wait_nodes": bool,
    "optimize_node_sequence": bool,
    "generate_dependencies": bool,
    "node_timeout": float
}
```

#### **输出 (Output)**
```python
# 测试流程输出
TestFlow {
    "flow_id": "string",
    "name": "string",
    "description": "string",
    "nodes": [TestNode],
    "dependencies": {"node_id": ["dependency_ids"]},
    "metadata": {
        "total_nodes": int,
        "estimated_duration": float,
        "complexity_score": float
    }
}

# 测试节点输出
TestNode {
    "node_id": "string",
    "node_type": "action|assertion|wait|setup|cleanup",
    "action_type": "click|input|scroll|verify|wait",
    "target_element": {
        "selector": "string",
        "xpath": "string",
        "coordinates": {"x": int, "y": int}
    },
    "input_data": "string",
    "expected_result": "string",
    "timeout": float,
    "retry_count": int,
    "dependencies": ["node_id1", "node_id2"],
    "metadata": dict
}
```

### **6. AGUIAutoGenerator (AG-UI组件生成器)**

#### **输入 (Input)**
```python
# 测试流程输入
TestFlow - 来自TestNodeGenerator的测试流程

# 生成配置输入
{
    "generate_react": bool,
    "generate_vue": bool,
    "generate_html": bool,
    "component_prefix": "string",
    "include_tests": bool,
    "include_stories": bool,
    "output_directory": "string"
}
```

#### **输出 (Output)**
```python
# AG-UI测试套件输出
AGUITestSuite {
    "suite_id": "string",
    "name": "string",
    "components": [AGUIComponent],
    "test_files": [TestFile],
    "integration_code": "string",
    "metadata": {
        "total_components": int,
        "frameworks": ["react", "vue"],
        "generated_at": datetime
    }
}

# AG-UI组件输出
AGUIComponent {
    "component_id": "string",
    "name": "string",
    "framework": "react|vue|html",
    "component_code": "string",
    "test_code": "string",
    "story_code": "string",
    "props": [ComponentProp],
    "events": [ComponentEvent],
    "styles": "string",
    "dependencies": ["dependency1", "dependency2"]
}
```

### **7. PlaybackVerificationEngine (回放验证引擎)**

#### **输入 (Input)**
```python
# 测试流程输入
TestFlow - 要验证的测试流程

# 验证配置输入
{
    "continue_on_failure": bool,
    "verification_timeout": float,
    "capture_screenshots": bool,
    "generate_report": bool,
    "parallel_execution": bool
}
```

#### **输出 (Output)**
```python
# 回放会话输出
PlaybackSession {
    "session_id": "string",
    "test_flow": TestFlow,
    "start_time": datetime,
    "end_time": datetime,
    "status": "running|completed|failed|cancelled",
    "execution_results": [NodeExecutionResult],
    "performance_metrics": {
        "total_duration": float,
        "average_node_time": float,
        "success_rate": float
    },
    "screenshots": ["step1.png", "step2.png"],
    "error_log": ["error1", "error2"]
}

# 节点执行结果输出
NodeExecutionResult {
    "node_id": "string",
    "status": "passed|failed|skipped",
    "start_time": datetime,
    "end_time": datetime,
    "duration": float,
    "actual_result": "string",
    "expected_result": "string",
    "error_message": "string",
    "screenshot_path": "string",
    "verification_details": dict
}
```

## 🔗 **数据流关系图**

```
用户操作 → ActionRecognitionEngine → UserAction[]
    ↓
TestNodeGenerator → TestFlow
    ↓
AGUIAutoGenerator → AGUITestSuite
    ↓
PlaybackVerificationEngine → PlaybackSession
    ↓
TestRunner → TestSession → 测试报告
```

## 📋 **接口总结**

### **主要输入类型**
1. **配置对象** - 各种Config类，控制框架行为
2. **用户动作** - 实时捕获的用户操作数据
3. **命令行参数** - 测试运行的控制参数
4. **测试数据** - 测试用例和测试套件定义

### **主要输出类型**
1. **会话对象** - 各种Session类，记录执行状态
2. **结果对象** - 各种Result类，记录执行结果
3. **生成文件** - 组件代码、测试代码、报告文件
4. **统计数据** - 性能指标、成功率、错误信息

### **数据格式标准**
- **时间格式**: ISO 8601 datetime对象
- **ID格式**: UUID字符串
- **文件路径**: 绝对路径字符串
- **配置格式**: 嵌套字典结构
- **状态枚举**: 预定义的Enum值

这个输入输出结构设计确保了Stagewise测试框架的各个组件之间能够无缝协作，同时提供了清晰的接口定义和数据流转机制。

