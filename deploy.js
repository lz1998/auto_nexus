const { ethers } = require("ethers");
const fs = require("fs");

// 连接到指定的自定义 RPC 节点
const provider = new ethers.JsonRpcProvider("https://rpc.nexus.xyz/http");

// 从命令行参数中读取私钥
const privateKey = process.argv[2];

if (!privateKey) {
  console.error("请通过命令行传递私钥！");
  process.exit(1);
}

// 设置钱包并使用私钥连接
const wallet = new ethers.Wallet(privateKey, provider);

// 读取 ABI 和字节码
const abi = JSON.parse(fs.readFileSync("./build/Storage_sol_Storage.abi"));
const bytecode = fs.readFileSync("./build/Storage_sol_Storage.bin", "utf8");

async function deploy() {
    // 通过合约的 ABI 和字节码创建一个合约工厂
    const factory = new ethers.ContractFactory(abi, bytecode, wallet);
    console.log("Deploying contract...");

    // 部署合约并等待交易确认
    const contract = await factory.deploy();
    console.log(`Contract deployed to: ${contract}`);
}

deploy().catch((error) => {
    console.error(error);
    process.exit(1);
});

