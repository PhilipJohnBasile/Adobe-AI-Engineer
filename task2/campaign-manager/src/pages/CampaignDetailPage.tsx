import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CampaignDetailV2 } from '../components/CampaignDetailV2';
import { Campaign } from '../types/Campaign';

// Mock campaign data (same as in CampaignDetailV2 component)
const mockCampaign: Campaign = {
  campaign_id: "SPRING_REFRESH_2026",
  campaign_name: "Spring Refresh - Coca-Cola Global",
  client: "The Coca-Cola Company", 
  status: "Upcoming",
  campaign_start_date: "2026-03-01",
  campaign_end_date: "2026-05-31",
  campaign_message: {
    primary_headline: "Refresh Your Spring",
    secondary_headline: "New Beginnings Start Here",
    brand_voice: "energetic, optimistic, fresh, inspiring"
  },
  products: [
    {
      id: "coca_cola_classic",
      name: "Coca-Cola Classic", 
      category: "Cola",
      description: "The original and iconic cola taste perfect for spring celebrations",
      key_benefits: ["Classic refreshing taste", "Perfect for spring gatherings", "Iconic brand heritage", "Social connection"],
      target_price: "$1.50"
    }
  ],
  target_regions: ["North America", "Europe", "Asia Pacific"],
  target_demographics: ["Gen Z", "Millennials", "Young Families"],
  primary_channels: ["Social Media", "Digital Display", "Connected TV"],
  budget_allocation: {
    social_media: "$15000",
    digital_display: "$8000", 
    connected_tv: "$12000",
    genai_budget: "$1960"
  }
};

export default function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const handleBack = () => {
    navigate('/campaigns');
  };

  const handleEdit = (campaign: Campaign) => {
    navigate(`/campaigns/${campaign.campaign_id}/edit`);
  };

  // Use mock data for now - the campaign exists and has the comprehensive detail view
  return (
    <CampaignDetailV2
      campaign={mockCampaign}
      onBack={handleBack}
      onEdit={handleEdit}
    />
  );
}