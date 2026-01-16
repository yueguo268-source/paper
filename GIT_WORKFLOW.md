# Git 工作流程指南

本指南将帮助您了解如何将项目上传到 Git 仓库，并在服务器上更新代码。

---

## 目录

1. [本地准备](#本地准备)
2. [上传到远程仓库](#上传到远程仓库)
3. [服务器更新代码](#服务器更新代码)
4. [日常开发流程](#日常开发流程)

---

## 本地准备

### 步骤 1：创建 `.gitignore` 文件

项目已包含 `.gitignore` 文件，会自动排除以下文件：
- 虚拟环境（`venv/`）
- 数据库文件（`*.db`）
- 上传的文件（`uploads/`）
- 环境变量文件（`.env`）
- 日志文件（`*.log`）
- IDE 配置文件等

### 步骤 2：检查当前 Git 状态

```bash
# 查看当前状态
git status

# 查看未跟踪的文件
git status --untracked-files=all
```

### 步骤 3：添加文件到 Git

```bash
# 添加所有文件（.gitignore 中的文件会自动排除）
git add .

# 或者选择性添加
git add app.py
git add requirements.txt
git add templates/
git add static/
# ... 其他需要的文件
```

### 步骤 4：提交更改

```bash
# 提交更改，添加提交信息
git commit -m "初始提交：问卷管理系统"

# 如果有多个文件，可以分批提交
# git add 文件1 文件2
# git commit -m "添加功能说明"
```

---

## 上传到远程仓库

### 方式一：GitHub（推荐）

#### 1. 在 GitHub 上创建仓库

1. 登录 [GitHub](https://github.com)
2. 点击右上角 "+" → "New repository"
3. 填写仓库名称（如 `survey-system`）
4. **不要**勾选 "Initialize this repository with a README"
5. 点击 "Create repository"

#### 2. 添加远程仓库并推送

```bash
# 添加远程仓库（替换 YOUR_USERNAME 和 REPO_NAME）
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 或者使用 SSH（需要配置 SSH 密钥）
# git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git

# 查看远程仓库
git remote -v

# 推送代码到远程仓库（首次推送）
git push -u origin master

# 如果默认分支是 main，使用：
# git push -u origin main
```

#### 3. 如果遇到分支名称问题

```bash
# 如果本地是 master，但远程是 main
git branch -M main
git push -u origin main

# 或者将远程分支重命名
git push -u origin master:main
```

### 方式二：GitLab

```bash
# 1. 在 GitLab 上创建仓库后，添加远程仓库
git remote add origin https://gitlab.com/YOUR_USERNAME/REPO_NAME.git

# 2. 推送代码
git push -u origin master
```

### 方式三：Gitee（码云）

```bash
# 1. 在 Gitee 上创建仓库后，添加远程仓库
git remote add origin https://gitee.com/YOUR_USERNAME/REPO_NAME.git

# 2. 推送代码
git push -u origin master
```

### 推送常见问题

#### 问题 1：需要认证

**GitHub**：
- 使用 Personal Access Token 代替密码
- 生成方式：GitHub → Settings → Developer settings → Personal access tokens → Generate new token
- 权限勾选：`repo`

**GitLab/Gitee**：
- 使用账号密码或 SSH 密钥

#### 问题 2：推送被拒绝

```bash
# 如果远程仓库有内容（如 README），需要先拉取
git pull origin master --allow-unrelated-histories

# 解决冲突后再次推送
git push -u origin master
```

---

## 服务器更新代码

### 方式一：首次部署（克隆仓库）

```bash
# 1. 登录服务器
ssh user@your-server.com

# 2. 进入项目目录（如 /opt/survey）
cd /opt

# 3. 克隆仓库
git clone https://github.com/YOUR_USERNAME/REPO_NAME.git survey

# 或者使用 SSH
# git clone git@github.com:YOUR_USERNAME/REPO_NAME.git survey

# 4. 进入项目目录
cd survey

# 5. 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. 配置环境变量
cp env.example .env
nano .env  # 编辑配置文件

# 7. 初始化数据库
python app.py  # 按 Ctrl+C 停止

# 8. 启动服务（参考 README.md 或 DEPLOYMENT.md）
```

### 方式二：更新已有项目（拉取更新）

```bash
# 1. 登录服务器
ssh user@your-server.com

# 2. 进入项目目录
cd /opt/survey

# 3. 备份数据库（重要！）
cp survey.db survey.db.backup.$(date +%Y%m%d_%H%M%S)

# 4. 拉取最新代码
git pull origin master

# 如果远程分支是 main
# git pull origin main

# 5. 检查是否有依赖更新
source venv/bin/activate
pip install -r requirements.txt

# 6. 重启服务

# 方式 A：如果使用 systemd
sudo systemctl restart survey

# 方式 B：如果使用后台运行
# 先停止：pkill -f "gunicorn.*app:app"
# 再启动：nohup gunicorn -c gunicorn_config.py app:app > app.log 2>&1 &
```

### 方式三：使用脚本自动更新

创建 `update.sh` 脚本：

```bash
#!/bin/bash
# 更新脚本

cd /opt/survey

# 备份数据库
echo "备份数据库..."
cp survey.db survey.db.backup.$(date +%Y%m%d_%H%M%S)

# 拉取代码
echo "拉取最新代码..."
git pull origin master

# 更新依赖
echo "更新依赖..."
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
echo "重启服务..."
sudo systemctl restart survey

echo "更新完成！"
```

使用脚本：

```bash
# 赋予执行权限
chmod +x update.sh

# 运行脚本
./update.sh
```

---

## 日常开发流程

### 本地开发

```bash
# 1. 确保在最新的代码基础上开发
git pull origin master

# 2. 创建新分支（可选，推荐）
git checkout -b feature/新功能名称

# 3. 进行开发...

# 4. 查看更改
git status
git diff

# 5. 添加更改
git add .

# 6. 提交更改
git commit -m "描述您的更改"

# 7. 推送到远程仓库
git push origin master  # 或 git push origin feature/新功能名称

# 8. 如果使用了分支，在 GitHub/GitLab 上创建 Pull Request/Merge Request
```

### 服务器更新流程

```bash
# 1. 登录服务器
ssh user@your-server.com

# 2. 进入项目目录
cd /opt/survey

# 3. 备份数据库
cp survey.db survey.db.backup.$(date +%Y%m%d_%H%M%S)

# 4. 拉取更新
git pull origin master

# 5. 更新依赖（如果 requirements.txt 有变化）
source venv/bin/activate
pip install -r requirements.txt

# 6. 重启服务
sudo systemctl restart survey

# 7. 检查服务状态
sudo systemctl status survey
```

### 推荐的工作流程

1. **开发阶段**（本地）：
   - 修改代码
   - 测试功能
   - 提交并推送到 Git 仓库

2. **部署阶段**（服务器）：
   - 备份数据库
   - 拉取最新代码
   - 更新依赖（如需要）
   - 重启服务
   - 验证功能

3. **回滚**（如果出现问题）：
   ```bash
   # 恢复数据库备份
   cp survey.db.backup.20241203_120000 survey.db
   
   # 回退代码到上一个版本
   git log  # 查看提交历史
   git reset --hard HEAD~1  # 回退一个版本
   # 或回退到特定版本
   # git reset --hard <commit-hash>
   
   # 重启服务
   sudo systemctl restart survey
   ```

---

## 常见问题

### Q1: 如何查看提交历史？

```bash
# 查看提交历史
git log

# 查看简洁的历史
git log --oneline

# 查看最近 5 条提交
git log -5
```

### Q2: 如何撤销本地更改？

```bash
# 撤销未提交的更改（危险！）
git checkout -- 文件名

# 撤销所有未提交的更改
git reset --hard HEAD
```

### Q3: 如何查看远程仓库地址？

```bash
git remote -v
```

### Q4: 如何更改远程仓库地址？

```bash
# 查看当前远程地址
git remote -v

# 更改远程地址
git remote set-url origin https://github.com/NEW_USERNAME/NEW_REPO.git

# 验证更改
git remote -v
```

### Q5: 如何忽略已经提交的文件？

```bash
# 1. 在 .gitignore 中添加文件
echo "文件名" >> .gitignore

# 2. 从 Git 中移除（但保留本地文件）
git rm --cached 文件名

# 3. 提交更改
git commit -m "从 Git 中移除文件"
git push
```

### Q6: 如何处理合并冲突？

```bash
# 1. 拉取代码时如果出现冲突
git pull origin master

# 2. 查看冲突文件
git status

# 3. 编辑冲突文件，解决冲突（删除 <<<<<<, =======, >>>>>>> 标记）

# 4. 标记冲突已解决
git add 文件名

# 5. 完成合并
git commit -m "解决合并冲突"

# 6. 推送
git push
```

---

## 最佳实践

1. **提交前检查**：
   - 确保代码可以正常运行
   - 不要提交敏感信息（密码、密钥等）
   - 确保 `.gitignore` 正确配置

2. **提交信息规范**：
   - 使用清晰的提交信息
   - 例如：`git commit -m "添加用户登录功能"`

3. **定期备份**：
   - 在服务器上更新代码前，始终备份数据库
   - 保留多个备份版本

4. **测试后再部署**：
   - 在本地测试通过后再推送到服务器
   - 在生产环境更新前，可在测试环境先验证

5. **使用分支**：
   - 对于大的功能改动，使用独立分支开发
   - 测试通过后再合并到主分支

---

## 快速参考命令

```bash
# 本地操作
git status                  # 查看状态
git add .                   # 添加所有更改
git commit -m "信息"        # 提交更改
git push origin master      # 推送到远程

# 服务器操作
git pull origin master      # 拉取更新
git log                     # 查看历史
git remote -v               # 查看远程仓库
```

---

**文档版本**: 1.0  
**最后更新**: 2024年12月

