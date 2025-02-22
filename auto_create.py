#!/usr/bin/env python3
import asyncio
import datetime
from asyncio import Semaphore

import aiohttp
import backoff
import eth_keys
import jwt
from aiohttp import ClientTimeout
from eth_account import Account
from eth_account.messages import encode_defunct


class NexusAutomation:
    def __init__(self, wallet_address, private_key, num_nodes=200):
        self.wallet_address = wallet_address
        self.private_key = (
            private_key if private_key.startswith("0x") else f"0x{private_key}"
        )
        self.num_nodes = num_nodes
        self.api_base = "https://app.dynamicauth.com/api/v0/sdk/adc09cea-6194-4667-8be8-931cc28dacd2"
        self.jwt_token = None
        self.user_id = None

    async def run(self):
        """运行主流程"""
        # 1. 登录获取 JWT
        if not await self.login():
            print("Login failed")
            return
        print("Login success")
#        existing_count, node_ids = await self.get_user_nodes()
#        if existing_count >= self.num_nodes:
#            print(f"Already have {existing_count} nodes, no need to create more")
#            for node_id in node_ids:
#                print(f"{node_id}")
#            return
#        # 2. 添加节点
#        if self.user_id:
#            nodes_to_add = self.num_nodes - existing_count
#            print(f"Adding {nodes_to_add} nodes (already have {existing_count})...")
#            self.num_nodes = nodes_to_add
#            await self.add_nodes()
#        else:
#            print("Failed to get user ID, cannot add nodes")
#        # print user all nodes
#        existing_count, node_ids = await self.get_user_nodes()
#        for node_id in node_ids:
#            print(f"{node_id}")

    async def get_tasks(self):
        """获取任务列表"""
        url = "https://beta.orchestrator.nexus.xyz/tasks"
        headers = {
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/octet-stream",
            "Origin": "https://app.nexus.xyz",
            "Referer": "https://app.nexus.xyz/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132"',
            "sec-ch-ua-platform": '"macOS"',
            "Authorization": f"Bearer {self.jwt_token}",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        print("Tasks retrieved successfully")
                        return await response.read()
                    else:
                        print(f"Failed to get tasks. Status: {response.status}")
                        return None
            except Exception as e:
                print(f"Error getting tasks: {str(e)}")
                return None

    async def get_user_nodes(self):
        """获取用户已有的节点及数量"""
        url = f"https://beta.orchestrator.nexus.xyz/users/{self.wallet_address}"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "DNT": "1",
            "Origin": "https://app.nexus.xyz",
            "Referer": "https://app.nexus.xyz/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
            "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132"',
            "sec-ch-ua-platform": '"macOS"',
            "Authorization": f"Bearer {self.jwt_token}",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data") and data["data"].get("nodes"):
                            nodes = data["data"]["nodes"]
                            print(f"\nFound {len(nodes)} existing nodes:")
                            for node in nodes:
                                print(f"Node ID: {node['id']}")
                            return len(nodes), [node["id"] for node in nodes]
                        return 0, []
                    else:
                        print(f"Failed to get nodes. Status: {response.status}")
                        return 0, []
            except Exception as e:
                print(f"Error getting nodes: {str(e)}")
                return 0, []

    async def login(self):
        """执行登录流程"""
        # 获取 nonce
        nonce = await self.get_nonce()
        print(f"Got nonce: {nonce}")

        # 构造并签名消息
        message, signed_message = await self.sign_message(nonce)
        print("Message signed successfully")

        # 获取 session public key
        session_public_key = self.get_session_public_key()

        # 验证签名
        verify_response = await self.verify_signature(
            signed_message, message, session_public_key
        )

        # 解析响应
        if verify_response.get("jwt"):
            self.jwt_token = verify_response["jwt"]
            # 从 JWT 中解析 user ID
            decoded = jwt.decode(self.jwt_token, options={"verify_signature": False})
            self.user_id = decoded.get("sub")

            # 添加新的用户注册API调用
            url = "https://beta.orchestrator.nexus.xyz/users"
            data = f"\n${self.user_id}\u0012*{self.wallet_address}"
            headers = {
                "Host": "beta.orchestrator.nexus.xyz",
                "Connection": "keep-alive",
                "Content-Type": "application/octet-stream",
                "Origin": "https://app.nexus.xyz",
                "Referer": "https://app.nexus.xyz/",
                "Authorization": f"Bearer {self.jwt_token}",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    print(f"User registration status: {response.status}")

            return True
        return False

    async def get_nonce(self):
        """获取 nonce"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"{self.api_base}/nonce",
                    headers={
                        "accept": "*/*",
                        "content-type": "application/json",
                        "x-dyn-api-version": "API/0.0.599",
                        "x-dyn-version": "WalletKit/4.3.2",
                    },
            ) as response:
                data = await response.json()
                return data["nonce"]

    async def sign_message(self, nonce):
        """构造并签名消息"""
        issued_at = (
                datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )

        message = (
            f"app.nexus.xyz wants you to sign in with your Ethereum account:\n"
            f"{self.wallet_address}\n\n"
            "Welcome to Nexus. Signing is the only way we can truly know that you are the owner of the wallet you are connecting. "
            "Signing is a safe, gas-less transaction that does not in any way give Nexus permission to perform any transactions with your wallet.\n\n"
            "URI: https://app.nexus.xyz/nodes\n"
            "Version: 1\n"
            "Chain ID: 392\n"
            f"Nonce: {nonce}\n"
            f"Issued At: {issued_at}\n"
            "Request ID: adc09cea-6194-4667-8be8-931cc28dacd2"
        )

        signed = Account.sign_message(
            encode_defunct(text=message), private_key=self.private_key
        )

        return message, f"0x{signed.signature.hex()}"

    def get_session_public_key(self):
        """获取压缩格式的公钥"""
        private_key_bytes = bytes.fromhex(self.private_key[2:])
        priv_key = eth_keys.main.KeyAPI.PrivateKey(private_key_bytes)
        pub_key = priv_key.public_key
        return pub_key.to_compressed_bytes().hex()

    async def verify_signature(self, signed_message, message, session_public_key):
        """验证签名"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.api_base}/verify",
                    headers={
                        "accept": "*/*",
                        "content-type": "application/json",
                        "dnt": "1",
                        "origin": "https://app.nexus.xyz",
                        "referer": "https://app.nexus.xyz/",
                        "x-dyn-api-version": "API/0.0.599",
                        "x-dyn-version": "WalletKit/4.3.2",
                    },
                    json={
                        "signedMessage": signed_message,
                        "messageToSign": message,
                        "publicWalletAddress": self.wallet_address.lower(),
                        "chain": "EVM",
                        "walletName": "metamask",
                        "walletProvider": "browserExtension",
                        "network": "392",
                        "additionalWalletAddresses": [],
                        "sessionPublicKey": session_public_key,
                    },
            ) as response:
                return await response.json()

    async def add_single_node(self, session, prefix, node_number):
        """添加单个节点"""
        url = "https://beta.orchestrator.nexus.xyz/nodes"
        headers = {
            "Host": "beta.orchestrator.nexus.xyz",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": '"Windows"',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Content-Type": "application/octet-stream",
            "Origin": "https://app.nexus.xyz",
            "Referer": "https://app.nexus.xyz/",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Authorization": f"Bearer {self.jwt_token}",
        }

        @backoff.on_exception(
            backoff.expo,
            (aiohttp.ClientError, asyncio.TimeoutError),
            max_tries=3,
            max_time=30,
        )
        async def _make_request():
            async with session.post(url, headers=headers, data=prefix) as response:
                if response.status == 200:
                    print(
                        f"Node #{node_number}: Successfully added. Status: {response.status}"
                    )
                    return True
                else:
                    print(
                        f"Node #{node_number}: Failed. Status: {response.status} response: {await response.text()}"
                    )
                    return False

        try:
            return await _make_request()
        except Exception as e:
            print(f"Node #{node_number}: Final failure after retries: {str(e)}")
            return False

    async def add_nodes(self):
        """添加多个节点 with connection pooling and concurrency control"""
        prefix = b"\x08\x01\x12$" + self.user_id.encode()
        semaphore = Semaphore(3)  # 限制并发为3

        # 配置连接池和超时
        timeout = ClientTimeout(total=30)
        connector = aiohttp.TCPConnector(limit=3, force_close=False)

        async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
        ) as session:
            async def bounded_add_node(node_number):
                async with semaphore:
                    return await self.add_single_node(session, prefix, node_number)

            tasks = [bounded_add_node(i + 1) for i in range(self.num_nodes)]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 统计结果
            successes = sum(1 for r in results if r is True)
            failures = self.num_nodes - successes
            print(f"\nSummary:")
            print(f"Total nodes attempted: {self.num_nodes}")
            print(f"Successful: {successes}")
            print(f"Failed: {failures}")


def gen_wallet():
    # 创建新的以太坊账户
    account = Account.create()
    # 获取账户的地址和私钥
    address = account.address
    private_key = account.key.hex()
    # 输出结果
    print(f"Address: {address}")
    print(f"Private Key: {private_key}")
    return account


async def main():
    account = gen_wallet()
    # 配置
    WALLET_ADDRESS = account.address
    PRIVATE_KEY = account.key.hex()
        
    NUM_NODES = 100

    # 创建自动化实例
    automation = NexusAutomation(WALLET_ADDRESS, PRIVATE_KEY, NUM_NODES)

    # 运行
    await automation.run()
    print(f"{WALLET_ADDRESS}")
    print(f"{PRIVATE_KEY}")
    with open(f"accounts/{WALLET_ADDRESS}.txt","w") as f:
        f.write(PRIVATE_KEY)

if __name__ == "__main__":
    asyncio.run(main())

