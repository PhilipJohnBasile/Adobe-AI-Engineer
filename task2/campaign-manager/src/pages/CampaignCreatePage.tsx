import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CampaignForm } from '../components/CampaignForm';
import { Campaign } from '../types/Campaign';

export default function CampaignCreatePage() {
  const navigate = useNavigate();

  const handleSave = (campaign: Campaign) => {
    navigate('/campaigns');
  };

  const handleCancel = () => {
    navigate('/campaigns');
  };

  return (
    <CampaignForm
      onSave={handleSave}
      onCancel={handleCancel}
    />
  );
}