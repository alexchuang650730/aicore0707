# GitHub Release Commands
# 请确保已安装GitHub CLI (gh)

# 1. 登录GitHub (如果尚未登录)
gh auth login

# 2. 创建远程仓库 (如果不存在)
gh repo create claudeditor/claudeditor-4.5 --public --description 'ClaudeEditor 4.5 with Mirror Code'

# 3. 添加远程仓库
git remote add origin https://github.com/claudeditor/claudeditor-4.5.git

# 4. 推送代码和标签
git push -u origin main
git push origin v4.5.0

# 5. 创建Release
gh release create v4.5.0 \
  --title 'ClaudeEditor 4.5.0 + Mirror Code' \
  --notes-file RELEASE_NOTES_v4.5_MIRROR.md \
  --latest

# 6. 上传发布包
gh release upload v4.5.0 \
  ../claudeditor-4.5-mirror-code-release.tar.gz \
  --clobber

# 7. 验证Release
gh release view v4.5.0