import { json } from "@remix-run/node";
import { readCampaign, writeCampaign } from "~/lib/campaignFs";
import { CampaignSchema } from "~/lib/campaignSchema";
import type { Campaign } from "~/lib/campaignSchema";

// GET /api/campaigns/[id] - Load campaign JSON from filesystem
export async function GET({ params }: { params: { id: string } }) {
  try {
    const campaignId = params.id;
    
    // Use the proper filesystem utility
    const campaignData = await readCampaign(campaignId);
    
    // Validate with Zod schema
    const validatedCampaign = CampaignSchema.parse(campaignData);
    
    console.log(`Loaded campaign ${campaignId} from filesystem`);
    
    return json(validatedCampaign);
  } catch (error) {
    console.error('Error loading campaign:', error);
    if (error instanceof Error && error.message.includes('ENOENT')) {
      return json({ error: 'Campaign not found' }, { status: 404 });
    }
    return json({ error: 'Failed to load campaign' }, { status: 500 });
  }
}

// PUT /api/campaigns/[id] - Save campaign JSON to filesystem
export async function PUT({ params, request }: { params: { id: string }, request: Request }) {
  try {
    const campaignId = params.id;
    
    // Parse the request body
    const campaignData = await request.json();
    
    // Ensure the campaign_id matches the URL parameter
    campaignData.campaign_id = campaignId;
    
    // Validate with Zod schema
    const validatedCampaign = CampaignSchema.parse(campaignData);
    
    // Use the proper filesystem utility
    await writeCampaign(campaignId, validatedCampaign);
    
    console.log(`Saved campaign ${campaignId} to filesystem`);
    
    return json({ success: true, campaign: validatedCampaign });
  } catch (error) {
    console.error('Error saving campaign:', error);
    return json({ error: 'Failed to save campaign' }, { status: 500 });
  }
}