'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { Provider, defaultTheme, Flex, View, Header, Heading, Text, ActionButton, Divider, Badge } from '@adobe/react-spectrum';
import CampaignList from '../src/components/CampaignList';
import { CampaignForm } from '../src/components/CampaignForm';
import { CampaignDetail } from '../src/components/CampaignDetail';
import { Campaign } from '../src/types/Campaign';
import { CampaignService } from '../src/services/CampaignService';

type View = 'list' | 'create' | 'edit' | 'detail';

export default function Home() {
  const [currentView, setCurrentView] = useState<View>('list');
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  
  // Shared pipeline state
  const [runningPipelines, setRunningPipelines] = useState<Set<string>>(new Set());
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastVariant, setToastVariant] = useState<'positive' | 'negative' | 'info'>('info');

  const handleSelectCampaign = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    setCurrentView('detail');
  };

  const handleCreateNew = () => {
    setSelectedCampaign(null);
    setCurrentView('create');
  };

  const handleEditCampaign = (campaign: Campaign) => {
    console.log('handleEditCampaign called with campaign:', campaign.campaign_name, 'ID:', campaign.campaign_id);
    setSelectedCampaign(campaign);
    setCurrentView('edit');
  };

  const handleSaveCampaign = (campaign: Campaign) => {
    setCurrentView('list');
    setRefreshTrigger(prev => prev + 1);
  };

  const handleBackToList = () => {
    setCurrentView('list');
    setSelectedCampaign(null);
  };

  // Shared pipeline handler
  const handleRunPipeline = async (campaign: Campaign) => {
    try {
      setRunningPipelines(prev => new Set([...prev, campaign.campaign_id]));
      setToastMessage(`Starting pipeline for ${campaign.campaign_name}...`);
      setToastVariant('info');
      
      await CampaignService.runPipeline(campaign.campaign_id);
      
      setToastMessage(`Pipeline completed successfully for ${campaign.campaign_name}!`);
      setToastVariant('positive');
      
      // Refresh campaigns
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
      
      // Clear toast after 5 seconds
      setTimeout(() => {
        setToastMessage(null);
      }, 5000);
    }
  };


  return (
    <Provider theme={defaultTheme} colorScheme="light" scale="medium">
      <View UNSAFE_className="campaign-manager-container" minHeight="100vh">
        <Header>
          <Flex justifyContent="space-between" alignItems="center" width="100%" maxWidth="1200px" marginX="auto" UNSAFE_style={{padding: 'var(--spectrum-global-dimension-size-300)'}}>
            <Flex alignItems="center" gap="size-200">
              {/* Official Adobe Logo */}
              <View
                UNSAFE_className="adobe-logo"
                UNSAFE_style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <Image 
                  src="https://upload.wikimedia.org/wikipedia/commons/b/b1/Adobe_Corporate_Horizontal_Red_HEX.svg"
                  alt="Adobe"
                  width={100}
                  height={32}
                  style={{
                    height: '32px',
                    width: 'auto',
                    filter: 'drop-shadow(0 2px 8px rgba(235, 68, 90, 0.2))'
                  }}
                  priority
                />
              </View>
              <Flex direction="column" gap="size-50">
                <Heading level={1} UNSAFE_style={{margin: 0, fontSize: '24px'}}>Creative Automation</Heading>
                <Flex alignItems="center" gap="size-100">
                  <Text UNSAFE_style={{fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)'}}>Campaign Manager</Text>
                </Flex>
              </Flex>
            </Flex>
          </Flex>
        </Header>

        <View maxWidth="1200px" marginX="auto" UNSAFE_style={{padding: 'var(--spectrum-global-dimension-size-400)'}}>
        {currentView === 'list' && (
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
        )}

        {(currentView === 'create' || currentView === 'edit') && (
          <CampaignForm
            campaign={currentView === 'edit' ? selectedCampaign || undefined : undefined}
            onSave={handleSaveCampaign}
            onCancel={handleBackToList}
          />
        )}

        {currentView === 'detail' && selectedCampaign && (
          <CampaignDetail
            campaign={selectedCampaign}
            onBack={handleBackToList}
            onEdit={handleEditCampaign}
            runningPipelines={runningPipelines}
            onRunPipeline={handleRunPipeline}
          />
        )}
        </View>
        
        {/* Global notification banner - visible across all pages */}
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
            <Text UNSAFE_style={{ 
              color: 'white',
              fontSize: 'var(--spectrum-global-dimension-font-size-100)',
              fontWeight: '600'
            }}>
              {toastMessage}
            </Text>
          </View>
        )}
      </View>
    </Provider>
  );
}