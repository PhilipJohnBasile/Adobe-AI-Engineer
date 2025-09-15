import fs from 'fs/promises';
import path from 'path';
import { CampaignSchema, Campaign } from './schema';

const CAMPAIGN_DIR = path.join(process.cwd(), "data/campaigns");

const fileFor = (id: string) => path.join(CAMPAIGN_DIR, `${id}.json`);

// Deep merge helper to preserve unknown keys
function deepMerge(target: any, source: any): any {
  const result = { ...target };
  
  for (const key in source) {
    if (source[key] !== null && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      if (target[key] && typeof target[key] === 'object' && !Array.isArray(target[key])) {
        result[key] = deepMerge(target[key], source[key]);
      } else {
        result[key] = { ...source[key] };
      }
    } else {
      result[key] = source[key];
    }
  }
  
  return result;
}

export async function readCampaign(id: string): Promise<Campaign> {
  try {
    const raw = await fs.readFile(fileFor(id), "utf8");
    const data = JSON.parse(raw);
    return CampaignSchema.parse(data);
  } catch (error) {
    throw new Error(`Failed to read campaign ${id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

export async function writeCampaign(id: string, data: any): Promise<Campaign> {
  try {
    // Ensure directory exists
    await fs.mkdir(CAMPAIGN_DIR, { recursive: true });
    
    // Validate with Zod before writing
    const parsed = CampaignSchema.parse(data);
    
    await fs.writeFile(fileFor(id), JSON.stringify(parsed, null, 2), "utf8");
    return parsed;
  } catch (error) {
    throw new Error(`Failed to write campaign ${id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

export async function updateCampaign(id: string, updates: Partial<Campaign>): Promise<Campaign> {
  try {
    // Read current campaign to preserve unknown keys
    const current = await readCampaign(id);
    
    // Merge old + edited
    const merged = deepMerge(current, updates);
    
    // Validate and write
    return await writeCampaign(id, merged);
  } catch (error) {
    throw new Error(`Failed to update campaign ${id}: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

export async function campaignExists(id: string): Promise<boolean> {
  try {
    await fs.access(fileFor(id));
    return true;
  } catch {
    return false;
  }
}

export { deepMerge };