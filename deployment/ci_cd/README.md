# aicore0707 CI/CD 配置

## 📋 概述

这个目录包含了aicore0707项目的完整CI/CD配置，支持自动化测试、构建、部署和发布流程。

## 📁 目录结构

```
ci_cd/
├── github_actions/     # GitHub Actions工作流配置
├── scripts/           # CI/CD脚本
├── configs/           # 配置文件
├── templates/         # 模板文件
└── README.md         # 本文档
```

## 🚀 功能特性

### GitHub Actions工作流
- **持续集成**: 自动运行测试和代码质量检查
- **持续部署**: 自动构建和部署到不同环境
- **发布管理**: 自动创建GitHub Releases
- **多平台支持**: Linux, macOS, Windows

### 自动化测试
- **单元测试**: pytest自动化测试
- **集成测试**: 组件间集成测试
- **代码覆盖率**: 测试覆盖率报告
- **性能测试**: 性能基准测试

### 代码质量
- **代码检查**: flake8, pylint代码质量检查
- **安全扫描**: 安全漏洞扫描
- **依赖检查**: 依赖安全性检查
- **文档生成**: 自动生成API文档

### 部署管理
- **环境管理**: 开发、测试、生产环境
- **容器化**: Docker镜像构建和推送
- **版本管理**: 语义化版本控制
- **回滚支持**: 快速回滚机制

## 🔧 使用方法

### 1. 设置GitHub Actions

将`github_actions/`目录中的工作流文件复制到项目根目录的`.github/workflows/`：

```bash
cp -r deployment/ci_cd/github_actions/* .github/workflows/
```

### 2. 配置环境变量

在GitHub仓库设置中添加以下Secrets：

```
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password
DEPLOY_KEY=your_deploy_key
SLACK_WEBHOOK=your_slack_webhook
```

### 3. 运行本地测试

```bash
# 运行所有测试
./deployment/ci_cd/scripts/run_tests.sh

# 代码质量检查
./deployment/ci_cd/scripts/quality_check.sh

# 构建Docker镜像
./deployment/ci_cd/scripts/build_docker.sh
```

## 📊 工作流触发条件

### 持续集成 (CI)
- Push到main分支
- Pull Request创建或更新
- 手动触发

### 持续部署 (CD)
- Tag推送 (v*.*.*)
- Release创建
- 手动触发

### 定时任务
- 每日安全扫描
- 每周依赖更新检查
- 每月性能基准测试

## 🎯 质量门禁

### 合并要求
- ✅ 所有测试通过
- ✅ 代码覆盖率 ≥ 80%
- ✅ 代码质量检查通过
- ✅ 安全扫描无高危漏洞
- ✅ 至少一个代码审查批准

### 发布要求
- ✅ 所有CI检查通过
- ✅ 集成测试通过
- ✅ 性能测试通过
- ✅ 文档更新完成
- ✅ 发布说明准备就绪

## 🔍 监控和通知

### 通知渠道
- **Slack**: 构建状态和部署通知
- **Email**: 失败通知和每日报告
- **GitHub**: PR状态检查和评论

### 监控指标
- **构建成功率**: 目标 ≥ 95%
- **测试覆盖率**: 目标 ≥ 80%
- **部署频率**: 每周至少一次
- **平均修复时间**: 目标 < 4小时

## 📚 相关文档

- [GitHub Actions文档](https://docs.github.com/en/actions)
- [Docker部署指南](./docs/docker_deployment.md)
- [测试策略文档](./docs/testing_strategy.md)
- [发布流程指南](./docs/release_process.md)

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request
5. 等待CI检查通过
6. 代码审查和合并

## 📞 支持

如有问题，请联系：
- **技术支持**: tech-support@aicore0707.com
- **DevOps团队**: devops@aicore0707.com
- **GitHub Issues**: https://github.com/aicore0707/issues

---

*最后更新: 2025年1月*  
*版本: 1.0.0*

