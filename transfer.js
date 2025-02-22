const { ethers } = require('ethers');

// 从命令行参数中读取主账户私钥和目标钱包地址
const mainPrivateKey = process.argv[2];
const toWalletAddress = process.argv[3];
const rpcUrl = "https://rpc.nexus.xyz/http";

// 创建 provider 和钱包实例
const provider = new ethers.JsonRpcProvider(rpcUrl);
const wallet = new ethers.Wallet(mainPrivateKey, provider);

async function transfer() {
    console.log(mainPrivateKey, toWalletAddress);
    try {
        // 获取钱包的余额
        const balance = await provider.getBalance(wallet.address);
        console.log(`Sender balance: ${ethers.formatEther(balance)} ETH`);

        // 设置交易参数
        const feeData = await provider.getFeeData();
        const tx = {
            to: toWalletAddress,
            value: ethers.parseEther('0.01'), // 转账 0.01 ETH
            gasLimit: 2100000, // 默认 gas limit
            maxFeePerGas: feeData.maxFeePerGas, // 使用获取的 gas 费用
            maxPriorityFeePerGas: feeData.maxPriorityFeePerGas,
        };

        // 执行转账
        console.log('Sending transaction...');
        const transactionResponse = await wallet.sendTransaction(tx);

        // 等待交易确认
        await transactionResponse.wait();
        console.log(`Transaction successful! Tx Hash: ${transactionResponse.hash}`);
        console.log(`Transaction sent from: ${wallet.address}`);
        console.log(`Transaction sent to: ${toWalletAddress}`);
    } catch (error) {
        console.error('Error:', error);
    }
}

// 执行转账
transfer();