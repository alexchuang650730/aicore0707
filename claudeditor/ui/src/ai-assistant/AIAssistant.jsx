import React, { useState, useEffect, useRef } from 'react';
import { 
  Brain, 
  Zap, 
  Code, 
  MessageSquare, 
  Settings, 
  Play, 
  Loader2,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  DollarSign,
  Clock,
  Sparkles
} from 'lucide-react';

// AI模型配置
const AI_MODELS = {
  claude: {
    name: 'Claude 3.5 Sonnet',
    description: '推理型 - 逻辑严密，代码质量高',
    capabilities: ['code_generation', 'explanation', 'review', 'refactoring'],
    maxTokens: 200000,
    icon: '🧠',
    strengths: ['代码解释', '代码审查', '逻辑推理'],
    costLevel: 'medium',
    speedLevel: 'medium',
    qualityLevel: 'high'
  },
  gemini: {
    name: 'Gemini 1.5 Pro',
    description: '性能型 - 高性价比，88%创新分数',
    capabilities: ['performance_optimization', 'rapid_prototyping', 'innovation'],
    maxTokens: 128000,
    icon: '⚡',
    strengths: ['性能优化', '快速原型', '创新解决方案'],
    costLevel: 'low',
    speedLevel: 'high',
    qualityLevel: 'medium'
  }
};

// 任务类型配置
const TASK_TYPES = {
  code_generation: { name: '代码生成', icon: '💻', recommendedModel: 'auto' },
  code_explanation: { name: '代码解释', icon: '📖', recommendedModel: 'claude' },
  code_debug: { name: '代码调试', icon: '🐛', recommendedModel: 'claude' },
  code_optimization: { name: '性能优化', icon: '⚡', recommendedModel: 'gemini' },
  code_refactoring: { name: '代码重构', icon: '🔄', recommendedModel: 'claude' },
  code_review: { name: '代码审查', icon: '👀', recommendedModel: 'claude' },
  test_generation: { name: '测试生成', icon: '🧪', recommendedModel: 'auto' },
  architecture_design: { name: '架构设计', icon: '🏗️', recommendedModel: 'gemini' },
  performance_analysis: { name: '性能分析', icon: '📊', recommendedModel: 'gemini' },
  innovation_solution: { name: '创新方案', icon: '💡', recommendedModel: 'gemini' }
};

// 选择策略配置
const SELECTION_STRATEGIES = {
  auto_select: { name: '智能选择', description: '自动选择最适合的模型', icon: '🤖' },
  quality_first: { name: '质量优先', description: '优先选择高质量输出', icon: '⭐' },
  cost_efficient: { name: '成本优先', description: '优先选择成本效益', icon: '💰' },
  speed_first: { name: '速度优先', description: '优先选择快速响应', icon: '🚀' },
  innovation_focus: { name: '创新优先', description: '优先选择创新方案', icon: '✨' },
  balanced: { name: '平衡策略', description: '平衡质量、成本和速度', icon: '⚖️' }
};

const AIAssistant = ({ selectedCode, language = 'python', onCodeUpdate }) => {
  // 状态管理
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [selectedTaskType, setSelectedTaskType] = useState('code_generation');
  const [selectedStrategy, setSelectedStrategy] = useState('auto_select');
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [apiStats, setApiStats] = useState(null);
  const [modelPerformance, setModelPerformance] = useState({});
  
  // API配置
  const [apiConfig, setApiConfig] = useState({
    claudeApiKey: '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',
    geminiApiKey: 'AIzaSyC_EsNirr14s8ypd3KafqWazSi_RW0NiqA',
    apiEndpoint: 'http://localhost:5000/api/ai-assistant'
  });
  
  const chatEndRef = useRef(null);

  // 自动滚动到聊天底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  // 加载API统计信息
  useEffect(() => {
    loadApiStatistics();
    const interval = setInterval(loadApiStatistics, 30000); // 每30秒更新
    return () => clearInterval(interval);
  }, []);

  const loadApiStatistics = async () => {
    try {
      const response = await fetch(`${apiConfig.apiEndpoint}/statistics`);
      if (response.ok) {
        const data = await response.json();
        setApiStats(data.coordinator_statistics);
        setModelPerformance(data.model_performance);
      }
    } catch (error) {
      console.error('加载API统计失败:', error);
    }
  };

  const handleSubmit = async () => {
    if (!prompt.trim()) return;

    setIsLoading(true);
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: prompt,
      timestamp: new Date().toLocaleTimeString(),
      taskType: selectedTaskType,
      strategy: selectedStrategy
    };

    setChatHistory(prev => [...prev, userMessage]);
    setPrompt('');

    try {
      const requestData = {
        task_type: selectedTaskType,
        prompt: selectedCode ? `${prompt}\n\n代码:\n\`\`\`${language}\n${selectedCode}\n\`\`\`` : prompt,
        language: language,
        strategy: selectedStrategy,
        context: selectedCode ? '用户选中的代码' : null,
        priority: 3,
        constraints: {}
      };

      const response = await fetch(`${apiConfig.apiEndpoint}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.status}`);
      }

      const data = await response.json();

      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: data.content,
        timestamp: new Date().toLocaleTimeString(),
        modelUsed: data.model_used,
        executionTime: data.execution_time,
        qualityScore: data.quality_score,
        innovationScore: data.innovation_score,
        estimatedCost: data.estimated_cost,
        success: data.success
      };

      setChatHistory(prev => [...prev, aiMessage]);
      setResponse(data.content);

      // 如果是代码生成任务，更新编辑器
      if (selectedTaskType === 'code_generation' && onCodeUpdate) {
        const codeMatch = data.content.match(/```[\w]*\n([\s\S]*?)\n```/);
        if (codeMatch) {
          onCodeUpdate(codeMatch[1]);
        }
      }

      // 更新统计信息
      loadApiStatistics();

    } catch (error) {
      console.error('AI请求失败:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `请求失败: ${error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (action) => {
    const quickPrompts = {
      explain: '请详细解释这段代码的功能和实现原理',
      optimize: '请优化这段代码的性能，提供改进建议',
      debug: '请帮助分析这段代码中可能存在的问题',
      refactor: '请重构这段代码，提高可读性和可维护性',
      test: '请为这段代码生成完整的单元测试',
      review: '请对这段代码进行全面的代码审查'
    };

    const taskTypeMap = {
      explain: 'code_explanation',
      optimize: 'code_optimization',
      debug: 'code_debug',
      refactor: 'code_refactoring',
      test: 'test_generation',
      review: 'code_review'
    };

    setSelectedTaskType(taskTypeMap[action]);
    setPrompt(quickPrompts[action]);
  };

  const renderModelComparison = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">模型对比</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(AI_MODELS).map(([key, model]) => (
          <div key={key} className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-2xl">{model.icon}</span>
              <div>
                <h4 className="font-semibold text-gray-800 dark:text-gray-200">{model.name}</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">{model.description}</p>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">成本效率</span>
                <div className="flex items-center gap-1">
                  {[...Array(3)].map((_, i) => (
                    <div
                      key={i}
                      className={`w-2 h-2 rounded-full ${
                        (model.costLevel === 'low' && i < 3) ||
                        (model.costLevel === 'medium' && i < 2) ||
                        (model.costLevel === 'high' && i < 1)
                          ? 'bg-green-500'
                          : 'bg-gray-300'
                      }`}
                    />
                  ))}
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">响应速度</span>
                <div className="flex items-center gap-1">
                  {[...Array(3)].map((_, i) => (
                    <div
                      key={i}
                      className={`w-2 h-2 rounded-full ${
                        (model.speedLevel === 'high' && i < 3) ||
                        (model.speedLevel === 'medium' && i < 2) ||
                        (model.speedLevel === 'low' && i < 1)
                          ? 'bg-blue-500'
                          : 'bg-gray-300'
                      }`}
                    />
                  ))}
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600 dark:text-gray-400">输出质量</span>
                <div className="flex items-center gap-1">
                  {[...Array(3)].map((_, i) => (
                    <div
                      key={i}
                      className={`w-2 h-2 rounded-full ${
                        (model.qualityLevel === 'high' && i < 3) ||
                        (model.qualityLevel === 'medium' && i < 2) ||
                        (model.qualityLevel === 'low' && i < 1)
                          ? 'bg-purple-500'
                          : 'bg-gray-300'
                      }`}
                    />
                  ))}
                </div>
              </div>
            </div>
            
            <div className="mt-3">
              <p className="text-xs text-gray-500 dark:text-gray-400">擅长领域:</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {model.strengths.map((strength, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded-full text-gray-600 dark:text-gray-300"
                  >
                    {strength}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderStatistics = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-800 dark:text-gray-200">性能统计</h3>
      
      {apiStats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span className="font-semibold text-gray-800 dark:text-gray-200">成功率</span>
            </div>
            <p className="text-2xl font-bold text-green-600">
              {(apiStats.success_rate * 100).toFixed(1)}%
            </p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {apiStats.successful_requests}/{apiStats.total_requests} 请求
            </p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <Clock className="w-5 h-5 text-blue-500" />
              <span className="font-semibold text-gray-800 dark:text-gray-200">平均响应时间</span>
            </div>
            <p className="text-2xl font-bold text-blue-600">
              {apiStats.average_response_time.toFixed(2)}s
            </p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-5 h-5 text-green-500" />
              <span className="font-semibold text-gray-800 dark:text-gray-200">成本节省</span>
            </div>
            <p className="text-2xl font-bold text-green-600">
              ${apiStats.total_cost_saved?.toFixed(4) || '0.0000'}
            </p>
          </div>
        </div>
      )}
      
      {modelPerformance && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
          <h4 className="font-semibold text-gray-800 dark:text-gray-200 mb-3">模型使用分布</h4>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">🧠</span>
                <span className="text-gray-700 dark:text-gray-300">Claude</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${(apiStats?.claude_usage_rate || 0) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {((apiStats?.claude_usage_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-lg">⚡</span>
                <span className="text-gray-700 dark:text-gray-300">Gemini</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-green-500 h-2 rounded-full"
                    style={{ width: `${(apiStats?.gemini_usage_rate || 0) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {((apiStats?.gemini_usage_rate || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderChatInterface = () => (
    <div className="flex flex-col h-full">
      {/* 任务类型和策略选择 */}
      <div className="bg-gray-50 dark:bg-gray-800 p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              任务类型
            </label>
            <select
              value={selectedTaskType}
              onChange={(e) => setSelectedTaskType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              {Object.entries(TASK_TYPES).map(([key, task]) => (
                <option key={key} value={key}>
                  {task.icon} {task.name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              选择策略
            </label>
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            >
              {Object.entries(SELECTION_STRATEGIES).map(([key, strategy]) => (
                <option key={key} value={key}>
                  {strategy.icon} {strategy.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        
        {/* 推荐模型显示 */}
        {TASK_TYPES[selectedTaskType]?.recommendedModel !== 'auto' && (
          <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded-md">
            <p className="text-sm text-blue-700 dark:text-blue-300">
              💡 推荐模型: {AI_MODELS[TASK_TYPES[selectedTaskType].recommendedModel]?.name}
            </p>
          </div>
        )}
      </div>

      {/* 聊天历史 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatHistory.length === 0 && (
          <div className="text-center text-gray-500 dark:text-gray-400 py-8">
            <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>选择代码并开始与AI助手对话</p>
            <p className="text-sm mt-2">支持代码生成、解释、优化、调试等功能</p>
          </div>
        )}
        
        {chatHistory.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.type === 'user'
                  ? 'bg-blue-500 text-white'
                  : message.type === 'error'
                  ? 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>
              
              {message.type === 'ai' && (
                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                  <div className="flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
                    <span className="flex items-center gap-1">
                      {message.modelUsed === 'claude' ? '🧠' : '⚡'} {message.modelUsed}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" /> {message.executionTime?.toFixed(2)}s
                    </span>
                    <span className="flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" /> {(message.qualityScore * 100)?.toFixed(0)}%
                    </span>
                    <span className="flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> {(message.innovationScore * 100)?.toFixed(0)}%
                    </span>
                    <span className="flex items-center gap-1">
                      <DollarSign className="w-3 h-3" /> ${message.estimatedCost?.toFixed(4)}
                    </span>
                  </div>
                </div>
              )}
              
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                {message.timestamp}
              </div>
            </div>
          </div>
        ))}
        <div ref={chatEndRef} />
      </div>

      {/* 快速操作按钮 */}
      {selectedCode && (
        <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700">
          <div className="flex flex-wrap gap-2">
            {[
              { key: 'explain', label: '解释', icon: '📖' },
              { key: 'optimize', label: '优化', icon: '⚡' },
              { key: 'debug', label: '调试', icon: '🐛' },
              { key: 'refactor', label: '重构', icon: '🔄' },
              { key: 'test', label: '测试', icon: '🧪' },
              { key: 'review', label: '审查', icon: '👀' }
            ].map((action) => (
              <button
                key={action.key}
                onClick={() => handleQuickAction(action.key)}
                className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md text-gray-700 dark:text-gray-300 transition-colors"
              >
                {action.icon} {action.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* 输入区域 */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="描述你的需求..."
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md resize-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            rows="3"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                handleSubmit();
              }
            }}
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || !prompt.trim()}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-md transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            发送
          </button>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
          Ctrl+Enter 快速发送 • 支持多模型智能选择
        </p>
      </div>
    </div>
  );

  return (
    <div className="relative">
      {/* AI助手触发按钮 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center z-50"
      >
        <Brain className="w-6 h-6" />
      </button>

      {/* AI助手面板 */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 w-96 h-[600px] bg-white dark:bg-gray-900 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 z-40 flex flex-col">
          {/* 头部 */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-blue-500" />
              <h3 className="font-semibold text-gray-800 dark:text-gray-200">AI编程助手</h3>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex bg-gray-100 dark:bg-gray-800 rounded-md p-1">
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`px-3 py-1 text-sm rounded transition-colors ${
                    activeTab === 'chat'
                      ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  <MessageSquare className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setActiveTab('models')}
                  className={`px-3 py-1 text-sm rounded transition-colors ${
                    activeTab === 'models'
                      ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  <Zap className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setActiveTab('stats')}
                  className={`px-3 py-1 text-sm rounded transition-colors ${
                    activeTab === 'stats'
                      ? 'bg-white dark:bg-gray-700 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200'
                  }`}
                >
                  <TrendingUp className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
          </div>

          {/* 内容区域 */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'chat' && renderChatInterface()}
            {activeTab === 'models' && (
              <div className="p-4 overflow-y-auto h-full">
                {renderModelComparison()}
              </div>
            )}
            {activeTab === 'stats' && (
              <div className="p-4 overflow-y-auto h-full">
                {renderStatistics()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAssistant;

