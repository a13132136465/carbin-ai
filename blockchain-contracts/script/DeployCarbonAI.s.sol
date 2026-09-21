// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script} from "forge-std/Script.sol";

import {CarbonProjectNFT} from "../src/CarbonProjectNFT.sol";

import {CarbonCredit} from "../src/CarbonCredit.sol";

contract DeployCarbonAI is Script {
    function run()
        external
        returns (CarbonProjectNFT projectNFT, CarbonCredit carbonCredit)
    {
        address admin = vm.envAddress("ADMIN_ADDRESS");

        address backend = vm.envAddress("BACKEND_ADDRESS");

        vm.startBroadcast();

        projectNFT = new CarbonProjectNFT(admin);

        carbonCredit = new CarbonCredit(admin, address(projectNFT));

        projectNFT.grantRole(projectNFT.ISSUER_ROLE(), backend);

        carbonCredit.grantRole(carbonCredit.ISSUER_ROLE(), backend);

        vm.stopBroadcast();
    }
}
