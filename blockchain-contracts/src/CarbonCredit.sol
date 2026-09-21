// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC1155} from "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

import {CarbonProjectNFT} from "./CarbonProjectNFT.sol";

contract CarbonCredit is ERC1155, AccessControl {
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");

    CarbonProjectNFT public immutable projectNFT;

    uint256 private _nextRetirementId = 1;

    struct CreditBatch {
        uint256 projectTokenId;
        bytes32 auditHash;
        uint64 vintage;
        uint256 totalIssued;
        uint256 totalRetired;
    }

    struct RetirementRecord {
        uint256 creditId;
        address account;
        uint256 amount;
        uint64 retiredAt;
        string beneficiary;
        string reason;
    }

    uint256 private _nextCreditId = 1;

    mapping(uint256 => CreditBatch) private _batches;

    mapping(bytes32 => uint256) private _creditIdByAuditHash;

    mapping(uint256 => RetirementRecord) private _retirements;

    error InvalidAmount();

    error AuditAlreadyMinted(bytes32 auditHash);

    error InvalidRecipient();
    error InvalidAuditHash();
    error InvalidVintage();
    error CreditBatchNotFound(uint256 creditId);
    error EmptyBeneficiary();
    error RetirementNotFound(uint256 retirementId);

    event CreditMinted(
        uint256 indexed creditId,
        uint256 indexed projectTokenId,
        bytes32 indexed auditHash,
        address recipient,
        uint64 vintage,
        uint256 amount
    );

    event CreditRetired(
        uint256 indexed retirementId,
        uint256 indexed creditId,
        address indexed account,
        uint256 amount,
        string beneficiary,
        string reason
    );

    error InvalidRetireAmount();

    constructor(address admin, address projectNFTAddress) ERC1155("") {
        projectNFT = CarbonProjectNFT(projectNFTAddress);

        _grantRole(DEFAULT_ADMIN_ROLE, admin);

        _grantRole(ISSUER_ROLE, admin);
    }

    function mintCredit(
        address to,
        uint256 projectTokenId,
        bytes32 auditHash,
        uint64 vintage,
        uint256 amount
    ) external onlyRole(ISSUER_ROLE) returns (uint256 creditId) {
        if (to == address(0)) {
            revert InvalidRecipient();
        }

        if (auditHash == bytes32(0)) {
            revert InvalidAuditHash();
        }

        if (vintage == 0) {
            revert InvalidVintage();
        }

        if (amount == 0) {
            revert InvalidAmount();
        }

        projectNFT.ownerOf(projectTokenId);

        if (_creditIdByAuditHash[auditHash] != 0) {
            revert AuditAlreadyMinted(auditHash);
        }

        creditId = _nextCreditId++;

        _batches[creditId] = CreditBatch({
            projectTokenId: projectTokenId,
            auditHash: auditHash,
            vintage: vintage,
            totalIssued: amount,
            totalRetired: 0
        });

        _creditIdByAuditHash[auditHash] = creditId;

        _mint(to, creditId, amount, "");

        emit CreditMinted(
            creditId,
            projectTokenId,
            auditHash,
            to,
            vintage,
            amount
        );
    }

    function retire(
        uint256 creditId,
        uint256 amount,
        string calldata beneficiary,
        string calldata reason
    ) external returns (uint256 retirementId) {
        _requireBatchExists(creditId);

        if (amount == 0) {
            revert InvalidRetireAmount();
        }

        if (bytes(beneficiary).length == 0) {
            revert EmptyBeneficiary();
        }

        _burn(msg.sender, creditId, amount);

        _batches[creditId].totalRetired += amount;

        retirementId = _nextRetirementId++;

        _retirements[retirementId] = RetirementRecord({
            creditId: creditId,
            account: msg.sender,
            amount: amount,
            retiredAt: uint64(block.timestamp),
            beneficiary: beneficiary,
            reason: reason
        });

        emit CreditRetired(
            retirementId,
            creditId,
            msg.sender,
            amount,
            beneficiary,
            reason
        );
    }

    function getRetirement(
        uint256 retirementId
    ) external view returns (RetirementRecord memory) {
        _requireRetirementExists(retirementId);
        return _retirements[retirementId];
    }

    function getBatch(
        uint256 creditId
    ) external view returns (CreditBatch memory) {
        _requireBatchExists(creditId);
        return _batches[creditId];
    }

    function creditIdByAuditHash(
        bytes32 auditHash
    ) external view returns (uint256) {
        return _creditIdByAuditHash[auditHash];
    }

    function supportsInterface(
        bytes4 interfaceId
    ) public view override(ERC1155, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }

    function _requireBatchExists(uint256 creditId) internal view {
        if (_batches[creditId].totalIssued == 0) {
            revert CreditBatchNotFound(creditId);
        }
    }
    function _requireRetirementExists(uint256 retirementId) internal view {
        if (_retirements[retirementId].account == address(0)) {
            revert RetirementNotFound(retirementId);
        }
    }
}
