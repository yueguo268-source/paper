# 部署说明文档

> **注意**：本文档为详细部署说明，完整系统文档请参考 `README.md`

## 服务器部署指南

### 一、系统要求

#### 硬件配置建议（3000人并发）
- **CPU**: 4核心或以上
- **内存**: 至少 **2GB**（推荐 4GB）
- **磁盘**: 至少 10GB 可用空间（用于存储问卷数据和文件）
- **网络**: 100Mbps 或以上带宽

#### 内存占用估算
- **基础内存**: ~200MB（Python + Flask）
- **每个并发用户**: ~5-10MB（包括连接、会话、数据处理）
- **数据库缓存**: 128MB（SQLite缓存）
- **3000人并发峰值**: 
  - 假设同时在线1000人（不是所有人同时提交）
  - 内存需求：200MB + (1000 × 8MB) + 128MB ≈ **8.3GB**
  - **实际建议**: 4-8GB内存（考虑到不是所有人同时在线）

#### 实际场景分析
- 3000人通常不会同时在线
- 假设峰值并发为500-800人
- **实际内存需求**: 约 **4-6GB** 即可稳定运行

### 二、部署步骤

#### 1. 上传代码到服务器
```bash
# 使用scp或git上传代码
scp -r /path/to/paper user@server:/opt/survey
# 或使用git
git clone your-repo /opt/survey
```

#### 2. 安装Python和依赖
```bash
cd /opt/survey

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**重要配置项**：
```bash
# 必须修改的配置

# 管理员账号（支持多个管理员）
# 方式1（推荐）：配置多个管理员账号
# 格式：用户名:密码，多个账号用逗号分隔
ADMIN_ACCOUNTS=admin1:your_password_1,admin2:your_password_2,admin3:your_password_3

# 方式2（向后兼容）：如果未设置 ADMIN_ACCOUNTS，使用单个账号
# ADMIN_USER=your_admin_username
# ADMIN_PASS=your_strong_password

SECRET_KEY=generate_a_random_32_char_string
SERVER_URL=http://8.148.69.148:5000

# 生产环境关闭调试
DEBUG=False

# 高并发优化
SQLITE_CACHE_SIZE=-128000  # 128MB缓存
```

#### 4. 初始化数据库
```bash
# 激活虚拟环境后运行
python app.py
# 这会创建数据库文件，然后按Ctrl+C停止
```

#### 5. 使用Gunicorn运行（推荐）

**方式一：直接运行**
```bash
gunicorn -c gunicorn_config.py app:app
```

**方式二：后台运行**
```bash
nohup gunicorn -c gunicorn_config.py app:app > app.log 2>&1 &
```

**方式三：使用systemd服务（推荐）**

创建服务文件 `/etc/systemd/system/survey.service`:
```ini
[Unit]
Description=Survey Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/survey
Environment="PATH=/opt/survey/venv/bin"
EnvironmentFile=/opt/survey/.env
ExecStart=/opt/survey/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable survey
sudo systemctl start survey
sudo systemctl status survey
```

#### 6. 配置Nginx反向代理（可选但推荐）

创建Nginx配置 `/etc/nginx/sites-available/survey`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;  # 允许上传大文件

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/survey /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 三、性能优化建议

#### 1. 数据库优化（针对短期高并发场景）
- SQLite已启用WAL模式，支持高并发读写
- **缓存大小已优化为256MB**（针对短期高并发场景）
- **移除全局锁**：让WAL模式自己处理并发，提高写入性能
- **自动重试机制**：数据库锁定时会自动重试（最多5次，指数退避）
- **优化事务处理**：减少锁持有时间，提高并发能力
- **预期并发能力**：
  - **安全范围**：80-120人同时提交
  - **可接受范围**：120-200人同时提交（可能有1-3秒延迟）
  - **峰值处理**：200-300人同时提交（使用重试机制）
- 如果数据量非常大（>10万条）或需要更高并发，考虑迁移到PostgreSQL

#### 2. Gunicorn Worker数量
```bash
# 计算公式：workers = (2 × CPU核心数) + 1
# 例如4核CPU：workers = 9

# 在.env中设置
GUNICORN_WORKERS=9
```

#### 3. 系统限制调整
```bash
# 增加文件描述符限制
sudo nano /etc/security/limits.conf
# 添加：
* soft nofile 65535
* hard nofile 65535

# 增加系统连接数
sudo nano /etc/sysctl.conf
# 添加：
net.core.somaxconn = 2048
net.ipv4.tcp_max_syn_backlog = 2048
```

### 四、监控和维护

#### 查看日志
```bash
# Gunicorn日志
tail -f app.log

# Systemd服务日志
journalctl -u survey -f

# Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

#### 查看资源使用
```bash
# 查看内存和CPU
htop
# 或
top

# 查看进程
ps aux | grep gunicorn
```

#### 备份数据库
```bash
# 定期备份
cp survey.db survey.db.backup.$(date +%Y%m%d)
```

### 五、故障排查

#### 常见问题

1. **数据库锁定错误**
   - 检查是否有其他进程占用数据库
   - 确保WAL模式已启用
   - 增加DB_TIMEOUT值

2. **内存不足**
   - 减少Gunicorn workers数量
   - 减少SQLite缓存大小
   - 增加服务器内存

3. **连接超时**
   - 检查防火墙设置
   - 增加Nginx超时时间
   - 检查网络带宽

4. **上传文件失败**
   - 检查Nginx的client_max_body_size设置
   - 检查磁盘空间
   - 检查文件权限

### 六、管理员账号配置

#### 多管理员账号配置

系统支持配置多个管理员账号，便于团队协作和权限管理。

**配置方式**：

1. **方式一：使用 ADMIN_ACCOUNTS（推荐）**
   ```bash
   # 在 .env 文件中配置
   ADMIN_ACCOUNTS=admin1:password1,admin2:password2,admin3:password3
   ```
   - 格式：`用户名:密码`，多个账号用逗号分隔
   - 示例：`ADMIN_ACCOUNTS=zhang:pass123,li:pass456,wang:pass789`
   - 所有配置的账号都可以登录管理系统

2. **方式二：使用单个账号（向后兼容）**
   ```bash
   # 如果未设置 ADMIN_ACCOUNTS，则使用以下配置
   ADMIN_USER=admin
   ADMIN_PASS=your_password
   ```

**配置示例**：
```bash
# 示例1：配置3个管理员
ADMIN_ACCOUNTS=admin:Admin@2024,manager:Manager@2024,supervisor:Super@2024

# 示例2：配置多个管理员，使用不同用户名
ADMIN_ACCOUNTS=zhangsan:Zhang123!,lisi:Li456@,wangwu:Wang789#

# 注意：密码中如果包含特殊字符，建议使用引号包裹
ADMIN_ACCOUNTS='admin1:Pass@123,admin2:Pass#456'
```

**注意事项**：
- 用户名和密码区分大小写
- 密码中如果包含逗号或冒号，需要使用引号包裹整个配置
- 建议为每个管理员使用不同的强密码
- 修改配置后需要重启服务才能生效

### 七、安全建议

1. **修改默认密码**：必须修改管理员账号密码
   - 使用 `ADMIN_ACCOUNTS` 配置多个管理员账号（推荐）
   - 格式：`ADMIN_ACCOUNTS=user1:pass1,user2:pass2,user3:pass3`
   - 每个管理员使用强密码，避免使用默认密码
2. **使用HTTPS**：配置SSL证书（Let's Encrypt免费）
3. **防火墙**：只开放必要端口（80, 443, 22）
4. **定期更新**：保持Python和依赖包最新
5. **备份数据**：定期备份数据库文件
6. **管理员账号管理**：
   - 为不同管理员分配不同账号，便于审计
   - 定期更换密码
   - 离职或转岗的管理员账号应及时删除
   - 使用强密码策略（至少8位，包含大小写字母、数字和特殊字符）

### 八、快速启动脚本

创建 `start.sh`:
```bash
#!/bin/bash
cd /opt/survey
source venv/bin/activate
export $(cat .env | xargs)
gunicorn -c gunicorn_config.py app:app
```

创建 `stop.sh`:
```bash
#!/bin/bash
pkill -f "gunicorn.*app:app"
```

### 九、内存使用监控脚本

创建 `check_memory.sh`:
```bash
#!/bin/bash
echo "=== 内存使用情况 ==="
free -h
echo ""
echo "=== Python进程内存 ==="
ps aux | grep -E "gunicorn|python.*app" | grep -v grep
echo ""
echo "=== 数据库大小 ==="
ls -lh survey.db
```

---

## 总结

**3000人并发内存需求**：
- **最低配置**: 4GB内存
- **推荐配置**: 8GB内存
- **实际占用**: 约4-6GB（考虑峰值并发500-800人）

**关键配置**：
- 使用Gunicorn运行（不要直接用Flask开发服务器）
- 配置足够的workers（CPU核心数×2+1）
- SQLite缓存设置为128MB
- 使用Nginx作为反向代理
