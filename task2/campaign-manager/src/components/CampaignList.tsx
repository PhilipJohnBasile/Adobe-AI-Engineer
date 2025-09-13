'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import {
  View, Flex, Grid, Heading, Text, Button, SearchField, Picker, Item,
  ProgressBar, Well, StatusLight, Divider, ActionButton, MenuTrigger, Menu
} from '@adobe/react-spectrum';
import Add from '@spectrum-icons/workflow/Add';
import Refresh from '@spectrum-icons/workflow/Refresh';
import More from '@spectrum-icons/workflow/More';
import { CampaignService } from '../services/CampaignService';
import { Campaign } from '../types/Campaign';

interface CampaignListProps {
  onSelectCampaign?: (campaign: Campaign) => void;
  onCreateNew?: () => void;
  onEditCampaign?: (campaign: Campaign) => void;
  refreshTrigger?: number;
}

export default function CampaignList({ onSelectCampaign, onCreateNew, onEditCampaign, refreshTrigger }: CampaignListProps) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('created_date');

  useEffect(() => {
    loadCampaigns();
  }, []);

  useEffect(() => {
    if (refreshTrigger !== undefined) {
      loadCampaigns();
    }
  }, [refreshTrigger]);

  const determineStatus = (campaign: Campaign) => {
    const now = new Date();
    const startDate = new Date(campaign.campaign_start_date);
    const endDate = new Date(campaign.campaign_end_date);
    
    if (now < startDate) {
      return 'pending';
    } else if (now >= startDate && now <= endDate) {
      return 'active';
    } else {
      return 'completed';
    }
  };

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const campaignData = await CampaignService.getAllCampaigns();
      
      // Add default status if not present
      const campaignsWithStatus = campaignData.map(campaign => ({
        ...campaign,
        status: campaign.status || determineStatus(campaign)
      }));
      
      setCampaigns(campaignsWithStatus);
      setError(null);
    } catch (err) {
      console.error('Failed to load campaigns:', err);
      setError('Failed to load campaigns. Please check if the server is running.');
    } finally {
      setLoading(false);
    }
  };

  const getClientLogo = (client: string) => {
    const logos: { [key: string]: { type: 'image' | 'emoji'; value: string } } = {
      'Coca-Cola Company': { 
        type: 'image', 
        value: '/assets/brand/coca_cola_logo.svg' 
      },
      'Coca-Cola Classic': { 
        type: 'image', 
        value: '/assets/products/coca_cola_classic/product_bottle.png' 
      },
      'Diet Coke': { 
        type: 'image', 
        value: '/assets/brand/diet_coke_logo.svg' 
      },
      'Coca-Cola Zero': { 
        type: 'image', 
        value: '/assets/brand/coca_cola_zero_logo.svg' 
      },
      'Sprite': { 
        type: 'image', 
        value: '/assets/products/sprite/product_can.png' 
      },
      'Fanta': { 
        type: 'image', 
        value: '/assets/products/fanta_apple/product_bottle.png' 
      },
      'Fanta Apple': { 
        type: 'image', 
        value: '/assets/products/fanta_apple/product_bottle.png' 
      },
      'Nike': { type: 'emoji', value: '👟' },
      'Apple': { type: 'emoji', value: '🍎' },
      'Microsoft': { type: 'emoji', value: '💻' },
      'Diageo': { type: 'emoji', value: '🥃' }
    };
    return logos[client] || { type: 'emoji', value: '🏢' };
  };

  const getClientColors = (client: string) => {
    const colors: { [key: string]: { primary: string; secondary: string } } = {
      'Coca-Cola Company': { primary: '#DA020E', secondary: '#FFFFFF' },
      'Coca-Cola Classic': { primary: '#DA020E', secondary: '#FFFFFF' },
      'Diet Coke': { primary: '#C0C0C0', secondary: '#FFFFFF' },
      'Coca-Cola Zero': { primary: '#000000', secondary: '#DA020E' },
      'Sprite': { primary: '#00A651', secondary: '#FFFFFF' },
      'Fanta': { primary: '#FF8C00', secondary: '#FFFFFF' },
      'Fanta Apple': { primary: '#FF8C00', secondary: '#FFFFFF' },
      'Diageo': { primary: '#8B4513', secondary: '#FFD700' },
      'Nike': { primary: '#000000', secondary: '#FFFFFF' },
      'Apple': { primary: '#007AFF', secondary: '#F2F2F7' },
      'Microsoft': { primary: '#0078D4', secondary: '#F3F2F1' }
    };
    return colors[client] || { primary: '#6B7280', secondary: '#F9FAFB' };
  };

  const getStatusVariant = (status: string): "positive" | "notice" | "neutral" | "negative" | "info" => {
    switch (status) {
      case 'active': return 'positive';
      case 'pending': return 'notice';
      case 'completed': return 'neutral';
      case 'draft': return 'info';
      default: return 'neutral';
    }
  };


  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = searchQuery === '' || 
      campaign.campaign_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      campaign.client.toLowerCase().includes(searchQuery.toLowerCase()) ||
      campaign.campaign_id.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || campaign.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const sortedCampaigns = [...filteredCampaigns].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.campaign_name.localeCompare(b.campaign_name);
      case 'client':
        return a.client.localeCompare(b.client);
      case 'budget':
        return (b.budget?.total || 0) - (a.budget?.total || 0);
      case 'created_date':
      default:
        return new Date(b.created_date || '').getTime() - new Date(a.created_date || '').getTime();
    }
  });

  if (loading) {
    return (
      <View padding="size-400">
        <Text>Loading campaigns...</Text>
      </View>
    );
  }

  if (error) {
    return (
      <View padding="size-400">
        <Well>
          <Heading level={3}>Error Loading Campaigns</Heading>
          <Text>{error}</Text>
          <Button variant="accent" onPress={loadCampaigns} marginTop="size-200">
            Retry
          </Button>
        </Well>
      </View>
    );
  }

  return (
    <View backgroundColor="gray-50" minHeight="100vh" padding="size-300" maxWidth="1200px" marginX="auto">
      {/* Header */}
      <View padding="size-300" marginBottom="size-300" UNSAFE_style={{ boxShadow: 'var(--spectrum-drop-shadow-color-medium)' }}>
        <Flex justifyContent="space-between" alignItems="center" marginBottom="size-300">
          <View>
            <Heading level={1} margin={0}>Campaign Manager</Heading>
            <Text UNSAFE_style={{color: 'var(--spectrum-alias-text-color-secondary)'}}>
              Create, manage, and monitor creative automation campaigns
            </Text>
          </View>
          <Button variant="accent" onPress={onCreateNew}>
            <Add />
            <Text>New Campaign</Text>
          </Button>
        </Flex>

        {/* Search and Filters */}
        <Flex gap="size-200" wrap>
          <SearchField
            isQuiet
            placeholder="Search by client, campaign, or ID..."
            value={searchQuery}
            onChange={setSearchQuery}
            width="size-3600"
          />
          <Picker
            isQuiet
            label="Status"
            selectedKey={statusFilter}
            onSelectionChange={(key) => setStatusFilter(key as string)}
          >
            <Item key="all">All</Item>
            <Item key="pending">Pending</Item>
            <Item key="active">Active</Item>
            <Item key="completed">Completed</Item>
          </Picker>
          <Picker
            isQuiet
            label="Sort By"
            selectedKey={sortBy}
            onSelectionChange={(key) => setSortBy(key as string)}
          >
            <Item key="created_date">Latest</Item>
            <Item key="name">Name</Item>
            <Item key="client">Assets</Item>
            <Item key="budget">Budget</Item>
          </Picker>
          <ActionButton isQuiet onPress={loadCampaigns}>
            <Refresh />
          </ActionButton>
        </Flex>
      </View>

      {/* Campaign Cards */}
      {sortedCampaigns.length === 0 ? (
        <View 
          padding="size-800" 
          textAlign="center"
          UNSAFE_style={{ border: '2px dashed var(--spectrum-global-color-gray-300)', borderRadius: '8px' }}
        >
          <Text UNSAFE_style={{ fontSize: '48px', marginBottom: 'var(--spectrum-global-dimension-size-200)' }}>📋</Text>
          <Heading level={3} marginBottom="size-100">
            {searchQuery || statusFilter !== 'all' ? 'No campaigns match your filters' : 'No campaigns yet'}
          </Heading>
          <Text UNSAFE_style={{color: 'var(--spectrum-alias-text-color-secondary)'}} marginBottom="size-300">
            {searchQuery || statusFilter !== 'all' ? 'Try adjusting your search or filters' : 'Get started by creating your first campaign'}
          </Text>
          {(!searchQuery && statusFilter === 'all') && (
            <Button variant="accent" onPress={onCreateNew}>
              <Add />
              <Text>Create Campaign</Text>
            </Button>
          )}
        </View>
      ) : (
        <Grid columns={['1fr', '1fr']} gap="size-300">
          {sortedCampaigns.map((campaign) => {
            const clientLogo = getClientLogo(campaign.client);
            const clientColors = getClientColors(campaign.client);
            
            return (
              <div
                key={campaign.campaign_id}
                onClick={() => onSelectCampaign?.(campaign)}
                style={{
                  cursor: 'pointer',
                  transition: 'all 0.2s ease'
                }}
              >
                <Well>
                {/* Top Row: Brand Tile + Status */}
                <Flex justifyContent="space-between" alignItems="center" marginBottom="size-200">
                  <Flex alignItems="center" gap="size-150">
                    <View
                      width="size-500"
                      height="size-500"
                      backgroundColor="gray-200"
                      borderRadius="medium"
                      UNSAFE_style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        overflow: 'hidden'
                      }}
                    >
                      {clientLogo.type === 'image' ? (
                        <Image
                          src={clientLogo.value}
                          alt={campaign.client}
                          width={32}
                          height={32}
                          style={{ objectFit: 'contain' }}
                        />
                      ) : (
                        <Text>{clientLogo.value}</Text>
                      )}
                    </View>
                    <StatusLight variant={getStatusVariant(campaign.status)} size="m">
                      {campaign.status}
                    </StatusLight>
                  </Flex>
                  <MenuTrigger>
                    <ActionButton isQuiet>
                      <More />
                    </ActionButton>
                    <Menu onAction={(key) => {
                      if (key === 'edit') onEditCampaign?.(campaign);
                      if (key === 'view') onSelectCampaign?.(campaign);
                    }}>
                      <Item key="view">View Details</Item>
                      <Item key="edit">Edit Campaign</Item>
                    </Menu>
                  </MenuTrigger>
                </Flex>

                {/* Campaign Title */}
                <Heading level={4} marginBottom="size-100">
                  {campaign.campaign_name}
                </Heading>
                <Text UNSAFE_style={{color: 'var(--spectrum-alias-text-color-secondary)'}} marginBottom="size-200">
                  {campaign.client}
                </Text>

                <Divider size="S" marginBottom="size-200" />

                {/* Metrics Row */}
                <Flex justifyContent="space-between" marginBottom="size-200">
                  <View>
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                      color: 'var(--spectrum-alias-text-color-secondary)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}>
                      Budget
                    </Text>
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-200)',
                      fontWeight: '700',
                      color: 'var(--spectrum-alias-text-color)'
                    }}>
                      {formatCurrency(parseFloat(campaign.budget_allocation?.total_budget?.replace(/[^\d.-]/g, '') || '125000') * 1000)}
                    </Text>
                  </View>
                  <View UNSAFE_style={{ textAlign: 'right' }}>
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                      color: 'var(--spectrum-alias-text-color-secondary)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px'
                    }}>
                      Assets
                    </Text>
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-200)',
                      fontWeight: '700',
                      color: 'var(--spectrum-alias-text-color)'
                    }}>
                      {campaign.deliverables?.total_assets || campaign.products?.length * 9 || 27}
                    </Text>
                  </View>
                </Flex>

                {/* Progress Bar for Active Campaigns */}
                {campaign.status === 'active' && (
                  <View marginBottom="size-200">
                    <Flex justifyContent="space-between" alignItems="center" marginBottom="size-100">
                      <Text UNSAFE_style={{
                        fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                        color: 'var(--spectrum-alias-text-color-secondary)'
                      }}>
                        Progress
                      </Text>
                      <Text UNSAFE_style={{
                        fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                        fontWeight: '600',
                        color: 'var(--spectrum-alias-text-color)'
                      }}>
                        72%
                      </Text>
                    </Flex>
                    <ProgressBar
                      label="Campaign Progress"
                      value={72}
                      showValueLabel={false}
                      size="S"
                    />
                  </View>
                )}

                <Divider size="S" marginBottom="size-200" />

                {/* Footer Row */}
                <Flex justifyContent="space-between" alignItems="center">
                  <Text UNSAFE_style={{
                    fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                    color: 'var(--spectrum-alias-text-color-secondary)',
                    fontFamily: 'monospace'
                  }}>
                    {campaign.campaign_id}
                  </Text>
                  <ActionButton
                    variant="accent"
                    onPress={() => onSelectCampaign?.(campaign)}
                  >
                    {campaign.status === 'completed' ? 'View Results' : 'Run Pipeline'}
                  </ActionButton>
                </Flex>
              </Well>
              </div>
            );
          })}
        </Grid>
      )}
    </View>
  );
}