'use client';

import React, { useState } from 'react';
import { Provider, defaultTheme, Flex, View, Header, Heading, Text, ActionButton, Divider, Badge } from '@adobe/react-spectrum';
import { Sun, Moon } from 'lucide-react';
import { CampaignList } from '../src/components/CampaignList';
import { CampaignForm } from '../src/components/CampaignForm';
import { CampaignDetail } from '../src/components/CampaignDetail';
import { Campaign } from '../src/types/Campaign';

type View = 'list' | 'create' | 'edit' | 'detail';

export default function Home() {
  const [currentView, setCurrentView] = useState<View>('list');
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [colorScheme, setColorScheme] = useState<'light' | 'dark'>('light');

  const handleSelectCampaign = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    setCurrentView('detail');
  };

  const handleCreateNew = () => {
    setSelectedCampaign(null);
    setCurrentView('create');
  };

  const handleEditCampaign = (campaign: Campaign) => {
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

  const toggleTheme = () => {
    setColorScheme(prev => prev === 'light' ? 'dark' : 'light');
  };

  return (
    <Provider theme={defaultTheme} colorScheme={colorScheme} scale="medium">
      <View UNSAFE_className="campaign-manager-container" minHeight="100vh">
        <Header>
          <Flex justifyContent="space-between" alignItems="center" width="100%" maxWidth="1200px" marginX="auto" UNSAFE_style={{padding: 'var(--spectrum-global-dimension-size-300)'}}>
            <Flex alignItems="center" gap="size-200">
              {/* Adobe Logo */}
              <View
                width="size-500"
                height="size-500"
                borderRadius="small"
                UNSAFE_className="adobe-logo"
                UNSAFE_style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '16px',
                  boxShadow: '0 2px 8px rgba(255, 0, 0, 0.2)'
                }}
              >
                Ae
              </View>
              <Flex direction="column" gap="size-50">
                <Heading level={1} UNSAFE_style={{margin: 0, fontSize: '24px'}}>Creative Automation</Heading>
                <Flex alignItems="center" gap="size-100">
                  <Text UNSAFE_style={{fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)'}}>Campaign Manager</Text>
                </Flex>
              </Flex>
            </Flex>
            <Flex alignItems="center" gap="size-150">
              <Text UNSAFE_style={{fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)'}}>
                {colorScheme === 'dark' ? 'Dark Mode' : 'Light Mode'}
              </Text>
              <ActionButton onPress={toggleTheme} isQuiet>
                {colorScheme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
              </ActionButton>
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
          />
        )}
        </View>
      </View>
    </Provider>
  );
}