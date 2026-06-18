import subprocess

subprocess.Popen([
    "uvicorn",
    "api.main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000"
    "--reload"
])

subprocess.Popen([
    "streamlit",
    "run",
    "monitor/dashboard.py"
])

print("AFR SERVICES RUNNING")

