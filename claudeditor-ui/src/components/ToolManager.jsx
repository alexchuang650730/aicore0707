import React, { useState, useEffect } from 'react';
import { Search, Settings, Play, Pause, RefreshCw, Zap, Brain, Clock, TrendingUp } from 'lucide-react';

const ToolManager = () => {
  const [tools, setTools] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [taskDescription, setTaskDescription] = useState('');
  const [selectedStrategy, setSelectedStrategy] = useState('balanced');
  const [activeTab, setActiveTab] = useState('discover');

  // API基础URL
  const API_BASE = 'http://localhost:5000/api';

  // 获取所有工具
  const fetchTools = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/tools`);
      const data = await response.json();
      if (data.success) {
        setTools(data.data);
      }
    } catch (error) {
      console.error('获取工具失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 发现工具
  const discoverTools = async (forceScan = false) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/tools/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ force_scan: forceScan })
      });
      const data = await response.json();
      if (data.success) {
        await fetchTools(); // 刷新工具列表
        return data.data;
      }
    } catch (error) {
      console.error('发现工具失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 推荐工具
  const recommendTools = async () => {
    if (!taskDescription.trim()) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/tools/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task_description: taskDescription,
          strategy: selectedStrategy,
          max_recommendations: 5
        })
      });
      const data = await response.json();
      if (data.success) {
        setRecommendations(data.data);
      }
    } catch (error) {
      console.error('推荐工具失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 执行工具
  const executeTool = async (toolId, parameters = {}) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/tools/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tool_id: toolId,
          parameters: parameters
        })
      });
      const data = await response.json();
      if (data.success) {
        alert(`工具执行成功！执行时间: ${data.data.execution_time?.toFixed(2)}秒`);
      } else {
        alert(`工具执行失败: ${data.error}`);
      }
    } catch (error) {
      console.error('执行工具失败:', error);
      alert('执行工具失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取系统状态
  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/system/status`);
      const data = await response.json();
      if (data.success) {
        setSystemStatus(data.data);
      }
    } catch (error) {
      console.error('获取系统状态失败:', error);
    }
  };

  // 初始化
  useEffect(() => {
    fetchTools();
    fetchSystemStatus();
    
    // 定期刷新系统状态
    const interval = setInterval(fetchSystemStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // 工具类型图标映射
  const getToolIcon = (type) => {
    const icons = {
      ai: <Brain className="w-4 h-4" />,
      file: <Settings className="w-4 h-4" />,
      web: <Zap className="w-4 h-4" />,
      terminal: <Play className="w-4 h-4" />,
      git: <RefreshCw className="w-4 h-4" />,
      deploy: <TrendingUp className="w-4 h-4" />
    };
    return icons[type] || <Settings className="w-4 h-4" />;
  };

  // 工具类型颜色映射
  const getToolColor = (type) => {
    const colors = {
      ai: 'bg-purple-100 text-purple-800',
      file: 'bg-blue-100 text-blue-800',
      web: 'bg-green-100 text-green-800',
      terminal: 'bg-gray-100 text-gray-800',
      git: 'bg-orange-100 text-orange-800',
      deploy: 'bg-red-100 text-red-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* 头部 */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">MCP-Zero Smart Engine</h1>
            <p className="text-sm text-gray-600">智能工具发现与选择系统</p>
          </div>
          
          {/* 系统状态 */}
          {systemStatus && (
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${systemStatus.system_status === 'running' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-gray-600">系统状态: {systemStatus.system_status}</span>
              </div>
              <div className="text-gray-600">
                工具总数: {systemStatus.tools?.total || 0}
              </div>
              <div className="text-gray-600">
                成功率: {((systemStatus.executions?.success_rate || 0) * 100).toFixed(1)}%
              </div>
            </div>
          )}
        </div>

        {/* 标签页 */}
        <div className="flex space-x-1 mt-4">
          {[
            { id: 'discover', label: '工具发现', icon: <Search className="w-4 h-4" /> },
            { id: 'recommend', label: '智能推荐', icon: <Brain className="w-4 h-4" /> },
            { id: 'manage', label: '工具管理', icon: <Settings className="w-4 h-4" /> }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 主内容区 */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'discover' && (
          <div className="h-full p-6">
            <div className="max-w-4xl mx-auto">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-semibold text-gray-900">工具发现</h2>
                  <div className="flex space-x-3">
                    <button
                      onClick={() => discoverTools(false)}
                      disabled={loading}
                      className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                      <span>增量扫描</span>
                    </button>
                    <button
                      onClick={() => discoverTools(true)}
                      disabled={loading}
                      className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      <Search className="w-4 h-4" />
                      <span>完整扫描</span>
                    </button>
                  </div>
                </div>

                {/* 工具统计 */}
                {systemStatus && (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">{systemStatus.tools?.total || 0}</div>
                      <div className="text-sm text-blue-600">总工具数</div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-green-600">{systemStatus.tools?.active || 0}</div>
                      <div className="text-sm text-green-600">活跃工具</div>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">{systemStatus.executions?.total || 0}</div>
                      <div className="text-sm text-purple-600">总执行次数</div>
                    </div>
                    <div className="bg-orange-50 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-orange-600">{systemStatus.executions?.active_executions || 0}</div>
                      <div className="text-sm text-orange-600">正在执行</div>
                    </div>
                  </div>
                )}

                {/* 工具类型分布 */}
                {systemStatus?.tools?.type_distribution && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-900 mb-3">工具类型分布</h3>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(systemStatus.tools.type_distribution).map(([type, count]) => (
                        <div key={type} className={`flex items-center space-x-2 px-3 py-1 rounded-full text-sm ${getToolColor(type)}`}>
                          {getToolIcon(type)}
                          <span>{type}: {count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'recommend' && (
          <div className="h-full p-6">
            <div className="max-w-4xl mx-auto">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 className="text-xl font-semibold text-gray-900 mb-6">智能工具推荐</h2>

                {/* 任务输入 */}
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    任务描述
                  </label>
                  <div className="flex space-x-3">
                    <input
                      type="text"
                      value={taskDescription}
                      onChange={(e) => setTaskDescription(e.target.value)}
                      placeholder="描述您要完成的任务..."
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      onKeyPress={(e) => e.key === 'Enter' && recommendTools()}
                    />
                    <select
                      value={selectedStrategy}
                      onChange={(e) => setSelectedStrategy(e.target.value)}
                      className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="balanced">平衡策略</option>
                      <option value="performance_first">性能优先</option>
                      <option value="cost_optimized">成本优化</option>
                      <option value="speed_first">速度优先</option>
                      <option value="accuracy_first">准确性优先</option>
                    </select>
                    <button
                      onClick={recommendTools}
                      disabled={loading || !taskDescription.trim()}
                      className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                    >
                      <Brain className="w-4 h-4" />
                      <span>推荐</span>
                    </button>
                  </div>
                </div>

                {/* 推荐结果 */}
                {recommendations.length > 0 && (
                  <div>
                    <h3 className="text-lg font-medium text-gray-900 mb-4">推荐工具</h3>
                    <div className="space-y-4">
                      {recommendations.map((rec, index) => (
                        <div key={rec.tool_id} className="border border-gray-200 rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3 mb-2">
                                <div className={`flex items-center space-x-2 px-2 py-1 rounded-full text-xs ${getToolColor(rec.tool_type)}`}>
                                  {getToolIcon(rec.tool_type)}
                                  <span>{rec.tool_type}</span>
                                </div>
                                <h4 className="font-medium text-gray-900">{rec.tool_name}</h4>
                                <div className="text-sm text-gray-500">#{index + 1}</div>
                              </div>
                              
                              <p className="text-sm text-gray-600 mb-2">{rec.tool_description}</p>
                              
                              <div className="flex items-center space-x-4 text-xs text-gray-500 mb-2">
                                <span>置信度: {(rec.confidence_score * 100).toFixed(1)}%</span>
                                <span>预估时间: {rec.estimated_time?.toFixed(1)}s</span>
                                <span>预估成本: ${rec.estimated_cost?.toFixed(3)}</span>
                              </div>
                              
                              <div className="text-sm text-gray-700 mb-2">
                                <strong>推荐理由:</strong> {rec.reasoning}
                              </div>
                              
                              {rec.usage_tips && rec.usage_tips.length > 0 && (
                                <div className="text-xs text-blue-600">
                                  <strong>使用提示:</strong> {rec.usage_tips.join('; ')}
                                </div>
                              )}
                            </div>
                            
                            <div className="flex flex-col space-y-2 ml-4">
                              <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-blue-500 transition-all duration-300"
                                  style={{ width: `${rec.confidence_score * 100}%` }}
                                ></div>
                              </div>
                              <button
                                onClick={() => executeTool(rec.tool_id)}
                                disabled={loading}
                                className="flex items-center space-x-1 px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                              >
                                <Play className="w-3 h-3" />
                                <span>执行</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'manage' && (
          <div className="h-full p-6">
            <div className="max-w-6xl mx-auto">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                <div className="p-6 border-b border-gray-200">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold text-gray-900">工具管理</h2>
                    <div className="text-sm text-gray-600">
                      共 {tools.length} 个工具
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">工具</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">类型</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">能力</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">性能</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">使用次数</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {tools.map((tool) => (
                        <tr key={tool.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div>
                              <div className="text-sm font-medium text-gray-900">{tool.name}</div>
                              <div className="text-sm text-gray-500 truncate max-w-xs">{tool.description}</div>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className={`flex items-center space-x-2 px-2 py-1 rounded-full text-xs ${getToolColor(tool.type)}`}>
                              {getToolIcon(tool.type)}
                              <span>{tool.type}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex flex-wrap gap-1">
                              {tool.capabilities.slice(0, 3).map((cap, index) => (
                                <span key={index} className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                  {cap}
                                </span>
                              ))}
                              {tool.capabilities.length > 3 && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-500 text-xs rounded">
                                  +{tool.capabilities.length - 3}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="w-16 h-2 bg-gray-200 rounded-full mr-2">
                                <div 
                                  className="h-full bg-green-500 rounded-full"
                                  style={{ width: `${tool.performance_score * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-sm text-gray-600">{(tool.performance_score * 100).toFixed(0)}%</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                            {tool.usage_count}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                              tool.is_active 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {tool.is_active ? '活跃' : '停用'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                            <button
                              onClick={() => executeTool(tool.id)}
                              disabled={loading || !tool.is_active}
                              className="text-blue-600 hover:text-blue-900 disabled:text-gray-400"
                            >
                              执行
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ToolManager;

