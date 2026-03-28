/**
 * Single StoreConf instance for login.js and server.js so both hit the same on-disk
 * w3access config (see @storacha/access drivers/conf.js + env-paths).
 */
import os from "node:os";
import { StoreConf } from "@storacha/access/stores/store-conf";

const profile = (process.env.STORACHA_PROFILE || "w3up-client").trim();

export const store = new StoreConf({ profile });

export const storePath = store.path;

export function storeDiagnostics() {
  return {
    profile,
    storePath,
    cwd: process.cwd(),
    homedir: os.homedir(),
    user: process.env.USERNAME || process.env.USER || "",
  };
}
