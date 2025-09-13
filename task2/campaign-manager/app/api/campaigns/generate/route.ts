import { NextRequest, NextResponse } from 'next/server';

// Campaign idea generation (mock AI service)
const generateCampaignIdeas = (region: string, target: string) => {
  const ideas = {
    'North America': {
      'Young Adults': [
        'Share a Coke: Campus Edition - Personalized bottles for college students',
        'Coke Studio Sessions - Music collaboration platform',
        'Refresh & Recharge - Energy-focused messaging for busy lifestyles'
      ],
      'Families': [
        'Coke Family Moments - Celebrating togetherness',
        'Holiday Magic with Coke - Seasonal family traditions',
        'Game Night Refresher - Family entertainment focus'
      ]
    },
    'Europe': {
      'Young Adults': [
        'Coke European Tour - Music festival partnerships',
        'Sustainability Heroes - Eco-friendly messaging',
        'Urban Adventures with Coke - City exploration theme'
      ],
      'Families': [
        'Coke Heritage Stories - Local cultural celebrations',
        'Weekend Family Escapes - Outdoor activity focus',
        'Cooking Together with Coke - Food pairing experiences'
      ]
    },
    'Asia Pacific': {
      'Young Adults': [
        'Coke Innovation Lab - Tech-forward experiences',
        'Festival Season Celebrations - Cultural event partnerships',
        'Connect & Share - Social media integration'
      ],
      'Families': [
        'Coke Family Traditions - Honoring local customs',
        'Generational Bonds - Multi-generational messaging',
        'Home Celebration Moments - Intimate gathering focus'
      ]
    }
  };

  return ideas[region as keyof typeof ideas]?.[target as keyof typeof ideas['North America']] || [
    'Global Refresh Campaign - Universal appeal messaging',
    'Taste the Feeling - Emotional connection focus',
    'Share Happiness - Community building theme'
  ];
};

// POST /api/campaigns/generate
export async function POST(request: NextRequest) {
  try {
    const { region, targetAudience, campaignType } = await request.json();
    
    if (!region || !targetAudience) {
      return NextResponse.json({ 
        error: 'Region and target audience are required' 
      }, { status: 400 });
    }
    
    const ideas = generateCampaignIdeas(region, targetAudience);
    
    const generatedCampaigns = ideas.map((idea, index) => ({
      id: `generated-${Date.now()}-${index}`,
      name: idea.split(' - ')[0],
      description: idea.split(' - ')[1] || idea,
      region,
      targetAudience,
      campaignType: campaignType || 'Brand Awareness',
      status: 'draft',
      createdAt: new Date().toISOString(),
      aiGenerated: true
    }));
    
    return NextResponse.json({
      ideas: generatedCampaigns,
      generated: true,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to generate campaign ideas' }, { status: 500 });
  }
}