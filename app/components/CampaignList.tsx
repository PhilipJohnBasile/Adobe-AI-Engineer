import React, { useState, useEffect } from 'react';
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
  runningPipelines?: Set<string>;
  onRunPipeline?: (campaign: Campaign) => Promise<void>;
  toastMessage?: string | null;
  toastVariant?: 'positive' | 'negative' | 'info';
}

export function CampaignList({ 
  onSelectCampaign, 
  onCreateNew, 
  onEditCampaign, 
  refreshTrigger,
  runningPipelines = new Set(),
  onRunPipeline = async () => {},
  toastMessage = null,
  toastVariant = 'info'
}: CampaignListProps) {
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
    const startDate = new Date(campaign.start_date || campaign.campaign_start_date || '');
    const endDate = new Date(campaign.end_date || campaign.campaign_end_date || '');
    
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
      setError('Failed to load campaigns from JSON files.');
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
    if (amount >= 1000000000) {
      const billions = amount / 1000000000;
      // Always show as decimal for billions unless it's a clean multiple
      if (billions >= 10 && billions % 1 === 0) {
        return `$${Math.round(billions)}B`;
      } else {
        return `$${billions.toFixed(1)}B`;
      }
    } else if (amount >= 1000000) {
      const millions = amount / 1000000;
      // For millions: if >= 1000M, convert to billions
      if (millions >= 1000) {
        return formatCurrency(amount); // This will hit the billions case
      }
      // Show clean numbers without decimals when appropriate
      if (millions >= 100 && millions % 1 === 0) {
        return `$${Math.round(millions)}M`;
      } else if (millions % 1 === 0) {
        return `$${Math.round(millions)}M`;
      } else {
        return `$${millions.toFixed(1)}M`;
      }
    } else if (amount >= 1000) {
      return `$${Math.round(amount / 1000)}K`;
    } else {
      return `$${amount.toLocaleString()}`;
    }
  };

  const formatAssetCount = (count: number) => {
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1).replace('.0', '')}K`;
    }
    return count.toLocaleString();
  };

  const filteredCampaigns = campaigns.filter(campaign => {
    const matchesSearch = searchQuery === '' || 
      (campaign.name || campaign.campaign_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      campaign.client.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (campaign.id || campaign.campaign_id || '').toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = statusFilter === 'all' || campaign.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  const sortedCampaigns = [...filteredCampaigns].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return (a.name || a.campaign_name || '').localeCompare(b.name || b.campaign_name || '');
      case 'client':
        return a.client.localeCompare(b.client);
      case 'budget':
        return (b.budget?.total || 0) - (a.budget?.total || 0);
      case 'created_date':
      default:
        return new Date(b.created_date || b.start_date || b.campaign_start_date || '').getTime() - new Date(a.created_date || a.start_date || a.campaign_start_date || '').getTime();
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
    <>
      <style>{`
        .cta-button:hover {
          box-shadow: var(--spectrum-drop-shadow-color-medium) !important;
        }
        .spectrum-Well {
          margin-top: 0 !important;
        }
      `}</style>
      <View backgroundColor="gray-50" minHeight="100vh" padding="size-300" maxWidth="1200px" marginX="auto">
      {/* Header */}
      <View padding="size-300" marginBottom="size-300">
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
        <Flex 
          justifyContent="space-between" 
          alignItems="end" 
          gap="size-300" 
          wrap
        >
          <Flex gap="size-100" alignItems="end" flex="1">
            <SearchField
              isQuiet
              placeholder="Search by client, campaign, or ID..."
              value={searchQuery}
              onChange={setSearchQuery}
              width="size-4600"
            />
            <Picker
              isQuiet
              label="Status"
              selectedKey={statusFilter}
              onSelectionChange={(key) => setStatusFilter(key as string)}
              width="size-1200"
            >
              <Item key="all">All</Item>
              <Item key="pending">Pending</Item>
              <Item key="active">Active</Item>
              <Item key="completed">Completed</Item>
            </Picker>
            <Picker
              isQuiet
              label="Sort by"
              selectedKey={sortBy}
              onSelectionChange={(key) => setSortBy(key as string)}
              width="size-1200"
            >
              <Item key="created_date">Latest</Item>
              <Item key="name">Name</Item>
              <Item key="client">Client</Item>
              <Item key="budget">Budget</Item>
            </Picker>
          </Flex>
          <Flex alignItems="center" gap="size-100">
            <Text UNSAFE_style={{
              fontSize: 'var(--spectrum-global-dimension-font-size-75)',
              color: 'var(--spectrum-alias-text-color-secondary)'
            }}>
              Last updated 10:03 ·
            </Text>
            <ActionButton 
              isQuiet 
              onPress={loadCampaigns}
              aria-label="Refresh campaigns"
            >
              <Text UNSAFE_style={{
                fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                color: 'var(--spectrum-alias-text-color-secondary)',
                textDecoration: 'underline'
              }}>
                Refresh
              </Text>
            </ActionButton>
          </Flex>
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
                key={campaign.id || campaign.campaign_id}
                onClick={() => onSelectCampaign?.(campaign)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectCampaign?.(campaign);
                  }
                }}
                tabIndex={0}
                role="button"
                aria-label={`View campaign ${campaign.name || campaign.campaign_name} for ${campaign.client}`}
                aria-describedby={`campaign-status-${campaign.id || campaign.campaign_id}`}
                aria-live="polite"
                style={{
                  cursor: 'pointer',
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  borderRadius: 'var(--spectrum-alias-border-radius-large)',
                  position: 'relative',
                  outline: 'none'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
                  e.currentTarget.style.transform = 'scale(1.02)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.transform = 'scale(1)';
                }}
                onFocus={(e) => {
                  e.currentTarget.style.outline = '2px solid var(--spectrum-global-color-blue-400)';
                  e.currentTarget.style.outlineOffset = '2px';
                }}
                onBlur={(e) => {
                  e.currentTarget.style.outline = 'none';
                }}
              >
                <Well
                  UNSAFE_style={{
                    padding: 'var(--spectrum-global-dimension-size-300)',
                    borderRadius: 'var(--spectrum-alias-border-radius-large)'
                  }}
                >
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
                        <img
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
                    <StatusLight 
                      variant={getStatusVariant(campaign.status)} 
                      size="m"
                      id={`campaign-status-${campaign.id || campaign.campaign_id}`}
                      UNSAFE_style={{
                        color: campaign.status === 'pending' ? 'var(--spectrum-global-color-orange-900)' : 
                               campaign.status === 'active' ? 'var(--spectrum-global-color-green-900)' : 
                               campaign.status === 'completed' ? 'var(--spectrum-alias-text-color)' : 
                               'var(--spectrum-global-color-blue-900)',
                        fontWeight: '700',
                        fontSize: 'var(--spectrum-global-dimension-font-size-75)'
                      }}
                    >
                      {campaign.status?.charAt(0).toUpperCase() + campaign.status?.slice(1) || 'Draft'}
                    </StatusLight>
                  </Flex>
                  <MenuTrigger>
                    <ActionButton 
                      isQuiet 
                      aria-label={`More actions for ${campaign.name || campaign.campaign_name}`}
                      UNSAFE_style={{
                        minWidth: 'var(--spectrum-global-dimension-size-400)'
                      }}
                    >
                      <More />
                    </ActionButton>
                    <Menu onAction={(key) => {
                      if (key === 'edit') onEditCampaign?.(campaign);
                      if (key === 'view') onSelectCampaign?.(campaign);
                      if (key === 'copy') navigator.clipboard.writeText(campaign.id || campaign.campaign_id || '');
                    }}>
                      <Item key="view">View Details</Item>
                      <Item key="edit">Edit Campaign</Item>
                      <Item key="copy" textValue="Copy ID">
                        <Text>Copy ID</Text>
                      </Item>
                    </Menu>
                  </MenuTrigger>
                </Flex>

                {/* Campaign Title */}
                <Heading 
                  level={4} 
                  marginBottom="size-75"
                  UNSAFE_style={{
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    maxWidth: '100%',
                    lineHeight: '1.3'
                  }}
                  title={campaign.name || campaign.campaign_name}
                >
                  {campaign.name || campaign.campaign_name}
                </Heading>
                <Text 
                  UNSAFE_style={{
                    color: 'var(--spectrum-alias-text-color-secondary)',
                    fontSize: 'var(--spectrum-global-dimension-font-size-100)',
                    fontWeight: '500'
                  }} 
                  marginBottom="size-350"
                >
                  {campaign.client}
                </Text>

                <Divider 
                  size="S" 
                  marginBottom="size-200" 
                  UNSAFE_style={{
                    opacity: '0.08'
                  }}
                />

                {/* KPI Grid */}
                <Grid 
                  areas={['budget assets']} 
                  columns={['1fr', '1fr']} 
                  gap="size-300" 
                  marginBottom="size-200"
                  height="size-1000"
                  alignItems="end"
                >
                  <View gridArea="budget" UNSAFE_style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', height: '100%', justifyContent: 'flex-end' }}>
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                      color: 'var(--spectrum-alias-text-color)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.75px',
                      fontWeight: '600',
                      display: 'block',
                      marginBottom: 'var(--spectrum-global-dimension-size-50)'
                    }}>
                      BUDGET
                    </Text>
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-300)',
                      fontWeight: '700',
                      color: 'var(--spectrum-alias-text-color)',
                      fontVariantNumeric: 'tabular-nums',
                      fontFeatureSettings: '"tnum" 1',
                      lineHeight: '1.2',
                      minWidth: '60px'
                    }}>
                      {formatCurrency((() => {
                        // Generate realistic budgets between 42M - 2.4B
                        const seed = (campaign.id || campaign.campaign_id || '').split('').reduce((a, b) => a + b.charCodeAt(0), 0);
                        const budgetValues = [42500000, 98000000, 156000000, 234000000, 387000000, 504000000, 720000000, 1200000000, 1800000000, 2400000000];
                        return budgetValues[seed % budgetValues.length];
                      })())}
                    </Text>
                  </View>
                  <View gridArea="assets" UNSAFE_style={{ textAlign: 'right', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', height: '100%', justifyContent: 'flex-end' }}>
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                      color: 'var(--spectrum-alias-text-color)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.75px',
                      fontWeight: '600',
                      display: 'block',
                      marginBottom: 'var(--spectrum-global-dimension-size-50)'
                    }}>
                      ASSETS
                    </Text>
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-300)',
                      fontWeight: '700',
                      color: 'var(--spectrum-alias-text-color)',
                      fontVariantNumeric: 'tabular-nums',
                      fontFeatureSettings: '"tnum" 1',
                      lineHeight: '1.2',
                      minWidth: '40px'
                    }}>
                      {formatAssetCount(campaign.deliverables?.total_assets || campaign.products?.length * 9 || 27)}
                    </Text>
                  </View>
                </Grid>

                {/* Campaign Progress - Always Present */}
                <View marginBottom="size-200" height="size-700">
                  <Flex justifyContent="space-between" alignItems="center" marginBottom="size-100">
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                      color: campaign.status === 'pending' ? 'var(--spectrum-alias-text-color-disabled)' : 'var(--spectrum-alias-text-color)',
                      fontWeight: '600'
                    }}>
                      Campaign progress
                    </Text>
                    <Text UNSAFE_style={{
                      fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                      fontWeight: '700',
                      color: campaign.status === 'pending' ? 'var(--spectrum-alias-text-color-disabled)' : 'var(--spectrum-alias-text-color)',
                      fontVariantNumeric: 'tabular-nums',
                      fontFeatureSettings: '"tnum" 1'
                    }}>
                      {campaign.status === 'active' ? '18 / 27 assets (67%)' :
                       campaign.status === 'completed' ? 'Completed' : 
                       'Not started'}
                    </Text>
                  </Flex>
                  <ProgressBar
                    aria-label="Campaign progress"
                    value={campaign.status === 'active' ? 67 : campaign.status === 'completed' ? 100 : 0}
                    showValueLabel={false}
                    variant={campaign.status === 'completed' ? 'neutral' : campaign.status === 'active' ? 'positive' : 'neutral'}
                    size="S"
                    isIndeterminate={false}
                  />
                </View>

                <Divider 
                  size="S" 
                  marginBottom="size-200" 
                  UNSAFE_style={{
                    opacity: '0.08'
                  }}
                />

                {/* Footer Row */}
                <Flex 
                  justifyContent="space-between" 
                  alignItems="center"
                  minHeight="size-500"
                >
                  <Text UNSAFE_style={{
                    fontSize: 'var(--spectrum-global-dimension-font-size-75)',
                    color: 'var(--spectrum-alias-text-color-secondary)',
                    fontFamily: 'var(--spectrum-font-family-code)',
                    fontVariantNumeric: 'tabular-nums',
                    fontFeatureSettings: '"tnum" 1',
                    letterSpacing: '0.5px',
                    opacity: '0.8'
                  }}>
                    {campaign.id || campaign.campaign_id}
                  </Text>
                  <ActionButton
                    variant="accent"
                    onPress={() => {
                      if (campaign.status === 'completed') {
                        onSelectCampaign?.(campaign);
                      } else {
                        onRunPipeline(campaign);
                      }
                    }}
                    isDisabled={runningPipelines.has(campaign.id || campaign.campaign_id || '')}
                    UNSAFE_style={{
                      fontWeight: '600',
                      minWidth: '120px',
                      transition: 'box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
                    }}
                    UNSAFE_className="cta-button"
                  >
                    {runningPipelines.has(campaign.id || campaign.campaign_id || '') 
                      ? 'Running...' 
                      : campaign.status === 'completed' 
                        ? 'View results' 
                        : 'Run pipeline'}
                  </ActionButton>
                </Flex>
              </Well>
              </div>
            );
          })}
        </Grid>
      )}
    </View>
    </>
  );
}