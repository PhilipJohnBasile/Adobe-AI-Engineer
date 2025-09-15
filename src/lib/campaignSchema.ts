import { z } from "zod";

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
  products: z.array(z.object({
    id: z.string(), 
    name: z.string(), 
    category: z.string(), 
    description: z.string(),
    key_benefits: z.array(z.string()),
    target_price: z.string(),
    messaging: z.object({ primary: z.string(), secondary: z.string() }),
    existing_assets: z.array(z.string())
  })),
  target_regions: z.array(z.object({
    region: z.string(),
    countries: z.array(z.string()),
    languages: z.array(z.string()),
    cultural_notes: z.string(),
    messaging_adaptation: z.object({
      tone: z.string(), 
      themes: z.array(z.string()), 
      local_context: z.string()
    })
  })),
  creative_requirements: z.object({
    formats: z.array(z.object({
      name: z.string(), 
      dimensions: z.string(), 
      platform: z.string(), 
      usage: z.string()
    })),
    brand_requirements: z.object({
      logo_placement: z.string(),
      color_compliance: z.string(),
      typography: z.string(),
      messaging: z.string()
    })
  }),
  budget_allocation: z.object({
    total_budget: z.string(),
    genai_budget: z.string(),
    estimated_assets: z.number(),
    cost_per_asset: z.string()
  }),
  success_metrics: z.object({
    primary_kpis: z.array(z.string()),
    target_metrics: z.object({
      awareness_lift: z.string(),
      engagement_rate: z.string(),
      seasonal_conversion: z.string(),
      global_reach: z.string()
    })
  }),
  deliverables: z.object({
    total_assets: z.number(),
    breakdown: z.record(z.string(), z.number()),
    formats_per_product: z.record(z.string(), z.number())
  })
});

export type Campaign = z.infer<typeof CampaignSchema>;