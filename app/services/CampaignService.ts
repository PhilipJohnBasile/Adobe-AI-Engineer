import { Campaign, CampaignValidation, ComplianceCheck } from '../types/Campaign';

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

// Use relative path for Azure deployment, fallback to localhost for dev
const API_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
  ? 'http://localhost:3002/api'
  : '/api';

export class CampaignService {

  // Campaign CRUD operations
  static async getAllCampaigns(): Promise<Campaign[]> {
    try {
      const response = await fetch(`${API_BASE}/campaigns`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error loading campaigns:', error);
      throw error;
    }
  }

  static async getCampaign(campaignId: string): Promise<Campaign> {
    try {
      const response = await fetch(`${API_BASE}/campaigns/${campaignId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching campaign:', error);
      throw error;
    }
  }

  static async createCampaign(campaign: Partial<Campaign>): Promise<Campaign> {
    try {
      const response = await fetch(`${API_BASE}/campaigns`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(campaign),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error creating campaign:', error);
      throw error;
    }
  }

  static async updateCampaign(campaignId: string, campaign: Partial<Campaign>): Promise<Campaign> {
    try {
      const response = await fetch(`${API_BASE}/campaigns/${campaignId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(campaign),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error updating campaign:', error);
      throw error;
    }
  }

  static async deleteCampaign(campaignId: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE}/campaigns/${campaignId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('Error deleting campaign:', error);
      throw error;
    }
  }

  // AI-powered campaign idea generation
  static async generateCampaignIdea(prompt: string): Promise<Partial<Campaign>> {
    try {
      const response = await fetch(`${API_BASE}/campaigns/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error generating campaign idea:', error);
      throw error;
    }
  }

  // Brand compliance and legal validation
  static async validateCampaign(campaign: Campaign): Promise<CampaignValidation> {
    try {
      const response = await fetch(`${API_BASE}/campaigns/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(campaign),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error validating campaign:', error);
      throw error;
    }
  }

  // Run pipeline to generate assets
  static async runPipeline(campaignId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE}/campaigns/${campaignId}/generate`, {
        method: 'POST',
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error running pipeline:', error);
      throw error;
    }
  }

  // Get generation logs and reports
  static async getGenerationLogs(campaignId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE}/campaigns/${campaignId}/logs`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching logs:', error);
      throw error;
    }
  }

  // Get existing generated assets
  static async getGeneratedAssets(campaignId: string): Promise<any> {
    try {
      const response = await fetch(`${API_BASE}/campaigns/${campaignId}/assets`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching assets:', error);
      throw error;
    }
  }
}

export class ComplianceService {
  static validateBrandCompliance(campaign: Campaign): ComplianceCheck[] {
    const checks: ComplianceCheck[] = [];

    // Check for brand color compliance requirement
    const requiredColor = '#DA020E';
    const hasRequiredColor = campaign.creative_requirements?.brand_requirements?.color_compliance?.includes?.(requiredColor) || false;
    
    checks.push({
      type: 'brand_color',
      status: hasRequiredColor ? 'passed' : 'failed',
      message: hasRequiredColor ? 'Brand color compliance verified' : `Missing required color ${requiredColor}`,
      score: hasRequiredColor ? 100 : 0
    });

    // Check logo placement requirements
    const logoPlacement = campaign.creative_requirements?.brand_requirements?.logo_placement;
    const validPlacements = ['bottom-right', 'top-left', 'bottom-left', 'top-right'];
    const hasValidPlacement = logoPlacement ? validPlacements.some(placement => logoPlacement.includes(placement)) : false;

    checks.push({
      type: 'logo_placement',
      status: hasValidPlacement ? 'passed' : 'warning',
      message: hasValidPlacement ? 'Logo placement follows brand guidelines' : 'Logo placement may not follow brand guidelines',
      score: hasValidPlacement ? 100 : 70
    });

    // Check brand voice compliance
    const brandVoice = campaign.campaign_message?.brand_voice?.toLowerCase() || '';
    const cocaColaBrandKeywords = ['uplifting', 'inclusive', 'joyful', 'authentic', 'refreshing', 'classic'];
    const brandVoiceScore = cocaColaBrandKeywords.filter(keyword => brandVoice.includes(keyword)).length;

    checks.push({
      type: 'brand_voice',
      status: brandVoiceScore >= 2 ? 'passed' : 'warning',
      message: `Brand voice alignment: ${brandVoiceScore}/${cocaColaBrandKeywords.length} keywords match`,
      score: Math.round((brandVoiceScore / cocaColaBrandKeywords.length) * 100)
    });

    return checks;
  }

  static validateLegalContent(campaign: Campaign): ComplianceCheck[] {
    const checks: ComplianceCheck[] = [];
    
    // Forbidden words for brand compliance
    const forbiddenWords = [
      'pepsi', 'mountain dew', 'dr pepper', 'alcohol', 'beer', 'wine', 
      'competitor', 'unhealthy', 'sugar-free', 'diet', 'zero calories'
    ];

    // Check all text content
    const allText = [
      campaign.campaign_name || '',
      campaign.campaign_message?.primary_headline || '',
      campaign.campaign_message?.secondary_headline || '',
      campaign.campaign_message?.brand_voice || '',
      campaign.campaign_message?.seasonal_theme || '',
      ...(campaign.products || []).flatMap(p => [p.name || '', p.description || '', p.messaging?.primary || '', p.messaging?.secondary || '']),
      ...(campaign.products || []).flatMap(p => p.key_benefits || [])
    ].join(' ').toLowerCase();

    const foundForbiddenWords = forbiddenWords.filter(word => allText.includes(word));

    checks.push({
      type: 'forbidden_words',
      status: foundForbiddenWords.length === 0 ? 'passed' : 'failed',
      message: foundForbiddenWords.length === 0 
        ? 'No prohibited words detected' 
        : `Prohibited words found: ${foundForbiddenWords.join(', ')}`,
      score: foundForbiddenWords.length === 0 ? 100 : Math.max(0, 100 - (foundForbiddenWords.length * 20))
    });

    // Check for health claims compliance
    const healthClaims = ['healthy', 'nutritious', 'vitamin', 'mineral', 'dietary supplement'];
    const foundHealthClaims = healthClaims.filter(claim => allText.includes(claim));

    checks.push({
      type: 'health_claims',
      status: foundHealthClaims.length === 0 ? 'passed' : 'warning',
      message: foundHealthClaims.length === 0
        ? 'No unauthorized health claims detected'
        : `Potential health claims require review: ${foundHealthClaims.join(', ')}`,
      score: foundHealthClaims.length === 0 ? 100 : 80
    });

    // Check for age-appropriate content
    const inappropriateContent = ['adult', 'mature', 'explicit', 'gambling', 'betting'];
    const foundInappropriate = inappropriateContent.filter(word => allText.includes(word));

    checks.push({
      type: 'age_appropriate',
      status: foundInappropriate.length === 0 ? 'passed' : 'failed',
      message: foundInappropriate.length === 0
        ? 'Content is age-appropriate'
        : `Inappropriate content detected: ${foundInappropriate.join(', ')}`,
      score: foundInappropriate.length === 0 ? 100 : 0
    });

    return checks;
  }
}