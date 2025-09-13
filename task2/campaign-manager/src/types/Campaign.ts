export interface Product {
  id: string;
  name: string;
  category: string;
  description: string;
  key_benefits: string[];
  target_price: string;
  messaging: {
    primary: string;
    secondary: string;
  };
  existing_assets: string[];
}

export interface Region {
  region: string;
  countries: string[];
  languages: string[];
  cultural_notes: string;
  messaging_adaptation: {
    tone: string;
    themes: string[];
    local_context: string;
  };
}

export interface CreativeFormat {
  name: string;
  dimensions: string;
  platform: string;
  usage: string;
}

export interface Campaign {
  campaign_id: string;
  campaign_name: string;
  client: string;
  campaign_start_date: string;
  campaign_end_date: string;
  campaign_message: {
    primary_headline: string;
    secondary_headline: string;
    brand_voice: string;
    seasonal_theme: string;
  };
  target_audience: {
    primary: {
      demographics: string;
      psychographics: string;
      behavior: string;
    };
  };
  products: Product[];
  target_regions: Region[];
  creative_requirements: {
    formats: CreativeFormat[];
    brand_requirements: {
      logo_placement: string;
      color_compliance: string;
      typography: string;
      messaging: string;
    };
  };
  budget_allocation: {
    total_budget: string;
    genai_budget: string;
    estimated_assets: number;
    cost_per_asset: string;
  };
  success_metrics: {
    primary_kpis: string[];
    target_metrics: {
      awareness_lift: string;
      engagement_rate: string;
      seasonal_conversion: string;
    };
  };
  deliverables: {
    total_assets: number;
    breakdown: Record<string, number>;
    formats_per_product: Record<string, number>;
  };
}

export interface ComplianceCheck {
  type: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  score?: number;
}

export interface CampaignValidation {
  overall_score: number;
  compliance_checks: ComplianceCheck[];
  legal_checks: ComplianceCheck[];
  brand_checks: ComplianceCheck[];
}