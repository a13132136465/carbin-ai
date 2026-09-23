// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";

import {CarbonProjectNFT} from "../src/CarbonProjectNFT.sol";
import {CarbonCredit} from "../src/CarbonCredit.sol";

contract CarbonProjectNFTTest is Test {
    CarbonProjectNFT nft;

    address admin = address(0x1);

    address projectOwner = address(0x2);

    address backend = address(0x3);

    CarbonCredit credit;

    function setUp() public {
        vm.prank(admin);

        nft = new CarbonProjectNFT(admin);
        credit = new CarbonCredit(admin, address(nft));
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
    function testAdminCanGrantIssuerRole() public {
        bytes32 issuerRole = nft.ISSUER_ROLE();

        vm.prank(admin);

        nft.grantRole(issuerRole, backend);

        assertTrue(nft.hasRole(issuerRole, backend));
    }

    function testGrantedIssuerCanMint() public {
        bytes32 issuerRole = nft.ISSUER_ROLE();

        vm.prank(admin);

        nft.grantRole(issuerRole, backend);

        vm.prank(backend);

        uint256 tokenId = nft.mintProject(
            projectOwner,
            "PRJ-2026-100",
            "ipfs://project-100"
        );

        assertEq(tokenId, 1);

        assertEq(nft.ownerOf(tokenId), projectOwner);
    }

    function testRevokedIssuerCannotMint() public {
        bytes32 issuerRole = nft.ISSUER_ROLE();

        vm.startPrank(admin);

        nft.grantRole(issuerRole, backend);

        nft.revokeRole(issuerRole, backend);

        vm.stopPrank();

        assertFalse(nft.hasRole(issuerRole, backend));

        vm.prank(backend);

        vm.expectRevert();

        nft.mintProject(projectOwner, "PRJ-2026-200", "ipfs://project-200");
    }

    function testAdminHasIssuerRole() public view {
        bytes32 role = credit.ISSUER_ROLE();

        assertTrue(credit.hasRole(role, admin));
    }

    function testCannotMintProjectToZeroAddress() public {
        vm.prank(admin);

        vm.expectRevert(CarbonProjectNFT.InvalidRecipient.selector);

        nft.mintProject(address(0), "PRJ-001", "ipfs://project");
    }
}
