// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";

import {CarbonProjectNFT} from "../src/CarbonProjectNFT.sol";

contract CarbonProjectNFTTest is Test {
    CarbonProjectNFT nft;

    address admin = address(0x1);

    address projectOwner = address(0x2);

    function setUp() public {
        vm.prank(admin);

        nft = new CarbonProjectNFT(admin);
    }

    function testMintProject() public {
        vm.prank(admin);

        uint256 tokenId = nft.mintProject(
            projectOwner,
            "PRJ-2026-001",
            "ipfs://project-001"
        );

        assertEq(tokenId, 1);

        assertEq(nft.ownerOf(tokenId), projectOwner);

        assertEq(nft.tokenURI(tokenId), "ipfs://project-001");

        assertEq(nft.projectIdOf(tokenId), "PRJ-2026-001");
    }

    function testNonIssuerCannotMint() public {
        address attacker = address(0x999);

        vm.prank(attacker);

        vm.expectRevert();

        nft.mintProject(projectOwner, "PRJ-2026-002", "ipfs://project-002");
    }

    function testCannotMintSameProjectTwice() public {
        vm.prank(admin);

        nft.mintProject(projectOwner, "PRJ-2026-001", "ipfs://project-001");

        bytes32 projectHash = keccak256(bytes("PRJ-2026-001"));

        vm.prank(admin);

        vm.expectRevert(
            abi.encodeWithSelector(
                CarbonProjectNFT.ProjectAlreadyMinted.selector,
                projectHash
            )
        );

        nft.mintProject(projectOwner, "PRJ-2026-001", "ipfs://project-001-v2");
    }

    function testCannotMintEmptyProjectId() public {
        vm.prank(admin);

        vm.expectRevert(CarbonProjectNFT.EmptyProjectId.selector);

        nft.mintProject(projectOwner, "", "ipfs://project");
    }
    event ProjectMinted(
        uint256 indexed tokenId,
        bytes32 indexed projectHash,
        string projectId,
        address indexed owner
    );

    function testEmitProjectMintedEvent() public {
        bytes32 projectHash = keccak256(bytes("PRJ-2026-001"));

        vm.expectEmit(true, true, true, true);

        emit ProjectMinted(1, projectHash, "PRJ-2026-001", projectOwner);

        vm.prank(admin);

        nft.mintProject(projectOwner, "PRJ-2026-001", "ipfs://project-001");
    }
}
