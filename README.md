# ComfyUI-Proxy

## 简介
`ComfyUI-Proxy` 是一个用于代理请求至 ComfyUI 的服务，支持 HTTP 请求和 WebSocket 请求代理，同时集成了 JWT Token 验证功能，保障接口访问的安全性。

## 功能特性
- **HTTP 请求代理**：支持 GET、POST、PUT、DELETE 等请求方法的代理。
- **WebSocket 请求代理**：支持 WebSocket 连接的代理。
- **JWT Token 验证**：对特定接口进行 Token 验证，确保只有授权用户可以访问。
- **Token 管理**：提供命令行工具进行 Token 的创建、查询和删除操作。

## 环境准备
### 依赖安装

你可以通过以下命令安装依赖：
```bash
pip install -r requirements.txt

```

### 启动服务
若未通过 setup.py 启动服务，可使用以下命令手动启动：
```bash
python proxy.py
```






### Token 管理
项目提供了 `token_management.py` 脚本用于管理 Token，你可以通过以下命令进行操作：

#### 列出所有 Token
```bash=
python token_management.py list
python token_management.py add <name>
python token_management.py del <name>
```



### 项目初始化
使用 setup.py 脚本可以完成项目的初始化工作，包括创建 .env 文件、设置命令别名、安装依赖、启动代理服务等操作。

命令参数
--comfyui-address：ComfyUI 的地址和端口，默认为 127.0.0.1:8188。
--port：代理服务端口，默认为 6006。

```bash
# 使用默认配置初始化项目
python setup.py

# 指定 ComfyUI 地址和代理服务端口
python setup.py --comfyui-address 192.168.1.100:8288 --port 8080
```

### 命令别名设置
setup.py 脚本会自动为 Token 管理命令设置别名，支持的 Shell 包括 bash 和 zsh。设置的别名如下：
```bash
alias whale='<python_path> ./token_management.py'

# 列出所有 Token
whale list

# 创建新 Token
whale add <name>

# 删除 Token
whale del <name>

```



