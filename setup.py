import os
import subprocess
import sys
import argparse
import psutil  # 用于查找和终止进程



python_path = sys.executable
parser = argparse.ArgumentParser(description='设置 ComfyUI 地址和端口')
parser.add_argument('--comfyui-address', default='127.0.0.1:8000', help='ComfyUI 的地址和端口，默认为 127.0.0.1:8000')
parser.add_argument('--port', type=int, default=8129, help='代理服务端口，默认为 8129')
parser.add_argument('command', choices=['setup', 'stop'], default='setup', nargs='?', help='执行命令，setup 进行安装和启动，stop 停止代理服务')


args = parser.parse_args()
comfyui_address = args.comfyui_address
port = args.port


env_content = f'''
JWT_PUBLIC_KEY=""
COMFYUI_URL="http://{comfyui_address}"
TARGET_WS_URL="ws://{comfyui_address}/ws"
ALGORITHM="RS256"
PORT={port}
'''

def add_aliases():
    home_dir = os.path.expanduser("~")
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        rc_file = os.path.join(home_dir, ".zshrc")
    elif "bash" in shell:
        rc_file = os.path.join(home_dir, ".bashrc")
    else:
        print("未检测到支持的 Shell（bash 或 zsh），跳过别名设置。")
        return

    alias_commands = [
        f"alias whale='{python_path} ./token_management.py'"
    ]

    try:
        existing_content = ""
        if os.path.exists(rc_file):
            with open(rc_file, 'r') as f:
                existing_content = f.read()

        new_aliases = []
        for alias in alias_commands:
            if alias not in existing_content:
                new_aliases.append(alias)

        if new_aliases:
            try:
                with open(rc_file, 'a') as f:
                    for alias in new_aliases:
                        f.write(f"\n{alias}\n")
                print(f"新别名已添加到 {rc_file}，请重新启动终端或运行 'source {rc_file}' 使别名生效。")
            except Exception as e:
                print(f"添加别名失败。错误信息: {e}")
        else:
            print("所有别名已存在，无需重复添加。")
    except Exception as e:
        print(f"添加别名失败。错误信息: {e}")


def stop_proxy():
    """停止正在运行的 proxy.py 进程"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline and 'proxy.py' in cmdline[-1]:
                proc.terminate()  # 尝试终止进程
                gone, still_alive = psutil.wait_procs([proc], timeout=5)
                if still_alive:
                    for p in still_alive:
                        p.kill()  # 强制终止进程
                    print("已强制终止代理服务进程。")
                else:
                    print("代理服务进程已成功终止。")
                return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    print("未找到正在运行的代理服务进程。")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("----------",script_dir)
    token_management_path = os.path.join(script_dir, 'token_management.py')
    requirements_path = os.path.join(script_dir, 'requirements.txt')
    proxy_path = os.path.join(script_dir, 'proxy.py')
    proxy_log_path = os.path.join(script_dir, 'proxy.log')
    env_file_path = os.path.join(script_dir, '.env')
    print(token_management_path)
    print(requirements_path)
    print(proxy_path)
    print(env_file_path)
    print(proxy_log_path)

    if args.command == 'stop':
        stop_proxy()
    elif args.command == 'setup':
        add_aliases()

        try:
            with open(env_file_path, 'w') as f:
                f.write(env_content.strip())
            print(f".env 文件已成功创建。")
        except Exception as e:
            print(f".env 文件创建失败，请检查权限或路径。错误信息: {e}")
            exit(1)


        if not os.path.exists('config_token.json'):
            subprocess.run([python_path, token_management_path, 'add', 'system'], check=True)

        try:
            subprocess.run([python_path, '-m', 'pip', 'install', '-r', requirements_path], check=True)
            print("依赖安装成功。")

        except subprocess.CalledProcessError as e:
            print(f"依赖安装失败。错误信息: {e}")
            exit(1)

        try:
            with open(proxy_log_path, 'a') as log_file:
                subprocess.Popen([python_path, proxy_path], stdout=log_file, stderr=subprocess.STDOUT)
            print("代理服务已启动，日志记录在 proxy.log 文件中。")
        except Exception as e:
            print(f"代理服务启动失败。错误信息: {e}")
            exit(1)