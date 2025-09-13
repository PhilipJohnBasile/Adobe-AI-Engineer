import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

const CAMPAIGNS_FILE = join(process.cwd(), 'campaigns.json');

// GET /api/campaigns/[id]
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const data = readFileSync(CAMPAIGNS_FILE, 'utf8');
    const campaigns = JSON.parse(data);
    const campaign = campaigns.find((c: any) => c.id === params.id);
    
    if (!campaign) {
      return NextResponse.json({ error: 'Campaign not found' }, { status: 404 });
    }
    
    return NextResponse.json(campaign);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to read campaign' }, { status: 500 });
  }
}

// PUT /api/campaigns/[id]
export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const updatedCampaign = await request.json();
    const data = readFileSync(CAMPAIGNS_FILE, 'utf8');
    const campaigns = JSON.parse(data);
    
    const index = campaigns.findIndex((c: any) => c.id === params.id);
    if (index === -1) {
      return NextResponse.json({ error: 'Campaign not found' }, { status: 404 });
    }
    
    campaigns[index] = { ...campaigns[index], ...updatedCampaign, id: params.id };
    writeFileSync(CAMPAIGNS_FILE, JSON.stringify(campaigns, null, 2));
    
    return NextResponse.json(campaigns[index]);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to update campaign' }, { status: 500 });
  }
}

// DELETE /api/campaigns/[id]
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const data = readFileSync(CAMPAIGNS_FILE, 'utf8');
    const campaigns = JSON.parse(data);
    
    const filteredCampaigns = campaigns.filter((c: any) => c.id !== params.id);
    if (filteredCampaigns.length === campaigns.length) {
      return NextResponse.json({ error: 'Campaign not found' }, { status: 404 });
    }
    
    writeFileSync(CAMPAIGNS_FILE, JSON.stringify(filteredCampaigns, null, 2));
    
    return NextResponse.json({ message: 'Campaign deleted successfully' });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to delete campaign' }, { status: 500 });
  }
}