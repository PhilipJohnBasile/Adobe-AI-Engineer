'use client';

import React, { useState } from 'react';
import { Provider, defaultTheme, View } from '@adobe/react-spectrum';
import CampaignList from '../../src/components/CampaignList';
import { Campaign } from '../../src/types/Campaign';
import { CampaignService } from '../../src/services/CampaignService';
import { useRouter } from 'next/navigation';

export default function CampaignsPage() {
  const router = useRouter();
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [runningPipelines, setRunningPipelines] = useState<Set<string>>(new Set());
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastVariant, setToastVariant] = useState<'positive' | 'negative' | 'info'>('info');

  const handleSelectCampaign = (campaign: Campaign) => {
    router.push(`/campaigns/${campaign.campaign_id}`);
  };

  const handleCreateNew = () => {
    router.push('/campaigns/new');
  };

  const handleEditCampaign = (campaign: Campaign) => {
    router.push(`/campaigns/${campaign.campaign_id}/edit`);
  };

  const handleRunPipeline = async (campaign: Campaign) => {
    try {
      setRunningPipelines(prev => new Set([...prev, campaign.campaign_id]));
      setToastMessage(`Starting pipeline for ${campaign.campaign_name}...`);
      setToastVariant('info');
      
      await CampaignService.runPipeline(campaign.campaign_id);
      
      setToastMessage(`Pipeline completed successfully for ${campaign.campaign_name}!`);
      setToastVariant('positive');
      
      setRefreshTrigger(prev => prev + 1);
      
    } catch (error) {
      console.error('Pipeline execution failed:', error);
      setToastMessage(`Pipeline failed for ${campaign.campaign_name}. Please try again.`);
      setToastVariant('negative');
    } finally {
      setRunningPipelines(prev => {
        const newSet = new Set(prev);
        newSet.delete(campaign.campaign_id);
        return newSet;
      });
      
      setTimeout(() => {
        setToastMessage(null);
      }, 5000);
    }
  };

  return (
    <>
      <CampaignList
        onSelectCampaign={handleSelectCampaign}
        onCreateNew={handleCreateNew}
        onEditCampaign={handleEditCampaign}
        refreshTrigger={refreshTrigger}
        runningPipelines={runningPipelines}
        onRunPipeline={handleRunPipeline}
        toastMessage={toastMessage}
        toastVariant={toastVariant}
      />
      
      {toastMessage && (
        <View
          position="fixed"
          top="size-300"
          right="size-300"
          borderRadius="medium"
          padding="size-200"
          UNSAFE_style={{
            zIndex: 1000,
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
            backgroundColor: toastVariant === 'positive' ? 'var(--spectrum-global-color-green-600)' : 
                             toastVariant === 'negative' ? 'var(--spectrum-global-color-red-600)' : 
                             'var(--spectrum-global-color-blue-600)',
            color: 'white',
            fontWeight: '600',
            maxWidth: '400px',
            minWidth: '300px'
          }}
        >
          {toastMessage}
        </View>
      )}
    </>
  );
}