// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";

import {ERC721URIStorage} from "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";

contract CarbonProjectNFT is ERC721URIStorage, AccessControl {
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");

    uint256 private _nextTokenId = 1;

    mapping(uint256 => string) private _projectIds;

    mapping(bytes32 => bool) private _projectMinted;

    error ProjectAlreadyMinted(bytes32 projectHash);

    error EmptyProjectId();

    event ProjectMinted(
        uint256 indexed tokenId,
        bytes32 indexed projectHash,
        string projectId,
        address indexed owner
    );

    constructor(address admin) ERC721("CarbonAI Project", "CAIP") {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);

        _grantRole(ISSUER_ROLE, admin);
    }

    function mintProject(
        address to,
        string calldata projectId,
        string calldata metadataURI
    ) external onlyRole(ISSUER_ROLE) returns (uint256) {
        if (bytes(projectId).length == 0) {
            revert EmptyProjectId();
        }

        bytes32 projectHash = keccak256(bytes(projectId));

        if (_projectMinted[projectHash]) {
            revert ProjectAlreadyMinted(projectHash);
        }

        uint256 tokenId = _nextTokenId++;

        _safeMint(to, tokenId);

        _setTokenURI(tokenId, metadataURI);

        _projectIds[tokenId] = projectId;

        _projectMinted[projectHash] = true;

        emit ProjectMinted(tokenId, projectHash, projectId, to);

        return tokenId;
    }

    function projectIdOf(
        uint256 tokenId
    ) external view returns (string memory) {
        ownerOf(tokenId);

        return _projectIds[tokenId];
    }

    function supportsInterface(
        bytes4 interfaceId
    ) public view override(ERC721URIStorage, AccessControl) returns (bool) {
        return super.supportsInterface(interfaceId);
    }
}
