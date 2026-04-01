# RDGen 汉化版部署教程

RDGen 是一个用于生成 RustDesk 自定义客户端的工具，本版本已完整汉化。

## 前置要求

1. Python 3.10 或更高版本
2. Git
3. GitHub 账号（需要 Fork 本仓库）
4. GitHub Fine-grained Access Token（用于触发 GitHub Actions）

## 方式一：Docker 部署（推荐）

### 1. Fork 仓库

在 GitHub 上 Fork 本仓库到你的账号。

### 2. 配置 GitHub Fine-grained Access Token

1. 登录 GitHub 账号
2. 点击右上角头像 → Settings
3. 左侧底部点击 Developer Settings
4. 点击 Personal access tokens → Fine-grained tokens
5. 点击 Generate new token
6. 设置 Token 名称和过期时间
7. 在 Repository access 中选择 Only select repositories，选择你的 rdgen 仓库
8. 授予 Actions 和 Workflows 的 Read and Write 权限
9. 访问 `https://github.com/你的用户名/rdgen/actions` 并点击绿色 Enable Actions 按钮

### 3. 配置 GitHub Secrets

1. 进入你的 rdgen 仓库页面
2. 点击 Settings → Secrets and variables → Actions
3. 点击 New repository secret，添加以下密钥：
   - **GENURL**: 你的服务器访问地址（如：`https://rdgen.example.com`）
   - **ZIP_PASSWORD**: 生成密码（运行：`python3 -c 'import secrets; print(secrets.token_hex(100))'`）

### 4. 配置 Docker Compose

编辑 `docker-compose.yml` 文件，填写以下环境变量：

```yaml
services:
  rdgen:
    image: bryangerlach/rdgen:latest
    restart: unless-stopped
    environment:
      SECRET_KEY: "你的密钥"  # 运行: python3 -c 'import secrets; print(secrets.token_hex(100))'
      GHUSER: "你的GitHub用户名"
      GHBEARER: "你的Fine-grained Access Token"
      GENURL: "你的服务器访问地址"
      ZIP_PASSWORD: "与GitHub Secret中相同的密码"
      GHBRANCH: "master"
      PROTOCOL: "https"  # 或 "http"
      REPONAME: "rdgen"  # 如果重命名了仓库，请修改此项
    ports:
      - "8000:8000"
```

### 5. 启动服务

```bash
docker compose up -d
```

### 6. 访问服务

在浏览器中访问：`http://你的服务器IP:8000` 或配置反向代理后的域名。

## 方式二：手动部署

### 1. Fork 仓库并配置 GitHub Token

参考方式一的步骤 1-2。

### 2. 克隆仓库

```bash
cd /opt  # 或你选择的安装目录
git clone https://github.com/你的用户名/rdgen.git
cd rdgen
```

### 3. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 Windows: .venv\Scripts\activate
```

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

### 5. 配置环境变量

设置以下环境变量：

```bash
export GHUSER="你的GitHub用户名"
export GHBEARER="你的Fine-grained Access Token"
export PROTOCOL="https"  # 或 "http"
export REPONAME="rdgen"  # 如果重命名了仓库，请修改
```

### 6. 配置 GitHub Secrets

在 GitHub 仓库中设置 Secrets：
- **GENURL**: 你的服务器访问地址和端口（如：`example.com:8000`）

### 7. 初始化数据库

```bash
python manage.py migrate
```

### 8. 启动服务

```bash
python manage.py runserver 0.0.0.0:8000
```

### 9. 配置反向代理（可选）

使用 Nginx、Caddy 或 Traefik 配置 SSL 反向代理。

## 配置 Systemd 服务（自动启动）

创建 `/etc/systemd/system/rdgen.service` 文件：

```ini
[Unit]
Description=Rustdesk Client Generator
[Service]
Type=simple
LimitNOFILE=1000000
Environment="GHUSER=你的GitHub用户名"
Environment="GHBEARER=你的GitHub Token"
PassEnvironment=GHUSER GHBEARER
ExecStart=/opt/rdgen/.venv/bin/python3 /opt/rdgen/manage.py runserver 0.0.0.0:8000
WorkingDirectory=/opt/rdgen/
User=root
Group=root
Restart=always
StandardOutput=file:/var/log/rdgen.log
StandardError=file:/var/log/rdgen.error
RestartSec=10
[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl enable rdgen.service
sudo systemctl start rdgen.service
```

查看服务状态：

```bash
sudo systemctl status rdgen.service
```

## 本地测试

### Windows 环境

1. 克隆仓库到本地
2. 创建虚拟环境：`python -m venv venv`
3. 激活虚拟环境：`.\venv\Scripts\Activate.ps1`
4. 安装依赖：`pip install -r requirements.txt`
5. 运行迁移：`python manage.py migrate`
6. 启动服务：`python manage.py runserver`
7. 访问：`http://127.0.0.1:8000`

### 注意事项

- 本地测试时，需要设置 `DEBUG = True`（已在 settings.py 中配置）
- 生产环境请确保 `DEBUG = False`
- 确保服务器可以从互联网访问（用于 GitHub Actions 回调）
- 建议使用 HTTPS 协议

## 故障排查

1. **GitHub Actions 无法触发**：检查 Fine-grained Token 权限和 Actions 是否已启用
2. **无法访问服务**：检查防火墙端口和反向代理配置
3. **数据库错误**：运行 `python manage.py migrate` 重新初始化
4. **依赖安装失败**：确保 Python 版本 >= 3.10

## 汉化说明

本版本已完整汉化所有用户界面，包括：
- 主生成器页面
- 等待页面
- 生成完成页面
- 维护页面

所有模板文件位于 `rdgenerator/templates/` 目录。
