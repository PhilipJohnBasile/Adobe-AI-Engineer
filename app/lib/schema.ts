import { z } from 'zod';

const MessagingSchema = z.object({
  primary: z.string(),
  secondary: z.string()
});

const ProductSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  description: z.string(),
  key_benefits: z.array(z.string()),
  target_price: z.string(),
  messaging: MessagingSchema,
  existing_assets: z.array(z.string())
});

const RegionSchema = z.object({
  region: z.string(),
  countries: z.array(z.string()),
  languages: z.array(z.string()),
  cultural_notes: z.string(),
  messaging_adaptation: z.object({
    tone: z.string(),
    themes: z.array(z.string()),
    local_context: z.string()
  })
});

const FormatSchema = z.object({
  name: z.string(),
  dimensions: z.string(),
  platform: z.string(),
  usage: z.string()
});

const BrandRequirementsSchema = z.object({
  logo_placement: z.string(),
  color_compliance: z.string(),
  typography: z.string(),
  messaging: z.string()
});

const CreativeRequirementsSchema = z.object({
  formats: z.array(FormatSchema),
  brand_requirements: BrandRequirementsSchema
});

const BudgetAllocationSchema = z.object({
  total_budget: z.string(),
  genai_budget: z.string(),
  estimated_assets: z.number(),
  cost_per_asset: z.string()
});

const TargetMetricsSchema = z.object({
  awareness_lift: z.string(),
  engagement_rate: z.string(),
  seasonal_conversion: z.string(),
  global_reach: z.string()
});

const SuccessMetricsSchema = z.object({
  primary_kpis: z.array(z.string()),
  target_metrics: TargetMetricsSchema
});

const DeliverablesSchema = z.object({
  total_assets: z.number(),
  breakdown: z.record(z.number()),
  formats_per_product: z.record(z.number())
});

export const CampaignSchema = z.object({
  campaign_id: z.string(),
  campaign_name: z.string(),
  client: z.string(),
  campaign_start_date: z.string(),
  campaign_end_date: z.string(),
  campaign_message: z.object({
    primary_headline: z.string(),
    secondary_headline: z.string(),
    brand_voice: z.string(),
    seasonal_theme: z.string()
  }),
  target_audience: z.object({
    primary: z.object({
      demographics: z.string(),
      psychographics: z.string(),
      behavior: z.string()
    })
  }),
  products: z.array(ProductSchema),
  target_regions: z.array(RegionSchema),
  creative_requirements: CreativeRequirementsSchema,
  budget_allocation: BudgetAllocationSchema,
  success_metrics: SuccessMetricsSchema,
  deliverables: DeliverablesSchema
});

export type Campaign = z.infer<typeof CampaignSchema>;
export type Product = z.infer<typeof ProductSchema>;
export type Region = z.infer<typeof RegionSchema>;
export type CreativeFormat = z.infer<typeof FormatSchema>;