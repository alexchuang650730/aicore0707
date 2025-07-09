import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Settings, 
  Activity, 
  Terminal,
  Code,
  Users,
  Shield,
  Zap
} from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';

// 导入组件
import MirrorToggle, { MirrorStatus } from '../components/MirrorToggle';
import MirrorStatusPanel, { MirrorStats, SyncEvent } from '../components/MirrorStatusPanel';
import ClaudeCLIStatus, { ClaudeCLIStatus as CLIStatus } from '../components/ClaudeCLIStatus';

export interface MirrorCodeLayoutProps {
  className?: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  theme?: 'light' | 'dark' | 'auto';
  compactMode?: boolean;
}

// Mock数据生成器
const generateMockStats = (): MirrorStats => ({
  totalSyncs: 156,
  successfulSyncs: 148,
  failedSyncs: 8,
  successRate: 94.9,
  averageDuration: 2.3,
  totalBytesTransferred: 1024 * 1024 * 45, // 45MB
  uptime: '2天 14小时 32分钟',
  lastSync: new Date(Date.now() - 5 * 60 * 1000).toISOString() // 5分钟前
});

const generateMockEvents = (): SyncEvent[] => [
  {
    id: '1',
    timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    type: 'sync_complete',
    message: '代码同步完成',
    duration: 2.1,
    filesCount: 12,
    bytesTransferred: 1024 * 256,
    status: 'success'
  },
  {
    id: '2',
    timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
    type: 'sync_start',
    message: '开始同步代码变更',
    status: 'info'
  },
  {
    id: '3',
    timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
    type: 'sync_error',
    message: '网络连接超时，同步失败',
    status: 'error'
  },
  {
    id: '4',
    timestamp: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    type: 'status_change',
    message: 'Mirror Code已启用',
    status: 'info'
  }
];

export const MirrorCodeLayout: React.FC<MirrorCodeLayoutProps> = ({
  className,
  position = 'top',
  theme = 'auto',
  compactMode = false
}) => {
  // 状态管理
  const [mirrorStatus, setMirrorStatus] = useState<MirrorStatus>({
    enabled: false,
    syncing: false,
    status: 'disabled',
    syncCount: 0
  });

  const [claudeStatus, setClaudeStatus] = useState<CLIStatus>({
    is_installed: false,
    installation_status: 'not_installed',
    timestamp: new Date().toISOString()
  });

  const [stats, setStats] = useState<MirrorStats>(generateMockStats());
  const [events, setEvents] = useState<SyncEvent[]>(generateMockEvents());
  
  // UI状态
  const [showStatusPanel, setShowStatusPanel] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);

  // 模拟Mirror引擎API
  const mirrorEngineAPI = {
    async toggleMirror(enabled: boolean): Promise<boolean> {
      setIsInitializing(true);
      
      try {
        // 模拟启动过程
        if (enabled) {
          setMirrorStatus(prev => ({ ...prev, status: 'syncing' }));
          
          // 模拟Claude CLI安装检查
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          if (!claudeStatus.is_installed) {
            // 触发Claude CLI安装
            await claudeEngineAPI.installCLI();
          }
          
          // 模拟Mirror启动
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          setMirrorStatus({
            enabled: true,
            syncing: false,
            status: 'enabled',
            syncCount: stats.totalSyncs,
            lastSync: new Date().toISOString()
          });
          
          return true;
        } else {
          setMirrorStatus({
            enabled: false,
            syncing: false,
            status: 'disabled',
            syncCount: 0
          });
          return true;
        }
      } catch (error) {
        setMirrorStatus(prev => ({ 
          ...prev, 
          status: 'error',
          errorMessage: String(error)
        }));
        return false;
      } finally {
        setIsInitializing(false);
      }
    },

    async forceSync(): Promise<boolean> {
      if (!mirrorStatus.enabled) return false;
      
      setMirrorStatus(prev => ({ ...prev, syncing: true }));
      
      try {
        // 模拟同步过程
        await new Promise(resolve => setTimeout(resolve, 3000));
        
        // 添加新的同步事件
        const newEvent: SyncEvent = {
          id: Date.now().toString(),
          timestamp: new Date().toISOString(),
          type: 'sync_complete',
          message: '手动同步完成',
          duration: 3.0,
          filesCount: 8,
          bytesTransferred: 1024 * 128,
          status: 'success'
        };
        
        setEvents(prev => [newEvent, ...prev]);
        setStats(prev => ({
          ...prev,
          totalSyncs: prev.totalSyncs + 1,
          successfulSyncs: prev.successfulSyncs + 1,
          lastSync: new Date().toISOString()
        }));
        
        setMirrorStatus(prev => ({
          ...prev,
          syncing: false,
          syncCount: prev.syncCount + 1,
          lastSync: new Date().toISOString()
        }));
        
        return true;
      } catch (error) {
        setMirrorStatus(prev => ({ ...prev, syncing: false }));
        return false;
      }
    }
  };

  // 模拟Claude CLI API
  const claudeEngineAPI = {
    async installCLI(): Promise<boolean> {
      setClaudeStatus(prev => ({
        ...prev,
        installation_status: 'installing'
      }));
      
      try {
        // 模拟安装过程
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        setClaudeStatus({
          is_installed: true,
          installation_status: 'installed',
          claude_version: '1.0.0',
          timestamp: new Date().toISOString()
        });
        
        return true;
      } catch (error) {
        setClaudeStatus(prev => ({
          ...prev,
          installation_status: 'error',
          installation_error: String(error)
        }));
        return false;
      }
    },

    async reinstallCLI(): Promise<boolean> {
      // 先卸载
      setClaudeStatus(prev => ({
        ...prev,
        is_installed: false,
        installation_status: 'not_installed'
      }));
      
      // 再安装
      return await this.installCLI();
    },

    async testCLI(): Promise<any> {
      if (!claudeStatus.is_installed) {
        return {
          success: false,
          error: 'Claude CLI未安装'
        };
      }
      
      // 模拟测试
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      return {
        success: true,
        message: 'Claude CLI功能正常',
        help_output: 'Claude CLI v1.0.0 - AI助手命令行工具'
      };
    },

    async executeCommand(command: string): Promise<any> {
      if (!claudeStatus.is_installed) {
        return {
          success: false,
          error: 'Claude CLI未安装'
        };
      }
      
      // 模拟命令执行
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      return {
        success: true,
        output: `执行命令: claude ${command}\n命令执行成功`
      };
    }
  };

  // 事件处理器
  const handleToggleMirror = useCallback(async (enabled: boolean) => {
    return await mirrorEngineAPI.toggleMirror(enabled);
  }, []);

  const handleForceSync = useCallback(async () => {
    return await mirrorEngineAPI.forceSync();
  }, []);

  const handleOpenSettings = useCallback(() => {
    setShowSettings(true);
  }, []);

  const handleClearHistory = useCallback(() => {
    setEvents([]);
    toast.success('历史记录已清空');
  }, []);

  const handleExportHistory = useCallback(() => {
    const data = JSON.stringify(events, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mirror-history-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('历史记录已导出');
  }, [events]);

  const handleRefreshStatus = useCallback(() => {
    // 刷新状态数据
    setStats(generateMockStats());
    toast.success('状态已刷新');
  }, []);

  // 布局样式
  const layoutClasses = clsx(
    'mirror-code-layout',
    'bg-white border border-gray-200 rounded-lg shadow-sm',
    {
      'p-2': compactMode,
      'p-4': !compactMode
    },
    className
  );

  const containerClasses = clsx(
    'flex items-center gap-4',
    {
      'flex-row': position === 'top' || position === 'bottom',
      'flex-col': position === 'left' || position === 'right'
    }
  );

  return (
    <div className={layoutClasses}>
      <div className={containerClasses}>
        {/* Mirror Toggle */}
        <MirrorToggle
          status={mirrorStatus}
          onToggle={handleToggleMirror}
          onForceSync={handleForceSync}
          onOpenSettings={handleOpenSettings}
          size={compactMode ? 'sm' : 'md'}
          showLabel={!compactMode}
          showStatus={true}
          disabled={isInitializing}
        />

        {/* 快速操作按钮 */}
        <div className="flex items-center gap-2">
          <motion.button
            onClick={() => setShowStatusPanel(true)}
            className="flex items-center gap-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title="查看状态面板"
          >
            <Activity className="h-4 w-4" />
            {!compactMode && '状态'}
          </motion.button>

          <motion.button
            onClick={() => setShowSettings(true)}
            className="flex items-center gap-1 px-3 py-2 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title="Mirror设置"
          >
            <Settings className="h-4 w-4" />
            {!compactMode && '设置'}
          </motion.button>
        </div>

        {/* Claude CLI状态 (紧凑模式下隐藏) */}
        {!compactMode && (
          <div className="flex-1 max-w-md">
            <ClaudeCLIStatus
              status={claudeStatus}
              onInstall={claudeEngineAPI.installCLI}
              onReinstall={claudeEngineAPI.reinstallCLI}
              onTest={claudeEngineAPI.testCLI}
              onExecuteCommand={claudeEngineAPI.executeCommand}
              showDetails={false}
            />
          </div>
        )}
      </div>

      {/* 状态面板 */}
      <MirrorStatusPanel
        stats={stats}
        events={events}
        isVisible={showStatusPanel}
        onClose={() => setShowStatusPanel(false)}
        onClearHistory={handleClearHistory}
        onExportHistory={handleExportHistory}
        onRefresh={handleRefreshStatus}
      />

      {/* 设置面板 */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center"
            onClick={() => setShowSettings(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-lg shadow-xl p-6 max-w-2xl w-full mx-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Mirror Code 设置</h2>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ✕
                </button>
              </div>
              
              <div className="space-y-6">
                {/* Claude CLI详细状态 */}
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Claude CLI</h3>
                  <ClaudeCLIStatus
                    status={claudeStatus}
                    onInstall={claudeEngineAPI.installCLI}
                    onReinstall={claudeEngineAPI.reinstallCLI}
                    onTest={claudeEngineAPI.testCLI}
                    onExecuteCommand={claudeEngineAPI.executeCommand}
                    showDetails={true}
                  />
                </div>

                {/* 其他设置选项 */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Code className="h-5 w-5 text-blue-600" />
                      <h4 className="font-medium">代码同步</h4>
                    </div>
                    <p className="text-sm text-gray-600">配置代码同步规则和频率</p>
                  </div>

                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Users className="h-5 w-5 text-green-600" />
                      <h4 className="font-medium">协作设置</h4>
                    </div>
                    <p className="text-sm text-gray-600">管理团队协作和权限</p>
                  </div>

                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Shield className="h-5 w-5 text-purple-600" />
                      <h4 className="font-medium">安全设置</h4>
                    </div>
                    <p className="text-sm text-gray-600">配置加密和访问控制</p>
                  </div>

                  <div className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="h-5 w-5 text-orange-600" />
                      <h4 className="font-medium">性能优化</h4>
                    </div>
                    <p className="text-sm text-gray-600">调整性能和资源使用</p>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default MirrorCodeLayout;

