import fs from "fs/promises";
import path from "path";

export const CAMPAIGN_DIR = path.join(process.cwd(), "..", "campaigns");
const ensureDir = async () => fs.mkdir(CAMPAIGN_DIR, { recursive: true });

export const fileFor = (id: string) =>
  path.join(CAMPAIGN_DIR, `${id}.json`);

export async function readCampaign(id: string) {
  await ensureDir();
  
  // First, try to read the file directly by ID
  try {
    const raw = await fs.readFile(fileFor(id), "utf8");
    return JSON.parse(raw);
  } catch (error) {
    // If that fails, search all campaign files for matching campaign_id
    const files = await fs.readdir(CAMPAIGN_DIR);
    const jsonFiles = files.filter(file => file.endsWith('.json'));
    
    for (const file of jsonFiles) {
      try {
        const filePath = path.join(CAMPAIGN_DIR, file);
        const content = await fs.readFile(filePath, "utf8");
        const campaign = JSON.parse(content);
        
        if (campaign.campaign_id === id) {
          return campaign;
        }
      } catch {
        // Skip files that can't be parsed
        continue;
      }
    }
    
    // If no match found, throw the original error
    throw error;
  }
}

export async function writeCampaign(id: string, data: any) {
  await ensureDir();
  
  // Try to find existing file by searching for matching campaign_id
  let targetFile = fileFor(id); // default to ID-based filename
  
  try {
    const files = await fs.readdir(CAMPAIGN_DIR);
    const jsonFiles = files.filter(file => file.endsWith('.json'));
    
    for (const file of jsonFiles) {
      try {
        const filePath = path.join(CAMPAIGN_DIR, file);
        const content = await fs.readFile(filePath, "utf8");
        const campaign = JSON.parse(content);
        
        if (campaign.campaign_id === id) {
          targetFile = filePath; // use the existing filename
          break;
        }
      } catch {
        // Skip files that can't be parsed
        continue;
      }
    }
  } catch {
    // If directory read fails, use default filename
  }
  
  await fs.writeFile(targetFile, JSON.stringify(data, null, 2), "utf8");
}