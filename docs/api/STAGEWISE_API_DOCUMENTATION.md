# Stagewise测试框架API文档和使用示例

## 📚 **API概览**

Stagewise测试框架提供了完整的测试自动化解决方案，包括录制、生成、验证和报告功能。本文档详细说明了所有API接口和使用方法。

## 🚀 **快速开始**

### **安装和初始化**
```python
from core.components.stagewise_mcp import (
    StagewiseService,
    EnhancedStagewiseTestingFramework,
    RecordAsTestOrchestrator,
    ActionRecognitionEngine,
    TestNodeGenerator,
    AGUIAutoGenerator,
    PlaybackVerificationEngine
)

# 初始化核心服务
stagewise = StagewiseService()
framework = EnhancedStagewiseTestingFramework()
orchestrator = RecordAsTestOrchestrator()
```

### **基本使用流程**
```python
# 1. 开始录制会话
session_id = await orchestrator.start_record_as_test_session(
    name="登录测试",
    description="测试用户登录流程"
)

# 2. 用户进行操作 (系统自动录制)
# ... 用户在浏览器中操作 ...

# 3. 完成录制并生成测试
session = await orchestrator.execute_complete_workflow()

# 4. 查看生成的文件
print(f"生成的组件: {session.component_files}")
print(f"测试文件: {session.test_files}")
print(f"报告文件: {session.report_files}")
```

## 🔧 **核心API接口**

### **1. StagewiseService API**

#### **创建编程会话**
```python
async def create_session(
    user_id: str,
    project_id: str,
    browser_context: Dict[str, Any]
) -> StagewiseSession
```

**参数:**
- `user_id`: 用户ID
- `project_id`: 项目ID  
- `browser_context`: 浏览器上下文信息

**返回:** StagewiseSession对象

**示例:**
```python
session = await stagewise.create_session(
    user_id="user123",
    project_id="project456",
    browser_context={
        "url": "https://example.com",
        "viewport": {"width": 1920, "height": 1080},
        "user_agent": "Mozilla/5.0..."
    }
)
```

#### **选择页面元素**
```python
async def select_element(
    session_id: str,
    element_info: Dict[str, Any]
) -> ElementSelection
```

**参数:**
- `session_id`: 会话ID
- `element_info`: 元素信息

**示例:**
```python
element = await stagewise.select_element(
    session_id=session.session_id,
    element_info={
        "selector": "#login-button",
        "tag_name": "button",
        "text_content": "登录",
        "position": {"x": 100, "y": 200}
    }
)
```

#### **生成代码**
```python
async def generate_code(
    session_id: str,
    element_selection: ElementSelection,
    action_type: str
) -> GeneratedCode
```

**参数:**
- `session_id`: 会话ID
- `element_selection`: 选中的元素
- `action_type`: 动作类型 ("click", "input", "extract", "wait")

**示例:**
```python
code = await stagewise.generate_code(
    session_id=session.session_id,
    element_selection=element,
    action_type="click"
)
print(code.generated_code)  # 输出生成的Python/JavaScript代码
```

### **2. TestRunner API**

#### **运行P0测试**
```python
async def run_p0_tests(config: Dict[str, Any] = None) -> TestSession
```

**示例:**
```python
from core.components.stagewise_mcp.test_runner import StagewiseTestRunner

runner = StagewiseTestRunner()
session = await runner.run_p0_tests({
    "timeout": 60,
    "parallel": False,
    "output": "p0_test_report.json"
})

print(f"测试结果: {session.passed_tests}/{session.total_tests} 通过")
```

#### **运行自定义测试套件**
```python
async def run_test_suite(suite_name: str) -> List[TestResult]
```

**示例:**
```python
results = await framework.run_test_suite("ui_functionality_tests")
for result in results:
    print(f"{result.test_name}: {result.status}")
```

### **3. RecordAsTestOrchestrator API**

#### **配置录制即测试**
```python
config = RecordAsTestConfig(
    # 录制配置
    auto_start_recording=True,
    recording_timeout=300.0,
    min_actions_required=3,
    
    # 生成配置
    generate_react_components=True,
    generate_vue_components=False,
    generate_html_components=True,
    component_prefix="Test",
    
    # 验证配置
    auto_playback_verification=True,
    continue_on_verification_failure=True,
    verification_timeout=60.0,
    
    # 输出配置
    output_directory="my_test_output",
    export_components=True,
    export_test_suite=True,
    export_playback_report=True
)

orchestrator = RecordAsTestOrchestrator(config)
```

#### **开始录制会话**
```python
async def start_record_as_test_session(
    name: str,
    description: str = "",
    config: RecordAsTestConfig = None
) -> str
```

**示例:**
```python
session_id = await orchestrator.start_record_as_test_session(
    name="用户注册流程测试",
    description="测试新用户注册的完整流程",
    config=custom_config
)
```

#### **执行完整工作流**
```python
async def execute_complete_workflow() -> RecordAsTestSession
```

**示例:**
```python
# 开始录制
session_id = await orchestrator.start_record_as_test_session("我的测试")

# 用户操作... (系统自动录制)
await asyncio.sleep(30)  # 模拟用户操作时间

# 执行完整工作流
session = await orchestrator.execute_complete_workflow()

# 查看结果
print(f"录制了 {session.total_actions} 个动作")
print(f"生成了 {session.total_components} 个组件")
print(f"成功率: {session.success_rate:.2%}")
```

### **4. ActionRecognitionEngine API**

#### **开始监控用户动作**
```python
def start_monitoring(
    callback: Callable[[UserAction], None] = None
) -> None
```

**示例:**
```python
def on_action(action: UserAction):
    print(f"检测到动作: {action.action_type} at {action.coordinates}")

engine = ActionRecognitionEngine()
engine.start_monitoring(callback=on_action)

# 停止监控
engine.stop_monitoring()
```

#### **获取动作历史**
```python
def get_action_history(
    start_time: float = None,
    end_time: float = None,
    action_types: List[ActionType] = None
) -> List[UserAction]
```

**示例:**
```python
# 获取最近5分钟的所有点击动作
import time
five_minutes_ago = time.time() - 300

actions = engine.get_action_history(
    start_time=five_minutes_ago,
    action_types=[ActionType.CLICK, ActionType.INPUT]
)

for action in actions:
    print(f"{action.action_type}: {action.element_info}")
```

### **5. TestNodeGenerator API**

#### **从动作生成测试流程**
```python
async def generate_test_flow_from_actions(
    actions: List[UserAction],
    config: Dict[str, Any] = None
) -> TestFlow
```

**示例:**
```python
# 获取录制的动作
actions = engine.get_action_history()

# 生成测试流程
generator = TestNodeGenerator()
test_flow = await generator.generate_test_flow_from_actions(
    actions=actions,
    config={
        "auto_generate_assertions": True,
        "insert_wait_nodes": True,
        "optimize_node_sequence": True
    }
)

print(f"生成了 {len(test_flow.nodes)} 个测试节点")
```

#### **优化测试流程**
```python
async def optimize_test_flow(test_flow: TestFlow) -> TestFlow
```

**示例:**
```python
optimized_flow = await generator.optimize_test_flow(test_flow)
print(f"优化后节点数: {len(optimized_flow.nodes)}")
```

### **6. AGUIAutoGenerator API**

#### **从测试流程生成组件**
```python
async def generate_components_from_test_flow(
    test_flow: TestFlow,
    config: Dict[str, Any] = None
) -> AGUITestSuite
```

**示例:**
```python
generator = AGUIAutoGenerator({
    'generate_react': True,
    'generate_vue': True,
    'component_prefix': 'Auto',
    'include_tests': True
})

test_suite = await generator.generate_components_from_test_flow(
    test_flow=test_flow,
    config={
        'output_directory': 'generated_components',
        'include_stories': True
    }
)

print(f"生成了 {len(test_suite.components)} 个组件")
```

#### **导出测试套件**
```python
def export_test_suite_to_files(
    test_suite: AGUITestSuite,
    output_directory: str
) -> List[str]
```

**示例:**
```python
file_paths = generator.export_test_suite_to_files(
    test_suite=test_suite,
    output_directory="./output"
)

for path in file_paths:
    print(f"生成文件: {path}")
```

### **7. PlaybackVerificationEngine API**

#### **验证测试流程**
```python
async def verify_test_flow(
    test_flow: TestFlow,
    config: Dict[str, Any] = None
) -> PlaybackSession
```

**示例:**
```python
engine = PlaybackVerificationEngine({
    'continue_on_failure': True,
    'capture_screenshots': True,
    'verification_timeout': 60.0
})

playback_session = await engine.verify_test_flow(
    test_flow=test_flow,
    config={
        'parallel_execution': False,
        'generate_report': True
    }
)

print(f"验证结果: {playback_session.performance_metrics['success_rate']:.2%}")
```

## 📋 **命令行接口 (CLI)**

### **基本命令**
```bash
# 运行P0测试
python -m core.components.stagewise_mcp.test_runner p0

# 运行MCP组件测试
python -m core.components.stagewise_mcp.test_runner mcp

# 运行UI测试
python -m core.components.stagewise_mcp.test_runner ui --output ui_report.json

# 运行性能测试
python -m core.components.stagewise_mcp.test_runner performance --parallel

# 运行指定测试套件
python -m core.components.stagewise_mcp.test_runner suite ui_functionality_tests

# 运行指定测试用例
python -m core.components.stagewise_mcp.test_runner case test_login_functionality
```

### **高级选项**
```bash
# 使用配置文件
python -m core.components.stagewise_mcp.test_runner p0 --config test_config.json

# 并行执行
python -m core.components.stagewise_mcp.test_runner all --parallel --max-workers 8

# 设置超时和重试
python -m core.components.stagewise_mcp.test_runner mcp --timeout 120 --retry 3

# 详细输出
python -m core.components.stagewise_mcp.test_runner ui --verbose --debug
```

## 🎯 **实际使用场景**

### **场景1: 快速UI测试录制**
```python
async def quick_ui_test_recording():
    """快速录制UI测试"""
    
    # 1. 初始化
    orchestrator = RecordAsTestOrchestrator(RecordAsTestConfig(
        recording_timeout=60.0,
        generate_react_components=True,
        auto_playback_verification=True
    ))
    
    # 2. 开始录制
    session_id = await orchestrator.start_record_as_test_session(
        name="快速UI测试",
        description="录制基本UI操作"
    )
    
    print("开始录制，请在浏览器中进行操作...")
    
    # 3. 等待用户操作
    await asyncio.sleep(30)  # 30秒录制时间
    
    # 4. 完成录制并生成
    session = await orchestrator.execute_complete_workflow()
    
    # 5. 输出结果
    print(f"录制完成！")
    print(f"- 动作数量: {session.total_actions}")
    print(f"- 生成组件: {session.total_components}")
    print(f"- 输出目录: {session.output_directory}")
    
    return session

# 运行
session = await quick_ui_test_recording()
```

### **场景2: 批量测试执行**
```python
async def batch_test_execution():
    """批量执行多个测试套件"""
    
    runner = StagewiseTestRunner("test_config.json")
    
    test_suites = [
        "p0_core_tests",
        "mcp_component_tests", 
        "ui_functionality_tests",
        "performance_tests"
    ]
    
    results = {}
    
    for suite in test_suites:
        print(f"执行测试套件: {suite}")
        
        session = await runner.run_test_suite(suite)
        results[suite] = {
            "total": session.total_tests,
            "passed": session.passed_tests,
            "failed": session.failed_tests,
            "success_rate": session.passed_tests / session.total_tests
        }
    
    # 生成汇总报告
    print("\n📊 测试汇总报告:")
    for suite, result in results.items():
        print(f"{suite}: {result['passed']}/{result['total']} "
              f"({result['success_rate']:.1%})")
    
    return results

# 运行
results = await batch_test_execution()
```

### **场景3: 自定义测试流程**
```python
async def custom_test_workflow():
    """自定义测试工作流程"""
    
    # 1. 动作识别
    action_engine = ActionRecognitionEngine()
    action_engine.start_monitoring()
    
    print("请进行操作，10秒后自动停止...")
    await asyncio.sleep(10)
    
    action_engine.stop_monitoring()
    actions = action_engine.get_action_history()
    
    # 2. 生成测试节点
    node_generator = TestNodeGenerator()
    test_flow = await node_generator.generate_test_flow_from_actions(actions)
    
    # 3. 生成AG-UI组件
    ag_ui_generator = AGUIAutoGenerator()
    test_suite = await ag_ui_generator.generate_components_from_test_flow(test_flow)
    
    # 4. 验证回放
    playback_engine = PlaybackVerificationEngine()
    playback_session = await playback_engine.verify_test_flow(test_flow)
    
    # 5. 导出结果
    output_files = ag_ui_generator.export_test_suite_to_files(
        test_suite, "custom_output"
    )
    
    print(f"工作流完成！生成了 {len(output_files)} 个文件")
    return {
        "actions": len(actions),
        "nodes": len(test_flow.nodes),
        "components": len(test_suite.components),
        "success_rate": playback_session.performance_metrics['success_rate'],
        "output_files": output_files
    }

# 运行
result = await custom_test_workflow()
```

## 🔍 **错误处理和调试**

### **常见错误处理**
```python
try:
    session = await orchestrator.start_record_as_test_session("测试")
except Exception as e:
    logger.error(f"录制启动失败: {str(e)}")
    # 处理错误...

# 检查会话状态
if session.status == RecordAsTestStatus.FAILED:
    print(f"录制失败，错误: {session.errors}")

# 验证配置
config = RecordAsTestConfig()
if not config.output_directory:
    config.output_directory = "default_output"
```

### **调试技巧**
```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查生成的文件
for file_path in session.component_files:
    if Path(file_path).exists():
        print(f"✅ 文件存在: {file_path}")
    else:
        print(f"❌ 文件缺失: {file_path}")

# 查看性能指标
metrics = playback_session.performance_metrics
print(f"平均节点执行时间: {metrics['average_node_time']:.2f}s")
print(f"总执行时间: {metrics['total_duration']:.2f}s")
```

## 📊 **性能优化建议**

### **录制性能优化**
```python
# 优化录制配置
config = RecordAsTestConfig(
    recording_timeout=120.0,  # 适当的超时时间
    min_actions_required=5,   # 最少动作数量
    auto_start_recording=True # 自动开始录制
)

# 减少截图频率
action_engine = ActionRecognitionEngine({
    'screenshot_interval': 2.0,  # 每2秒截图一次
    'action_buffer_size': 1000   # 增大缓冲区
})
```

### **测试执行优化**
```python
# 并行执行测试
runner = StagewiseTestRunner({
    'parallel': True,
    'max_workers': 4,
    'timeout': 60
})

# 优化测试流程
optimized_flow = await node_generator.optimize_test_flow(test_flow)
```

这个API文档提供了Stagewise测试框架的完整使用指南，包括所有核心接口、实际使用场景和最佳实践建议。

