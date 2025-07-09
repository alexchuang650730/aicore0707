import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Power, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertCircle,
  Wifi,
  WifiOff,
  Settings
} from 'lucide-react';
import { clsx } from 'clsx';
import toast from 'react-hot-toast';

export interface MirrorStatus {
  enabled: boolean;
  syncing: boolean;
  status: 'disabled' | 'enabled' | 'syncing' | 'error' | 'offline';
  lastSync?: string;
  syncCount: number;
  errorMessage?: string;
}

export interface MirrorToggleProps {
  status: MirrorStatus;
  onToggle: (enabled: boolean) => Promise<boolean>;
  onForceSync: () => Promise<boolean>;
  onOpenSettings: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showStatus?: boolean;
  disabled?: boolean;
}

const statusConfig = {
  disabled: {
    color: 'text-gray-500',
    bgColor: 'bg-gray-100',
    borderColor: 'border-gray-300',
    icon: Power,
    label: '已禁用'
  },
  enabled: {
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-300',
    icon: CheckCircle,
    label: '已启用'
  },
  syncing: {
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-300',
    icon: RefreshCw,
    label: '同步中'
  },
  error: {
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-300',
    icon: XCircle,
    label: '错误'
  },
  offline: {
    color: 'text-orange-600',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-300',
    icon: WifiOff,
    label: '离线'
  }
};

const sizeConfig = {
  sm: {
    toggle: 'h-6 w-11',
    thumb: 'h-5 w-5',
    container: 'p-2',
    text: 'text-sm',
    icon: 'h-4 w-4'
  },
  md: {
    toggle: 'h-7 w-12',
    thumb: 'h-6 w-6',
    container: 'p-3',
    text: 'text-base',
    icon: 'h-5 w-5'
  },
  lg: {
    toggle: 'h-8 w-14',
    thumb: 'h-7 w-7',
    container: 'p-4',
    text: 'text-lg',
    icon: 'h-6 w-6'
  }
};

export const MirrorToggle: React.FC<MirrorToggleProps> = ({
  status,
  onToggle,
  onForceSync,
  onOpenSettings,
  className,
  size = 'md',
  showLabel = true,
  showStatus = true,
  disabled = false
}) => {
  const [isToggling, setIsToggling] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const config = statusConfig[status.status];
  const sizes = sizeConfig[size];
  const StatusIcon = config.icon;

  const handleToggle = useCallback(async () => {
    if (disabled || isToggling) return;

    setIsToggling(true);
    try {
      const success = await onToggle(!status.enabled);
      if (success) {
        toast.success(
          status.enabled ? 'Mirror Code已禁用' : 'Mirror Code已启用',
          {
            icon: status.enabled ? '⭕' : '✅',
            duration: 2000
          }
        );
      } else {
        toast.error('操作失败，请重试');
      }
    } catch (error) {
      toast.error(`操作失败: ${error}`);
    } finally {
      setIsToggling(false);
    }
  }, [status.enabled, onToggle, disabled, isToggling]);

  const handleForceSync = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!status.enabled || status.syncing) return;

    try {
      const success = await onForceSync();
      if (success) {
        toast.success('同步完成', { icon: '✅' });
      } else {
        toast.error('同步失败');
      }
    } catch (error) {
      toast.error(`同步失败: ${error}`);
    }
  }, [status.enabled, status.syncing, onForceSync]);

  const getTooltipText = () => {
    let text = `Mirror Code ${config.label}`;
    if (status.lastSync) {
      text += `\n最后同步: ${status.lastSync}`;
    }
    if (status.syncCount > 0) {
      text += `\n同步次数: ${status.syncCount}`;
    }
    if (status.errorMessage) {
      text += `\n错误: ${status.errorMessage}`;
    }
    return text;
  };

  return (
    <div 
      className={clsx(
        'relative inline-flex items-center gap-3 rounded-lg border transition-all duration-200',
        config.bgColor,
        config.borderColor,
        sizes.container,
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* 主开关 */}
      <button
        onClick={handleToggle}
        disabled={disabled || isToggling}
        className={clsx(
          'relative inline-flex items-center rounded-full border-2 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
          sizes.toggle,
          status.enabled 
            ? 'bg-blue-600 border-blue-600' 
            : 'bg-gray-200 border-gray-300'
        )}
        aria-label={`${status.enabled ? '禁用' : '启用'} Mirror Code`}
      >
        <motion.div
          className={clsx(
            'inline-block rounded-full bg-white shadow transform transition-transform duration-200',
            sizes.thumb
          )}
          animate={{
            x: status.enabled ? '100%' : '0%'
          }}
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
        >
          <div className="flex items-center justify-center h-full">
            <motion.div
              animate={{ rotate: isToggling ? 360 : 0 }}
              transition={{ duration: 0.5 }}
            >
              <StatusIcon 
                className={clsx(
                  sizes.icon,
                  status.enabled ? 'text-blue-600' : 'text-gray-400'
                )}
              />
            </motion.div>
          </div>
        </motion.div>
      </button>

      {/* 状态信息 */}
      {(showLabel || showStatus) && (
        <div className="flex flex-col">
          {showLabel && (
            <span className={clsx('font-medium', config.color, sizes.text)}>
              Mirror Code
            </span>
          )}
          {showStatus && (
            <div className="flex items-center gap-1">
              <motion.div
                animate={{ 
                  rotate: status.syncing ? 360 : 0 
                }}
                transition={{ 
                  duration: 1, 
                  repeat: status.syncing ? Infinity : 0,
                  ease: 'linear'
                }}
              >
                <StatusIcon className={clsx('h-3 w-3', config.color)} />
              </motion.div>
              <span className={clsx('text-xs', config.color)}>
                {config.label}
              </span>
            </div>
          )}
        </div>
      )}

      {/* 快速操作按钮 */}
      <div className="flex items-center gap-1">
        {/* 强制同步按钮 */}
        {status.enabled && (
          <motion.button
            onClick={handleForceSync}
            disabled={status.syncing}
            className={clsx(
              'p-1 rounded-md transition-colors duration-200',
              'hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500',
              status.syncing && 'cursor-not-allowed opacity-50'
            )}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            title="立即同步"
          >
            <motion.div
              animate={{ rotate: status.syncing ? 360 : 0 }}
              transition={{ 
                duration: 1, 
                repeat: status.syncing ? Infinity : 0,
                ease: 'linear'
              }}
            >
              <RefreshCw className="h-4 w-4 text-blue-600" />
            </motion.div>
          </motion.button>
        )}

        {/* 设置按钮 */}
        <motion.button
          onClick={onOpenSettings}
          className="p-1 rounded-md transition-colors duration-200 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          title="Mirror设置"
        >
          <Settings className="h-4 w-4 text-gray-600" />
        </motion.button>
      </div>

      {/* 工具提示 */}
      <AnimatePresence>
        {showTooltip && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg shadow-lg whitespace-pre-line z-50"
          >
            {getTooltipText()}
            <div className="absolute top-full left-1/2 transform -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* 连接状态指示器 */}
      <div className="absolute -top-1 -right-1">
        <motion.div
          className={clsx(
            'h-3 w-3 rounded-full',
            status.status === 'offline' ? 'bg-red-500' : 'bg-green-500'
          )}
          animate={{ 
            scale: status.syncing ? [1, 1.2, 1] : 1 
          }}
          transition={{ 
            duration: 1, 
            repeat: status.syncing ? Infinity : 0 
          }}
        />
      </div>
    </div>
  );
};

export default MirrorToggle;

