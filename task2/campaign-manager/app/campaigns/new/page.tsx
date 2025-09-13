'use client';

import React from 'react';
import { Provider, defaultTheme, View } from '@adobe/react-spectrum';
import { CampaignForm } from '../../../src/components/CampaignForm';
import { Campaign } from '../../../src/types/Campaign';
import { useRouter } from 'next/navigation';

export default function NewCampaignPage() {
  const router = useRouter();

  const handleSave = (campaign: Campaign) => {
    router.push('/campaigns');
  };

  const handleCancel = () => {
    router.push('/campaigns');
  };

  return (
    <CampaignForm
      onSave={handleSave}
      onCancel={handleCancel}
    />
  );
}