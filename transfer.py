import os
import subprocess
from web3 import Web3

# 连接到 RPC 节点
w3 = Web3(Web3.HTTPProvider('https://rpc.nexus.xyz/http'))

# 指定账户文件的目录
accounts_dir = 'accounts'
zero_balance_dir = 'accounts/zero_balance'

# 获取所有有余额的账户
account_files = [f for f in os.listdir(accounts_dir) if f.endswith('.txt')]

# 读取零余额账户
zero_balance_accounts = [f for f in os.listdir(zero_balance_dir) if f.endswith('.txt')]

# 检查是否有零余额账户
if not zero_balance_accounts:
    print("没有找到任何零余额账户！")
    exit(1)

# 遍历每个账户文件并进行转账
for account_file in account_files:
    account_file_path = os.path.join(accounts_dir, account_file)

    # 读取 .txt 文件，文件名是地址，内容是私钥
    address = account_file[:-4]  # 去掉 .txt 后缀
    with open(account_file_path, 'r') as file:
        private_key = file.readline().strip()  # 读取私钥

    # 检查私钥和地址是否存在
    if not private_key or not address:
        print(f"账户文件 {account_file} 中缺少私钥，跳过该文件。")
        continue

    # 检查私钥长度，低于16位则删除文件
    if len(private_key) < 16:
        print(f"账户文件 {account_file} 中的私钥长度低于16位，删除该文件。")
        os.remove(account_file_path)  # 删除文件
        continue

    # 检查余额
    balance = w3.eth.get_balance(address)
    balance_in_eth = w3.from_wei(balance, 'ether')

    print(f"账户 {address} 的余额: {balance_in_eth} NEX")
    if balance_in_eth > 1:  # 只对余额大于 1 NEX 的账户进行转账
        for zero_account_file in zero_balance_accounts:
            zero_account_path = os.path.join(zero_balance_dir, zero_account_file)

            # 读取零余额账户的私钥
            zero_address = zero_account_file[:-4]  # 去掉 .txt 后缀
            with open(zero_account_path, 'r') as file:
                zero_private_key = file.readline().strip()  # 读取私钥

            # 调用 transfer.js 进行转账
            try:
                print(f"从账户 {address} 向账户 {zero_address} 转账 0.01 NEX...")
                subprocess.run(['node', 'transfer.js', private_key, zero_address], check=True)

                # 调用被转账的零余额账户进行部署
                print(f"正在使用账户 {zero_address} 部署合约...")
                subprocess.run(['node', 'deploy.js', zero_private_key], check=True)

                # 将零余额账户的文件移动到部署目录
                deploy_dir = 'accounts/deployed'
                if not os.path.exists(deploy_dir):
                    os.makedirs(deploy_dir)

                os.rename(zero_account_path, os.path.join(deploy_dir, zero_account_file))
                print(f"账户 {zero_address} 的文件已移动到部署目录。")

            except subprocess.CalledProcessError as e:
                print(f"调用 transfer.js 或 deploy.js 时出错: {e}")