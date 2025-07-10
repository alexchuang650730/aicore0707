#!/usr/bin/env python3
"""
修正的里程碑验证测试
基于发现的本地ClaudEditor UI存在，重新验证所有组件
"""

import os
import json
from datetime import datetime

def check_file_exists(path):
    """检查文件是否存在"""
    return os.path.exists(path)

def check_directory_exists(path):
    """检查目录是否存在"""
    return os.path.isdir(path)

def get_file_size(path):
    """获取文件大小"""
    try:
        return os.path.getsize(path)
    except:
        return 0

def main():
    print("🔍 修正的里程碑验证测试")
    print("=" * 80)
    
    base_path = "/home/ubuntu/aicore0707"
    results = {
        "verification_time": datetime.now().isoformat(),
        "base_path": base_path,
        "components": {},
        "summary": {}
    }
    
    # 1. ClaudEditor UI 组件验证 (修正路径)
    print("🎨 验证ClaudEditor UI组件")
    print("-" * 60)
    
    claudeditor_ui_components = {
        "App.jsx": f"{base_path}/claudeditor/ui/src/App.jsx",
        "App.css": f"{base_path}/claudeditor/ui/src/App.css", 
        "main.jsx": f"{base_path}/claudeditor/ui/src/main.jsx",
        "index.css": f"{base_path}/claudeditor/ui/src/index.css",
        "MonacoEditor.jsx": f"{base_path}/claudeditor/ui/src/editor/MonacoEditor.jsx",
        "ai-assistant/": f"{base_path}/claudeditor/ui/src/ai-assistant",
        "collaboration/": f"{base_path}/claudeditor/ui/src/collaboration", 
        "components/": f"{base_path}/claudeditor/ui/src/components",
        "editor/": f"{base_path}/claudeditor/ui/src/editor",
        "lsp/": f"{base_path}/claudeditor/ui/src/lsp",
        "hooks/": f"{base_path}/claudeditor/ui/src/hooks",
        "index.html": f"{base_path}/claudeditor/ui/index.html",
        "package.json": f"{base_path}/claudeditor/ui/package.json",
        "vite.config.js": f"{base_path}/claudeditor/ui/vite.config.js"
    }
    
    claudeditor_results = {}
    claudeditor_found = 0
    
    for component, path in claudeditor_ui_components.items():
        if component.endswith('/'):
            exists = check_directory_exists(path)
        else:
            exists = check_file_exists(path)
            
        if exists:
            claudeditor_found += 1
            size = get_file_size(path) if not component.endswith('/') else "目录"
            print(f"   ✅ 存在 {component} ({size} bytes)")
        else:
            print(f"   ❌ 缺失 {component}")
            
        claudeditor_results[component] = {
            "exists": exists,
            "path": path,
            "size": get_file_size(path) if exists and not component.endswith('/') else None
        }
    
    claudeditor_percentage = (claudeditor_found / len(claudeditor_ui_components)) * 100
    print(f"📊 ClaudEditor UI: {claudeditor_found}/{len(claudeditor_ui_components)} 存在 ({claudeditor_percentage:.1f}%)")
    
    results["components"]["claudeditor_ui"] = {
        "components": claudeditor_results,
        "found": claudeditor_found,
        "total": len(claudeditor_ui_components),
        "percentage": claudeditor_percentage
    }
    
    # 2. Core Components 验证 (修正路径)
    print("\n📦 验证Core Components")
    print("-" * 60)
    
    core_components = {
        "local_adapter_mcp/": f"{base_path}/core/components/local_adapter_mcp",
        "ag_ui_mcp/": f"{base_path}/core/components/ag_ui_mcp", 
        "agent_zero_mcp/": f"{base_path}/core/components/agent_zero_mcp",
        "agents_mcp/": f"{base_path}/core/components/agents_mcp",
        "claude_mcp/": f"{base_path}/core/components/claude_mcp",
        "claude_unified_mcp/": f"{base_path}/core/components/claude_unified_mcp",
        "collaboration_mcp/": f"{base_path}/core/components/collaboration_mcp",
        "command_mcp/": f"{base_path}/core/components/command_mcp",
        "config_mcp/": f"{base_path}/core/components/config_mcp"
    }
    
    core_results = {}
    core_found = 0
    
    for component, path in core_components.items():
        exists = check_directory_exists(path)
        if exists:
            core_found += 1
            print(f"   ✅ 存在 {component}")
        else:
            print(f"   ❌ 缺失 {component}")
            
        core_results[component] = {
            "exists": exists,
            "path": path
        }
    
    core_percentage = (core_found / len(core_components)) * 100
    print(f"📊 Core Components: {core_found}/{len(core_components)} 存在 ({core_percentage:.1f}%)")
    
    results["components"]["core_components"] = {
        "components": core_results,
        "found": core_found,
        "total": len(core_components),
        "percentage": core_percentage
    }
    
    # 3. PowerAutomation Core 验证
    print("\n⚡ 验证PowerAutomation Core")
    print("-" * 60)
    
    powerautomation_components = {
        "__init__.py": f"{base_path}/deployment/devices/mac/v4.5.0/core/powerautomation_core/__init__.py",
        "automation_core.py": f"{base_path}/deployment/devices/mac/v4.5.0/core/powerautomation_core/automation_core.py",
        "workflow_engine.py": f"{base_path}/deployment/devices/mac/v4.5.0/core/powerautomation_core/workflow_engine.py",
        "task_scheduler.py": f"{base_path}/deployment/devices/mac/v4.5.0/core/powerautomation_core/task_scheduler.py",
        "resource_manager.py": f"{base_path}/deployment/devices/mac/v4.5.0/core/powerautomation_core/resource_manager.py",
        "monitoring_service.py": f"{base_path}/deployment/devices/mac/v4.5.0/core/powerautomation_core/monitoring_service.py"
    }
    
    pa_results = {}
    pa_found = 0
    
    for component, path in powerautomation_components.items():
        exists = check_file_exists(path)
        if exists:
            pa_found += 1
            size = get_file_size(path)
            print(f"   ✅ 存在 {component} ({size} bytes)")
        else:
            print(f"   ❌ 缺失 {component}")
            
        pa_results[component] = {
            "exists": exists,
            "path": path,
            "size": get_file_size(path) if exists else None
        }
    
    pa_percentage = (pa_found / len(powerautomation_components)) * 100
    print(f"📊 PowerAutomation Core: {pa_found}/{len(powerautomation_components)} 存在 ({pa_percentage:.1f}%)")
    
    results["components"]["powerautomation_core"] = {
        "components": pa_results,
        "found": pa_found,
        "total": len(powerautomation_components),
        "percentage": pa_percentage
    }
    
    # 4. Mirror Code 验证
    print("\n🪞 验证Mirror Code")
    print("-" * 60)
    
    mirror_components = {
        "mirror_engine.py": f"{base_path}/core/mirror_code/engine/mirror_engine.py",
        "sync_manager.py": f"{base_path}/core/mirror_code/sync/sync_manager.py",
        "comm_manager.py": f"{base_path}/core/mirror_code/communication/comm_manager.py",
        "launch_mirror.py": f"{base_path}/core/mirror_code/launch_mirror.py"
    }
    
    mirror_results = {}
    mirror_found = 0
    
    for component, path in mirror_components.items():
        exists = check_file_exists(path)
        if exists:
            mirror_found += 1
            size = get_file_size(path)
            print(f"   ✅ 存在 {component} ({size} bytes)")
        else:
            print(f"   ❌ 缺失 {component}")
            
        mirror_results[component] = {
            "exists": exists,
            "path": path,
            "size": get_file_size(path) if exists else None
        }
    
    mirror_percentage = (mirror_found / len(mirror_components)) * 100
    print(f"📊 Mirror Code: {mirror_found}/{len(mirror_components)} 存在 ({mirror_percentage:.1f}%)")
    
    results["components"]["mirror_code"] = {
        "components": mirror_results,
        "found": mirror_found,
        "total": len(mirror_components),
        "percentage": mirror_percentage
    }
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 修正后的验证总结")
    print("=" * 80)
    
    total_found = claudeditor_found + core_found + pa_found + mirror_found
    total_components = len(claudeditor_ui_components) + len(core_components) + len(powerautomation_components) + len(mirror_components)
    overall_percentage = (total_found / total_components) * 100
    
    print(f"📊 总体完成度: {total_found}/{total_components} ({overall_percentage:.1f}%)")
    print(f"📅 验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n🔍 各组件验证结果:")
    print(f"   ✅ ClaudEditor UI: {claudeditor_percentage:.1f}%")
    print(f"   ✅ Core Components: {core_percentage:.1f}%") 
    print(f"   ✅ PowerAutomation Core: {pa_percentage:.1f}%")
    print(f"   ✅ Mirror Code: {mirror_percentage:.1f}%")
    
    # 与之前声称的对比
    print("\n🎯 与里程碑声称对比:")
    print(f"   📊 ClaudEditor UI: 声称100% → 实际{claudeditor_percentage:.1f}%")
    print(f"   📊 Core Components: 发现{core_percentage:.1f}%完成")
    print(f"   📊 PowerAutomation: 声称100% → 实际{pa_percentage:.1f}%")
    print(f"   📊 Mirror Code: 实际{mirror_percentage:.1f}%完成")
    
    results["summary"] = {
        "total_found": total_found,
        "total_components": total_components,
        "overall_percentage": overall_percentage,
        "previous_error": "之前验证路径错误，ClaudEditor UI实际存在"
    }
    
    # 保存结果
    with open(f"{base_path}/CORRECTED_MILESTONE_VERIFICATION_REPORT.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 详细报告已保存: {base_path}/CORRECTED_MILESTONE_VERIFICATION_REPORT.json")

if __name__ == "__main__":
    main()

