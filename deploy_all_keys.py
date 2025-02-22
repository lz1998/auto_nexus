import os
import subprocess
import json
from web3 import Web3
from eth_account import Account

# 连接到 RPC 节点
w3 = Web3(Web3.HTTPProvider('https://rpc.nexus.xyz/http'))

# 指定账户文件的目录
accounts_dir = 'accounts'
deployed_contracts_file = 'deployed_contracts.txt'

# 获取所有 .json 文件
account_files = [f for f in os.listdir(accounts_dir) if f.endswith('.json')]

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
    account_file_path = os.path.join(accounts_dir, account_file)

    # 读取 JSON 文件
    with open(account_file_path, 'r') as file:
        account_data = json.load(file)
        private_key = account_data.get('key')
        address = account_data.get('address')

    # 检查私钥和地址是否存在
    if not private_key or not address:
        print(f"账户文件 {account_file} 中缺少私钥或地址，跳过该文件。")
        continue

    # 检查余额
    balance = w3.eth.get_balance(address)
    balance_in_eth = w3.from_wei(balance, 'ether')

    print(f"账户 {address} 的余额: {balance_in_eth} NEX")
    if balance_in_eth < 0.01:
        print(f"账户 {address} 余额不足，跳过部署")
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