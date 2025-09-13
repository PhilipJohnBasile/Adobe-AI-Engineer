import { NextRequest, NextResponse } from 'next/server';

// Brand compliance validation
const validateBrandCompliance = (campaign: any) => {
  const results = [];
  
  // Check for logo presence
  if (!campaign.brandElements?.logo) {
    results.push({
      level: 'error',
      message: 'Brand logo is required for all campaigns'
    });
  } else {
    results.push({
      level: 'success',
      message: 'Brand logo is present'
    });
  }
  
  // Check brand colors
  const allowedColors = ['#DA020E', '#FFFFFF', '#000000']; // Coca-Cola brand colors
  if (campaign.brandElements?.colors) {
    const validColors = campaign.brandElements.colors.filter((color: string) => 
      allowedColors.includes(color.toUpperCase())
    );
    
    if (validColors.length === 0) {
      results.push({
        level: 'warning',
        message: 'No approved brand colors detected'
      });
    } else {
      results.push({
        level: 'success',
        message: `${validColors.length} approved brand colors used`
      });
    }
  }
  
  return results;
};

// Legal content validation
const validateLegalContent = (campaign: any) => {
  const results = [];
  const prohibitedWords = ['competitor', 'pepsi', 'rival', 'lawsuit', 'controversy'];
  
  const content = `${campaign.name} ${campaign.description} ${campaign.message || ''}`.toLowerCase();
  
  const foundProhibited = prohibitedWords.filter(word => content.includes(word));
  
  if (foundProhibited.length > 0) {
    results.push({
      level: 'error',
      message: `Prohibited terms detected: ${foundProhibited.join(', ')}`
    });
  } else {
    results.push({
      level: 'success',
      message: 'No prohibited terms detected'
    });
  }
  
  return results;
};

// POST /api/campaigns/validate
export async function POST(request: NextRequest) {
  try {
    const campaign = await request.json();
    
    const brandValidation = validateBrandCompliance(campaign);
    const legalValidation = validateLegalContent(campaign);
    
    const validation = {
      isValid: ![...brandValidation, ...legalValidation].some(r => r.level === 'error'),
      brandCompliance: brandValidation,
      legalCompliance: legalValidation,
      timestamp: new Date().toISOString()
    };
    
    return NextResponse.json(validation);
  } catch (error) {
    return NextResponse.json({ error: 'Validation failed' }, { status: 500 });
  }
}