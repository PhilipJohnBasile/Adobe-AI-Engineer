import { json } from "@remix-run/node";
import { readCampaign, writeCampaign, CAMPAIGN_DIR } from "~/lib/campaignFs";
import { CampaignSchema } from "~/lib/campaignSchema";
import type { Campaign } from "~/lib/campaignSchema";
import * as fs from 'fs';
import * as path from 'path';

// GET /api/campaigns - List all campaigns from filesystem
export async function GET() {
  try {
    // Read all JSON files from the campaigns directory
    const files = fs.readdirSync(CAMPAIGN_DIR);
    const jsonFiles = files.filter(file => file.endsWith('.json'));
    
    const campaigns = await Promise.all(
      jsonFiles.map(async (filename) => {
        try {
          const campaignId = path.basename(filename, '.json');
          const campaignData = await readCampaign(campaignId);
          const validatedCampaign = CampaignSchema.parse(campaignData);
          
          const filePath = path.join(CAMPAIGN_DIR, filename);
          return {
            ...validatedCampaign,
            id: validatedCampaign.campaign_id || campaignId,
            name: validatedCampaign.campaign_name,
            status: determineStatus(validatedCampaign),
            created_date: fs.statSync(filePath).ctime.toISOString()
          };
        } catch (error) {
          console.warn(`Failed to load ${filename}:`, error);
          return null;
        }
      })
    );
    
    // Filter out failed loads
    const validCampaigns = campaigns.filter(campaign => campaign !== null);
    console.log(`Loaded ${validCampaigns.length} campaigns from filesystem`);
    
    return json(validCampaigns);
  } catch (error) {
    console.error('Error loading campaigns:', error);
    return json({ error: 'Failed to load campaigns' }, { status: 500 });
  }
}

// POST /api/campaigns - Create new campaign JSON file
export async function POST({ request }: { request: Request }) {
  try {
    // Parse the request body
    const campaignData = await request.json();
    
    // Generate campaign ID if not provided
    if (!campaignData.campaign_id) {
      campaignData.campaign_id = `CAMPAIGN_${Date.now()}`;
    }
    
    const campaignId = campaignData.campaign_id;
    const filePath = path.join(CAMPAIGN_DIR, `${campaignId}.json`);
    
    // Check if file already exists
    if (fs.existsSync(filePath)) {
      return json({ error: 'Campaign already exists' }, { status: 409 });
    }
    
    // Validate with Zod schema
    const validatedCampaign = CampaignSchema.parse(campaignData);
    
    // Use the proper filesystem utility
    await writeCampaign(campaignId, validatedCampaign);
    
    console.log(`Created new campaign ${campaignId} in filesystem`);
    
    return json({ success: true, campaign: validatedCampaign }, { status: 201 });
  } catch (error) {
    console.error('Error creating campaign:', error);
    return json({ error: 'Failed to create campaign' }, { status: 500 });
  }
}

// Helper function to determine campaign status
function determineStatus(campaign: any): 'pending' | 'active' | 'completed' {
  const now = new Date();
  const startDate = new Date(campaign.campaign_start_date || '');
  const endDate = new Date(campaign.campaign_end_date || '');
  
  if (now < startDate) {
    return 'pending';
  } else if (now >= startDate && now <= endDate) {
    return 'active';
  } else {
    return 'completed';
  }
}