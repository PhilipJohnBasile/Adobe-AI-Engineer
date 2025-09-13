import { NextRequest, NextResponse } from 'next/server';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { join } from 'path';

const CAMPAIGNS_FILE = join(process.cwd(), 'campaigns.json');

// Ensure campaigns.json exists
if (!existsSync(CAMPAIGNS_FILE)) {
  writeFileSync(CAMPAIGNS_FILE, JSON.stringify([]));
}

// GET /api/campaigns
export async function GET() {
  try {
    const data = readFileSync(CAMPAIGNS_FILE, 'utf8');
    const campaigns = JSON.parse(data);
    return NextResponse.json(campaigns);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to read campaigns' }, { status: 500 });
  }
}

// POST /api/campaigns
export async function POST(request: NextRequest) {
  try {
    const campaign = await request.json();
    const data = readFileSync(CAMPAIGNS_FILE, 'utf8');
    const campaigns = JSON.parse(data);
    
    const newCampaign = {
      ...campaign,
      id: Date.now().toString(),
      createdAt: new Date().toISOString()
    };
    
    campaigns.push(newCampaign);
    writeFileSync(CAMPAIGNS_FILE, JSON.stringify(campaigns, null, 2));
    
    return NextResponse.json(newCampaign);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to create campaign' }, { status: 500 });
  }
}