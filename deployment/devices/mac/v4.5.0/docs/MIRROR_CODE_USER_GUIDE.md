# Mirror Code 用户指南

## 📖 目录
1. [快速开始](#快速开始)
2. [功能概述](#功能概述)
3. [用户界面](#用户界面)
4. [配置设置](#配置设置)
5. [高级功能](#高级功能)
6. [故障排除](#故障排除)
7. [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 第一次使用Mirror Code

1. **启动ClaudeEditor 4.5**
   - 打开ClaudeEditor应用程序
   - 确保您有稳定的网络连接

2. **启用Mirror Code**
   - 在工具栏找到Mirror Code开关
   - 点击开关启用功能
   - 系统将自动开始安装Claude CLI

3. **等待自动配置**
   - 安装过程大约需要2-5分钟
   - 您可以在状态指示器中查看进度
   - 安装完成后会显示绿色的"已启用"状态

4. **开始使用**
   - 编辑您的代码文件
   - Mirror Code会自动同步您的更改
   - 查看状态面板了解同步详情

### 系统要求

- **Node.js**: 18.0或更高版本
- **网络连接**: 稳定的互联网连接
- **存储空间**: 至少500MB可用空间
- **权限**: 管理员权限（用于安装Claude CLI）

---

## 🔄 功能概述

### 核心功能

#### **实时代码同步**
- 自动检测代码文件变更
- 实时同步到配置的镜像位置
- 支持增量同步，只传输变更部分
- 智能冲突检测和解决

#### **多平台支持**
- **本地镜像**: 同步到本地不同目录
- **远程服务器**: 通过SSH同步到远程服务器
- **云存储**: 支持主流云存储服务
- **版本控制**: 集成Git等版本控制系统

#### **协作编辑**
- 多人实时协作编辑
- 冲突自动检测和标记
- 变更历史追踪
- 用户权限管理

#### **智能备份**
- 自动创建代码备份
- 版本历史管理
- 快速恢复功能
- 定期清理旧备份

---

## 🎛️ 用户界面

### Mirror Toggle (开关组件)

#### **状态指示**
- 🔴 **禁用**: Mirror Code功能关闭
- 🟢 **启用**: 功能正常运行
- 🔵 **同步中**: 正在执行同步操作
- 🟠 **离线**: 网络连接问题
- 🔴 **错误**: 发生错误需要处理

#### **快速操作**
- **立即同步**: 手动触发同步操作
- **设置**: 打开配置面板
- **历史**: 查看同步历史记录

### Status Panel (状态面板)

#### **统计信息**
- **成功率**: 同步操作的成功百分比
- **总同步**: 累计同步次数
- **平均耗时**: 每次同步的平均时间
- **传输量**: 累计传输的数据量
- **运行时间**: Mirror Code的运行时长

#### **事件日志**
- **时间戳**: 每个事件的精确时间
- **事件类型**: 同步开始、完成、错误等
- **详细信息**: 包含文件数量、传输量等
- **状态**: 成功、失败、警告

#### **操作功能**
- **搜索**: 在事件日志中搜索特定内容
- **过滤**: 按事件类型过滤显示
- **导出**: 将历史记录导出为JSON文件
- **清空**: 清除所有历史记录

### Settings Panel (设置面板)

#### **常规设置**
- **自动同步**: 启用/禁用自动同步
- **同步间隔**: 设置自动同步的时间间隔
- **保存时同步**: 文件保存时立即同步
- **启动时同步**: 应用启动时执行同步

#### **镜像目标**
- **本地目录**: 配置本地镜像目录
- **远程服务器**: SSH连接配置
- **云存储**: 云服务认证和配置
- **版本控制**: Git仓库集成设置

#### **高级选项**
- **文件过滤**: 设置要同步的文件类型
- **排除规则**: 配置不同步的文件或目录
- **压缩设置**: 启用/禁用传输压缩
- **并发数**: 设置并发同步的文件数量

#### **安全设置**
- **加密传输**: 启用端到端加密
- **访问控制**: 配置用户权限
- **审计日志**: 启用操作审计记录
- **备份加密**: 本地备份文件加密

---

## ⚙️ 配置设置

### 基础配置

#### **启用Mirror Code**
```yaml
mirror_code:
  enabled: true
  auto_sync: true
  sync_interval: 5  # 秒
```

#### **文件同步设置**
```yaml
sync_settings:
  max_file_size: 10485760  # 10MB
  compression: true
  encryption: true
  include_patterns:
    - "*.js"
    - "*.py"
    - "*.md"
  exclude_patterns:
    - "node_modules/"
    - ".git/"
    - "*.log"
```

### 镜像目标配置

#### **本地目录镜像**
```yaml
local_mirror:
  enabled: true
  target_directory: "/Users/username/code-mirror"
  create_subdirs: true
  preserve_structure: true
```

#### **远程服务器镜像**
```yaml
remote_mirror:
  enabled: true
  host: "your-server.com"
  port: 22
  username: "your-username"
  key_file: "~/.ssh/id_rsa"
  remote_path: "/home/username/code-mirror"
```

#### **云存储镜像**
```yaml
cloud_mirror:
  enabled: true
  provider: "aws_s3"  # aws_s3, google_drive, dropbox
  bucket: "your-bucket-name"
  access_key: "your-access-key"
  secret_key: "your-secret-key"
  region: "us-west-2"
```

### 高级配置

#### **性能优化**
```yaml
performance:
  max_concurrent_syncs: 5
  retry_attempts: 3
  retry_delay: 1000  # 毫秒
  timeout: 30000     # 毫秒
  buffer_size: 65536 # 64KB
```

#### **安全配置**
```yaml
security:
  encryption_algorithm: "AES-256-GCM"
  key_derivation: "PBKDF2"
  salt_length: 32
  iteration_count: 100000
  verify_certificates: true
```

---

## 🔧 高级功能

### 冲突解决

#### **自动解决策略**
- **最新优先**: 使用最新修改的版本
- **本地优先**: 优先保留本地版本
- **远程优先**: 优先使用远程版本
- **手动解决**: 提示用户手动选择

#### **冲突标记**
```javascript
<<<<<<< LOCAL
// 本地版本的代码
function localFunction() {
    return "local";
}
=======
// 远程版本的代码
function remoteFunction() {
    return "remote";
}
>>>>>>> REMOTE
```

### 版本历史

#### **查看历史版本**
1. 右键点击文件
2. 选择"Mirror Code" > "版本历史"
3. 浏览不同时间点的版本
4. 选择要恢复的版本

#### **比较版本**
- 并排显示不同版本
- 高亮显示差异
- 支持行级和字符级比较
- 可以选择性合并更改

### 协作功能

#### **实时协作**
- 多用户同时编辑
- 实时显示其他用户的光标位置
- 变更实时同步到所有用户
- 用户在线状态显示

#### **权限管理**
- **只读**: 只能查看，不能编辑
- **编辑**: 可以编辑和同步
- **管理**: 可以管理设置和权限
- **所有者**: 完全控制权限

---

## 🔍 故障排除

### 常见问题

#### **Claude CLI安装失败**

**问题**: 安装过程中出现错误
**解决方案**:
1. 检查网络连接
2. 确保有管理员权限
3. 检查npm是否正确安装
4. 尝试手动安装：
   ```bash
   sudo npm install -g https://claude.o3pro.pro/install --registry=https://registry.npmmirror.com
   ```

#### **同步失败**

**问题**: 文件同步不成功
**解决方案**:
1. 检查网络连接
2. 验证目标路径权限
3. 检查文件大小限制
4. 查看错误日志获取详细信息

#### **性能问题**

**问题**: 同步速度慢
**解决方案**:
1. 启用压缩传输
2. 减少并发同步数量
3. 排除大文件或不必要的文件
4. 检查网络带宽

#### **权限错误**

**问题**: 无法访问某些文件或目录
**解决方案**:
1. 检查文件权限设置
2. 确保应用有足够权限
3. 在macOS上检查隐私设置
4. 在Windows上以管理员身份运行

### 日志和调试

#### **启用调试模式**
```yaml
debug:
  enabled: true
  log_level: "DEBUG"
  log_file: "mirror_code_debug.log"
  verbose_sync: true
```

#### **查看日志文件**
- **位置**: `~/.claudeditor/logs/mirror_code.log`
- **格式**: JSON格式，包含时间戳和详细信息
- **轮转**: 自动轮转，保留最近7天的日志

#### **常用调试命令**
```bash
# 检查Claude CLI状态
claude --version

# 测试网络连接
ping your-server.com

# 检查SSH连接
ssh -T user@your-server.com

# 查看系统资源使用
top -p $(pgrep claudeditor)
```

---

## 💡 最佳实践

### 文件组织

#### **项目结构建议**
```
project/
├── src/           # 源代码文件
├── docs/          # 文档文件
├── tests/         # 测试文件
├── config/        # 配置文件
└── .mirrorignore  # Mirror忽略文件
```

#### **.mirrorignore文件**
```
# 依赖目录
node_modules/
venv/
.venv/

# 构建输出
dist/
build/
*.min.js

# 日志文件
*.log
logs/

# 临时文件
*.tmp
*.temp
.DS_Store
```

### 性能优化

#### **文件过滤策略**
- 只同步源代码文件
- 排除编译输出和依赖
- 使用文件大小限制
- 定期清理不需要的文件

#### **网络优化**
- 使用压缩传输
- 配置合适的并发数
- 选择就近的服务器
- 避免在网络繁忙时同步

#### **存储优化**
- 定期清理历史版本
- 使用增量备份
- 压缩存储的备份文件
- 监控磁盘空间使用

### 安全建议

#### **访问控制**
- 使用强密码和密钥
- 定期更换访问凭证
- 限制网络访问范围
- 启用双因素认证

#### **数据保护**
- 启用端到端加密
- 定期备份重要数据
- 使用安全的传输协议
- 监控异常访问活动

#### **隐私保护**
- 不同步敏感信息
- 使用环境变量存储密钥
- 定期审查同步内容
- 遵守数据保护法规

### 团队协作

#### **工作流建议**
1. **项目初始化**: 团队负责人设置Mirror Code配置
2. **成员加入**: 新成员获取访问权限和配置
3. **日常开发**: 使用自动同步进行日常开发
4. **冲突解决**: 及时解决同步冲突
5. **版本管理**: 结合Git等版本控制系统

#### **沟通协调**
- 建立同步时间约定
- 使用注释说明重要更改
- 定期同步团队配置
- 及时通知重大变更

---

## 📚 相关资源

### 文档链接
- [API文档](https://docs.claudeditor.com/api)
- [开发者指南](https://docs.claudeditor.com/dev)
- [插件开发](https://docs.claudeditor.com/plugins)
- [故障排除](https://docs.claudeditor.com/troubleshooting)

### 社区资源
- [用户论坛](https://forum.claudeditor.com)
- [GitHub仓库](https://github.com/claudeditor/claudeditor)
- [示例项目](https://github.com/claudeditor/examples)
- [视频教程](https://youtube.com/claudeditor)

### 技术支持
- **邮件**: support@claudeditor.com
- **在线聊天**: 工作日9:00-18:00
- **电话**: +1-800-CLAUDE-ED
- **紧急支持**: emergency@claudeditor.com

---

**感谢使用ClaudeEditor Mirror Code！**

如果您有任何问题或建议，请随时联系我们。我们致力于为您提供最好的代码编辑和同步体验。

---

*最后更新: 2025年1月*  
*版本: 4.5.0*

