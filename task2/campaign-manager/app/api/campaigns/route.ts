import { NextRequest, NextResponse } from 'next/server';
import { readdir, readFile } from 'fs/promises';
import { CAMPAIGN_DIR } from '@/lib/campaignFs';
import { existsSync } from 'fs';

// GET /api/campaigns
export async function GET() {
  try {
    if (!existsSync(CAMPAIGN_DIR)) {
      return NextResponse.json([]);
    }

    const files = await readdir(CAMPAIGN_DIR);
    const jsonFiles = files.filter(file => file.endsWith('.json'));
    
    const campaigns = await Promise.all(
      jsonFiles.map(async (file) => {
        try {
          const filePath = `${CAMPAIGN_DIR}/${file}`;
          const content = await readFile(filePath, 'utf8');
          const campaign = JSON.parse(content);
          return {
            id: campaign.campaign_id,
            name: campaign.campaign_name,
            client: campaign.client,
            start_date: campaign.campaign_start_date,
            end_date: campaign.campaign_end_date
          };
        } catch (error) {
          console.error(`Error reading campaign file ${file}:`, error);
          return null;
        }
      })
    );

    return NextResponse.json(campaigns.filter(Boolean));
  } catch (error) {
    console.error('Error listing campaigns:', error);
    return NextResponse.json({ error: 'Failed to read campaigns' }, { status: 500 });
  }
}

// POST /api/campaigns
export async function POST(request: NextRequest) {
  try {
    const campaign = await request.json();
    
    // Use the writeCampaign function to save to filesystem
    const { writeCampaign } = await import('@/lib/campaignFs');
    const { CampaignSchema } = await import('@/lib/campaignSchema');
    
    // Validate the campaign data
    const validatedCampaign = CampaignSchema.parse(campaign);
    
    // Write the campaign to filesystem
    await writeCampaign(validatedCampaign.campaign_id, validatedCampaign);
    
    return NextResponse.json(validatedCampaign);
  } catch (error) {
    console.error('Error creating campaign:', error);
    return NextResponse.json({ error: 'Failed to create campaign' }, { status: 500 });
  }
}