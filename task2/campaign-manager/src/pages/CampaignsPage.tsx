import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CampaignList } from '../components/CampaignList';
import { Campaign } from '../types/Campaign';

export default function CampaignsPage() {
  const navigate = useNavigate();
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleSelectCampaign = (campaign: Campaign) => {
    navigate(`/campaigns/${campaign.campaign_id}`);
  };

  const handleCreateNew = () => {
    navigate('/campaigns/new');
  };

  const handleEditCampaign = (campaign: Campaign) => {
    navigate(`/campaigns/${campaign.campaign_id}/edit`);
  };

  return (
    <CampaignList
      onSelectCampaign={handleSelectCampaign}
      onCreateNew={handleCreateNew}
      onEditCampaign={handleEditCampaign}
      refreshTrigger={refreshTrigger}
    />
  );
}