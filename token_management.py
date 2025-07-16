import json
import os
import sys
import secrets
import string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config_token.json")

def ensure_config_file():
    """确保配置文件存在，若不存在则初始化为空列表"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            json.load(f)
    except FileNotFoundError:
        with open(CONFIG_FILE, 'w') as f:
            json.dump([], f)
    except json.JSONDecodeError:
        with open(CONFIG_FILE, 'w') as f:
            json.dump([], f)

def list_token():
    """列出配置文件中所有 token 信息"""
    ensure_config_file()
    with open(CONFIG_FILE, 'r') as f:
        data = json.load(f)
    
    if not data:
        print("暂无 Token 信息。")
        return

    print("Name\t\tToken")
    print("-" * 30)
    for item in data:
        name = item["name"]
        token = item["token"]
        print(f"{name}\t\t{token}")

def generate_token():
    """生成一个 16 字符长的随机安全 token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for i in range(16))

def create_token(name):
    """创建新的 token 信息并添加到配置文件中"""
    ensure_config_file()
    # 自动生成 token
    token = generate_token()
    with open(CONFIG_FILE, 'r') as f:
        data = json.load(f)
    new_entry = {
        "name": name,
        "token": token
    }
    data.append(new_entry)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Token {name} 创建成功，生成的 Token 为: {token}")

def del_token(name):
    """根据名称删除配置文件中的 token 信息"""
    ensure_config_file()
    with open(CONFIG_FILE, 'r') as f:
        data = json.load(f)
    new_data = [item for item in data if item["name"] != name]
    if len(new_data) == len(data):
        print(f"未找到名为 {name} 的 Token")
        return
    with open(CONFIG_FILE, 'w') as f:
        json.dump(new_data, f, indent=4)
    print(f"Token {name} 删除成功")

def main():
    if len(sys.argv) < 2:
        print("用法: python token_management.py {add|del|list} [参数]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        list_token()
    elif command == "add":
        if len(sys.argv) != 3:
            print("用法: python token_management.py add <name>")
            sys.exit(1)
        name = sys.argv[2]
        create_token(name)
    elif command == "del":
        if len(sys.argv) != 3:
            print("用法: python token_management.py del <name>")
            sys.exit(1)
        name = sys.argv[2]
        del_token(name)
    else:
        print("用法: python token_management.py {add|del|list} [参数]")
        sys.exit(1)

if __name__ == "__main__":
    main()