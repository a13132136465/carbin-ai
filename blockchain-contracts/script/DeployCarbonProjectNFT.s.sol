// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script} from "forge-std/Script.sol";

import {CarbonProjectNFT} from "../src/CarbonProjectNFT.sol";

contract DeployCarbonProjectNFT is Script {
    function run() external returns (CarbonProjectNFT) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");

        address admin = vm.addr(deployerPrivateKey);

        vm.startBroadcast(deployerPrivateKey);

        CarbonProjectNFT nft = new CarbonProjectNFT(admin);

        vm.stopBroadcast();

        return nft;
    }
}
