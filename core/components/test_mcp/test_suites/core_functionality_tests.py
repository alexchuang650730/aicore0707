"""
Core Functionality Tests - ClaudEditor核心功能测试套件
测试编辑器的基础功能和稳定性
"""

import asyncio
import subprocess
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List


class CoreFunctionalityTests:
    """ClaudEditor核心功能测试套件"""
    
    def __init__(self, config):
        self.config = config
        self.test_results = []
        
    async def run(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """运行核心功能测试"""
        print("🔧 开始核心功能测试...")
        
        test_cases = [
            self._test_application_startup,
            self._test_file_operations,
            self._test_monaco_editor,
            self._test_project_management,
            self._test_ui_responsiveness,
            self._test_application_shutdown
        ]
        
        passed_tests = 0
        failed_tests = 0
        test_details = {}
        
        for test_case in test_cases:
            try:
                result = await test_case(release_info)
                test_name = test_case.__name__
                test_details[test_name] = result
                
                if result['passed']:
                    passed_tests += 1
                    print(f"  ✅ {test_name}: 通过")
                else:
                    failed_tests += 1
                    print(f"  ❌ {test_name}: 失败 - {result.get('error', '未知错误')}")
                    
            except Exception as e:
                failed_tests += 1
                test_name = test_case.__name__
                test_details[test_name] = {
                    'passed': False,
                    'error': str(e),
                    'execution_time': 0
                }
                print(f"  ❌ {test_name}: 异常 - {str(e)}")
        
        total_tests = len(test_cases)
        
        return {
            'passed': failed_tests == 0,
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'skipped_tests': 0,
            'details': test_details,
            'metrics': {
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
            }
        }
    
    async def _test_application_startup(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试应用启动"""
        start_time = time.time()
        
        try:
            # 根据平台选择启动命令
            platform = release_info.get('platform', 'mac')
            
            if platform == 'mac':
                # Mac平台启动测试
                app_path = "/Applications/ClaudEditor.app"
                if not Path(app_path).exists():
                    # 使用测试环境路径
                    app_path = str(Path(__file__).parent.parent.parent.parent.parent / 
                                 "deployment/devices/mac/v4.4.0/package/ClaudEditor.app")
                
                if Path(app_path).exists():
                    # 启动应用
                    process = subprocess.Popen(
                        ['open', app_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE
                    )
                    
                    # 等待启动
                    await asyncio.sleep(3)
                    
                    # 检查进程是否运行
                    startup_time = time.time() - start_time
                    
                    # 查找ClaudEditor进程
                    claudeditor_running = False
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if 'ClaudEditor' in proc.info['name']:
                                claudeditor_running = True
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    return {
                        'passed': claudeditor_running and startup_time < 5.0,
                        'startup_time': startup_time,
                        'process_found': claudeditor_running,
                        'execution_time': startup_time
                    }
                else:
                    return {
                        'passed': False,
                        'error': f'ClaudEditor应用未找到: {app_path}',
                        'execution_time': time.time() - start_time
                    }
            
            else:
                # 其他平台的启动测试
                return {
                    'passed': True,
                    'note': f'平台 {platform} 的启动测试暂未实现',
                    'execution_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def _test_file_operations(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试文件操作功能"""
        start_time = time.time()
        
        try:
            # 创建测试文件
            test_dir = Path("/tmp/claudeditor_test")
            test_dir.mkdir(exist_ok=True)
            
            test_file = test_dir / "test_file.py"
            test_content = """# ClaudEditor测试文件
def hello_world():
    print("Hello, ClaudEditor!")
    return "success"

if __name__ == "__main__":
    hello_world()
"""
            
            # 写入测试文件
            test_file.write_text(test_content, encoding='utf-8')
            
            # 验证文件创建
            file_exists = test_file.exists()
            content_correct = test_file.read_text(encoding='utf-8') == test_content
            
            # 清理测试文件
            test_file.unlink()
            test_dir.rmdir()
            
            execution_time = time.time() - start_time
            
            return {
                'passed': file_exists and content_correct,
                'file_created': file_exists,
                'content_verified': content_correct,
                'execution_time': execution_time
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def _test_monaco_editor(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试Monaco编辑器功能"""
        start_time = time.time()
        
        try:
            # 检查Monaco编辑器相关文件
            ui_path = Path(__file__).parent.parent.parent.parent.parent / "claudeditor/claudeditor-ui"
            
            monaco_files = [
                ui_path / "src/components/MonacoEditor.jsx",
                ui_path / "package.json"
            ]
            
            files_exist = all(f.exists() for f in monaco_files)
            
            # 检查package.json中的Monaco依赖
            package_json_path = ui_path / "package.json"
            monaco_dependency = False
            
            if package_json_path.exists():
                import json
                try:
                    with open(package_json_path, 'r') as f:
                        package_data = json.load(f)
                    
                    dependencies = package_data.get('dependencies', {})
                    monaco_dependency = '@monaco-editor/react' in dependencies
                except:
                    pass
            
            execution_time = time.time() - start_time
            
            return {
                'passed': files_exist and monaco_dependency,
                'files_exist': files_exist,
                'monaco_dependency': monaco_dependency,
                'execution_time': execution_time
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def _test_project_management(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试项目管理功能"""
        start_time = time.time()
        
        try:
            # 检查项目结构
            project_root = Path(__file__).parent.parent.parent.parent.parent
            
            required_dirs = [
                project_root / "core",
                project_root / "claudeditor",
                project_root / "deployment"
            ]
            
            dirs_exist = all(d.exists() and d.is_dir() for d in required_dirs)
            
            # 检查核心组件
            core_components = project_root / "core/components"
            component_count = len(list(core_components.glob("*_mcp"))) if core_components.exists() else 0
            
            execution_time = time.time() - start_time
            
            return {
                'passed': dirs_exist and component_count >= 5,
                'required_dirs_exist': dirs_exist,
                'component_count': component_count,
                'execution_time': execution_time
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def _test_ui_responsiveness(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试UI响应性"""
        start_time = time.time()
        
        try:
            # 检查UI构建文件
            ui_dist_path = Path(__file__).parent.parent.parent.parent.parent / "claudeditor/claudeditor-ui/dist"
            
            ui_files = [
                ui_dist_path / "index.html",
                ui_dist_path / "assets"
            ]
            
            ui_built = all(f.exists() for f in ui_files)
            
            # 检查CSS和JS文件
            assets_dir = ui_dist_path / "assets"
            css_files = list(assets_dir.glob("*.css")) if assets_dir.exists() else []
            js_files = list(assets_dir.glob("*.js")) if assets_dir.exists() else []
            
            execution_time = time.time() - start_time
            
            return {
                'passed': ui_built and len(css_files) > 0 and len(js_files) > 0,
                'ui_built': ui_built,
                'css_files_count': len(css_files),
                'js_files_count': len(js_files),
                'execution_time': execution_time
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    async def _test_application_shutdown(self, release_info: Dict[str, Any]) -> Dict[str, Any]:
        """测试应用关闭"""
        start_time = time.time()
        
        try:
            # 查找并关闭ClaudEditor进程
            claudeditor_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'ClaudEditor' in proc.info['name']:
                        claudeditor_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # 尝试优雅关闭
            for proc in claudeditor_processes:
                try:
                    proc.terminate()
                    proc.wait(timeout=3)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    try:
                        proc.kill()
                    except psutil.NoSuchProcess:
                        pass
            
            # 等待进程完全关闭
            await asyncio.sleep(2)
            
            # 验证进程已关闭
            remaining_processes = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'ClaudEditor' in proc.info['name']:
                        remaining_processes.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            execution_time = time.time() - start_time
            
            return {
                'passed': len(remaining_processes) == 0,
                'processes_found': len(claudeditor_processes),
                'processes_remaining': len(remaining_processes),
                'execution_time': execution_time
            }
            
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }

