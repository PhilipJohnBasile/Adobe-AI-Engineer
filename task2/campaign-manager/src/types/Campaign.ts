import { z } from "zod";

export const MessagingAdaptation = z.object({
  tone: z.string(),
  themes: z.array(z.string()),
  local_context: z.string(),
});

export const TargetRegion = z.object({
  region: z.string(),
  countries: z.array(z.string()),
  languages: z.array(z.string()),
  cultural_notes: z.string(),
  messaging_adaptation: MessagingAdaptation,
});

export const Product = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  description: z.string(),
  key_benefits: z.array(z.string()),
  target_price: z.string(),           // keep as string like "$1.50"
  messaging: z.object({
    primary: z.string(),
    secondary: z.string(),
  }),
  existing_assets: z.array(z.string()),
});

export const CampaignSchema = z.object({
  campaign_id: z.string(),
  campaign_name: z.string(),
  client: z.string(),
  campaign_start_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  campaign_end_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),

  campaign_message: z.object({
    primary_headline: z.string(),
    secondary_headline: z.string(),
    brand_voice: z.string(),
    seasonal_theme: z.string(),
  }),

  target_audience: z.object({
    primary: z.object({
      demographics: z.string(),
      psychographics: z.string(),
      behavior: z.string(),
    }),
  }),

  products: z.array(Product).min(1),
  target_regions: z.array(TargetRegion).min(1),

  // Optional blocks (accept if present)
  creative_requirements: z.any().optional(),
  budget_allocation: z.any().optional(),
  success_metrics: z.any().optional(),
  deliverables: z.any().optional(),
});

export type Campaign = z.infer<typeof CampaignSchema>;

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