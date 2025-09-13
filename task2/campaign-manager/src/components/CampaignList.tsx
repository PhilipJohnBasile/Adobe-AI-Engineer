import React, { useState, useEffect } from 'react';
import { Campaign } from '../types/Campaign';
import { CampaignService } from '../services/CampaignService';
import { Play, Edit, Trash2, Plus, Eye, AlertTriangle, CheckCircle } from 'lucide-react';
import {
  View,
  Flex,
  Heading,
  Text,
  ActionButton,
  Button,
  ProgressCircle,
  StatusLight,
  Badge,
  Divider,
  Grid,
  Card,
  IllustratedMessage,
  Content
} from '@adobe/react-spectrum';

interface CampaignListProps {
  onSelectCampaign: (campaign: Campaign) => void;
  onCreateNew: () => void;
  onEditCampaign: (campaign: Campaign) => void;
  refreshTrigger: number;
}

export const CampaignList: React.FC<CampaignListProps> = ({
  onSelectCampaign,
  onCreateNew,
  onEditCampaign,
  refreshTrigger
}) => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runningPipeline, setRunningPipeline] = useState<string | null>(null);

  useEffect(() => {
    loadCampaigns();
  }, [refreshTrigger]);

  const loadCampaigns = async () => {
    console.log('CampaignList: Starting loadCampaigns()');
    setLoading(true);
    setError(null);
    try {
      console.log('CampaignList: About to call CampaignService.getAllCampaigns()');
      const data = await CampaignService.getAllCampaigns();
      console.log('CampaignList: Received campaign data:', data);
      setCampaigns(data);
    } catch (err) {
      console.error('CampaignList: Error in loadCampaigns:', err);
      setError('Failed to load campaigns');
      console.error(err);
    } finally {
      setLoading(false);
      console.log('CampaignList: loadCampaigns() completed');
    }
  };

  const handleDelete = async (campaignId: string, campaignName: string) => {
    if (window.confirm(`Are you sure you want to delete "${campaignName}"?`)) {
      try {
        await CampaignService.deleteCampaign(campaignId);
        setCampaigns(campaigns.filter(c => c.campaign_id !== campaignId));
      } catch (err) {
        setError('Failed to delete campaign');
        console.error(err);
      }
    }
  };

  const handleRunPipeline = async (campaign: Campaign) => {
    setRunningPipeline(campaign.campaign_id);
    try {
      const result = await CampaignService.runPipeline(campaign.campaign_id);
      alert(`Pipeline completed! Generated ${result.assets_generated?.length || 0} assets.`);
    } catch (err) {
      alert('Pipeline failed to run. Check console for details.');
      console.error(err);
    } finally {
      setRunningPipeline(null);
    }
  };

  const getStatusColor = (campaign: Campaign) => {
    const now = new Date();
    const startDate = new Date(campaign.campaign_start_date);
    const endDate = new Date(campaign.campaign_end_date);

    if (now < startDate) return 'bg-blue-100 text-blue-800';
    if (now > endDate) return 'bg-gray-100 text-gray-800';
    return 'bg-green-100 text-green-800';
  };

  const getStatusText = (campaign: Campaign) => {
    const now = new Date();
    const startDate = new Date(campaign.campaign_start_date);
    const endDate = new Date(campaign.campaign_end_date);

    if (now < startDate) return 'Upcoming';
    if (now > endDate) return 'Completed';
    return 'Active';
  };

  if (loading) {
    return (
      <Flex direction="column" alignItems="center" justifyContent="center" height="size-3000" gap="size-200">
        <ProgressCircle size="M" isIndeterminate />
        <Text>Loading campaigns...</Text>
      </Flex>
    );
  }

  return (
    <View>
      <Flex direction="column" gap="size-300">
        <Flex justifyContent="space-between" alignItems="center">
          <View>
            <Heading level={2}>Campaign Manager</Heading>
            <Text UNSAFE_style={{color: 'var(--spectrum-global-color-gray-600)'}}>
              Manage creative automation campaigns
            </Text>
          </View>
          <Button variant="cta" onPress={onCreateNew}>
            <Plus size={16} />
            <Text>New Campaign</Text>
          </Button>
        </Flex>

        {error && (
          <View backgroundColor="negative" UNSAFE_style={{borderRadius: '4px', padding: '12px'}}>
            <Flex alignItems="center" gap="size-100">
              <AlertTriangle size={20} />
              <Text UNSAFE_style={{color: 'var(--spectrum-global-color-red-600)'}}>{error}</Text>
            </Flex>
          </View>
        )}

        <Grid
          columns={['1fr', '1fr', '1fr']}
          gap="size-300"
          marginTop="size-300"
          UNSAFE_className="campaign-grid"
        >
          {campaigns.map((campaign) => (
            <View
              key={campaign.campaign_id}
              backgroundColor="gray-75"
              borderWidth="thin"
              borderColor="gray-300"
              borderRadius="medium"
              padding="size-300"
              height="size-3600"
              UNSAFE_className="adobe-enhanced-card"
              UNSAFE_style={{
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column'
              }}
              onPress={() => onSelectCampaign(campaign)}
            >
              <Flex direction="column" height="100%" justifyContent="space-between">
                <Flex direction="column" gap="size-200">
                  <Flex justifyContent="space-between" alignItems="start">
                    <Heading level={4} UNSAFE_style={{margin: 0, fontSize: '18px', lineHeight: '1.3'}}>
                      {campaign.campaign_name}
                    </Heading>
                    <Badge variant={
                      getStatusText(campaign) === 'Active' ? 'positive' :
                      getStatusText(campaign) === 'Upcoming' ? 'info' : 'neutral'
                    }>
                      {getStatusText(campaign)}
                    </Badge>
                  </Flex>

                  <Flex direction="column" gap="size-75">
                    <Flex justifyContent="space-between">
                      <Text UNSAFE_style={{color: 'var(--spectrum-global-color-gray-600)', fontSize: '14px'}}>Client:</Text>
                      <Text UNSAFE_style={{fontSize: '14px'}}>{campaign.client}</Text>
                    </Flex>
                    <Flex justifyContent="space-between">
                      <Text UNSAFE_style={{color: 'var(--spectrum-global-color-gray-600)', fontSize: '14px'}}>Products:</Text>
                      <Text UNSAFE_style={{fontSize: '14px'}}>{campaign.products.length}</Text>
                    </Flex>
                    <Flex justifyContent="space-between">
                      <Text UNSAFE_style={{color: 'var(--spectrum-global-color-gray-600)', fontSize: '14px'}}>Regions:</Text>
                      <Text UNSAFE_style={{fontSize: '14px'}}>{campaign.target_regions.length}</Text>
                    </Flex>
                    <Flex justifyContent="space-between">
                      <Text UNSAFE_style={{color: 'var(--spectrum-global-color-gray-600)', fontSize: '14px'}}>Assets:</Text>
                      <Text UNSAFE_style={{fontSize: '14px'}}>{campaign.deliverables.total_assets}</Text>
                    </Flex>
                    <Flex justifyContent="space-between">
                      <Text UNSAFE_style={{color: 'var(--spectrum-global-color-gray-600)', fontSize: '14px'}}>Budget:</Text>
                      <Text UNSAFE_style={{fontSize: '14px'}}>{campaign.budget_allocation.total_budget}</Text>
                    </Flex>
                  </Flex>
                </Flex>

                <Flex direction="column" gap="size-150">
                  <Divider />
                  <Flex justifyContent="space-between" alignItems="center">
                    <Flex gap="size-100" UNSAFE_style={{ pointerEvents: 'auto' }}>
                      <ActionButton
                        onPress={() => onSelectCampaign(campaign)}
                        isQuiet
                        aria-label="View Details"
                        UNSAFE_style={{ cursor: 'pointer' }}
                      >
                        <Eye size={16} />
                      </ActionButton>
                      <ActionButton
                        onPress={() => onEditCampaign(campaign)}
                        isQuiet
                        aria-label="Edit Campaign"
                        UNSAFE_style={{ cursor: 'pointer' }}
                      >
                        <Edit size={16} />
                      </ActionButton>
                      <ActionButton
                        onPress={() => handleDelete(campaign.campaign_id, campaign.campaign_name)}
                        isQuiet
                        aria-label="Delete Campaign"
                        UNSAFE_style={{
                          color: 'var(--spectrum-global-color-red-600)',
                          cursor: 'pointer'
                        }}
                      >
                        <Trash2 size={16} />
                      </ActionButton>
                    </Flex>

                    <Button
                      variant="cta"
                      onPress={() => handleRunPipeline(campaign)}
                      isDisabled={runningPipeline === campaign.campaign_id}
                      UNSAFE_style={{
                        cursor: runningPipeline === campaign.campaign_id ? 'not-allowed' : 'pointer',
                        pointerEvents: 'auto'
                      }}
                    >
                      {runningPipeline === campaign.campaign_id ? (
                        <ProgressCircle size="S" isIndeterminate />
                      ) : (
                        <Play size={16} />
                      )}
                    </Button>
                  </Flex>
                </Flex>
              </Flex>
            </View>
          ))}
        </Grid>

        {campaigns.length === 0 && !loading && (
          <IllustratedMessage>
            <Plus size={48} />
            <Heading>No campaigns yet</Heading>
            <Content>Create your first campaign to get started with creative automation.</Content>
            <Button variant="cta" onPress={onCreateNew}>
              <Plus size={16} />
              <Text>Create Campaign</Text>
            </Button>
          </IllustratedMessage>
        )}
      </Flex>
    </View>
  );
};