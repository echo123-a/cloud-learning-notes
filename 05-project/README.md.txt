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

## 七、 自建 Docker 镜像与容器运行

### 1. Dockerfile 编写规范与分层缓存原理
*   **Dockerfile 核心指令**：
    *   `FROM python:3.10-slim`：指定基础镜像。
    *   `WORKDIR /app`：设置工作目录。
    *   `COPY requirements.txt .`：先拷贝依赖清单。
    *   `RUN pip install ...`：安装依赖（使用阿里云源加速）。
    *   `COPY . .`：拷贝所有代码。
    *   `EXPOSE 5000`：声明容器内服务监听的端口（**仅作声明，不开放**）。
    *   `CMD ["python3", "app.py"]`：容器启动时的默认命令。
*   **分层缓存机制**：把 `COPY requirements.txt` 和 `RUN pip install` 放在 `COPY . .` 之前，是为了最大化利用 Docker 的缓存。只要依赖不变，修改代码后重建镜像时，会跳过耗时的 `pip install`，极大提升构建速度。

### 2. 容器运行与端口映射
*   **运行命令**：`docker run -d -p 5001:5000 --name my-web-app my-python-app:v1`
*   **端口映射原理**：`-p 宿主机端口:容器内端口`。Docker 通过底层的 iptables 规则，将外部访问云服务器 5001 端口的流量，转发到容器内部的 5000 端口。
*   **常见排障**：如果浏览器访问不了，先查 `docker ps` 看容器是否正常运行，再查阿里云安全组是否放行了 5001 端口。

### 3. 容器生命周期管理
*   查看运行中的容器：`docker ps`
*   查看所有容器（含已停止）：`docker ps -a`
*   停止容器：`docker stop my-web-app`
*   删除容器：`docker rm my-web-app`
*   查看本地镜像：`docker images`
*   删除镜像：`docker rmi my-python-app:v1`

### 解决 K3s 镜像拉取 403 Forbidden (限流) 问题

*   **现象**：`svclb-traefik` 一直处于 `ImagePullBackOff`，`describe` 发现报错 `403 Forbidden`，提示 `ntoomanyrequests: 免费节点当前繁忙`。
*   **原因**：K3s 的 containerd 通过公共免费镜像加速节点拉取镜像时，触发限流。
*   **解决方案（离线导入法）**：
    1.  利用 Docker（配置了独立加速）拉取镜像：`docker pull rancher/klipper-lb:v0.4.17`
    2.  导出为 tar 包并放入 K3s 的自动导入目录：`docker save ... -o /var/lib/rancher/k3s/agent/images/klipper-lb.tar`
    3.  重启 K3s：`systemctl restart k3s`，K3s 会自动导入。
*   **验证命令**：`k3s crictl images | grep klipper-lb`（注意：查看 K3s 镜像必须用 crictl，不能用 docker images）。
*   **面试延伸**：生产环境中，为了防止外部镜像仓库挂掉或限流，通常会搭建私有镜像仓库（如 Harbor），并将镜像推送到私有仓库，K8s 从内网拉取。

### K3s 高负载下的 TLS 超时与 Slow SQL 问题

*   **现象**：`kubectl` 执行命令报 `TLS handshake timeout`；`journalctl -u k3s` 显示大量 `Slow SQL`、`connection refused` 到 kubelet 端口以及 `Housekeeping took longer than expected`。
*   **根因**：2核2G 的云服务器资源（尤其是内存和磁盘 I/O）被 K3s 控制面组件、容器运行时及工作负载耗尽。K3s 官方建议单节点带负载至少需要 1.6GB 内存，当前环境已触及瓶颈，导致 kubelet 响应缓慢、SQLite 写入阻塞。
*   **解决**：
    1.  临时缓解：重启 K3s 释放内存；删除非必要的 `svclb-traefik`、`metrics-server` 等组件。
    2.  长期方案：为 K3s 瘦身（安装时 `--disable traefik --disable servicelb`），或升级服务器内存至 4GB。
*   **面试延伸**：K8s 对资源（内存、I/O）非常敏感。在资源不足时，控制面组件的响应会变慢，表现为 API 超时、Pod 调度延迟等。排查此类问题应先看系统资源（`free -h`、`iostat`），而非盲目调整 K8s 配置。


## 九、 K3s 资源瓶颈调优与终极部署

### 1. 2G 内存跑 K8s 的生存指南
*   **现象**：执行 kubectl 报 `TLS handshake timeout`，系统日志疯狂刷 `Slow SQL` 和 `connection refused`。
*   **根因**：K3s 组件（kubelet, apiserver 等）占用大量物理内存，1.7G 内存耗尽时触发系统 I/O 阻塞，导致 API Server 响应超时。
*   **调优手段**：
    1.  **启用 Swap**：通过 `sysctl vm.swappiness=60` 让系统在物理内存不足时积极使用 Swap 虚拟内存，避免 OOM Killer 强杀进程。
    2.  **裁剪组件**：删除单节点不需要的 `metrics-server`、`svclb-traefik` 等资源消耗大户。
    3.  **卸载 Docker**：镜像导入 K3s 后，停止 Docker 服务，彻底释放内存。

### 2. K8s 核心对象实战总结
*   **Deployment**：负责管理 Pod 的生命周期和副本数。我们通过 YAML 告诉 K8s 跑一个副本，它会自动实现故障自愈。
*   **Service (NodePort)**：给 Pod 提供统一的访问入口。NodePort 会在宿主机的 30000-32767 范围内随机分配一个端口（如 31234），外部通过 `公网IP:31234` 即可访问应用。
*   **访问链路**：`浏览器 -> 公网 IP:NodePort -> K8s Service -> Pod (容器内 5000 端口)`。

### 3. 云原生部署完整闭环
`本地写代码 -> Docker 打包镜像 -> 导出 tar 离线喂给 K3s -> 编写 YAML 部署 -> Service 暴露端口 -> 公网访问成功`