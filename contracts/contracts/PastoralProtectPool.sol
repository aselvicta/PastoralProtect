// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {AccessControl} from "@openzeppelin/contracts/access/AccessControl.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// @title PastoralProtectPool
/// @notice Climate-triggered livestock protection pool: zones, policies, oracle-validated triggers, payout recording.
contract PastoralProtectPool is AccessControl, ReentrancyGuard {
    bytes32 public constant ORACLE_ROLE = keccak256("ORACLE_ROLE");

    struct Zone {
        uint256 zoneId;
        string name;
        /// NDVI stored in micro-units (e.g. 0.35 == 350_000)
        uint256 ndviThresholdMicro;
        bool isActive;
    }

    struct Policy {
        address farmerWallet;
        string farmerId;
        uint256 zoneId;
        uint256 livestockCount;
        uint256 premiumPaid;
        bool isActive;
        uint256 enrolledAt;
        uint256 lastPayoutWeek;
    }

    uint256 public nextPolicyId = 1;

    mapping(uint256 => Zone) public zones;
    mapping(uint256 => bool) public zonesInitialized;
    mapping(uint256 => Policy) public policies;
    /// @dev zoneId => count of active policies
    mapping(uint256 => uint256) public activePoliciesByZone;

    uint256 public totalPremiums;
    uint256 public totalPayoutsRecorded;
    uint256 public activePolicies;

    event ZoneUpdated(
        uint256 indexed zoneId,
        string name,
        uint256 ndviThresholdMicro,
        bool isActive
    );
    event PolicyEnrolled(
        uint256 indexed policyId,
        string farmerId,
        uint256 indexed zoneId,
        uint256 livestockCount,
        uint256 premiumPaid,
        address farmerWallet
    );
    event TriggerValidated(
        uint256 indexed zoneId,
        uint256 week,
        uint256 ndviMicro,
        uint256 thresholdMicro
    );
    event PayoutExecuted(
        uint256 indexed policyId,
        uint256 indexed zoneId,
        uint256 week,
        uint256 amount,
        string farmerId
    );

    constructor(address admin, address oracle) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ORACLE_ROLE, oracle);
    }

    function addZone(
        uint256 zoneId,
        string calldata name,
        uint256 ndviThresholdMicro,
        bool isActive
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        zones[zoneId] = Zone({
            zoneId: zoneId,
            name: name,
            ndviThresholdMicro: ndviThresholdMicro,
            isActive: isActive
        });
        zonesInitialized[zoneId] = true;
        emit ZoneUpdated(zoneId, name, ndviThresholdMicro, isActive);
    }

    function updateZoneThreshold(
        uint256 zoneId,
        uint256 newNdviThresholdMicro
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(zonesInitialized[zoneId], "zone");
        zones[zoneId].ndviThresholdMicro = newNdviThresholdMicro;
        emit ZoneUpdated(
            zoneId,
            zones[zoneId].name,
            newNdviThresholdMicro,
            zones[zoneId].isActive
        );
    }

    function setZoneActive(uint256 zoneId, bool isActive) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(zonesInitialized[zoneId], "zone");
        zones[zoneId].isActive = isActive;
        emit ZoneUpdated(
            zoneId,
            zones[zoneId].name,
            zones[zoneId].ndviThresholdMicro,
            isActive
        );
    }

    function enrollPolicy(
        string calldata farmerId,
        uint256 zoneId,
        uint256 livestockCount,
        address farmerWallet
    ) external payable onlyRole(DEFAULT_ADMIN_ROLE) returns (uint256 policyId) {
        require(zonesInitialized[zoneId] && zones[zoneId].isActive, "zone");
        require(livestockCount > 0, "livestock");
        require(msg.value > 0, "premium");
        require(bytes(farmerId).length > 0, "farmer");

        policyId = nextPolicyId++;
        policies[policyId] = Policy({
            farmerWallet: farmerWallet,
            farmerId: farmerId,
            zoneId: zoneId,
            livestockCount: livestockCount,
            premiumPaid: msg.value,
            isActive: true,
            enrolledAt: block.timestamp,
            lastPayoutWeek: 0
        });

        totalPremiums += msg.value;
        activePolicies += 1;
        activePoliciesByZone[zoneId] += 1;

        emit PolicyEnrolled(
            policyId,
            farmerId,
            zoneId,
            livestockCount,
            msg.value,
            farmerWallet
        );
    }

    /// @notice Oracle validates drought (NDVI below threshold) and records payouts in one transaction.
    /// @param ndviMicro current NDVI in micro-units; breach if ndviMicro < threshold.
    function validateAndPayout(
        uint256 zoneId,
        uint256 ndviMicro,
        uint256 week,
        uint256[] calldata policyIds,
        uint256[] calldata amounts
    ) external onlyRole(ORACLE_ROLE) nonReentrant {
        require(zonesInitialized[zoneId] && zones[zoneId].isActive, "zone");
        uint256 threshold = zones[zoneId].ndviThresholdMicro;
        require(ndviMicro < threshold, "no breach");
        require(policyIds.length == amounts.length && policyIds.length > 0, "inputs");

        emit TriggerValidated(zoneId, week, ndviMicro, threshold);

        for (uint256 i = 0; i < policyIds.length; i++) {
            uint256 pid = policyIds[i];
            uint256 amt = amounts[i];
            Policy storage p = policies[pid];
            require(p.isActive, "policy inactive");
            require(p.zoneId == zoneId, "zone mismatch");
            require(p.lastPayoutWeek != week, "duplicate week");
            require(amt > 0, "amount");

            p.lastPayoutWeek = week;
            totalPayoutsRecorded += amt;

            emit PayoutExecuted(pid, zoneId, week, amt, p.farmerId);
        }
    }

    function getPoolMetrics()
        external
        view
        returns (
            uint256 premiums_,
            uint256 payouts_,
            uint256 activePolicyCount
        )
    {
        return (totalPremiums, totalPayoutsRecorded, activePolicies);
    }

    function getPolicy(uint256 policyId) external view returns (Policy memory) {
        return policies[policyId];
    }

    function getZone(uint256 zoneId) external view returns (Zone memory) {
        return zones[zoneId];
    }

    function withdrawFunds(address payable to, uint256 amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(to != address(0), "to");
        (bool ok, ) = to.call{value: amount}("");
        require(ok, "transfer");
    }

    receive() external payable {}
}
