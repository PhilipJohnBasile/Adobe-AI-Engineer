import React, { useState } from 'react';
import { Provider, defaultTheme, Flex, View, Header, Heading, Text, ActionButton, Divider, Badge, Content } from '@adobe/react-spectrum';
import Light from '@spectrum-icons/workflow/Light';
import Moon from '@spectrum-icons/workflow/Moon';
import { CampaignList } from './components/CampaignList';
import { CampaignForm } from './components/CampaignForm';
import { CampaignDetail } from './components/CampaignDetail';
import { Campaign } from './types/Campaign';
import './App.css';

type View = 'list' | 'create' | 'edit' | 'detail';

function App() {
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
        {/* Adobe.com style hero header */}
        <View
          UNSAFE_className="adobe-hero-gradient"
          paddingY="size-300"
          borderBottomWidth="thin"
          borderBottomColor="gray-300"
          UNSAFE_style={{
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
            backdropFilter: 'blur(10px)'
          }}
        >
          <Flex justifyContent="space-between" alignItems="center" width="100%" maxWidth="1200px" marginX="auto" paddingX="size-300">
            <Flex alignItems="center" gap="size-200">
              {/* Enhanced Adobe Logo */}
              <View
                width="size-600"
                height="size-600"
                borderRadius="medium"
                UNSAFE_className="adobe-logo"
                UNSAFE_style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '20px',
                  fontWeight: '800',
                  position: 'relative',
                  overflow: 'hidden'
                }}
              >
                Ae
              </View>
              <Flex direction="column" gap="size-50">
                <Heading level={1} UNSAFE_style={{margin: 0, fontSize: '28px', fontWeight: '700', color: 'white', textShadow: '0 2px 4px rgba(0,0,0,0.3)'}}>
                  Creative Automation
                </Heading>
                <Text UNSAFE_style={{fontSize: '16px', color: 'rgba(255,255,255,0.9)', fontWeight: '500'}}>
                  Campaign Manager • Adobe Experience Cloud
                </Text>
              </Flex>
            </Flex>
            <Flex alignItems="center" gap="size-200">
              <View
                UNSAFE_className="adobe-glass-panel"
                paddingX="size-200"
                paddingY="size-100"
                borderRadius="medium"
              >
                <Flex alignItems="center" gap="size-100">
                  <Text UNSAFE_style={{fontSize: '14px', color: 'rgba(255,255,255,0.9)', fontWeight: '500'}}>
                    {colorScheme === 'dark' ? 'Dark' : 'Light'}
                  </Text>
                  <ActionButton onPress={toggleTheme} isQuiet UNSAFE_style={{color: 'white'}}>
                    {colorScheme === 'dark' ? <Light /> : <Moon />}
                  </ActionButton>
                </Flex>
              </View>
            </Flex>
          </Flex>
        </View>

        {/* Adobe.com style main content with glassmorphism */}
        <View maxWidth="1200px" marginX="auto" padding="size-400">
          <View
            UNSAFE_className="adobe-enhanced-card"
            borderRadius="large"
            padding="size-400"
            minHeight="80vh"
          >
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

        {/* Adobe.com style footer */}
        <View
          backgroundColor="gray-100"
          paddingY="size-300"
          marginTop="size-600"
          borderTopWidth="thin"
          borderTopColor="gray-300"
        >
          <Flex direction="row" justifyContent="center" alignItems="center" gap="size-100">
            <Text UNSAFE_style={{fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)'}}>
              Powered by
            </Text>
            <Text UNSAFE_className="adobe-gradient-text" UNSAFE_style={{fontSize: '14px', fontWeight: '700'}}>
              Adobe Experience Cloud
            </Text>
            <Text UNSAFE_style={{fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)'}}>
              • Creative Automation Platform
            </Text>
          </Flex>
        </View>
      </View>
    </Provider>
  );
}

export default App;