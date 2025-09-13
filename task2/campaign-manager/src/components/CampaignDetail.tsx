import React, { useState, useEffect } from 'react';
import { Campaign, CampaignValidation } from '../types/Campaign';
import { CampaignService, ComplianceService } from '../services/CampaignService';
import { LivePipelineView } from './LivePipelineView';
import {
  ActionButton,
  Badge,
  ButtonGroup,
  Content,
  Divider,
  Flex,
  Grid,
  Heading,
  IllustratedMessage,
  Item,
  NumberField,
  Picker,
  ProgressCircle,
  StatusLight,
  TabList,
  TabPanels,
  Tabs,
  Text,
  View,
  Well,
  Meter,
  SearchField,
  Switch
} from '@adobe/react-spectrum';
import ArrowLeft from '@spectrum-icons/workflow/ArrowLeft';
import Play from '@spectrum-icons/workflow/Play';
import Edit from '@spectrum-icons/workflow/Edit';
import Shield from '@spectrum-icons/workflow/Shield';
import Alert from '@spectrum-icons/workflow/Alert';
import CheckmarkCircle from '@spectrum-icons/workflow/CheckmarkCircle';
import Clock from '@spectrum-icons/workflow/Clock';
import FileTemplate from '@spectrum-icons/workflow/FileTemplate';
import Download from '@spectrum-icons/workflow/Download';
import ViewIcon from '@spectrum-icons/workflow/ViewGrid';
import ChevronLeft from '@spectrum-icons/workflow/ChevronLeft';
import ChevronRight from '@spectrum-icons/workflow/ChevronRight';

interface CampaignDetailProps {
  campaign: Campaign;
  onBack: () => void;
  onEdit: (campaign: Campaign) => void;
  runningPipelines: Set<string>;
  onRunPipeline: (campaign: Campaign) => Promise<void>;
}

export const CampaignDetail: React.FC<CampaignDetailProps> = ({
  campaign,
  onBack,
  onEdit,
  runningPipelines,
  onRunPipeline
}) => {
  const [validation, setValidation] = useState<CampaignValidation | null>(null);
  const [logs, setLogs] = useState<any>(null);
  const [assets, setAssets] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'validation' | 'logs' | 'live'>('overview');
  const [showLivePipeline, setShowLivePipeline] = useState(false);
  const [logsView, setLogsView] = useState<'assets' | 'logs'>('assets');
  const [currentPage, setCurrentPage] = useState(1);
  const [assetsPerPage, setAssetsPerPage] = useState(20);
  const [expandedProducts, setExpandedProducts] = useState<Set<number>>(new Set());

  useEffect(() => {
    runValidation();
    loadLogs();
    loadAssets();
  }, [campaign]);


  const runValidation = () => {
    const brandChecks = ComplianceService.validateBrandCompliance(campaign);
    const legalChecks = ComplianceService.validateLegalContent(campaign);
    
    const overallScore = Math.round(
      [...brandChecks, ...legalChecks].reduce((sum, check) => sum + (check.score || 0), 0) /
      [...brandChecks, ...legalChecks].length
    );

    setValidation({
      overall_score: overallScore,
      compliance_checks: [...brandChecks, ...legalChecks],
      brand_checks: brandChecks,
      legal_checks: legalChecks
    });
  };

  const loadLogs = async () => {
    try {
      const logsData = await CampaignService.getGenerationLogs(campaign.campaign_id);
      setLogs(logsData);
    } catch (error) {
      console.log('No logs available for this campaign');
    }
  };

  const loadAssets = async () => {
    try {
      const assetsData = await CampaignService.getGeneratedAssets(campaign.campaign_id);
      setAssets(assetsData);
      setCurrentPage(1); // Reset to first page when assets are reloaded
    } catch (error) {
      console.log('No assets available for this campaign');
    }
  };

  const handleRunPipeline = async () => {
    await onRunPipeline(campaign);
    loadLogs(); // Refresh logs after pipeline run
    loadAssets(); // Refresh assets after pipeline run
  };


  const getStatusText = () => {
    const now = new Date();
    const startDate = new Date(campaign.campaign_start_date);
    const endDate = new Date(campaign.campaign_end_date);

    if (now < startDate) return 'Pending';
    if (now > endDate) return 'Completed';
    return 'Active';
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'Active': return 'positive';
      case 'Pending': return 'info';
      case 'Completed': return 'neutral';
      default: return 'neutral';
    }
  };

  const formatCurrency = (amount: string) => {
    const num = parseFloat(amount.replace(/[^0-9.]/g, ''));
    if (num >= 1000000) return `$${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `$${(num / 1000).toFixed(0)}K`;
    return `$${num.toFixed(2)}`;
  };

  const getValidationCounts = () => {
    if (!validation) return { warnings: 0, errors: 0, passed: 0 };
    const warnings = validation.compliance_checks.filter(c => c.status === 'warning').length;
    const errors = validation.compliance_checks.filter(c => c.status === 'failed').length;
    const passed = validation.compliance_checks.filter(c => c.status === 'passed').length;
    return { warnings, errors, passed };
  };

  const getAssetCounts = () => {
    if (!assets) return { generated: 0, planned: campaign.deliverables.total_assets };
    return {
      generated: assets.total_assets || 0,
      planned: campaign.deliverables.total_assets
    };
  };

  const getValidationIcon = (score: number) => {
    if (score >= 85) return <CheckmarkCircle />;
    if (score >= 70) return <Clock />;
    return <Alert />;
  };

  return (
    <View maxWidth="size-7000" margin="auto">
      <View
        backgroundColor="gray-75"
        borderRadius="medium"
        borderWidth="thin"
        borderColor="gray-300"
        marginBottom="size-300"
      >
        <View
          paddingX="size-400"
          paddingY="size-400"
          backgroundColor="gray-50"
          borderBottomWidth="thin"
          borderBottomColor="gray-300"
          UNSAFE_style={{ 
            borderBottom: '2px solid var(--spectrum-global-color-gray-200)',
            marginBottom: 'var(--spectrum-global-dimension-size-500)'
          }}
        >
          <Flex direction="row" justifyContent="space-between" alignItems="center">
            <Flex direction="row" alignItems="center" gap="size-300">
              <ActionButton onPress={onBack} isQuiet>
                <ArrowLeft />
                <Text>Back to Campaigns</Text>
              </ActionButton>
              <View>
                <Heading level={1} margin={0} UNSAFE_style={{ marginBottom: '4px' }}>
                  {campaign.campaign_name}
                </Heading>
                <Text UNSAFE_style={{ 
                  color: 'var(--spectrum-global-color-gray-600)',
                  fontSize: '16px',
                  fontWeight: '400'
                }}>
                  {campaign.client}
                </Text>
              </View>
            </Flex>
            {/* Elevated Action Bar */}
            <Flex direction="row" alignItems="center" gap="size-200" UNSAFE_style={{
              padding: '12px 16px',
              backgroundColor: 'white',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              border: '1px solid var(--spectrum-global-color-gray-200)'
            }}>
              <StatusLight variant={getStatusVariant(getStatusText())} aria-label={`Campaign status: ${getStatusText()}`}>
                {getStatusText()}
              </StatusLight>
              {validation && (
                <Badge 
                  variant={validation.overall_score >= 85 ? 'positive' : validation.overall_score >= 70 ? 'notice' : 'negative'}
                  aria-label={`Compliance score: ${validation.overall_score} percent`}
                >
                  {validation.overall_score}% Compliant
                </Badge>
              )}
              <ButtonGroup>
                <ActionButton 
                  onPress={() => onEdit(campaign)} 
                  variant="secondary"
                  aria-label={`Edit ${campaign.campaign_name} campaign`}
                >
                  <Edit />
                  <Text>Edit</Text>
                </ActionButton>
                <ActionButton
                  onPress={handleRunPipeline}
                  isDisabled={runningPipelines.has(campaign.campaign_id)}
                  variant="accent"
                  aria-label={`${runningPipelines.has(campaign.campaign_id) ? 'Pipeline running for' : 'Run pipeline for'} ${campaign.campaign_name}`}
                >
                  {runningPipelines.has(campaign.campaign_id) ? (
                    <ProgressCircle size="S" isIndeterminate />
                  ) : (
                    <Play />
                  )}
                  <Text>{runningPipelines.has(campaign.campaign_id) ? 'Running...' : 'Run pipeline'}</Text>
                </ActionButton>
              </ButtonGroup>
            </Flex>
          </Flex>
        </View>

        <View UNSAFE_style={{
          borderBottom: '1px solid var(--spectrum-global-color-gray-200)',
          marginBottom: 'var(--spectrum-global-dimension-size-300)'
        }}>
          <Tabs aria-label="Campaign Details" selectedKey={activeTab} onSelectionChange={(key) => setActiveTab(key as any)}
            UNSAFE_style={{
              '--spectrum-tabs-item-font-size': '15px',
              '--spectrum-tabs-item-padding-x': 'var(--spectrum-global-dimension-size-300)'
            }}
          >
            <TabList UNSAFE_style={{ gap: 'var(--spectrum-global-dimension-size-200)' }}>
              <Item key="overview">
                <View />
                <Text>Overview</Text>
              </Item>
              <Item key="validation">
                <Shield />
                <Flex alignItems="center" gap="size-100">
                  <Text>Compliance</Text>
                  {validation && (() => {
                    const counts = getValidationCounts();
                    return (counts.warnings + counts.errors) > 0 ? (
                      <Badge variant="notice" UNSAFE_style={{ fontSize: '11px', minWidth: '20px' }}>
                        {counts.warnings + counts.errors}
                      </Badge>
                    ) : null;
                  })()}
                </Flex>
              </Item>
              <Item key="logs">
                <FileTemplate />
                <Flex alignItems="center" gap="size-100">
                  <Text>Logs</Text>
                  {assets && assets.total_assets > 0 && (
                    <Badge variant="info" UNSAFE_style={{ fontSize: '11px', minWidth: '20px' }}>
                      {assets.total_assets}
                    </Badge>
                  )}
                </Flex>
              </Item>
              <Item key="live">
                <Play />
                <Text>Live Pipeline</Text>
              </Item>
            </TabList>
          <TabPanels>

            <Item key="overview">
              <View paddingY="size-300">
                <Grid
                  areas={['main stats', 'main stats']}
                  columns={['2fr', '1fr']}
                  rows={['auto']}
                  gap="size-300"
                >
                  <View gridArea="main">
                    <Well>
                      <Heading level={2}>Campaign Details</Heading>
                      <Divider size="S" />
                      <Grid columns={['120px', '1fr']} gap="size-200" rowGap="size-150">
                        <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)', textAlign: 'right' }}>Start Date:</Text>
                        <Flex alignItems="center" gap="size-100">
                          <Text>{new Date(campaign.campaign_start_date).toLocaleDateString()}</Text>
                        </Flex>
                        
                        <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)', textAlign: 'right' }}>End Date:</Text>
                        <Flex alignItems="center" gap="size-100">
                          <Text>{new Date(campaign.campaign_end_date).toLocaleDateString()}</Text>
                        </Flex>
                        
                        <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)', textAlign: 'right' }}>Brand Voice:</Text>
                        <Text>{campaign.campaign_message.brand_voice}</Text>
                        
                        <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)', textAlign: 'right' }}>Target Audience:</Text>
                        <View>
                          <Text><strong>Demographics:</strong> {campaign.target_audience.primary.demographics}</Text>
                          <Text><strong>Psychographics:</strong> {campaign.target_audience.primary.psychographics}</Text>
                        </View>
                      </Grid>

                      <Divider size="S" marginY="size-200" />
                      <View>
                        <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)', marginBottom: '8px', display: 'block' }}>Campaign Message</Text>
                        <Well marginY="size-100">
                          <Heading level={4}>{campaign.campaign_message.primary_headline}</Heading>
                          <Text>{campaign.campaign_message.secondary_headline}</Text>
                          <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)', fontSize: '14px', marginTop: '8px' }}>
                            {campaign.campaign_message.seasonal_theme}
                          </Text>
                        </Well>
                      </View>

                    </Well>
                  </View>

                  <View gridArea="stats">
                    <Flex direction="column" gap="size-300">
                      <Well>
                        <Heading level={2}>Campaign Stats</Heading>
                        <Divider size="S" />
                        <Flex direction="column" gap="size-200">
                          <Flex direction="row" justifyContent="space-between">
                            <Text>Products</Text>
                            <Text UNSAFE_style={{ fontVariantNumeric: 'tabular-nums' }}>{campaign.products.length}</Text>
                          </Flex>
                          
                          <Flex direction="row" justifyContent="space-between">
                            <Text>Regions</Text>
                            <Text UNSAFE_style={{ fontVariantNumeric: 'tabular-nums' }}>{campaign.target_regions.length}</Text>
                          </Flex>
                          
                          <View>
                            <Flex direction="row" justifyContent="space-between" marginBottom="size-75">
                              <Text>Assets Progress</Text>
                              <Text UNSAFE_style={{ fontVariantNumeric: 'tabular-nums' }}>
                                {getAssetCounts().generated} / {getAssetCounts().planned}
                              </Text>
                            </Flex>
                            <Meter 
                              value={getAssetCounts().generated} 
                              maxValue={getAssetCounts().planned}
                              size="S"
                              variant="positive"
                              aria-label={`${getAssetCounts().generated} of ${getAssetCounts().planned} assets generated`}
                            />
                          </View>
                          
                          <Flex direction="row" justifyContent="space-between">
                            <Text>Budget</Text>
                            <Text UNSAFE_style={{ fontVariantNumeric: 'tabular-nums' }}>
                              {formatCurrency(campaign.budget_allocation.total_budget)}
                            </Text>
                          </Flex>
                          
                          <Flex direction="row" justifyContent="space-between">
                            <Text>Cost per Asset</Text>
                            <Badge variant="neutral" UNSAFE_style={{ fontVariantNumeric: 'tabular-nums' }}>
                              {formatCurrency(campaign.budget_allocation.cost_per_asset)}
                            </Badge>
                          </Flex>
                        </Flex>
                      </Well>

                      {validation && (
                        <Well>
                          <Heading level={2}>Compliance Status</Heading>
                          <Divider size="S" />
                          <Flex direction="column" gap="size-200">
                            <View>
                              <Flex direction="row" justifyContent="space-between" alignItems="center" marginBottom="size-75">
                                <Text>Overall Score</Text>
                                <Flex direction="row" alignItems="center" gap="size-100">
                                  <Text UNSAFE_style={{ fontVariantNumeric: 'tabular-nums', fontWeight: '600' }}>
                                    {validation.overall_score}%
                                  </Text>
                                </Flex>
                              </Flex>
                              <Meter 
                                value={validation.overall_score} 
                                maxValue={100}
                                size="S"
                                variant={validation.overall_score >= 85 ? 'positive' : validation.overall_score >= 70 ? 'notice' : 'critical'}
                                aria-label={`Compliance score: ${validation.overall_score} percent`}
                              />
                            </View>
                            
                            <Flex direction="row" gap="size-100" wrap>
                              {(() => {
                                const counts = getValidationCounts();
                                return (
                                  <>
                                    {counts.warnings > 0 && (
                                      <Badge variant="notice" UNSAFE_style={{ fontSize: '12px' }}>
                                        {counts.warnings} Warnings
                                      </Badge>
                                    )}
                                    {counts.errors > 0 && (
                                      <Badge variant="negative" UNSAFE_style={{ fontSize: '12px' }}>
                                        {counts.errors} Errors
                                      </Badge>
                                    )}
                                    {counts.passed > 0 && (
                                      <Badge variant="positive" UNSAFE_style={{ fontSize: '12px' }}>
                                        {counts.passed} Passed
                                      </Badge>
                                    )}
                                  </>
                                );
                              })()}
                            </Flex>
                          </Flex>
                        </Well>
                      )}
                    </Flex>
                  </View>
                </Grid>

                <Well marginY="size-300">
                  <Heading level={2}>Products</Heading>
                  <Divider size="S" />
                  <Grid
                    columns={['1fr', '1fr', '1fr']}
                    gap="size-300"
                    marginTop="size-200"
                  >
                    {campaign.products.map((product, index) => (
                      <View 
                        key={index} 
                        backgroundColor="gray-25"
                        padding="size-200"
                        borderRadius="medium"
                        borderWidth="thin"
                        borderColor="gray-300"
                        UNSAFE_style={{
                          transition: 'all 0.2s ease',
                          ':hover': {
                            transform: 'translateY(-2px)',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
                          }
                        }}
                      >
                        <Flex direction="column" height="100%">
                          <View flex="1">
                            <Heading level={3} marginBottom="size-75">{product.name}</Heading>
                            <Badge variant="neutral" UNSAFE_style={{ marginBottom: '8px', fontSize: '11px' }}>
                              {product.category}
                            </Badge>
                            <Text UNSAFE_style={{ 
                              fontSize: '14px', 
                              lineHeight: '1.4',
                              display: '-webkit-box',
                              WebkitLineClamp: '2',
                              WebkitBoxOrient: 'vertical',
                              overflow: 'hidden'
                            }}>
                              {product.description}
                            </Text>
                            
                            {/* Collapsible Key Benefits */}
                            <View marginTop="size-150">
                              <ActionButton 
                                isQuiet
                                onPress={() => {
                                  const newExpanded = new Set(expandedProducts);
                                  if (expandedProducts.has(index)) {
                                    newExpanded.delete(index);
                                  } else {
                                    newExpanded.add(index);
                                  }
                                  setExpandedProducts(newExpanded);
                                }}
                                UNSAFE_style={{ 
                                  fontSize: '12px', 
                                  padding: '4px 0',
                                  justifyContent: 'flex-start'
                                }}
                                aria-label={`${expandedProducts.has(index) ? 'Hide' : 'Show'} key benefits for ${product.name}`}
                              >
                                <Text UNSAFE_style={{ 
                                  fontWeight: '500', 
                                  fontSize: '12px',
                                  color: 'var(--spectrum-global-color-blue-600)'
                                }}>
                                  {expandedProducts.has(index) ? 'Hide benefits' : 'Show benefits'}
                                </Text>
                              </ActionButton>
                              
                              {expandedProducts.has(index) && (
                                <View marginTop="size-75">
                                  {product.key_benefits.slice(0, 3).map((benefit, i) => (
                                    <Text key={i} UNSAFE_style={{ 
                                      fontSize: '12px', 
                                      color: 'var(--spectrum-global-color-gray-600)',
                                      display: 'block',
                                      marginBottom: '4px'
                                    }}>
                                      • {benefit}
                                    </Text>
                                  ))}
                                </View>
                              )}
                            </View>
                          </View>
                          
                          {/* Footer with price and assets */}
                          <Flex direction="row" justifyContent="space-between" alignItems="center" marginTop="size-200">
                            <Text UNSAFE_style={{ 
                              fontSize: '12px', 
                              fontWeight: '600',
                              color: 'var(--spectrum-global-color-gray-700)',
                              fontVariantNumeric: 'tabular-nums'
                            }}>
                              {formatCurrency(product.target_price)}
                            </Text>
                            <Badge variant="neutral" UNSAFE_style={{ fontSize: '11px' }}>
                              {product.existing_assets.length} Assets
                            </Badge>
                          </Flex>
                        </Flex>
                      </View>
                    ))}
                  </Grid>
                </Well>

                <Well marginY="size-300">
                  <Heading level={2}>Target Regions</Heading>
                  <Divider size="S" />
                  <View marginTop="size-200">
                    <Flex direction="column" gap="size-100">
                      {campaign.target_regions.map((region, index) => (
                        <View 
                          key={index} 
                          backgroundColor="gray-25"
                          borderRadius="medium"
                          borderWidth="thin"
                          borderColor="gray-300"
                          padding="size-200"
                        >
                          <Flex direction="column" gap="size-150">
                            {/* Region Header */}
                            <Flex direction="row" justifyContent="space-between" alignItems="center">
                              <Flex direction="row" alignItems="center" gap="size-150">
                                <Heading level={3}>{region.region}</Heading>
                                <Badge variant="neutral" UNSAFE_style={{ fontSize: '11px' }}>
                                  {region.countries.length} {region.countries.length === 1 ? 'Country' : 'Countries'}
                                </Badge>
                              </Flex>
                              <Text UNSAFE_style={{ 
                                fontSize: '12px', 
                                color: 'var(--spectrum-global-color-gray-600)',
                                fontFamily: 'monospace'
                              }}>
                                {region.region.substring(0, 3).toUpperCase()}
                              </Text>
                            </Flex>
                            
                            {/* Countries and Languages */}
                            <View>
                              <Text UNSAFE_style={{ 
                                fontSize: '12px', 
                                fontWeight: '600', 
                                color: 'var(--spectrum-global-color-gray-700)',
                                marginBottom: '4px'
                              }}>Countries & Languages</Text>
                              <Flex direction="row" gap="size-100" wrap aria-label={`Countries and languages for ${region.region}`}>
                                {region.countries.map((country, i) => (
                                  <Badge key={`country-${i}`} variant="accent">
                                    {country}
                                  </Badge>
                                ))}
                                {region.languages.map((language, i) => (
                                  <Badge key={`lang-${i}`} variant="positive">
                                    {language}
                                  </Badge>
                                ))}
                              </Flex>
                            </View>
                            
                            {/* Cultural Notes */}
                            <View>
                              <Text UNSAFE_style={{ fontSize: '14px', lineHeight: '1.4' }}>
                                {region.cultural_notes}
                              </Text>
                            </View>
                            
                            {/* Messaging Tone */}
                            <Flex direction="row" alignItems="center" gap="size-150">
                              <Text UNSAFE_style={{ 
                                fontSize: '12px', 
                                fontWeight: '600',
                                color: 'var(--spectrum-global-color-gray-700)'
                              }}>Messaging Tone:</Text>
                              <Badge variant="info" UNSAFE_style={{ fontSize: '12px' }}>
                                {region.messaging_adaptation.tone}
                              </Badge>
                            </Flex>
                          </Flex>
                        </View>
                      ))}
                    </Flex>
                  </View>
                </Well>
              </View>
            </Item>

            <Item key="validation">
              {validation && (
                <View paddingY="size-300">
                  <Well>
                    <Flex direction="row" justifyContent="space-between" alignItems="center">
                      <Heading level={2}>Compliance & Validation Report</Heading>
                      <Flex direction="row" alignItems="center" gap="size-100">
                        {validation.overall_score >= 85 ? (
                          <CheckmarkCircle color="positive" />
                        ) : validation.overall_score >= 70 ? (
                          <Clock color="notice" />
                        ) : (
                          <Alert color="negative" />
                        )}
                        <Text>Overall Score: {validation.overall_score}%</Text>
                      </Flex>
                    </Flex>
                    <Divider size="S" />

                    <Flex direction="column" gap="size-300" marginTop="size-300">
                      <View>
                        <Heading level={3}>Brand Compliance Checks</Heading>
                        <Flex direction="column" gap="size-150" marginTop="size-200">
                          {validation.brand_checks.map((check, index) => (
                            <Well key={index} UNSAFE_style={{ border: '1px solid var(--spectrum-global-color-gray-300)' }}>
                              <Flex direction="row" alignItems="flex-start" gap="size-150">
                                <View
                                  width="size-300"
                                  height="size-300"
                                  borderRadius="small"
                                  UNSAFE_style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backgroundColor:
                                      check.status === 'passed' ? 'var(--spectrum-global-color-green-100)' :
                                      check.status === 'warning' ? 'var(--spectrum-global-color-orange-100)' : 'var(--spectrum-global-color-red-100)'
                                  }}
                                >
                                  {check.status === 'passed' ? (
                                    <CheckmarkCircle size="S" color="positive" />
                                  ) : check.status === 'warning' ? (
                                    <Clock size="S" color="notice" />
                                  ) : (
                                    <Alert size="S" color="negative" />
                                  )}
                                </View>
                                <View flex="1">
                                  <Flex direction="row" justifyContent="space-between" alignItems="center">
                                    <Heading level={4}>{check.type.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}</Heading>
                                    <StatusLight variant={check.status === 'passed' ? 'positive' : check.status === 'warning' ? 'notice' : 'negative'}>
                                      {check.status === 'passed' ? 'Pass' : check.status === 'warning' ? 'Warning' : 'Error'}
                                    </StatusLight>
                                  </Flex>
                                  <Text>{check.message}</Text>
                                  {check.score && (
                                    <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-500)', fontSize: '12px' }}>
                                      Score: {check.score}%
                                    </Text>
                                  )}
                                  
                                  <ActionButton 
                                    isQuiet 
                                    marginTop="size-100"
                                    UNSAFE_style={{ fontSize: '12px', alignSelf: 'flex-start' }}
                                    aria-label={`Mark ${check.type} check as acknowledged`}
                                  >
                                    <Text>Mark as acknowledged</Text>
                                  </ActionButton>
                                </View>
                              </Flex>
                            </Well>
                          ))}
                        </Flex>
                      </View>

                      <View>
                        <Heading level={3}>Legal Content Checks</Heading>
                        <Flex direction="column" gap="size-150" marginTop="size-200">
                          {validation.legal_checks.map((check, index) => (
                            <Well key={index} UNSAFE_style={{ border: '1px solid var(--spectrum-global-color-gray-300)' }}>
                              <Flex direction="row" alignItems="flex-start" gap="size-150">
                                <View
                                  width="size-300"
                                  height="size-300"
                                  borderRadius="small"
                                  UNSAFE_style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    backgroundColor:
                                      check.status === 'passed' ? 'var(--spectrum-global-color-green-100)' :
                                      check.status === 'warning' ? 'var(--spectrum-global-color-orange-100)' : 'var(--spectrum-global-color-red-100)'
                                  }}
                                >
                                  {check.status === 'passed' ? (
                                    <CheckmarkCircle size="S" color="positive" />
                                  ) : check.status === 'warning' ? (
                                    <Clock size="S" color="notice" />
                                  ) : (
                                    <Alert size="S" color="negative" />
                                  )}
                                </View>
                                <View flex="1">
                                  <Flex direction="row" justifyContent="space-between" alignItems="center">
                                    <Heading level={4}>{check.type.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}</Heading>
                                    <StatusLight variant={check.status === 'passed' ? 'positive' : check.status === 'warning' ? 'notice' : 'negative'}>
                                      {check.status === 'passed' ? 'Pass' : check.status === 'warning' ? 'Warning' : 'Error'}
                                    </StatusLight>
                                  </Flex>
                                  <Text>{check.message}</Text>
                                  {check.score && (
                                    <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-500)', fontSize: '12px' }}>
                                      Score: {check.score}%
                                    </Text>
                                  )}
                                  
                                  <ActionButton 
                                    isQuiet 
                                    marginTop="size-100"
                                    UNSAFE_style={{ fontSize: '12px', alignSelf: 'flex-start' }}
                                    aria-label={`Mark ${check.type} check as acknowledged`}
                                  >
                                    <Text>Mark as acknowledged</Text>
                                  </ActionButton>
                                </View>
                              </Flex>
                            </Well>
                          ))}
                        </Flex>
                      </View>
                    </Flex>
                  </Well>
                </View>
              )}
            </Item>

            <Item key="logs">
              <View paddingY="size-400" UNSAFE_style={{
                backgroundColor: 'var(--spectrum-global-color-gray-25)',
                minHeight: '100vh'
              }}>
                <View UNSAFE_style={{
                  backgroundColor: 'white',
                  padding: 'var(--spectrum-global-dimension-size-400)',
                  borderRadius: '8px',
                  boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  border: '1px solid var(--spectrum-global-color-gray-200)',
                  marginBottom: 'var(--spectrum-global-dimension-size-400)'
                }}>
                  <Flex direction="row" justifyContent="space-between" alignItems="center" marginBottom="size-300">
                    <View>
                      <Heading level={2} UNSAFE_style={{ 
                        marginBottom: '4px',
                        fontSize: '24px',
                        fontWeight: '600'
                      }}>
                        Generation Logs & Reports
                      </Heading>
                      <Text UNSAFE_style={{ 
                        color: 'var(--spectrum-global-color-gray-600)',
                        fontSize: '14px'
                      }}>
                        View generated assets and pipeline execution details
                      </Text>
                    </View>
                    <Flex gap="size-200" alignItems="center">
                      {/* Tab-style toggles */}
                      <View UNSAFE_style={{
                        backgroundColor: 'var(--spectrum-global-color-gray-100)',
                        padding: '4px',
                        borderRadius: '6px',
                        display: 'flex',
                        flexDirection: 'row'
                      }}>
                        <ActionButton 
                          variant={logsView === 'assets' ? 'accent' : 'secondary'}
                          onPress={() => setLogsView('assets')}
                          UNSAFE_style={{
                            backgroundColor: logsView === 'assets' ? 'white' : 'transparent',
                            boxShadow: logsView === 'assets' ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                            border: 'none'
                          }}
                        >
                          <ViewIcon />
                          <Text>Assets Gallery</Text>
                        </ActionButton>
                        <ActionButton 
                          variant={logsView === 'logs' ? 'accent' : 'secondary'}
                          onPress={() => setLogsView('logs')}
                          UNSAFE_style={{
                            backgroundColor: logsView === 'logs' ? 'white' : 'transparent',
                            boxShadow: logsView === 'logs' ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                            border: 'none'
                          }}
                        >
                          <FileTemplate />
                          <Text>Pipeline Logs</Text>
                        </ActionButton>
                      </View>
                      {logs && (
                        <ActionButton variant="secondary" UNSAFE_style={{
                          borderColor: 'var(--spectrum-global-color-blue-400)',
                          color: 'var(--spectrum-global-color-blue-600)'
                        }}>
                          <Download />
                          <Text>Download Report</Text>
                        </ActionButton>
                      )}
                    </Flex>
                  </Flex>

                  {logsView === 'assets' ? (
                    // Assets Gallery View
                    assets && assets.total_assets > 0 ? (
                      <Flex direction="column" gap="size-400">
                        {/* Enhanced Metrics Grid */}
                        <Grid 
                          areas={['main secondary tertiary quaternary']}
                          columns={['2fr', '1.5fr', '1.5fr', '2fr']}
                          gap="size-300"
                        >
                          {/* Dominant Total Assets Card */}
                          <View gridArea="main" UNSAFE_style={{
                            backgroundColor: 'var(--spectrum-global-color-green-100)',
                            border: '2px solid var(--spectrum-global-color-green-400)',
                            borderRadius: '12px',
                            padding: '24px 20px',
                            textAlign: 'center'
                          }}>
                            <Text UNSAFE_style={{ 
                              fontSize: '14px', 
                              fontWeight: '500',
                              color: 'var(--spectrum-global-color-green-700)',
                              marginBottom: '8px',
                              display: 'block'
                            }}>
                              Total Assets
                            </Text>
                            <Text UNSAFE_style={{ 
                              fontSize: '42px', 
                              fontWeight: '700', 
                              color: 'var(--spectrum-global-color-green-600)',
                              lineHeight: '1',
                              fontVariantNumeric: 'tabular-nums'
                            }}>
                              {assets.total_assets.toLocaleString()}
                            </Text>
                            <Badge variant="positive" UNSAFE_style={{ marginTop: '8px' }}>
                              Ready
                            </Badge>
                          </View>

                          {/* Campaign ID Card */}
                          <View gridArea="secondary" UNSAFE_style={{
                            backgroundColor: 'var(--spectrum-global-color-gray-50)',
                            border: '1px solid var(--spectrum-global-color-gray-300)',
                            borderRadius: '8px',
                            padding: '16px'
                          }}>
                            <Text UNSAFE_style={{ 
                              fontSize: '12px', 
                              fontWeight: '400',
                              color: 'var(--spectrum-global-color-gray-600)',
                              marginBottom: '6px',
                              display: 'block'
                            }}>
                              Campaign ID
                            </Text>
                            <Flex alignItems="center" gap="size-100">
                              <Text UNSAFE_style={{ 
                                fontSize: '14px', 
                                fontWeight: '600', 
                                color: 'var(--spectrum-global-color-blue-600)',
                                fontFamily: 'monospace'
                              }}>
                                {assets.campaign_id}
                              </Text>
                              <ActionButton isQuiet UNSAFE_style={{ minWidth: 'auto', padding: '2px' }} aria-label="Copy campaign ID">
                                <Text UNSAFE_style={{ fontSize: '10px' }}>Copy</Text>
                              </ActionButton>
                            </Flex>
                          </View>

                          {/* Formats Card */}
                          <View gridArea="tertiary" UNSAFE_style={{
                            backgroundColor: 'var(--spectrum-global-color-gray-50)',
                            border: '1px solid var(--spectrum-global-color-gray-300)',
                            borderRadius: '8px',
                            padding: '16px'
                          }}>
                            <Text UNSAFE_style={{ 
                              fontSize: '12px', 
                              fontWeight: '400',
                              color: 'var(--spectrum-global-color-gray-600)',
                              marginBottom: '6px',
                              display: 'block'
                            }}>
                              Formats
                            </Text>
                            <Flex direction="row" gap="size-100" wrap aria-label="Asset formats">
                              <Badge variant="positive">Square</Badge>
                              <Badge variant="notice">Story</Badge>
                              <Badge variant="info">Landscape</Badge>
                            </Flex>
                          </View>

                          {/* Last Generated Card - Right Aligned */}
                          <View gridArea="quaternary" UNSAFE_style={{
                            backgroundColor: 'var(--spectrum-global-color-gray-50)',
                            border: '1px solid var(--spectrum-global-color-gray-300)',
                            borderRadius: '8px',
                            padding: '16px',
                            textAlign: 'right'
                          }}>
                            <Text UNSAFE_style={{ 
                              fontSize: '12px', 
                              fontWeight: '400',
                              color: 'var(--spectrum-global-color-gray-600)',
                              marginBottom: '6px',
                              display: 'block'
                            }}>
                              Last Generated
                            </Text>
                            <Text UNSAFE_style={{ 
                              fontSize: '13px', 
                              color: 'var(--spectrum-global-color-gray-700)',
                              fontWeight: '500'
                            }}>
                              {new Date(assets.assets[0]?.modified).toLocaleString()}
                            </Text>
                          </View>
                        </Grid>

                        {/* Enhanced Asset Gallery */}
                        <View UNSAFE_style={{
                          backgroundColor: 'white',
                          border: '1px solid var(--spectrum-global-color-gray-300)',
                          borderRadius: '8px',
                          overflow: 'hidden'
                        }}>
                          {/* Gallery Header with Filters */}
                          <View UNSAFE_style={{
                            backgroundColor: 'var(--spectrum-global-color-gray-75)',
                            padding: '20px',
                            borderBottom: '1px solid var(--spectrum-global-color-gray-300)'
                          }}>
                            <Flex direction="row" justifyContent="space-between" alignItems="center">
                              <View>
                                <Heading level={3} UNSAFE_style={{ marginBottom: '4px' }}>
                                  Asset Gallery
                                </Heading>
                                <Text UNSAFE_style={{ 
                                  fontSize: '13px', 
                                  color: 'var(--spectrum-global-color-gray-600)'
                                }}>
                                  Browse and manage your generated campaign assets
                                </Text>
                              </View>
                              {/* Filters Bar */}
                              <Flex direction="row" alignItems="center" gap="size-200">
                                <Text UNSAFE_style={{ fontSize: '13px', color: 'var(--spectrum-global-color-gray-700)' }}>
                                  Filters:
                                </Text>
                                <Badge variant="neutral" UNSAFE_style={{ cursor: 'pointer' }}>
                                  All Formats
                                </Badge>
                                <Badge variant="neutral" UNSAFE_style={{ cursor: 'pointer' }}>
                                  All Regions
                                </Badge>
                              </Flex>
                            </Flex>
                          </View>

                          <View padding="size-300">
                            {(() => {
                              const startIndex = (currentPage - 1) * assetsPerPage;
                              const endIndex = startIndex + assetsPerPage;
                              const paginatedAssets = assets.assets.slice(startIndex, endIndex);
                              const totalPages = Math.ceil(assets.assets.length / assetsPerPage);

                              return (
                                <>
                                  {/* Enhanced Pagination Controls */}
                                  <Flex direction="row" justifyContent="space-between" alignItems="center" marginBottom="size-300" UNSAFE_style={{
                                    padding: '16px 20px',
                                    backgroundColor: 'var(--spectrum-global-color-gray-50)',
                                    borderRadius: '8px',
                                    border: '1px solid var(--spectrum-global-color-gray-200)'
                                  }}>
                                    <Flex direction="row" alignItems="center" gap="size-200">
                                      <Text UNSAFE_style={{ fontWeight: '500' }}>Show:</Text>
                                      <Picker
                                        selectedKey={assetsPerPage.toString()}
                                        onSelectionChange={(key) => {
                                          setAssetsPerPage(Number(key));
                                          setCurrentPage(1);
                                        }}
                                        width="size-1200"
                                      >
                                        <Item key="10">10 per page</Item>
                                        <Item key="20">20 per page</Item>
                                        <Item key="50">50 per page</Item>
                                        <Item key="100">100 per page</Item>
                                        <Item key={assets.assets.length.toString()}>All ({assets.assets.length})</Item>
                                      </Picker>
                                    </Flex>
                                    <Flex direction="row" alignItems="center" gap="size-150">
                                      <ActionButton
                                        variant="secondary"
                                        isDisabled={currentPage <= 1}
                                        onPress={() => setCurrentPage(currentPage - 1)}
                                        UNSAFE_style={{ minWidth: '80px' }}
                                      >
                                        <ChevronLeft />
                                        <Text>Previous</Text>
                                      </ActionButton>
                                      <Text UNSAFE_style={{ 
                                        minWidth: '200px', 
                                        textAlign: 'center',
                                        fontWeight: '500'
                                      }}>
                                        Page {currentPage} of {totalPages}
                                      </Text>
                                      <Text UNSAFE_style={{ 
                                        fontSize: '13px', 
                                        color: 'var(--spectrum-global-color-gray-600)',
                                        minWidth: '120px'
                                      }}>
                                        ({startIndex + 1}-{Math.min(endIndex, assets.assets.length)} of {assets.assets.length})
                                      </Text>
                                      <ActionButton
                                        variant="secondary"
                                        isDisabled={currentPage >= totalPages}
                                        onPress={() => setCurrentPage(currentPage + 1)}
                                        UNSAFE_style={{ minWidth: '80px' }}
                                      >
                                        <Text>Next</Text>
                                        <ChevronRight />
                                      </ActionButton>
                                    </Flex>
                                  </Flex>

                                  {/* Enhanced Asset Grid */}
                                  <Grid
                                    columns={['1fr', '1fr', '1fr', '1fr', '1fr']}
                                    gap="size-300"
                                  >
                                    {paginatedAssets.map((asset: any, index: number) => (
                                      <View
                                        key={startIndex + index}
                                        UNSAFE_style={{
                                          backgroundColor: 'white',
                                          borderRadius: '10px',
                                          padding: '12px',
                                          border: '1px solid var(--spectrum-global-color-gray-200)',
                                          cursor: 'pointer',
                                          transition: 'all 0.2s ease',
                                          boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
                                        }}
                                        onMouseEnter={(e) => {
                                          e.currentTarget.style.transform = 'translateY(-2px)';
                                          e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                                        }}
                                        onMouseLeave={(e) => {
                                          e.currentTarget.style.transform = 'translateY(0)';
                                          e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.05)';
                                        }}
                                      >
                                        <Flex direction="column" gap="size-150">
                                          {/* Enhanced Image Preview */}
                                          <View
                                            UNSAFE_style={{
                                              height: '120px',
                                              backgroundColor: 'var(--spectrum-global-color-gray-100)',
                                              borderRadius: '6px',
                                              backgroundImage: `url(http://localhost:3001${asset.url})`,
                                              backgroundSize: 'cover',
                                              backgroundPosition: 'center',
                                              position: 'relative',
                                              overflow: 'hidden'
                                            }}
                                          >
                                            {/* Format Badge Overlay */}
                                            <View UNSAFE_style={{
                                              position: 'absolute',
                                              top: '8px',
                                              left: '8px'
                                            }}>
                                              <Badge 
                                                variant={
                                                  asset.format === 'square' ? 'positive' : 
                                                  asset.format === 'story' ? 'notice' : 'info'
                                                }
                                                UNSAFE_style={{
                                                  fontSize: '10px',
                                                  padding: '4px 8px'
                                                }}
                                              >
                                                {asset.format.toUpperCase()}
                                              </Badge>
                                            </View>
                                          </View>
                                          
                                          {/* File Info */}
                                          <View>
                                            <Text UNSAFE_style={{ 
                                              fontSize: '11px', 
                                              fontWeight: '500',
                                              color: 'var(--spectrum-global-color-gray-800)',
                                              marginBottom: '4px',
                                              wordBreak: 'break-all',
                                              display: '-webkit-box',
                                              WebkitLineClamp: 2,
                                              WebkitBoxOrient: 'vertical',
                                              overflow: 'hidden'
                                            }}>
                                              {asset.filename.replace(/\.[^/.]+$/, "")}
                                            </Text>
                                            
                                            {/* Region and Metadata */}
                                            <Flex direction="row" justifyContent="space-between" alignItems="center">
                                              <Flex direction="row" alignItems="center" gap="size-75">
                                                <Text UNSAFE_style={{ 
                                                  fontSize: '10px', 
                                                  color: 'var(--spectrum-global-color-gray-600)',
                                                  fontWeight: '500'
                                                }}>
                                                  🌍 {asset.region}
                                                </Text>
                                              </Flex>
                                              <Text UNSAFE_style={{ 
                                                fontSize: '9px', 
                                                color: 'var(--spectrum-global-color-gray-500)',
                                                textAlign: 'right'
                                              }}>
                                                {new Date(asset.modified).toLocaleDateString()}
                                              </Text>
                                            </Flex>
                                          </View>
                                        </Flex>
                                      </View>
                                    ))}
                                  </Grid>
                                </>
                              );
                            })()}
                          </View>
                        </View>
                      </Flex>
                    ) : (
                      <View textAlign="center" paddingY="size-600" marginTop="size-300">
                        <IllustratedMessage>
                          <ViewIcon />
                          <Heading>No assets generated yet</Heading>
                          <Content>Run the pipeline to generate creative assets for this campaign.</Content>
                        </IllustratedMessage>
                      </View>
                    )
                  ) : (
                    // Pipeline Logs View
                    logs ? (
                      <Flex direction="column" gap="size-300" marginTop="size-300">
                        <Grid columns={['1fr', '1fr', '1fr']} gap="size-200">
                          <Well UNSAFE_style={{ backgroundColor: 'var(--spectrum-global-color-gray-75)' }}>
                            <Text UNSAFE_style={{ fontSize: '12px', fontWeight: '500', color: 'var(--spectrum-global-color-gray-600)', marginBottom: '4px' }}>
                              Assets Generated
                            </Text>
                            <Text UNSAFE_style={{ 
                              fontSize: '24px', 
                              fontWeight: '700', 
                              color: 'var(--spectrum-global-color-green-600)',
                              fontVariantNumeric: 'tabular-nums'
                            }}>
                              {(logs.assets_generated?.length || 0).toLocaleString()}
                            </Text>
                            <Badge variant="positive" UNSAFE_style={{ marginTop: '4px', fontSize: '10px' }}>
                              Ready
                            </Badge>
                          </Well>
                          <Well UNSAFE_style={{ backgroundColor: 'var(--spectrum-global-color-gray-75)' }}>
                            <Text UNSAFE_style={{ fontSize: '12px', fontWeight: '500', color: 'var(--spectrum-global-color-gray-600)', marginBottom: '4px' }}>
                              Total Cost
                            </Text>
                            <Text UNSAFE_style={{ 
                              fontSize: '24px', 
                              fontWeight: '700', 
                              color: 'var(--spectrum-global-color-blue-600)',
                              fontVariantNumeric: 'tabular-nums'
                            }}>
                              ${(parseFloat(logs.total_cost || '0')).toFixed(2)}
                            </Text>
                            <Text UNSAFE_style={{ fontSize: '10px', color: 'var(--spectrum-global-color-gray-500)', marginTop: '4px' }}>
                              USD
                            </Text>
                          </Well>
                          <Well UNSAFE_style={{ backgroundColor: 'var(--spectrum-global-color-gray-75)' }}>
                            <Text UNSAFE_style={{ fontSize: '12px', fontWeight: '500', color: 'var(--spectrum-global-color-gray-600)', marginBottom: '4px' }}>
                              Processing Time
                            </Text>
                            <Text UNSAFE_style={{ 
                              fontSize: '24px', 
                              fontWeight: '700', 
                              color: 'var(--spectrum-global-color-purple-600)',
                              fontVariantNumeric: 'tabular-nums'
                            }}>
                              {logs.processing_time || 'N/A'}
                            </Text>
                            <Text UNSAFE_style={{ fontSize: '10px', color: 'var(--spectrum-global-color-gray-500)', marginTop: '4px' }}>
                              Duration
                            </Text>
                          </Well>
                        </Grid>

                        <Well UNSAFE_style={{ border: '1px solid var(--spectrum-global-color-gray-300)' }}>
                          <View
                            backgroundColor="gray-75"
                            padding="size-150"
                            borderBottomWidth="thin"
                            borderBottomColor="gray-300"
                          >
                            <Heading level={3}>Pipeline Execution Log</Heading>
                          </View>
                          <View padding="size-200">
                            <pre style={{
                              fontSize: '12px',
                              color: 'var(--spectrum-global-color-gray-600)',
                              backgroundColor: 'var(--spectrum-global-color-gray-100)',
                              padding: '16px',
                              borderRadius: '4px',
                              overflowX: 'auto',
                              whiteSpace: 'pre-wrap'
                            }}>
                              {JSON.stringify(logs, null, 2)}
                            </pre>
                          </View>
                        </Well>
                      </Flex>
                    ) : (
                      <View textAlign="center" paddingY="size-600" marginTop="size-300">
                        <IllustratedMessage>
                          <FileTemplate />
                          <Heading>No logs available</Heading>
                          <Content>Run the pipeline to generate logs and reports.</Content>
                          <ActionButton
                            onPress={handleRunPipeline}
                            isDisabled={runningPipelines.has(campaign.campaign_id)}
                            variant="accent"
                          >
                            {runningPipelines.has(campaign.campaign_id) ? (
                              <ProgressCircle size="S" isIndeterminate />
                            ) : (
                              <Play />
                            )}
                            <Text>{runningPipelines.has(campaign.campaign_id) ? 'Running...' : 'Run Pipeline'}</Text>
                          </ActionButton>
                        </IllustratedMessage>
                      </View>
                    )
                  )}
                </View>
              </View>
            </Item>
            
            <Item key="live">
              <View paddingY="size-300">
                <LivePipelineView 
                  campaignId={campaign.campaign_id} 
                  runningPipelines={runningPipelines}
                  onRunPipeline={onRunPipeline}
                  campaign={campaign}
                />
              </View>
            </Item>
          </TabPanels>
          </Tabs>
        </View>
      </View>
    </View>
  );
};