'use client';

import React, { useState, useEffect } from 'react';
import { Provider, defaultTheme, View } from '@adobe/react-spectrum';
import { CampaignDetail } from '../../../src/components/CampaignDetail';
import { Campaign } from '../../../src/types/Campaign';
import { CampaignService } from '../../../src/services/CampaignService';
import { useRouter, useParams } from 'next/navigation';

export default function CampaignDetailPage() {
  const router = useRouter();
  const params = useParams();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [runningPipelines, setRunningPipelines] = useState<Set<string>>(new Set());
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

  const handleBack = () => {
    router.push('/campaigns');
  };

  const handleEdit = (campaign: Campaign) => {
    router.push(`/campaigns/${campaign.campaign_id}/edit`);
  };

  const handleRunPipeline = async (campaign: Campaign) => {
    try {
      setRunningPipelines(prev => new Set([...prev, campaign.campaign_id]));
      await CampaignService.runPipeline(campaign.campaign_id);
    } catch (error) {
      console.error('Pipeline execution failed:', error);
    } finally {
      setRunningPipelines(prev => {
        const newSet = new Set(prev);
        newSet.delete(campaign.campaign_id);
        return newSet;
      });
    }
  };

  if (loading) {
    return <View padding="size-400">Loading campaign...</View>;
  }

  if (!campaign) {
    return <View padding="size-400">Campaign not found</View>;
  }

  return (
    <CampaignDetail
      campaign={campaign}
      onBack={handleBack}
      onEdit={handleEdit}
      runningPipelines={runningPipelines}
      onRunPipeline={handleRunPipeline}
    />
  );
}