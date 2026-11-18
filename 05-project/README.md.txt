# 项目：基于阿里云 ECS 的 Python Web 应用部署与运维实战

## 一、 项目背景与目标
本项目旨在模拟真实的云计算运维场景，将一个本地开发的 Python Web 应用（Flask 框架）部署到阿里云 ECS 实例上，实现公网可访问、后台常驻运行及开机自启。通过本项目，深入理解云服务器网络配置、Linux 进程管理与服务守护机制。

## 二、 技术栈
- **云平台**：阿里云 ECS (Ubuntu 22.04)
- **Web 框架**：Python 3 + Flask
- **服务管理**：systemd / systemctl
- **版本控制**：Git / GitHub
- **网络工具**：安全组、Nginx（后续扩展）

## 三、 核心实现步骤
1. **本地开发与代码托管**：编写 `app.py` 并推送到 GitHub。
2. **服务器环境准备**：安装 Git 和 Python 依赖（pip）。
3. **代码拉取**：从 GitHub 克隆项目至服务器 `/var/www/` 目录。
4. **前台测试**：运行 `python3 app.py`，通过配置阿里云安全组入方向规则（放行 5000 端口），在本地浏览器成功访问。
5. **配置系统服务**：编写 `myapp.service` 文件，使用 `systemctl` 将其托管为后台守护进程。

## 四、 核心原理深度解析（面试高频考点）

### 1. 为什么代码里要写 `host='0.0.0.0'`？
**原理**：`0.0.0.0` 在服务器中代表“所有 IPv4 地址”。如果写成 `127.0.0.1`，应用只监听本地回环网卡，外部请求无法进入；写成 `0.0.0.0`，应用会监听服务器上所有网卡（包括公网 IP 和私网 IP），从而允许外部访问。

### 2. 为什么必须配置安全组？（云网络原理）
**原理**：阿里云的安全组相当于云服务器外部的“虚拟防火墙”。即使服务器内部（如 Ubuntu 的 ufw 防火墙）放行了端口，如果安全组未放行，数据包也会在到达服务器网卡前被阿里云的底层网络拦截。**面试口诀：内查防火墙，外查安全组。**

### 3. 为什么不能直接用 `python3 app.py` 在后台运行？
**原理**：直接运行（或使用 `&`、`nohup`）的程序运行在前台终端。一旦 SSH 断开，进程会收到 `SIGHUP` 信号而退出。此外，如果程序遇到未捕获的异常崩溃，它不会自动重启，导致业务中断。

### 4. `systemctl` / `systemd` 是如何管理应用的？
**原理**：`systemd` 是 Linux 系统的初始化系统（PID 为 1 的进程）。当你把 `myapp.service` 文件放入 `/etc/systemd/system/` 并执行 `systemctl start myapp` 时：
- **拉起进程**：systemd 作为父进程，按照 `ExecStart` 路径拉起你的 Python 进程。
- **后台守护**：systemd 会接管进程的输入输出，让它在后台静默运行，SSH 断开不受影响。
- **自动重启**：`Restart=always` 配置使 systemd 会监控该进程，一旦进程崩溃退出，systemd 会立即重新拉起它。
- **日志接管**：程序的 `print` 输出会自动被 systemd 收集，可通过 `journalctl -u myapp` 查看。

### 5. `daemon-reload` 做了什么？
**原理**：Linux 系统启动时会扫描并加载 `/etc/systemd/system/` 下的配置。当你新增或修改了 `.service` 文件后，必须执行 `systemctl daemon-reload` 让 systemd 重新读取配置缓存，否则 `systemctl start` 会找不到新配置。

## 五、 常用排障命令
- 查看服务状态：`systemctl status myapp`
- 重启服务：`systemctl restart myapp`
- 查看应用实时日志：`journalctl -u myapp -f`
- 查看端口监听：`ss -tlnp | grep 5000`