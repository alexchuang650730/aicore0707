import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Terminal, 
  CheckCircle, 
  XCircle, 
  RefreshCw, 
  Download,
  AlertTriangle,
  Play,
  Settings
} from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';

export interface ClaudeCLIStatus {
  is_installed: boolean;
  installation_status: 'not_installed' | 'installing' | 'installed' | 'error';
  claude_version?: string;
  installation_error?: string;
  timestamp: string;
}

export interface ClaudeCLIStatusProps {
  status: ClaudeCLIStatus;
  onInstall: () => Promise<boolean>;
  onReinstall: () => Promise<boolean>;
  onTest: () => Promise<any>;
  onExecuteCommand: (command: string) => Promise<any>;
  className?: string;
  showDetails?: boolean;
}

const statusConfig = {
  not_installed: {
    color: 'text-gray-500',
    bgColor: 'bg-gray-50',
    borderColor: 'border-gray-300',
    icon: Terminal,
    label: '未安装',
    description: 'Claude CLI尚未安装'
  },
  installing: {
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-300',
    icon: RefreshCw,
    label: '安装中',
    description: '正在安装Claude CLI...'
  },
  installed: {
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-300',
    icon: CheckCircle,
    label: '已安装',
    description: 'Claude CLI已成功安装'
  },
  error: {
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-300',
    icon: XCircle,
    label: '错误',
    description: 'Claude CLI安装失败'
  }
};

export const ClaudeCLIStatus: React.FC<ClaudeCLIStatusProps> = ({
  status,
  onInstall,
  onReinstall,
  onTest,
  onExecuteCommand,
  className,
  showDetails = true
}) => {
  const [isOperating, setIsOperating] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [showCommandInput, setShowCommandInput] = useState(false);
  const [commandInput, setCommandInput] = useState('');

  const config = statusConfig[status.installation_status];
  const StatusIcon = config.icon;

  const handleInstall = async () => {
    if (isOperating) return;

    setIsOperating(true);
    try {
      const success = await onInstall();
      if (success) {
        toast.success('Claude CLI安装成功！', { icon: '✅' });
      } else {
        toast.error('Claude CLI安装失败');
      }
    } catch (error) {
      toast.error(`安装失败: ${error}`);
    } finally {
      setIsOperating(false);
    }
  };

  const handleReinstall = async () => {
    if (isOperating) return;

    setIsOperating(true);
    try {
      const success = await onReinstall();
      if (success) {
        toast.success('Claude CLI重新安装成功！', { icon: '✅' });
      } else {
        toast.error('Claude CLI重新安装失败');
      }
    } catch (error) {
      toast.error(`重新安装失败: ${error}`);
    } finally {
      setIsOperating(false);
    }
  };

  const handleTest = async () => {
    if (isOperating || !status.is_installed) return;

    setIsOperating(true);
    try {
      const result = await onTest();
      setTestResult(result);
      
      if (result.success) {
        toast.success('Claude CLI测试通过！', { icon: '✅' });
      } else {
        toast.error(`测试失败: ${result.error}`);
      }
    } catch (error) {
      toast.error(`测试失败: ${error}`);
    } finally {
      setIsOperating(false);
    }
  };

  const handleExecuteCommand = async () => {
    if (!commandInput.trim() || isOperating || !status.is_installed) return;

    setIsOperating(true);
    try {
      const result = await onExecuteCommand(commandInput.trim());
      
      if (result.success) {
        toast.success('命令执行成功！', { icon: '✅' });
        setCommandInput('');
        setShowCommandInput(false);
      } else {
        toast.error(`命令执行失败: ${result.error}`);
      }
    } catch (error) {
      toast.error(`命令执行失败: ${error}`);
    } finally {
      setIsOperating(false);
    }
  };

  return (
    <div className={clsx(
      'rounded-lg border p-4 transition-all duration-200',
      config.bgColor,
      config.borderColor,
      className
    )}>
      {/* 头部状态 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <motion.div
            animate={{ 
              rotate: status.installation_status === 'installing' ? 360 : 0 
            }}
            transition={{ 
              duration: 1, 
              repeat: status.installation_status === 'installing' ? Infinity : 0,
              ease: 'linear'
            }}
          >
            <StatusIcon className={clsx('h-6 w-6', config.color)} />
          </motion.div>
          
          <div>
            <h3 className="font-semibold text-gray-900">Claude CLI</h3>
            <p className={clsx('text-sm', config.color)}>
              {config.label}
              {status.claude_version && ` (v${status.claude_version})`}
            </p>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-2">
          {!status.is_installed && status.installation_status !== 'installing' && (
            <motion.button
              onClick={handleInstall}
              disabled={isOperating}
              className="flex items-center gap-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Download className="h-4 w-4" />
              安装
            </motion.button>
          )}

          {status.is_installed && (
            <>
              <motion.button
                onClick={handleTest}
                disabled={isOperating}
                className="flex items-center gap-1 px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Play className="h-4 w-4" />
                测试
              </motion.button>

              <motion.button
                onClick={handleReinstall}
                disabled={isOperating}
                className="flex items-center gap-1 px-3 py-2 text-sm bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <RefreshCw className="h-4 w-4" />
                重装
              </motion.button>
            </>
          )}
        </div>
      </div>

      {/* 详细信息 */}
      {showDetails && (
        <div className="space-y-3">
          {/* 状态描述 */}
          <p className="text-sm text-gray-600">
            {config.description}
          </p>

          {/* 错误信息 */}
          {status.installation_error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-red-700">
                <p className="font-medium">安装错误:</p>
                <p className="mt-1">{status.installation_error}</p>
              </div>
            </div>
          )}

          {/* 测试结果 */}
          {testResult && (
            <div className={clsx(
              'p-3 border rounded-lg',
              testResult.success 
                ? 'bg-green-50 border-green-200' 
                : 'bg-red-50 border-red-200'
            )}>
              <div className="flex items-start gap-2">
                {testResult.success ? (
                  <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                ) : (
                  <XCircle className="h-4 w-4 text-red-500 mt-0.5" />
                )}
                <div className="text-sm">
                  <p className={clsx(
                    'font-medium',
                    testResult.success ? 'text-green-700' : 'text-red-700'
                  )}>
                    {testResult.success ? '测试通过' : '测试失败'}
                  </p>
                  {testResult.message && (
                    <p className={clsx(
                      'mt-1',
                      testResult.success ? 'text-green-600' : 'text-red-600'
                    )}>
                      {testResult.message}
                    </p>
                  )}
                  {testResult.error && (
                    <p className="mt-1 text-red-600">{testResult.error}</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* 命令执行 */}
          {status.is_installed && (
            <div className="space-y-2">
              <button
                onClick={() => setShowCommandInput(!showCommandInput)}
                className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 transition-colors"
              >
                <Terminal className="h-4 w-4" />
                执行Claude命令
              </button>

              <AnimatePresence>
                {showCommandInput && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-2"
                  >
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={commandInput}
                        onChange={(e) => setCommandInput(e.target.value)}
                        placeholder="输入Claude命令 (例如: --help)"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') {
                            handleExecuteCommand();
                          }
                        }}
                      />
                      <motion.button
                        onClick={handleExecuteCommand}
                        disabled={!commandInput.trim() || isOperating}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 text-sm"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        执行
                      </motion.button>
                    </div>
                    <p className="text-xs text-gray-500">
                      提示: 命令会自动添加 "claude" 前缀
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {/* 安装信息 */}
          <div className="text-xs text-gray-500 space-y-1">
            <p>安装源: https://claude.o3pro.pro/install</p>
            <p>Registry: https://registry.npmmirror.com</p>
            <p>更新时间: {new Date(status.timestamp).toLocaleString('zh-CN')}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClaudeCLIStatus;

