// SPDX-License-Identifier: GPL-3.0

pragma solidity ^0.8.2;
contract Storage {

    uint256 number;

    function store(uint256 num) public {
        number = num + 1;
    }
    function retrieve() public view returns (uint256){
        return number;
    }
}
