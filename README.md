# 问卷管理系统 - 完整部署与使用手册

> **部署包说明**  
> 本压缩包包含完整的系统代码和配置文件，管理员可以根据本文档独立完成部署。  
> **开始部署前，请先阅读本文档的"快速开始"部分。**

---

## 目录

1. [系统简介](#系统简介)
2. [开始之前](#开始之前)
3. [系统要求](#系统要求)
4. [快速开始](#快速开始)
5. [详细部署步骤](#详细部署步骤)
6. [配置说明](#配置说明)
7. [高并发优化说明](#高并发优化说明)
8. [管理员账号配置](#管理员账号配置)
9. [监控与维护](#监控与维护)
10. [故障排查](#故障排查)
11. [安全建议](#安全建议)

---

## 系统简介

本系统是一个基于 Flask 的问卷收集与管理平台，专为学院长期运行、短期高并发的场景设计。系统支持学生在线提交问卷、上传附件，管理员可以查看、管理和导出所有提交记录。

### 功能特性

**学生端功能**：
- 在线填写问卷（支持多个问题）
- 多文件上传（图片、Word文档等）
- 二维码扫描快速访问
- 提交成功提示

**管理员功能**：
- 多管理员账号支持
- 查看所有提交记录
- 批量删除记录（支持全选）
- 导出功能（全部/图片/文档）
- 文件下载和预览

**系统特性**：
- **高并发优化**：支持80-200人同时提交
- **数据安全**：SQLite数据库，支持WAL模式
- **性能监控**：自动重试机制，确保高成功率
- **易于部署**：一键部署，配置简单

---

## 开始之前

### 部署前准备清单

在开始部署之前，请确保：

- **服务器已准备好**：Linux服务器（推荐Ubuntu 20.04+或CentOS 7+）
- **Python已安装**：Python 3.8 或更高版本
- **有管理员权限**：可以使用 `sudo` 命令
- **网络已配置**：服务器可以访问互联网（用于安装依赖）
- **端口已开放**：5000端口（或您配置的其他端口）已开放

### 需要的信息

部署时需要准备以下信息：

1. **服务器IP地址或域名**
2. **管理员账号和密码**（至少一个）
3. **一个随机密钥**（用于Flask会话加密，建议32位以上）

### 预计部署时间

- **有经验的管理员**：30-60分钟
- **初次部署**：1-2小时

---

## 系统要求

### 硬件配置建议（3000人并发）

- **CPU**: 4核心或以上
- **内存**: 至少 **4GB**（推荐 8GB）
- **磁盘**: 至少 10GB 可用空间（用于存储问卷数据和文件）
- **网络**: 100Mbps 或以上带宽
- **磁盘类型**: SSD推荐（提高数据库I/O性能）

### 内存占用估算

- **基础内存**: ~200MB（Python + Flask）
- **每个并发用户**: ~5-10MB（包括连接、会话、数据处理）
- **数据库缓存**: 256MB（SQLite缓存，针对高并发优化）
- **3000人并发峰值**: 
  - 假设同时在线1000人（不是所有人同时提交）
  - 内存需求：200MB + (1000 × 8MB) + 256MB ≈ **8.5GB**
  - **实际建议**: 4-8GB内存（考虑到不是所有人同时在线）

## 快速开始

### 步骤一：解压并进入项目目录

```bash
# 解压压缩包（假设压缩包名为 paper.zip）
unzip paper.zip
cd paper

# 或者如果使用tar压缩
tar -xzf paper.tar.gz
cd paper
```

### 步骤二：检查Python环境

```bash
# 确保已安装 Python 3.8 或更高版本
python3 --version

# 如果未安装Python，请先安装
# Ubuntu/Debian: sudo apt-get install python3 python3-venv python3-pip
# CentOS/RHEL: sudo yum install python3 python3-pip
```

### 步骤三：创建虚拟环境并安装依赖

```bash
# 创建Python虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# Windows系统使用: venv\Scripts\activate

# 升级pip（可选但推荐）
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

### 步骤四：配置环境变量

```bash
# 复制环境变量模板文件
cp env.example .env

# 编辑配置文件（使用nano、vim或其他文本编辑器）
nano .env
```

**必须修改的配置项**（在.env文件中）：
```bash
# 管理员账号配置（支持多个管理员）
# 格式：用户名:密码，多个账号用逗号分隔
ADMIN_ACCOUNTS=admin1:your_password_1,admin2:your_password_2

# 安全密钥（必须修改！建议使用随机字符串，至少32位）
# 可以使用以下命令生成：python3 -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_random_32_char_string_here

# 服务器访问地址（必须修改为实际服务器地址）
SERVER_URL=http://8.148.69.148:5000

# 生产环境必须关闭调试模式
DEBUG=False
```

**重要提示**：
- `ADMIN_ACCOUNTS`：至少配置一个管理员账号，格式为 `用户名:密码`
- `SECRET_KEY`：必须修改，用于Flask会话加密，建议使用随机生成的32位以上字符串
- `SERVER_URL`：必须修改为实际的服务器访问地址，用于生成二维码

### 步骤五：初始化数据库

```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 运行初始化（这会创建数据库文件）
python app.py

# 看到"访问地址"提示后，按 Ctrl+C 停止程序
# 数据库文件 survey.db 已创建
```

### 步骤六：启动服务

**方式一：使用Gunicorn直接运行（测试用）**
```bash
# 确保虚拟环境已激活
source venv/bin/activate

# 启动服务
gunicorn -c gunicorn_config.py app:app

# 看到启动信息后，服务已运行
# 按 Ctrl+C 可停止服务
```

**方式二：使用systemd服务（生产环境推荐）**

详细步骤请参考"详细部署步骤"章节中的"使用systemd服务"部分。

### 验证部署

1. **检查服务是否运行**：
   ```bash
   # 检查进程
   ps aux | grep gunicorn
   
   # 检查端口
   netstat -tlnp | grep 5000
   # 或使用
   ss -tlnp | grep 5000
   ```

2. **访问系统**：
   - 在浏览器中访问：`http://8.148.69.148:5000`
   - 应该能看到问卷提交页面
   - 访问：`http://8.148.69.148:5000/login` 进行管理员登录测试

3. **检查日志**：
   ```bash
   # 如果有app.log文件
   tail -f app.log
   
   # 或查看systemd日志
   journalctl -u survey -f
   ```

---

## 详细部署步骤

### 一、服务器部署

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

# 安装依赖
pip install -r requirements.txt
```

#### 3. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
nano .env
```

**重要配置项**：
```bash
# 必须修改的配置

# 管理员账号（支持多个管理员）
ADMIN_ACCOUNTS=admin1:your_password_1,admin2:your_password_2,admin3:your_password_3

# 安全密钥（必须修改！）
SECRET_KEY=generate_a_random_32_char_string

# 服务器URL
SERVER_URL=http://8.148.69.148:5000

# 生产环境关闭调试
DEBUG=False

# 高并发优化（针对短期高并发场景）
SQLITE_CACHE_SIZE=-256000  # 256MB缓存
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

---

## 配置说明

### 环境变量配置

完整的环境变量说明请参考 `env.example` 文件。主要配置项：

| 配置项 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `ADMIN_ACCOUNTS` | 管理员账号（格式：user1:pass1,user2:pass2） | - | 是 |
| `SECRET_KEY` | Flask会话密钥 | - | 是 |
| `SERVER_URL` | 服务器访问地址 | - | 是 |
| `DEBUG` | 调试模式 | False | 否 |
| `SQLITE_CACHE_SIZE` | SQLite缓存大小（KB，负值表示MB） | -256000 | 否 |
| `GUNICORN_WORKERS` | Gunicorn worker数量 | CPU核心数×2+1 | 否 |

### Gunicorn Worker数量

```bash
# 计算公式：workers = (2 × CPU核心数) + 1
# 例如4核CPU：workers = 9

# 在.env中设置
GUNICORN_WORKERS=9
```

### 系统限制调整

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

---

## 高并发优化说明

### 优化概述

系统针对**长期运行但短期高并发**的场景进行了专门优化，所有原有功能保持不变。

### 核心优化措施

#### 1. 数据库连接优化

- **移除全局锁**：让 SQLite 的 WAL 模式自己处理并发，大幅提高并发写入性能
- **增加缓存**：从128MB提升到256MB（可通过环境变量调整）
- **内存映射**：256MB内存映射，提高读取性能
- **超时时间**：从30秒增加到60秒（高并发时可能需要更长时间）

#### 2. 提交接口优化

- **文件预处理**：先读取文件到内存（减少数据库锁持有时间）
- **批量插入**：使用 `executemany` 批量插入文件数据
- **自动重试**：最多5次，指数退避策略（0.05s → 0.1s → 0.2s → 0.4s → 0.8s）

#### 3. Gunicorn配置优化

- **连接数**：1000 → 2000
- **超时时间**：120秒 → 180秒
- **Keepalive**：5秒 → 10秒

### 性能提升

| 场景 | 优化前 | 优化后 |
|------|--------|--------|
| 安全范围 | 20-50人 | **80-120人** |
| 可接受范围 | 50-80人 | **120-200人** |
| 峰值处理 | 80-100人 | **200-300人** |

### 响应时间

- **正常情况**：< 1秒
- **高并发时**：1-3秒（自动重试）
- **峰值时**：3-5秒（多次重试）

### 配置建议

```bash
# SQLite缓存大小（针对短期高并发）
SQLITE_CACHE_SIZE=-256000  # 256MB（默认值）
# 如果服务器内存充足（8GB+），可以设置为512MB
# SQLITE_CACHE_SIZE=-512000

# Gunicorn workers（根据CPU核心数调整）
GUNICORN_WORKERS=9  # 4核CPU推荐9个workers
```

---

## 管理员账号配置

### 多管理员账号配置

系统支持配置多个管理员账号，便于团队协作和权限管理。

#### 配置方式

**方式一：使用 ADMIN_ACCOUNTS（推荐）**
```bash
# 在 .env 文件中配置
ADMIN_ACCOUNTS=admin1:password1,admin2:password2,admin3:password3
```
- 格式：`用户名:密码`，多个账号用逗号分隔
- 示例：`ADMIN_ACCOUNTS=zhang:pass123,li:pass456,wang:pass789`
- 所有配置的账号都可以登录管理系统

**方式二：使用单个账号（向后兼容）**
```bash
# 如果未设置 ADMIN_ACCOUNTS，则使用以下配置
ADMIN_USER=admin
ADMIN_PASS=your_password
```

#### 配置示例

```bash
# 示例1：配置3个管理员
ADMIN_ACCOUNTS=admin:Admin@2024,manager:Manager@2024,supervisor:Super@2024

# 示例2：配置多个管理员，使用不同用户名
ADMIN_ACCOUNTS=zhangsan:Zhang123!,lisi:Li456@,wangwu:Wang789#

# 注意：密码中如果包含特殊字符，建议使用引号包裹
ADMIN_ACCOUNTS='admin1:Pass@123,admin2:Pass#456'
```

#### 注意事项

- 用户名和密码区分大小写
- 密码中如果包含逗号或冒号，需要使用引号包裹整个配置
- 建议为每个管理员使用不同的强密码
- 修改配置后需要重启服务才能生效

---

## 监控与维护

### 查看日志

```bash
# Gunicorn日志
tail -f app.log

# Systemd服务日志
journalctl -u survey -f

# Nginx日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 查看资源使用

```bash
# 查看内存和CPU
htop
# 或
top

# 查看进程
ps aux | grep gunicorn
```

### 备份数据库

```bash
# 定期备份
cp survey.db survey.db.backup.$(date +%Y%m%d)
```

### 关键监控指标

1. **数据库锁定错误率**：
   - 正常：< 1%
   - 警告：1-5%
   - 需要优化：> 5%

2. **平均响应时间**：
   - 正常：< 2秒
   - 警告：2-5秒
   - 需要优化：> 5秒

3. **重试次数**：
   - 正常：大部分请求1次成功
   - 警告：较多请求需要2-3次重试
   - 需要优化：大量请求需要4-5次重试

### 监控脚本

创建 `check_status.sh`:
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
echo ""
echo "=== 服务状态 ==="
systemctl status survey --no-pager
```

---

## 故障排查

### 常见问题

#### 1. 数据库锁定错误

**症状**：出现 "database is locked" 错误

**解决方案**：
- 检查是否有其他进程占用数据库
- 确保WAL模式已启用
- 增加DB_TIMEOUT值（已在代码中优化为60秒）
- 检查磁盘I/O性能（使用SSD可以显著改善）

#### 2. 内存不足

**症状**：系统响应变慢，可能出现OOM错误

**解决方案**：
- 减少Gunicorn workers数量
- 减少SQLite缓存大小
- 增加服务器内存
- 检查是否有内存泄漏

#### 3. 连接超时

**症状**：用户无法访问或连接超时

**解决方案**：
- 检查防火墙设置
- 增加Nginx超时时间
- 检查网络带宽
- 检查Gunicorn worker数量是否足够

#### 4. 上传文件失败

**症状**：文件上传失败或超时

**解决方案**：
- 检查Nginx的client_max_body_size设置（建议100M）
- 检查磁盘空间
- 检查文件权限
- 检查网络带宽

#### 5. 高并发时响应慢

**症状**：高并发时响应时间过长

**解决方案**：
- 增加SQLite缓存大小（512MB）
- 增加Gunicorn workers数量
- 使用SSD存储数据库
- 检查服务器CPU和内存使用率

### 故障处理流程

1. **检查服务状态**
   ```bash
   systemctl status survey
   ```

2. **查看错误日志**
   ```bash
   journalctl -u survey -n 100 --no-pager
   tail -f app.log
   ```

3. **检查资源使用**
   ```bash
   htop
   df -h  # 检查磁盘空间
   ```

4. **重启服务**
   ```bash
   sudo systemctl restart survey
   ```

---

## 安全建议

### 1. 账号安全

- **修改默认密码**：必须修改管理员账号密码
- **使用强密码**：至少8位，包含大小写字母、数字和特殊字符
- **多管理员账号**：为不同管理员分配不同账号，便于审计
- **定期更换密码**：建议每3-6个月更换一次
- **及时删除账号**：离职或转岗的管理员账号应及时删除

### 2. 系统安全

- **使用HTTPS**：配置SSL证书（Let's Encrypt免费）
- **防火墙配置**：只开放必要端口（80, 443, 22）
- **定期更新**：保持Python和依赖包最新
- **备份数据**：定期备份数据库文件
- **日志审计**：定期检查访问日志，发现异常访问

### 3. 数据安全

- **定期备份**：建议每天备份数据库
- **备份验证**：定期验证备份文件的完整性
- **异地备份**：重要数据建议异地备份
- **访问控制**：限制管理员账号的访问IP（可选）

### 4. 网络安全

- **使用HTTPS**：加密数据传输
- **限制访问**：使用防火墙限制访问来源
- **DDoS防护**：配置Nginx限流（可选）
- **监控异常**：监控异常访问模式

---

## 快速启动脚本

### 启动脚本

创建 `start.sh`:
```bash
#!/bin/bash
cd /opt/survey
source venv/bin/activate
export $(cat .env | xargs)
gunicorn -c gunicorn_config.py app:app
```

### 停止脚本

创建 `stop.sh`:
```bash
#!/bin/bash
pkill -f "gunicorn.*app:app"
```

### 重启脚本

创建 `restart.sh`:
```bash
#!/bin/bash
./stop.sh
sleep 2
./start.sh
```

---

## 系统总结

### 硬件配置建议

**3000人并发内存需求**：
- **最低配置**: 4GB内存
- **推荐配置**: 8GB内存
- **实际占用**: 约4-6GB（考虑峰值并发500-800人）

### 关键配置

- 使用Gunicorn运行（不要直接用Flask开发服务器）
- 配置足够的workers（CPU核心数×2+1）
- SQLite缓存设置为256MB（针对高并发优化）
- 使用Nginx作为反向代理
- 配置多个管理员账号
- 定期备份数据库

### 性能指标

- **并发能力**：80-200人同时提交
- **响应时间**：正常<1秒，高并发1-3秒
- **成功率**：自动重试机制确保高成功率

### 技术支持

如遇到问题，请检查：
1. 日志文件（app.log 或 systemd日志）
2. 服务器资源使用情况
3. 数据库状态
4. 网络连接

---

## 附录

### 文件结构

```
survey_system/
├── app.py                    # 主应用文件
├── requirements.txt          # Python依赖
├── gunicorn_config.py        # Gunicorn配置
├── env.example              # 环境变量模板
├── README.md                # 本文档
├── survey.db                # SQLite数据库（运行后生成）
├── templates/               # HTML模板
│   ├── survey.html          # 问卷页面
│   ├── login.html           # 登录页面
│   ├── records.html         # 记录管理页面
│   └── thankyou.html        # 提交成功页面
└── static/                  # 静态文件
    └── uploads/             # 上传文件目录
```

### 主要依赖

- Flask 3.0.0
- qrcode 7.4.2
- gunicorn 21.2.0
- Werkzeug 3.0.1

### 版本信息

- Python版本要求：3.8+
- 数据库：SQLite 3（支持WAL模式）
- Web服务器：Gunicorn + Nginx（推荐）

---

**文档版本**: 1.0  
**最后更新**: 2024年  
**维护者**: 系统管理员
