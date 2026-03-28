const { expect } = require("chai");
const hre = require("hardhat");

describe("PastoralProtectPool", () => {
  async function setup() {
    const [admin, oracle, user] = await hre.ethers.getSigners();
    const F = await hre.ethers.getContractFactory("PastoralProtectPool");
    const pool = await F.deploy(await admin.getAddress(), await oracle.getAddress());
    await pool.waitForDeployment();
    return { pool, admin, oracle, user };
  }

  it("enrolls policy and emits PolicyEnrolled", async () => {
    const { pool, admin, user } = await setup();
    const zoneId = 1n;
    await pool
      .connect(admin)
      .addZone(zoneId, "Arusha North", 350_000n, true);

    await expect(
      pool
        .connect(admin)
        .enrollPolicy("F-001", zoneId, 10n, await user.getAddress(), {
          value: hre.ethers.parseEther("0.01"),
        })
    ).to.emit(pool, "PolicyEnrolled");
  });

  it("oracle validates breach and records payout", async () => {
    const { pool, admin, oracle, user } = await setup();
    const zoneId = 2n;
    await pool.connect(admin).addZone(zoneId, "Manyara", 400_000n, true);

    const t = await pool
      .connect(admin)
      .enrollPolicy("F-002", zoneId, 5n, await user.getAddress(), {
        value: hre.ethers.parseEther("0.02"),
      });
    const rc = await t.wait();
    const ev = rc.logs.find((l) => {
      try {
        return pool.interface.parseLog(l).name === "PolicyEnrolled";
      } catch {
        return false;
      }
    });
    const parsed = pool.interface.parseLog(ev);
    const policyId = parsed.args.policyId;

    await expect(
      pool
        .connect(oracle)
        .validateAndPayout(zoneId, 200_000n, 12n, [policyId], [5000n])
    )
      .to.emit(pool, "TriggerValidated")
      .and.to.emit(pool, "PayoutExecuted");

    const p = await pool.getPolicy(policyId);
    expect(p.lastPayoutWeek).to.equal(12n);
  });

  it("reverts validateAndPayout when NDVI not below threshold", async () => {
    const { pool, admin, oracle, user } = await setup();
    const zoneId = 3n;
    await pool.connect(admin).addZone(zoneId, "Test", 100_000n, true);
    const t = await pool
      .connect(admin)
      .enrollPolicy("F-003", zoneId, 2n, await user.getAddress(), {
        value: hre.ethers.parseEther("0.01"),
      });
    const rc = await t.wait();
    const ev = rc.logs.find((l) => {
      try {
        return pool.interface.parseLog(l).name === "PolicyEnrolled";
      } catch {
        return false;
      }
    });
    const policyId = pool.interface.parseLog(ev).args.policyId;

    await expect(
      pool
        .connect(oracle)
        .validateAndPayout(zoneId, 500_000n, 1n, [policyId], [1000n])
    ).to.be.revertedWith("no breach");
  });
});
