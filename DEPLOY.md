# 部署与更新指南

## 服务器信息

- **公网IP**: 8.148.69.148
- **内网IP**: 172.24.133.196
- **端口**: 5000

## 首次部署

### 1. 上传代码到服务器

```bash
# 方式一：使用scp上传（在本地执行）
scp -r /path/to/paper root@8.148.69.148:/opt/survey

# 方式二：使用git（如果服务器已配置git）
ssh root@8.148.69.148
cd /opt
git clone your-repo survey
```

### 2. 服务器环境配置

```bash
# 登录服务器
ssh root@8.148.69.148

# 进入项目目录
cd /opt/survey

# 安装Python和依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制配置文件
cp env.example .env

# 编辑配置文件
nano .env
```

**必须修改的配置项**：
```bash
# 管理员账号（至少配置一个）
ADMIN_ACCOUNTS=admin:your_password_here

# 安全密钥（必须修改，使用随机字符串）
SECRET_KEY=your_random_secret_key_here

# 服务器地址（使用公网IP）
SERVER_URL=http://8.148.69.148:5000

# 关闭调试模式
DEBUG=False
```

### 4. 初始化数据库

```bash
source venv/bin/activate
python app.py
# 看到启动信息后按Ctrl+C停止
```

### 5. 启动服务

**使用systemd服务（推荐）**：

```bash
# 创建服务文件
sudo nano /etc/systemd/system/survey.service
```

服务文件内容：
```ini
[Unit]
Description=Survey Application
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/opt/survey
Environment="PATH=/opt/survey/venv/bin"
EnvironmentFile=/opt/survey/.env
ExecStart=/opt/survey/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable survey
sudo systemctl start survey

# 检查状态
sudo systemctl status survey
```

## 更新代码

### 方式一：手动更新（推荐用于生产环境）

```bash
# 1. 备份数据库
ssh root@8.148.69.148
cd /opt/survey
cp survey.db survey.db.backup

# 2. 停止服务
sudo systemctl stop survey

# 3. 上传新代码（在本地执行）
# 方式1：使用scp
scp -r /path/to/paper/* root@8.148.69.148:/opt/survey/

# 方式2：使用rsync（推荐，只同步更改的文件）
rsync -avz --exclude 'venv' --exclude 'survey.db' /path/to/paper/ root@8.148.69.148:/opt/survey/

# 4. 在服务器上更新依赖（如果需要）
ssh root@8.148.69.148
cd /opt/survey
source venv/bin/activate
pip install -r requirements.txt

# 5. 检查配置文件（如有变更）
nano .env

# 6. 启动服务
sudo systemctl start survey

# 7. 检查服务状态
sudo systemctl status survey
```

### 方式二：使用Git更新

```bash
# 在服务器上执行
ssh root@8.148.69.148
cd /opt/survey

# 备份数据库
cp survey.db survey.db.backup

# 停止服务
sudo systemctl stop survey

# 拉取最新代码
git pull origin main

# 更新依赖（如果需要）
source venv/bin/activate
pip install -r requirements.txt

# 启动服务
sudo systemctl start survey

# 检查状态
sudo systemctl status survey
```

## 常用命令

### 查看日志

```bash
# 查看服务日志
sudo journalctl -u survey -f

# 查看最近100行日志
sudo journalctl -u survey -n 100
```

### 服务管理

```bash
# 启动服务
sudo systemctl start survey

# 停止服务
sudo systemctl stop survey

# 重启服务
sudo systemctl restart survey

# 查看服务状态
sudo systemctl status survey

# 设置开机自启
sudo systemctl enable survey
```

### 检查端口

```bash
# 检查5000端口是否监听
netstat -tlnp | grep 5000
# 或
ss -tlnp | grep 5000
```

### 防火墙配置

```bash
# 开放5000端口（如果使用iptables）
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables-save

# 或使用firewalld（CentOS/RHEL）
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## 故障排查

### 服务无法启动

1. 检查日志：`sudo journalctl -u survey -n 50`
2. 检查配置文件：`cat /opt/survey/.env`
3. 检查端口占用：`netstat -tlnp | grep 5000`
4. 手动测试：`cd /opt/survey && source venv/bin/activate && python app.py`

### 无法访问

1. 检查防火墙是否开放5000端口
2. 检查服务是否运行：`sudo systemctl status survey`
3. 检查公网IP是否正确：访问 `http://8.148.69.148:5000`

### 数据库问题

```bash
# 备份数据库
cp /opt/survey/survey.db /opt/survey/survey.db.backup

# 检查数据库文件权限
ls -l /opt/survey/survey.db
```

## 注意事项

1. **每次更新前务必备份数据库**
2. **生产环境必须关闭DEBUG模式**
3. **定期备份survey.db文件**
4. **确保.env文件中的SECRET_KEY已修改为随机字符串**
5. **更新代码后检查.env配置文件是否有变更**

