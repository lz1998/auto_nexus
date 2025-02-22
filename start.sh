#!/bin/bash
npx solc --bin --abi --optimize -o build Storage.sol

export PRIVATE_KEY=$1

node deploy.js
