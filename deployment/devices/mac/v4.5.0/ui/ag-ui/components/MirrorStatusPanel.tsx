import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AgGridReact } from 'ag-grid-react';
import { ColDef, GridReadyEvent } from 'ag-grid-community';
import {
  Activity,
  Clock,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Download,
  Trash2,
  Filter,
  Search
} from 'lucide-react';
import { clsx } from 'clsx';

export interface SyncEvent {
  id: string;
  timestamp: string;
  type: 'sync_start' | 'sync_complete' | 'sync_error' | 'status_change';
  message: string;
  duration?: number;
  filesCount?: number;
  bytesTransferred?: number;
  status: 'success' | 'error' | 'info';
}

export interface MirrorStats {
  totalSyncs: number;
  successfulSyncs: number;
  failedSyncs: number;
  successRate: number;
  averageDuration: number;
  totalBytesTransferred: number;
  uptime: string;
  lastSync?: string;
}

export interface MirrorStatusPanelProps {
  stats: MirrorStats;
  events: SyncEvent[];
  isVisible: boolean;
  onClose: () => void;
  onClearHistory: () => void;
  onExportHistory: () => void;
  onRefresh: () => void;
  className?: string;
}

const StatusIcon: React.FC<{ status: string; className?: string }> = ({ status, className }) => {
  const icons = {
    success: CheckCircle,
    error: XCircle,
    info: RefreshCw
  };
  
  const Icon = icons[status as keyof typeof icons] || RefreshCw;
  const colors = {
    success: 'text-green-500',
    error: 'text-red-500',
    info: 'text-blue-500'
  };
  
  return <Icon className={clsx(colors[status as keyof typeof colors], className)} />;
};

const StatCard: React.FC<{
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: number;
  color?: string;
}> = ({ title, value, icon, trend, color = 'blue' }) => {
  return (
    <motion.div
      className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm"
      whileHover={{ scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={clsx('text-2xl font-bold', `text-${color}-600`)}>
            {value}
          </p>
          {trend !== undefined && (
            <div className="flex items-center mt-1">
              <TrendingUp className={clsx(
                'h-4 w-4 mr-1',
                trend >= 0 ? 'text-green-500' : 'text-red-500'
              )} />
              <span className={clsx(
                'text-sm',
                trend >= 0 ? 'text-green-600' : 'text-red-600'
              )}>
                {trend >= 0 ? '+' : ''}{trend}%
              </span>
            </div>
          )}
        </div>
        <div className={clsx('p-3 rounded-full', `bg-${color}-100`)}>
          {icon}
        </div>
      </div>
    </motion.div>
  );
};

export const MirrorStatusPanel: React.FC<MirrorStatusPanelProps> = ({
  stats,
  events,
  isVisible,
  onClose,
  onClearHistory,
  onExportHistory,
  onRefresh,
  className
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [gridApi, setGridApi] = useState<any>(null);

  const columnDefs: ColDef[] = [
    {
      headerName: '状态',
      field: 'status',
      width: 80,
      cellRenderer: (params: any) => (
        <StatusIcon status={params.value} className="h-4 w-4" />
      )
    },
    {
      headerName: '时间',
      field: 'timestamp',
      width: 150,
      valueFormatter: (params) => {
        return new Date(params.value).toLocaleString('zh-CN');
      }
    },
    {
      headerName: '类型',
      field: 'type',
      width: 120,
      valueFormatter: (params) => {
        const typeMap = {
          sync_start: '开始同步',
          sync_complete: '同步完成',
          sync_error: '同步错误',
          status_change: '状态变更'
        };
        return typeMap[params.value as keyof typeof typeMap] || params.value;
      }
    },
    {
      headerName: '消息',
      field: 'message',
      flex: 1,
      minWidth: 200
    },
    {
      headerName: '耗时',
      field: 'duration',
      width: 100,
      valueFormatter: (params) => {
        return params.value ? `${params.value}s` : '-';
      }
    },
    {
      headerName: '文件数',
      field: 'filesCount',
      width: 100,
      valueFormatter: (params) => {
        return params.value || '-';
      }
    },
    {
      headerName: '传输量',
      field: 'bytesTransferred',
      width: 120,
      valueFormatter: (params) => {
        if (!params.value) return '-';
        const bytes = params.value;
        if (bytes < 1024) return `${bytes}B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
      }
    }
  ];

  const filteredEvents = events.filter(event => {
    const matchesSearch = event.message.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterType === 'all' || event.type === filterType;
    return matchesSearch && matchesFilter;
  });

  const onGridReady = (params: GridReadyEvent) => {
    setGridApi(params.api);
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)}GB`;
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, x: 300 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 300 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className={clsx(
            'fixed right-0 top-0 h-full w-96 bg-white shadow-2xl border-l border-gray-200 z-50 overflow-hidden',
            className
          )}
        >
          {/* 头部 */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-600" />
              <h2 className="text-lg font-semibold text-gray-900">Mirror状态</h2>
            </div>
            <div className="flex items-center gap-2">
              <motion.button
                onClick={onRefresh}
                className="p-2 rounded-md hover:bg-gray-200 transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title="刷新"
              >
                <RefreshCw className="h-4 w-4 text-gray-600" />
              </motion.button>
              <motion.button
                onClick={onClose}
                className="p-2 rounded-md hover:bg-gray-200 transition-colors"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title="关闭"
              >
                <XCircle className="h-4 w-4 text-gray-600" />
              </motion.button>
            </div>
          </div>

          {/* 统计卡片 */}
          <div className="p-4 space-y-3 border-b border-gray-200">
            <div className="grid grid-cols-2 gap-3">
              <StatCard
                title="成功率"
                value={`${stats.successRate}%`}
                icon={<CheckCircle className="h-6 w-6 text-green-600" />}
                color="green"
              />
              <StatCard
                title="总同步"
                value={stats.totalSyncs}
                icon={<RefreshCw className="h-6 w-6 text-blue-600" />}
                color="blue"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <StatCard
                title="平均耗时"
                value={`${stats.averageDuration}s`}
                icon={<Clock className="h-6 w-6 text-orange-600" />}
                color="orange"
              />
              <StatCard
                title="传输量"
                value={formatBytes(stats.totalBytesTransferred)}
                icon={<TrendingUp className="h-6 w-6 text-purple-600" />}
                color="purple"
              />
            </div>
            
            {/* 运行时间 */}
            <div className="bg-blue-50 rounded-lg p-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-blue-900">运行时间</span>
                <span className="text-lg font-bold text-blue-600">{stats.uptime}</span>
              </div>
              {stats.lastSync && (
                <div className="mt-1 text-xs text-blue-700">
                  最后同步: {new Date(stats.lastSync).toLocaleString('zh-CN')}
                </div>
              )}
            </div>
          </div>

          {/* 搜索和过滤 */}
          <div className="p-4 border-b border-gray-200 space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="搜索事件..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">所有事件</option>
                <option value="sync_complete">同步完成</option>
                <option value="sync_error">同步错误</option>
                <option value="status_change">状态变更</option>
              </select>
            </div>
          </div>

          {/* 事件列表 */}
          <div className="flex-1 overflow-hidden">
            <div className="h-full ag-theme-alpine">
              <AgGridReact
                columnDefs={columnDefs}
                rowData={filteredEvents}
                onGridReady={onGridReady}
                defaultColDef={{
                  sortable: true,
                  filter: true,
                  resizable: true
                }}
                animateRows={true}
                rowSelection="multiple"
                suppressRowClickSelection={true}
                getRowStyle={(params) => {
                  if (params.data.status === 'error') {
                    return { backgroundColor: '#fef2f2' };
                  }
                  if (params.data.status === 'success') {
                    return { backgroundColor: '#f0fdf4' };
                  }
                  return {};
                }}
              />
            </div>
          </div>

          {/* 底部操作 */}
          <div className="p-4 border-t border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">
                共 {filteredEvents.length} 条记录
              </span>
              <div className="flex items-center gap-2">
                <motion.button
                  onClick={onExportHistory}
                  className="flex items-center gap-1 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Download className="h-4 w-4" />
                  导出
                </motion.button>
                <motion.button
                  onClick={onClearHistory}
                  className="flex items-center gap-1 px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Trash2 className="h-4 w-4" />
                  清空
                </motion.button>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default MirrorStatusPanel;

