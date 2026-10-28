import os
import subprocess

# 设置端口为 OpenXLab 要求的 7860
PORT = 7860

# 启动 Streamlit 应用
subprocess.run([
    "streamlit", "run", "streamlit_app.py",
    "--server.address=0.0.0.0",
    f"--server.port={PORT}",
    "--server.headless=true"
], check=True)