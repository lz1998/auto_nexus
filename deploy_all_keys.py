import os
import subprocess

# 指定账户文件的目录
accounts_dir = 'accounts'

# 获取所有 .txt 文件
account_files = [f for f in os.listdir(accounts_dir) if f.endswith('.txt')]

# 检查是否有账户文件
if not account_files:
    print("没有找到任何账户文件！")
    exit(1)

# 遍历每个账户文件并调用 deploy.js
for account_file in account_files:
    account_file_path = os.path.join(accounts_dir, account_file)

    # 读取私钥
    with open(account_file_path, 'r') as file:
        private_key = file.read().strip()

    # 调用 deploy.js 脚本并传递私钥
    try:
        print(f"正在使用私钥从 {account_file} 部署合约...")
        subprocess.run(['node', 'deploy.js', private_key], check=True)
    except subprocess.CalledProcessError as e:
        print(f"调用 deploy.js 时出错: {e}")