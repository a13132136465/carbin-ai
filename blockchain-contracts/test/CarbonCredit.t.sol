// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";

import {CarbonProjectNFT} from "../src/CarbonProjectNFT.sol";

import {CarbonCredit} from "../src/CarbonCredit.sol";

contract CarbonCreditTest is Test {
    CarbonProjectNFT projectNFT;
    CarbonCredit credit;

    address admin = address(0x1);

    address projectOwner = address(0x2);

    function setUp() public {
        vm.startPrank(admin);

        projectNFT = new CarbonProjectNFT(admin);

        credit = new CarbonCredit(admin, address(projectNFT));

        projectNFT.mintProject(
            projectOwner,
            "PRJ-2026-001",
            "ipfs://project-001"
        );

        vm.stopPrank();
    }

    function testMintCredit() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        uint256 creditId = credit.mintCredit(
            projectOwner,
            1,
            auditHash,
            2026,
            2900
        );

        assertEq(creditId, 1);

        assertEq(credit.balanceOf(projectOwner, creditId), 2900);
    }

    function testBatchData() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        uint256 creditId = credit.mintCredit(
            projectOwner,
            1,
            auditHash,
            2026,
            2900
        );

        CarbonCredit.CreditBatch memory batch = credit.getBatch(creditId);

        assertEq(batch.projectTokenId, 1);

        assertEq(batch.auditHash, auditHash);

        assertEq(batch.vintage, 2026);

        assertEq(batch.totalIssued, 2900);
    }

    function testCannotMintSameAuditTwice() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        credit.mintCredit(projectOwner, 1, auditHash, 2026, 2900);

        vm.prank(admin);

        vm.expectRevert(
            abi.encodeWithSelector(
                CarbonCredit.AuditAlreadyMinted.selector,
                auditHash
            )
        );

        credit.mintCredit(projectOwner, 1, auditHash, 2026, 2900);
    }

    function testCannotMintZeroAmount() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        vm.expectRevert(CarbonCredit.InvalidAmount.selector);

        credit.mintCredit(projectOwner, 1, auditHash, 2026, 0);
    }

    function testCannotMintForUnknownProject() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        vm.expectRevert();

        credit.mintCredit(projectOwner, 999, auditHash, 2026, 2900);
    }

    function testNonIssuerCannotMintCredit() public {
        address attacker = address(0x999);

        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(attacker);

        vm.expectRevert();

        credit.mintCredit(attacker, 1, auditHash, 2026, 2900);
    }

    function testRetireCredit() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        uint256 creditId = credit.mintCredit(
            projectOwner,
            1,
            auditHash,
            2026,
            2900
        );

        vm.prank(projectOwner);

        credit.retire(
            creditId,
            100,
            "ABC Manufacturing",
            "2026 Q3 emissions offset"
        );

        assertEq(credit.balanceOf(projectOwner, creditId), 2800);

        CarbonCredit.CreditBatch memory batch = credit.getBatch(creditId);

        assertEq(batch.totalIssued, 2900);

        assertEq(batch.totalRetired, 100);
    }

    function testCannotRetireMoreThanBalance() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        uint256 creditId = credit.mintCredit(
            projectOwner,
            1,
            auditHash,
            2026,
            100
        );

        vm.prank(projectOwner);

        vm.expectRevert();

        credit.retire(
            creditId,
            200,
            "ABC Manufacturing",
            "2026 Q3 emissions offset"
        );
    }

    function testOtherUserCannotRetireMyCredit() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        uint256 creditId = credit.mintCredit(
            projectOwner,
            1,
            auditHash,
            2026,
            2900
        );

        address attacker = address(0x999);

        vm.prank(attacker);

        vm.expectRevert();

        credit.retire(
            creditId,
            100,
            "ABC Manufacturing",
            "2026 Q3 emissions offset"
        );
    }

    function testCannotRetireZero() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        uint256 creditId = credit.mintCredit(
            projectOwner,
            1,
            auditHash,
            2026,
            2900
        );
        vm.prank(projectOwner);

        vm.expectRevert(CarbonCredit.InvalidRetireAmount.selector);

        credit.retire(creditId, 0, "ABC Manufacturing", "2026 Q3 emissions offset");
    }

    event CreditRetired(
        uint256 indexed retirementId,
        uint256 indexed creditId,
        address indexed account,
        uint256 amount,
        string beneficiary,
        string reason
    );

    function testEmitCreditRetiredEvent() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        uint256 creditId = credit.mintCredit(
            projectOwner,
            1,
            auditHash,
            2026,
            2900
        );

        vm.expectEmit(false, true, true, true);

        emit CreditRetired(
            123,
            creditId,
            projectOwner,
            100,
            "ABC Manufacturing",
            "2026 Q3 emissions offset"
        );

        vm.prank(projectOwner);

        credit.retire(
            creditId,
            100,
            "ABC Manufacturing",
            "2026 Q3 emissions offset"
        );
    }

    function testRetirementRecord() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        uint256 creditId = credit.mintCredit(
            projectOwner,
            1,
            auditHash,
            2026,
            2900
        );

        vm.prank(projectOwner);

        uint256 retirementId = credit.retire(
            creditId,
            100,
            "ABC Manufacturing",
            "2026 Q3 emissions offset"
        );

        assertEq(retirementId, 1);

        CarbonCredit.RetirementRecord memory record = credit.getRetirement(
            retirementId
        );

        assertEq(record.creditId, creditId);

        assertEq(record.account, projectOwner);

        assertEq(record.amount, 100);

        assertEq(record.beneficiary, "ABC Manufacturing");

        assertEq(record.reason, "2026 Q3 emissions offset");

        assertGt(record.retiredAt, 0);
    }

    function testCannotMintCreditToZeroAddress() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        vm.expectRevert(CarbonCredit.InvalidRecipient.selector);

        credit.mintCredit(address(0), 1, auditHash, 2026, 2900);
    }

    function testCannotMintWithEmptyAuditHash() public {
        vm.prank(admin);

        vm.expectRevert(CarbonCredit.InvalidAuditHash.selector);

        credit.mintCredit(projectOwner, 1, bytes32(0), 2026, 2900);
    }

    function testCannotRetireUnknownCredit() public {
        vm.prank(projectOwner);

        vm.expectRevert(
            abi.encodeWithSelector(
                CarbonCredit.CreditBatchNotFound.selector,
                999
            )
        );

        credit.retire(999, 100, "ABC Manufacturing", "offset");
    }

    function testCannotRetireWithEmptyBeneficiary() public {
        bytes32 auditHash = keccak256(bytes("AUDIT-001"));

        vm.prank(admin);

        uint256 creditId = credit.mintCredit(
            projectOwner,
            1,
            auditHash,
            2026,
            2900
        );

        vm.prank(projectOwner);

        vm.expectRevert(CarbonCredit.EmptyBeneficiary.selector);

        credit.retire(creditId, 100, "", "offset");
    }
}
