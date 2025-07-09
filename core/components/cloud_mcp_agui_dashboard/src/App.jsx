import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Cloud, 
  Server, 
  Activity, 
  Settings, 
  Shield, 
  Zap, 
  Monitor, 
  Users,
  Database,
  Network,
  Bell,
  Search,
  Menu,
  X,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock,
  Cpu,
  HardDrive,
  Wifi,
  Bot,
  MessageSquare,
  Sparkles
} from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert.jsx'
import './App.css'

// AG-UI增强的侧边栏组件
const AGUISidebar = ({ isOpen, onToggle, activeTab, onTabChange }) => {
  const menuItems = [
    { id: 'dashboard', label: '智能仪表板', icon: Monitor, description: '系统概览和AI洞察' },
    { id: 'environments', label: '环境管理', icon: Server, description: 'AI辅助环境配置' },
    { id: 'deployments', label: '智能部署', icon: Cloud, description: '自动化部署管理' },
    { id: 'monitoring', label: 'AI监控', icon: Activity, description: '智能告警和预测' },
    { id: 'security', label: '安全防护', icon: Shield, description: 'AI安全分析' },
    { id: 'performance', label: '性能优化', icon: Zap, description: 'AI性能调优' },
    { id: 'users', label: '用户管理', icon: Users, description: '智能权限管理' },
    { id: 'settings', label: '系统设置', icon: Settings, description: 'AI配置助手' }
  ]

  return (
    <motion.div
      initial={{ x: -300 }}
      animate={{ x: isOpen ? 0 : -250 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
      className="fixed left-0 top-0 h-full w-72 bg-gradient-to-b from-white to-gray-50 dark:from-gray-900 dark:to-gray-800 border-r border-gray-200 dark:border-gray-700 z-50 shadow-2xl backdrop-blur-sm"
    >
      <div className="p-6">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Cloud className="h-8 w-8 text-blue-600" />
              <Sparkles className="h-4 w-4 text-yellow-400 absolute -top-1 -right-1 animate-pulse" />
            </div>
            <div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">Cloud MCP</span>
              <div className="text-xs text-gray-600 dark:text-gray-400 flex items-center gap-1">
                <Bot className="h-3 w-3" />
                AG-UI Powered
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className="lg:hidden"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
        
        <nav className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            return (
              <motion.button
                key={item.id}
                whileHover={{ scale: 1.02, x: 4 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => onTabChange(item.id)}
                className={`w-full flex flex-col items-start space-y-1 px-4 py-3 rounded-xl text-left transition-all duration-200 group ${
                  activeTab === item.id
                    ? 'bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/50 dark:to-blue-800/50 text-blue-900 dark:text-blue-100 shadow-lg'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 hover:shadow-md'
                }`}
              >
                <div className="flex items-center space-x-3 w-full">
                  <Icon className={`h-5 w-5 transition-colors ${
                    activeTab === item.id ? 'text-blue-600' : 'text-gray-500 group-hover:text-blue-600'
                  }`} />
                  <span className="font-medium">{item.label}</span>
                  {activeTab === item.id && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="ml-auto"
                    >
                      <ChevronRight className="h-4 w-4 text-blue-600" />
                    </motion.div>
                  )}
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400 ml-8 group-hover:text-gray-700 dark:group-hover:text-gray-300">
                  {item.description}
                </span>
              </motion.button>
            )
          })}
        </nav>

        {/* AI助手快捷入口 */}
        <div className="mt-8 p-4 bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl border border-blue-200 dark:border-blue-700">
          <div className="flex items-center space-x-2 mb-2">
            <Bot className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-gray-900 dark:text-white">AI助手</span>
          </div>
          <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
            智能分析系统状态，提供优化建议
          </p>
          <Button size="sm" className="w-full bg-blue-100 hover:bg-blue-200 text-blue-700 border-blue-300 dark:bg-blue-800 dark:hover:bg-blue-700 dark:text-blue-100">
            <MessageSquare className="h-3 w-3 mr-1" />
            开始对话
          </Button>
        </div>
      </div>
    </motion.div>
  )
}

// AG-UI增强的顶部导航栏
const AGUITopBar = ({ onMenuToggle, onSearch }) => {
  const [searchQuery, setSearchQuery] = useState('')

  const handleSearch = (e) => {
    setSearchQuery(e.target.value)
    onSearch(e.target.value)
  }

  return (
    <div className="h-16 bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6 shadow-sm">
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={onMenuToggle}
          className="lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </Button>
        
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="AI智能搜索：环境、部署、服务..."
            value={searchQuery}
            onChange={handleSearch}
            className="pl-10 w-96 bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-600"
          />
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
            <Sparkles className="h-3 w-3 text-blue-500" />
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full text-xs flex items-center justify-center text-white">
            3
          </span>
        </Button>
        
        <div className="flex items-center space-x-3 px-3 py-1 rounded-lg bg-gray-100 dark:bg-gray-800">
          <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
            <span className="text-white text-sm font-medium">AI</span>
          </div>
          <div>
            <span className="text-sm font-medium text-gray-900 dark:text-white">AI管理员</span>
            <div className="text-xs text-gray-500 dark:text-gray-400">在线</div>
          </div>
        </div>
      </div>
    </div>
  )
}

// AG-UI增强的仪表板组件
const AGUIDashboard = () => {
  const [stats, setStats] = useState({
    totalEnvironments: 12,
    activeDeployments: 8,
    systemHealth: 95,
    aiRecommendations: 5,
    cpuUsage: 68,
    memoryUsage: 72,
    networkTraffic: 45,
    aiOptimizations: 3
  })

  const statusCards = [
    {
      title: "环境总数",
      value: stats.totalEnvironments,
      change: "+2",
      changeType: "positive",
      icon: Server,
      color: "text-blue-600",
      aiInsight: "AI建议：可优化3个环境配置"
    },
    {
      title: "智能部署",
      value: stats.activeDeployments,
      change: "+3",
      changeType: "positive", 
      icon: Cloud,
      color: "text-green-600",
      aiInsight: "AI预测：下次部署成功率98%"
    },
    {
      title: "系统健康度",
      value: `${stats.systemHealth}%`,
      change: "+1%",
      changeType: "positive",
      icon: Activity,
      color: "text-emerald-600",
      aiInsight: "AI分析：系统运行状态优秀"
    },
    {
      title: "AI优化建议",
      value: stats.aiRecommendations,
      change: "新增2条",
      changeType: "neutral",
      icon: Sparkles,
      color: "text-purple-600",
      aiInsight: "AI助手：发现性能优化机会"
    }
  ]

  const systemMetrics = [
    { 
      label: "CPU 使用率", 
      value: stats.cpuUsage, 
      icon: Cpu, 
      color: "bg-blue-500",
      aiStatus: "正常",
      aiTrend: "稳定"
    },
    { 
      label: "内存使用率", 
      value: stats.memoryUsage, 
      icon: HardDrive, 
      color: "bg-green-500",
      aiStatus: "良好",
      aiTrend: "优化中"
    },
    { 
      label: "网络流量", 
      value: stats.networkTraffic, 
      icon: Wifi, 
      color: "bg-purple-500",
      aiStatus: "正常",
      aiTrend: "平稳"
    }
  ]

  return (
    <div className="space-y-6">
      {/* AI洞察横幅 */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-blue-50 via-purple-50 to-transparent dark:from-blue-900/20 dark:via-purple-900/20 p-4 rounded-xl border border-blue-200 dark:border-blue-700"
      >
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-blue-100 dark:bg-blue-800 rounded-lg">
            <Bot className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">AI智能洞察</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              系统运行良好，AI检测到3个优化机会，预计可提升15%性能
            </p>
          </div>
          <Button variant="outline" size="sm" className="ml-auto">
            查看详情
          </Button>
        </div>
      </motion.div>

      {/* 增强状态卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statusCards.map((card, index) => {
          const Icon = card.icon
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -4, shadow: "0 10px 25px rgba(0,0,0,0.1)" }}
            >
              <Card className="hover:shadow-xl transition-all duration-300 border-gray-200 dark:border-gray-700 bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                    {card.title}
                  </CardTitle>
                  <div className="relative">
                    <Icon className={`h-4 w-4 ${card.color}`} />
                    {card.icon === Sparkles && (
                      <div className="absolute -top-1 -right-1 w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold mb-1 text-gray-900 dark:text-white">{card.value}</div>
                  <p className={`text-xs mb-2 ${
                    card.changeType === 'positive' ? 'text-green-600' : 
                    card.changeType === 'negative' ? 'text-red-600' : 'text-gray-500'
                  }`}>
                    {card.change} 较上周
                  </p>
                  <div className="text-xs text-blue-700 dark:text-blue-300 bg-blue-50 dark:bg-blue-900/30 px-2 py-1 rounded-md">
                    {card.aiInsight}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* AI增强的系统指标 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm border-gray-200 dark:border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                  <Activity className="h-5 w-5 text-blue-600" />
                  AI系统性能监控
                </CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">实时AI分析的系统资源使用情况</CardDescription>
              </div>
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-700">
                AI监控中
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {systemMetrics.map((metric) => {
              const Icon = metric.icon
              return (
                <div key={metric.label} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Icon className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                      <span className="text-sm font-medium text-gray-900 dark:text-white">{metric.label}</span>
                      <Badge variant="secondary" className="text-xs">
                        {metric.aiStatus}
                      </Badge>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-600 dark:text-gray-400">{metric.value}%</span>
                      <span className="text-xs text-blue-600">{metric.aiTrend}</span>
                    </div>
                  </div>
                  <div className="relative">
                    <Progress value={metric.value} className="h-2" />
                    <div className="absolute top-0 right-0 w-1 h-2 bg-blue-500 rounded-full animate-pulse" />
                  </div>
                </div>
              )
            })}
          </CardContent>
        </Card>

        <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm border-gray-200 dark:border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                  <Clock className="h-5 w-5 text-blue-600" />
                  AI活动分析
                </CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">AI智能分析的系统活动记录</CardDescription>
              </div>
              <Button variant="ghost" size="sm">
                <Bot className="h-4 w-4 mr-1" />
                AI分析
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { action: "智能部署完成", target: "生产环境", time: "2分钟前", status: "success", aiScore: 98 },
                { action: "AI环境优化", target: "测试环境", time: "15分钟前", status: "success", aiScore: 95 },
                { action: "安全扫描", target: "开发环境", time: "1小时前", status: "warning", aiScore: 87 },
                { action: "AI备份优化", target: "数据库", time: "2小时前", status: "success", aiScore: 92 }
              ].map((activity, index) => (
                <motion.div 
                  key={index} 
                  className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  whileHover={{ x: 4 }}
                >
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === 'success' ? 'bg-green-500' :
                    activity.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{activity.action}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{activity.target}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-gray-500 dark:text-gray-400">{activity.time}</span>
                    <div className="text-xs text-blue-600">AI: {activity.aiScore}%</div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI建议和告警 */}
      <div className="space-y-4">
        <Alert className="border-blue-200 bg-blue-50 dark:border-blue-700 dark:bg-blue-900/20">
          <Sparkles className="h-4 w-4 text-blue-600" />
          <AlertTitle className="text-blue-800 dark:text-blue-200">AI智能建议</AlertTitle>
          <AlertDescription className="text-blue-700 dark:text-blue-300">
            检测到开发环境CPU使用率较高，AI建议调整资源配置以优化性能。
            <Button variant="link" className="p-0 h-auto text-blue-600 ml-2">
              应用AI优化方案
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    </div>
  )
}

// AG-UI增强的智能部署组件
const AGUISmartDeployment = () => {
  const [deployments, setDeployments] = useState([
    {
      id: 1,
      name: "ClaudEditor 4.3",
      type: "AI编辑器",
      status: "running",
      environment: "生产环境",
      version: "v4.3.0",
      lastDeploy: "2小时前",
      aiScore: 98,
      health: "excellent"
    },
    {
      id: 2,
      name: "Cloud MCP API",
      type: "后端服务",
      status: "running",
      environment: "生产环境",
      version: "v2.1.0",
      lastDeploy: "1天前",
      aiScore: 95,
      health: "good"
    },
    {
      id: 3,
      name: "AG-UI Dashboard",
      type: "前端界面",
      status: "deploying",
      environment: "测试环境",
      version: "v2.0.0",
      lastDeploy: "进行中",
      aiScore: 92,
      health: "deploying"
    }
  ])

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-100 dark:bg-green-900/30'
      case 'deploying': return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30'
      case 'stopped': return 'text-red-600 bg-red-100 dark:bg-red-900/30'
      case 'warning': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30'
    }
  }

  const getHealthIcon = (health) => {
    switch (health) {
      case 'excellent': return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'good': return <CheckCircle className="h-4 w-4 text-blue-600" />
      case 'warning': return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      case 'deploying': return <Clock className="h-4 w-4 text-blue-600 animate-spin" />
      default: return <AlertTriangle className="h-4 w-4 text-red-600" />
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
            <Cloud className="h-6 w-6 text-blue-600" />
            AI智能部署
          </h2>
          <p className="text-gray-600 dark:text-gray-400">AI驱动的自动化部署管理系统</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" className="flex items-center gap-2">
            <Bot className="h-4 w-4" />
            AI分析
          </Button>
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2">
            <Cloud className="h-4 w-4" />
            一键部署
          </Button>
        </div>
      </div>

      {/* AI洞察横幅 */}
      <Alert className="border-blue-200 bg-blue-50 dark:border-blue-700 dark:bg-blue-900/20">
        <Sparkles className="h-4 w-4 text-blue-600" />
        <AlertTitle className="text-blue-800 dark:text-blue-200">AI部署洞察</AlertTitle>
        <AlertDescription className="text-blue-700 dark:text-blue-300">
          AI检测到3个部署优化机会，预计可提升部署成功率15%，减少部署时间30%。
          <Button variant="link" className="p-0 h-auto text-blue-600 ml-2">
            查看AI建议
          </Button>
        </AlertDescription>
      </Alert>

      {/* 部署统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { title: "活跃部署", value: "8", change: "+2", icon: Cloud, color: "text-blue-600" },
          { title: "成功率", value: "98.5%", change: "+1.2%", icon: CheckCircle, color: "text-green-600" },
          { title: "平均时间", value: "3.2分钟", change: "-0.8分钟", icon: Clock, color: "text-purple-600" },
          { title: "AI优化", value: "15%", change: "+5%", icon: TrendingUp, color: "text-orange-600" }
        ].map((stat, index) => {
          const Icon = stat.icon
          return (
            <motion.div
              key={stat.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm border-gray-200 dark:border-gray-700">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{stat.title}</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-white">{stat.value}</p>
                      <p className="text-xs text-green-600">{stat.change} 较上周</p>
                    </div>
                    <Icon className={`h-8 w-8 ${stat.color}`} />
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </div>

      {/* 部署列表 */}
      <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm border-gray-200 dark:border-gray-700">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
                <Server className="h-5 w-5 text-blue-600" />
                部署管理
              </CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-400">
                AI智能监控的部署状态和性能指标
              </CardDescription>
            </div>
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-700">
              AI监控中
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {deployments.map((deployment) => (
              <motion.div
                key={deployment.id}
                className="p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors cursor-pointer"
                whileHover={{ scale: 1.01 }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      {getHealthIcon(deployment.health)}
                      <div>
                        <h3 className="font-semibold text-gray-900 dark:text-white">{deployment.name}</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{deployment.type}</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Badge className={`${getStatusColor(deployment.status)} border-0`}>
                        {deployment.status === 'running' ? '运行中' : 
                         deployment.status === 'deploying' ? '部署中' : 
                         deployment.status === 'stopped' ? '已停止' : '警告'}
                      </Badge>
                      <span className="text-sm text-gray-600 dark:text-gray-400">{deployment.environment}</span>
                      <span className="text-sm font-mono text-gray-600 dark:text-gray-400">{deployment.version}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-sm text-gray-600 dark:text-gray-400">AI评分</p>
                      <p className="font-semibold text-blue-600">{deployment.aiScore}%</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600 dark:text-gray-400">最后部署</p>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{deployment.lastDeploy}</p>
                    </div>
                    <Button variant="ghost" size="sm">
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 一键部署区域 */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 border-blue-200 dark:border-blue-700">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-3 bg-blue-100 dark:bg-blue-800 rounded-lg">
                <Sparkles className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">AI端云一键部署</h3>
                <p className="text-gray-600 dark:text-gray-400">
                  智能分析最佳部署策略，自动化端到云的完整部署流程
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button variant="outline" className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                配置
              </Button>
              <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white flex items-center gap-2">
                <Zap className="h-4 w-4" />
                启动AI部署
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// AG-UI增强的环境管理组件
const AGUIEnvironmentManagement = () => {
  const [environments, setEnvironments] = useState([
    {
      id: 1,
      name: "生产环境",
      type: "production",
      status: "running",
      resources: { cpu: 75, memory: 68, storage: 45 },
      services: 12,
      lastUpdate: "2小时前",
      aiHealth: 95
    },
    {
      id: 2,
      name: "测试环境",
      type: "testing",
      status: "running",
      resources: { cpu: 45, memory: 52, storage: 30 },
      services: 8,
      lastUpdate: "30分钟前",
      aiHealth: 88
    },
    {
      id: 3,
      name: "开发环境",
      type: "development",
      status: "warning",
      resources: { cpu: 85, memory: 78, storage: 65 },
      services: 6,
      lastUpdate: "1小时前",
      aiHealth: 72
    },
    {
      id: 4,
      name: "预发布环境",
      type: "staging",
      status: "stopped",
      resources: { cpu: 0, memory: 0, storage: 25 },
      services: 0,
      lastUpdate: "1天前",
      aiHealth: 0
    }
  ])

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-100 dark:bg-green-900/30'
      case 'warning': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30'
      case 'stopped': return 'text-red-600 bg-red-100 dark:bg-red-900/30'
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30'
    }
  }

  const getTypeIcon = (type) => {
    switch (type) {
      case 'production': return <Server className="h-5 w-5 text-red-600" />
      case 'testing': return <Monitor className="h-5 w-5 text-blue-600" />
      case 'development': return <Cpu className="h-5 w-5 text-green-600" />
      case 'staging': return <Cloud className="h-5 w-5 text-purple-600" />
      default: return <Server className="h-5 w-5 text-gray-600" />
    }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
            <Server className="h-6 w-6 text-blue-600" />
            AI环境管理
          </h2>
          <p className="text-gray-600 dark:text-gray-400">智能化环境配置和资源管理</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" className="flex items-center gap-2">
            <Bot className="h-4 w-4" />
            AI优化
          </Button>
          <Button className="bg-blue-600 hover:bg-blue-700 flex items-center gap-2">
            <Cloud className="h-4 w-4" />
            创建环境
          </Button>
        </div>
      </div>

      {/* 环境概览卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {environments.map((env, index) => (
          <motion.div
            key={env.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ y: -4 }}
          >
            <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all duration-300">
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    {getTypeIcon(env.type)}
                    <span className="font-semibold text-gray-900 dark:text-white">{env.name}</span>
                  </div>
                  <Badge className={`${getStatusColor(env.status)} border-0 text-xs`}>
                    {env.status === 'running' ? '运行中' : 
                     env.status === 'warning' ? '警告' : '已停止'}
                  </Badge>
                </div>
                
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">服务数量</span>
                    <span className="font-medium text-gray-900 dark:text-white">{env.services}</span>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600 dark:text-gray-400">CPU</span>
                      <span className="text-gray-900 dark:text-white">{env.resources.cpu}%</span>
                    </div>
                    <Progress value={env.resources.cpu} className="h-1" />
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-600 dark:text-gray-400">内存</span>
                      <span className="text-gray-900 dark:text-white">{env.resources.memory}%</span>
                    </div>
                    <Progress value={env.resources.memory} className="h-1" />
                  </div>
                  
                  <div className="flex items-center justify-between text-xs pt-2 border-t border-gray-200 dark:border-gray-700">
                    <span className="text-gray-600 dark:text-gray-400">AI健康度</span>
                    <span className="font-medium text-blue-600">{env.aiHealth}%</span>
                  </div>
                  
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    更新于 {env.lastUpdate}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* AI环境分析 */}
      <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm border-gray-200 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-gray-900 dark:text-white">
            <Bot className="h-5 w-5 text-blue-600" />
            AI环境分析
          </CardTitle>
          <CardDescription className="text-gray-600 dark:text-gray-400">
            AI智能分析环境配置和性能优化建议
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Alert className="border-yellow-200 bg-yellow-50 dark:border-yellow-700 dark:bg-yellow-900/20">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <AlertTitle className="text-yellow-800 dark:text-yellow-200">AI优化建议</AlertTitle>
              <AlertDescription className="text-yellow-700 dark:text-yellow-300">
                开发环境CPU使用率过高(85%)，建议调整资源配置或优化应用性能。
              </AlertDescription>
            </Alert>
            
            <Alert className="border-blue-200 bg-blue-50 dark:border-blue-700 dark:bg-blue-900/20">
              <Sparkles className="h-4 w-4 text-blue-600" />
              <AlertTitle className="text-blue-800 dark:text-blue-200">AI洞察</AlertTitle>
              <AlertDescription className="text-blue-700 dark:text-blue-300">
                预发布环境已停止1天，AI建议定期启动以保持环境同步。
              </AlertDescription>
            </Alert>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// 其他功能组件的占位符
const AGUIMonitoring = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
      <Activity className="h-6 w-6 text-blue-600" />
      AI监控
    </h2>
    <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
      <CardContent className="p-6">
        <p className="text-gray-600 dark:text-gray-400">AI监控功能正在开发中...</p>
      </CardContent>
    </Card>
  </div>
)

const AGUISecurity = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
      <Shield className="h-6 w-6 text-blue-600" />
      安全防护
    </h2>
    <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
      <CardContent className="p-6">
        <p className="text-gray-600 dark:text-gray-400">AI安全防护功能正在开发中...</p>
      </CardContent>
    </Card>
  </div>
)

const AGUIPerformance = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
      <Zap className="h-6 w-6 text-blue-600" />
      性能优化
    </h2>
    <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
      <CardContent className="p-6">
        <p className="text-gray-600 dark:text-gray-400">AI性能优化功能正在开发中...</p>
      </CardContent>
    </Card>
  </div>
)

const AGUIUserManagement = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
      <Users className="h-6 w-6 text-blue-600" />
      用户管理
    </h2>
    <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
      <CardContent className="p-6">
        <p className="text-gray-600 dark:text-gray-400">智能用户管理功能正在开发中...</p>
      </CardContent>
    </Card>
  </div>
)

const AGUISettings = () => (
  <div className="space-y-6">
    <h2 className="text-2xl font-bold flex items-center gap-2 text-gray-900 dark:text-white">
      <Settings className="h-6 w-6 text-blue-600" />
      系统设置
    </h2>
    <Card className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-sm">
      <CardContent className="p-6">
        <p className="text-gray-600 dark:text-gray-400">AI配置助手功能正在开发中...</p>
      </CardContent>
    </Card>
  </div>
)

// 主应用组件
function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [searchQuery, setSearchQuery] = useState('')

  const handleTabChange = (tab) => {
    setActiveTab(tab)
  }

  const handleSearch = (query) => {
    setSearchQuery(query)
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <AGUIDashboard />
      case 'environments':
        return <AGUIEnvironmentManagement />
      case 'deployments':
        return <AGUISmartDeployment />
      case 'monitoring':
        return <AGUIMonitoring />
      case 'security':
        return <AGUISecurity />
      case 'performance':
        return <AGUIPerformance />
      case 'users':
        return <AGUIUserManagement />
      case 'settings':
        return <AGUISettings />
      default:
        return <AGUIDashboard />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-white to-gray-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <AGUISidebar 
        isOpen={sidebarOpen} 
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        activeTab={activeTab}
        onTabChange={handleTabChange}
      />
      
      <div className={`transition-all duration-300 ${sidebarOpen ? 'lg:ml-72' : 'ml-0'}`}>
        <AGUITopBar 
          onMenuToggle={() => setSidebarOpen(!sidebarOpen)}
          onSearch={handleSearch}
        />
        
        <main className="p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}

export default App

