'use client';

import React, { useState, useEffect } from 'react';
import { Provider, defaultTheme, View } from '@adobe/react-spectrum';
import { CampaignForm } from '../../../../src/components/CampaignForm';
import { Campaign } from '../../../../src/types/Campaign';
import { CampaignService } from '../../../../src/services/CampaignService';
import { useRouter, useParams } from 'next/navigation';

export default function EditCampaignPage() {
  const router = useRouter();
  const params = useParams();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCampaign = async () => {
      if (params.id) {
        try {
          const campaignData = await CampaignService.getCampaign(params.id as string);
          setCampaign(campaignData);
        } catch (error) {
          console.error('Failed to load campaign:', error);
          router.push('/campaigns');
        } finally {
          setLoading(false);
        }
      }
    };

    loadCampaign();
  }, [params.id, router]);

  const handleSave = (campaign: Campaign) => {
    router.push('/campaigns');
  };

  const handleCancel = () => {
    router.push('/campaigns');
  };

  if (loading) {
    return <View padding="size-400">Loading campaign...</View>;
  }

  if (!campaign) {
    return <View padding="size-400">Campaign not found</View>;
  }

  return (
    <CampaignForm
      campaign={campaign}
      onSave={handleSave}
      onCancel={handleCancel}
    />
  );
}