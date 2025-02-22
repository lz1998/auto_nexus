import os
import subprocess
import shutil
from web3 import Web3

# 连接到 RPC 节点
w3 = Web3(Web3.HTTPProvider('https://rpc.nexus.xyz/http'))

# 指定账户文件的目录
accounts_dir = 'accounts'
zero_balance_dir = 'accounts/zero_balance'
deployed_contracts_file = 'deployed_contracts.txt'

# 创建零余额账户目录（如果不存在）
if not os.path.exists(zero_balance_dir):
    os.makedirs(zero_balance_dir)

# 获取所有 .txt 文件
account_files = [f for f in os.listdir(accounts_dir) if f.endswith('.txt')]

# 检查是否有账户文件
if not account_files:
    print("没有找到任何账户文件！")
    exit(1)

# 读取已部署合约地址
if os.path.exists(deployed_contracts_file):
    with open(deployed_contracts_file, 'r') as file:
        deployed_contracts = set(line.strip() for line in file)
else:
    deployed_contracts = set()

# 遍历每个账户文件并调用 deploy.js
for account_file in account_files:
    # 跳过 zero_balance 目录中的文件
    if 'zero_balance' in account_file:
        continue

    account_file_path = os.path.join(accounts_dir, account_file)

    # 读取 .txt 文件，文件名是地址，内容是私钥
    address = account_file[:-4]  # 去掉 .txt 后缀
    with open(account_file_path, 'r') as file:
        private_key = file.readline().strip()  # 读取私钥

    # 检查私钥和地址是否存在
    if not private_key or not address:
        print(f"账户文件 {account_file} 中缺少私钥，删除该文件。")
        os.remove(account_file_path)  # 删除缺少私钥的文件
        continue

    # 检查余额
    balance = w3.eth.get_balance(address)
    balance_in_eth = w3.from_wei(balance, 'ether')

    print(f"账户 {address} 的余额: {balance_in_eth} NEX")
    if balance_in_eth < 0.01:
        print(f"账户 {address} 余额不足，移动到 zero_balance 目录")
        # 移动文件到 zero_balance 目录
        shutil.move(account_file_path, os.path.join(zero_balance_dir, account_file))
        continue

    # 检查是否已部署
    if address in deployed_contracts:
        print(f"账户 {address} 已经部署过合约，跳过部署")
        continue

    # 调用 deploy.js 脚本并传递私钥
    try:
        print(f"正在使用账户 {address} 部署合约...")
        subprocess.run(['node', 'deploy.js', private_key], check=True)

        # 记录已部署的合约地址
        deployed_contracts.add(address)
        with open(deployed_contracts_file, 'a') as file:
            file.write(f"{address}\n")

    except subprocess.CalledProcessError as e:
        print(f"调用 deploy.js 时出错: {e}")