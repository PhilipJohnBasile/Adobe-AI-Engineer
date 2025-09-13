'use client';

import React from 'react';
import { Provider, defaultTheme } from '@adobe/react-spectrum';
import CampaignFormCreator from '../../../src/components/CampaignFormCreator';
import { Campaign } from '../../../src/types/Campaign';
import { useRouter } from 'next/navigation';

export default function NewCampaignPage() {
  const router = useRouter();

  const handleSave = async (campaign: Campaign) => {
    const response = await fetch('/api/campaigns', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(campaign)
    });

    if (!response.ok) {
      throw new Error('Failed to create campaign');
    }

    router.push(`/campaigns/${campaign.campaign_id}`);
  };

  const handleCancel = () => {
    router.push('/campaigns');
  };

  return (
    <Provider theme={defaultTheme}>
      <CampaignFormCreator
        onSave={handleSave}
        onCancel={handleCancel}
      />
    </Provider>
  );
}