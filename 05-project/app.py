from flask import Flask
import socket

app = Flask(__name__)

@app.route('/')
def hello():
    # 获取当前服务器的真实主机名（在云服务器上运行会显示实例 ID）
    hostname = socket.gethostname()
    return f"<h1>Hello, CI/CD!</h1><p>我是被自动化流水线部署的，当前主机名: {hostname}</p>"

if __name__ == '__main__':
    # 监听 0.0.0.0 非常重要，代表允许所有外部 IP 访问
    app.run(host='0.0.0.0', port=5000)