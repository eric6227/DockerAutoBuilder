# Docker BuildX 构建工具

一个面向开发机的桌面图形化工具，让你可以轻松使用 Docker BuildX 构建多平台镜像。

## ✨ 功能特点

### 🖥️ 图形化界面

- 无需命令行，直接通过桌面窗口操作

### 📦 多平台构建

- 支持 **18 种 Docker BuildX 架构**，包括：
  - 主流：`linux/amd64`, `linux/arm64`, `linux/arm/v7`, `linux/arm/v6`
  - 冷门：`linux/ppc64le`, `linux/s390x`, `linux/mips*`, `linux/riscv64`, `linux/loong64`
- 快捷选择按钮：
  - 「选择常见平台」：自动选中 7 个最常用架构（官方镜像几乎都支持）
  - 「全选」：选中全部 18 个架构
  - 「清空选择」：取消全部勾选

### 🔐 仓库登录

- 支持 Docker Hub、GHCR、自定义仓库、私有仓库登录
- 支持用户名+密码或 Token 登录
- 勾选「构建后推送」时自动尝试登录
- 登录失败时弹窗提示并支持重新输入

### 📝 构建配置

- 选择项目目录和 Dockerfile（自动搜索子目录）
- 输入镜像名称和版本号
- 支持构建参数（--build-arg）
- 自动推送版本号标签和 latest 标签

## 🚀 快速开始

### 方式 1：安装软件（推荐）

1. 从 [Releases](https://github.com/eric6227/DockerAutoBuilder/releases) 下载最新版本
2. 运行安装程序，按照提示完成安装
3. 安装完成后在开始菜单找到「DockerAutoBuilder」并运行

### 方式 2：直接运行 EXE

1. 从 [Releases](https://github.com/eric6227/DockerAutoBuilder/releases) 下载最新版本
2. 运行 `DockerAutoBuilder.exe`
3. 无需安装 Python 环境

### 方式 3：源码运行

```bash
# 克隆仓库
git clone https://github.com/eric6227/DockerAutoBuilder.git
cd DockerAutoBuilder

# 安装依赖
pip install -r requirements.txt

# 运行
python app.py
```

## 📖 使用指南

### 基本使用流程

1. **选择项目目录**：点击「选择目录」按钮，选择你的 Docker 项目根目录
2. **选择 Dockerfile**：程序会自动搜索目录及子目录中的 Dockerfile
3. **填写镜像信息**：
   - 镜像名称：如 `myapp`
        > 注意：此处仅填写镜像名称，不能完整填写仓库和用户名
   - 版本号：如 `v1.0.0`（可选，留空则只推送 latest）
4. **选择平台**：
   - 推荐点击「选择常见平台」（7 个常用架构）
   - 或手动选择需要的架构
5. **（可选）登录仓库**：如果需要推送镜像，填写仓库地址、用户名和密码或Token，点击「登录仓库」
6. **开始构建**：勾选「构建后推送到仓库」（可选），点击「开始构建」

### 高级功能

#### 自动推送多标签

- 填写版本号后，程序会自动推送两个标签：
  - `registry/username/myapp:v1.0.0`（版本号标签）
  - `registry/username/myapp:latest`（latest 标签）

#### 自定义仓库地址

- 选择「自定义」仓库类型，输入你的私有仓库地址
- 支持 HTTP/HTTPS 和端口号，如 `http://myregistry:5000`

#### 构建参数

- 在「构建参数」输入框中填写键值对，逗号分隔
- 示例：`HTTP_PORT=8080,ENV=prod`

## 🛠️ 技术栈

- **Python 3.11+**
- **Tkinter + ttk**（GUI）
- **Docker BuildX**（多平台构建）
- **PyInstaller**（打包）

## 📋 系统要求

### Windows

- Windows 10/11 64 位
- Docker Desktop 4.0+（开启 BuildX）
- 至少 4GB 内存
- （可选）软件支持高 DPI 显示器

### Linux

- 理论支持，但未经过测试（直接用python运行app.py即可）
- 需要安装 Python 3.11+ 和 tkinter
- 需要桌面环境（如果没有桌面环境，直接让AI生成docker build命令即可）
- 安装 Docker 和 buildx

## AI使用声明

本项目使用AI辅助构建，包含AI生成的代码等

## 📄 许可证

MIT License - 详见 [LICENSE](./LICENSE)

## 😕 常见问题

如果遇到问题，请：

1. 确保 Docker Desktop 已启动并开启 BuildX
2. 检查 Dockerfile 是否正确
3. 查看程序日志获取详细错误信息
4. 问AI

---

**注意**：构建多平台镜像需要 Docker BuildX 支持，首次使用可能需要运行：

```bash
docker buildx create --use
```
