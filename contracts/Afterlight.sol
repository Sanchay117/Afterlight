// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

/// @notice Prototype energy evidence registry; certificates are not accredited RECs or offsets.
/// @dev The verifier and asset registry are trust boundaries. Weather screening stays off chain.
contract Afterlight {
    address public immutable verifier;
    struct Asset { address operator; uint32 capacityWh; }
    struct Certificate {
        bytes32 asset;
        uint64 day;
        uint64 wattHours;
        bytes32 evidenceRoot;
        address owner;
        bool retired;
        bytes32 beneficiary;
    }
    mapping(bytes32 => Asset) public assets;
    mapping(bytes32 => bool) public consumed;
    mapping(uint256 => Certificate) public certificates;
    uint256 public count;
    event AssetRegistered(bytes32 indexed asset, address operator, uint32 capacityWh);
    event Issued(uint256 indexed id, bytes32 indexed asset, uint64 day, uint64 wattHours, bytes32 evidenceRoot);
    event Retired(uint256 indexed id, bytes32 beneficiary);
    error Unauthorized();
    error InvalidClaim();
    error DuplicateInterval(uint8 hour);
    error AlreadyRetired();
    constructor() { verifier = msg.sender; }
    modifier onlyVerifier() { if (msg.sender != verifier) revert Unauthorized(); _; }
    function registerAsset(bytes32 id, address operator, uint32 capacityWh) external onlyVerifier {
        if (id == bytes32(0) || operator == address(0) || capacityWh == 0 || assets[id].operator != address(0)) revert InvalidClaim();
        assets[id] = Asset(operator, capacityWh);
        emit AssetRegistered(id, operator, capacityWh);
    }
    function slot(bytes32 asset, uint64 day, uint8 hour) public pure returns (bytes32) {
        return keccak256(abi.encode(asset, day / 3600 + hour));
    }
    function issue(bytes32 asset, uint64 day, uint32[24] calldata wh, bytes32 root) external onlyVerifier returns (uint256 id) {
        Asset memory a = assets[asset];
        if (a.operator == address(0) || day % 86400 != 0 || root == bytes32(0)) revert InvalidClaim();
        uint64 total;
        for (uint8 i; i < 24; ++i) {
            if (wh[i] > a.capacityWh) revert InvalidClaim();
            // Reserve every interval, including zero generation, so revisions cannot mint twice.
            bytes32 key = slot(asset, day, i);
            if (consumed[key]) revert DuplicateInterval(i);
            consumed[key] = true;
            total += wh[i];
        }
        if (total == 0) revert InvalidClaim();
        id = ++count;
        certificates[id] = Certificate(asset, day, total, root, a.operator, false, bytes32(0));
        emit Issued(id, asset, day, total, root);
    }
    function retire(uint256 id, bytes32 beneficiary) external {
        Certificate storage c = certificates[id];
        if (c.owner != msg.sender || beneficiary == bytes32(0)) revert Unauthorized();
        if (c.retired) revert AlreadyRetired();
        c.retired = true;
        c.beneficiary = beneficiary;
        emit Retired(id, beneficiary);
    }
}
