import fs from "fs/promises";
import path from "path";

export const CAMPAIGN_DIR = path.join(process.cwd(), "..", "campaigns");
const ensureDir = async () => fs.mkdir(CAMPAIGN_DIR, { recursive: true });

export const fileFor = (id: string) =>
  path.join(CAMPAIGN_DIR, `${id}.json`);

export async function readCampaign(id: string) {
  await ensureDir();
  const raw = await fs.readFile(fileFor(id), "utf8");
  return JSON.parse(raw);
}

export async function writeCampaign(id: string, data: any) {
  await ensureDir();
  await fs.writeFile(fileFor(id), JSON.stringify(data, null, 2), "utf8");
}