const hre = require("hardhat");

async function main() {
  const admin = process.env.ADMIN_ADDRESS;
  const oracle = process.env.ORACLE_ADDRESS;

  const [deployer] = await hre.ethers.getSigners();
  const deployerAddr = await deployer.getAddress();

  const adminAddr = admin && admin.length > 0 ? admin : deployerAddr;
  const oracleAddr = oracle && oracle.length > 0 ? oracle : deployerAddr;

  console.log("Deployer:", deployerAddr);
  console.log("Admin:", adminAddr);
  console.log("Oracle:", oracleAddr);

  const Factory = await hre.ethers.getContractFactory("PastoralProtectPool");
  const pool = await Factory.deploy(adminAddr, oracleAddr);
  await pool.waitForDeployment();

  const addr = await pool.getAddress();
  console.log("PastoralProtectPool:", addr);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
