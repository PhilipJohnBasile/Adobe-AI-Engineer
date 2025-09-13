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
  Well
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
}

export const CampaignDetail: React.FC<CampaignDetailProps> = ({
  campaign,
  onBack,
  onEdit
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
    setLoading(true);
    try {
      const result = await CampaignService.runPipeline(campaign.campaign_id);
      alert(`Pipeline completed! Generated ${result.assets_generated?.length || 0} assets.`);
      loadLogs(); // Refresh logs after pipeline run
    } catch (error) {
      alert('Pipeline failed to run. Check console for details.');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };


  const getStatusText = () => {
    const now = new Date();
    const startDate = new Date(campaign.campaign_start_date);
    const endDate = new Date(campaign.campaign_end_date);

    if (now < startDate) return 'Upcoming';
    if (now > endDate) return 'Completed';
    return 'Active';
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
              <StatusLight variant={getStatusText() === 'Active' ? 'positive' : getStatusText() === 'Upcoming' ? 'notice' : 'neutral'}>
                {getStatusText()}
              </StatusLight>
              {validation && (
                <Badge variant={validation.overall_score >= 85 ? 'positive' : validation.overall_score >= 70 ? 'notice' : 'negative'}>
                  {validation.overall_score}% Compliant
                </Badge>
              )}
              <ButtonGroup>
                <ActionButton onPress={() => onEdit(campaign)} variant="secondary">
                  <Edit />
                  <Text>Edit</Text>
                </ActionButton>
                <ActionButton
                  onPress={handleRunPipeline}
                  isDisabled={loading}
                  variant="accent"
                >
                  {loading ? (
                    <ProgressCircle size="S" isIndeterminate />
                  ) : (
                    <Play />
                  )}
                  <Text>Run Pipeline</Text>
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
                <Text>Compliance & Validation</Text>
              </Item>
              <Item key="logs">
                <FileTemplate />
                <Text>Generation Logs</Text>
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
                      <Flex direction="column" gap="size-200">
                        <Flex direction="row" gap="size-400">
                          <View>
                            <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)' }}>Start Date</Text>
                            <Text>{campaign.campaign_start_date}</Text>
                          </View>
                          <View>
                            <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)' }}>End Date</Text>
                            <Text>{campaign.campaign_end_date}</Text>
                          </View>
                        </Flex>

                        <View>
                          <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)' }}>Campaign Message</Text>
                          <Well marginY="size-100">
                            <Heading level={4}>{campaign.campaign_message.primary_headline}</Heading>
                            <Text>{campaign.campaign_message.secondary_headline}</Text>
                            <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)', fontSize: '14px', marginTop: '8px' }}>
                              {campaign.campaign_message.seasonal_theme}
                            </Text>
                          </Well>
                        </View>

                        <View>
                          <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)' }}>Brand Voice</Text>
                          <Text>{campaign.campaign_message.brand_voice}</Text>
                        </View>

                        <View>
                          <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)' }}>Target Audience</Text>
                          <Well marginY="size-100">
                            <Text><strong>Demographics:</strong> {campaign.target_audience.primary.demographics}</Text>
                            <Text><strong>Psychographics:</strong> {campaign.target_audience.primary.psychographics}</Text>
                            <Text><strong>Behavior:</strong> {campaign.target_audience.primary.behavior}</Text>
                          </Well>
                        </View>
                      </Flex>
                    </Well>
                  </View>

                  <View gridArea="stats">
                    <Flex direction="column" gap="size-300">
                      <Well>
                        <Heading level={2}>Campaign Stats</Heading>
                        <Divider size="S" />
                        <Flex direction="column" gap="size-150">
                          <Flex direction="row" justifyContent="space-between">
                            <Text>Products</Text>
                            <Text>{campaign.products.length}</Text>
                          </Flex>
                          <Flex direction="row" justifyContent="space-between">
                            <Text>Regions</Text>
                            <Text>{campaign.target_regions.length}</Text>
                          </Flex>
                          <Flex direction="row" justifyContent="space-between">
                            <Text>Total Assets</Text>
                            <Text>{campaign.deliverables.total_assets}</Text>
                          </Flex>
                          <Flex direction="row" justifyContent="space-between">
                            <Text>Budget</Text>
                            <Text>{campaign.budget_allocation.total_budget}</Text>
                          </Flex>
                          <Flex direction="row" justifyContent="space-between">
                            <Text>Cost per Asset</Text>
                            <Text>{campaign.budget_allocation.cost_per_asset}</Text>
                          </Flex>
                        </Flex>
                      </Well>

                      {validation && (
                        <Well>
                          <Heading level={2}>Compliance Status</Heading>
                          <Divider size="S" />
                          <Flex direction="column" gap="size-150">
                            <Flex direction="row" justifyContent="space-between" alignItems="center">
                              <Text>Overall Score</Text>
                              <Flex direction="row" alignItems="center" gap="size-100">
                                {validation.overall_score >= 85 ? (
                                  <CheckmarkCircle color="positive" />
                                ) : validation.overall_score >= 70 ? (
                                  <Clock color="notice" />
                                ) : (
                                  <Alert color="negative" />
                                )}
                                <Text>{validation.overall_score}%</Text>
                              </Flex>
                            </Flex>
                            <Flex direction="row" justifyContent="space-between">
                              <Text>Brand Checks</Text>
                              <Text>{validation.brand_checks.filter(c => c.status === 'passed').length}/{validation.brand_checks.length}</Text>
                            </Flex>
                            <Flex direction="row" justifyContent="space-between">
                              <Text>Legal Checks</Text>
                              <Text>{validation.legal_checks.filter(c => c.status === 'passed').length}/{validation.legal_checks.length}</Text>
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
                    gap="size-200"
                    marginTop="size-200"
                  >
                    {campaign.products.map((product, index) => (
                      <Well key={index} UNSAFE_style={{ border: '1px solid var(--spectrum-global-color-gray-300)' }}>
                        <Heading level={3}>{product.name}</Heading>
                        <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)', fontSize: '14px' }}>
                          {product.category}
                        </Text>
                        <Text UNSAFE_style={{ fontSize: '14px', marginTop: '8px' }}>
                          {product.description}
                        </Text>
                        <View marginTop="size-150">
                          <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)' }}>Key Benefits:</Text>
                          {product.key_benefits.map((benefit, i) => (
                            <Text key={i} UNSAFE_style={{ fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)' }}>
                              • {benefit}
                            </Text>
                          ))}
                        </View>
                        <Flex direction="row" justifyContent="space-between" alignItems="center" marginTop="size-150">
                          <Text UNSAFE_style={{ fontSize: '12px', color: 'var(--spectrum-global-color-gray-600)' }}>
                            Price: {product.target_price}
                          </Text>
                          <Text UNSAFE_style={{ fontSize: '12px', color: 'var(--spectrum-global-color-gray-600)' }}>
                            Assets: {product.existing_assets.length}
                          </Text>
                        </Flex>
                      </Well>
                    ))}
                  </Grid>
                </Well>

                <Well marginY="size-300">
                  <Heading level={2}>Target Regions</Heading>
                  <Divider size="S" />
                  <Grid
                    columns={['1fr', '1fr', '1fr']}
                    gap="size-200"
                    marginTop="size-200"
                  >
                    {campaign.target_regions.map((region, index) => (
                      <Well key={index} UNSAFE_style={{ border: '1px solid var(--spectrum-global-color-gray-300)' }}>
                        <Heading level={3}>{region.region}</Heading>
                        <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)', fontSize: '14px' }}>
                          {region.countries.join(', ')} • {region.languages.join(', ')}
                        </Text>
                        <Text UNSAFE_style={{ fontSize: '14px', marginTop: '8px' }}>
                          {region.cultural_notes}
                        </Text>
                        <View marginTop="size-150">
                          <Text UNSAFE_style={{ fontWeight: '600', color: 'var(--spectrum-global-color-gray-700)' }}>Messaging Tone:</Text>
                          <Text UNSAFE_style={{ fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)' }}>
                            {region.messaging_adaptation.tone}
                          </Text>
                        </View>
                      </Well>
                    ))}
                  </Grid>
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
                                      check.status === 'passed' ? '#D4EDDA' :
                                      check.status === 'warning' ? '#FFF3CD' : '#F8D7DA'
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
                                <View>
                                  <Heading level={4}>{check.type.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}</Heading>
                                  <Text>{check.message}</Text>
                                  {check.score && (
                                    <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-500)', fontSize: '12px' }}>
                                      Score: {check.score}%
                                    </Text>
                                  )}
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
                                      check.status === 'passed' ? '#D4EDDA' :
                                      check.status === 'warning' ? '#FFF3CD' : '#F8D7DA'
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
                                <View>
                                  <Heading level={4}>{check.type.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}</Heading>
                                  <Text>{check.message}</Text>
                                  {check.score && (
                                    <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-500)', fontSize: '12px' }}>
                                      Score: {check.score}%
                                    </Text>
                                  )}
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
                              lineHeight: '1'
                            }}>
                              {assets.total_assets}
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
                            <Text UNSAFE_style={{ 
                              fontSize: '14px', 
                              fontWeight: '600', 
                              color: 'var(--spectrum-global-color-blue-600)',
                              wordBreak: 'break-all'
                            }}>
                              {assets.campaign_id}
                            </Text>
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
                            <Flex direction="column" gap="size-75">
                              <Badge variant="info" UNSAFE_style={{ alignSelf: 'flex-start' }}>Square</Badge>
                              <Badge variant="info" UNSAFE_style={{ alignSelf: 'flex-start' }}>Story</Badge>
                              <Badge variant="info" UNSAFE_style={{ alignSelf: 'flex-start' }}>Landscape</Badge>
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
                            <Heading level={3}>Assets Generated</Heading>
                            <Text UNSAFE_style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--spectrum-global-color-green-600)' }}>
                              {logs.assets_generated?.length || 0}
                            </Text>
                          </Well>
                          <Well UNSAFE_style={{ backgroundColor: 'var(--spectrum-global-color-gray-75)' }}>
                            <Heading level={3}>Total Cost</Heading>
                            <Text UNSAFE_style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--spectrum-global-color-blue-600)' }}>
                              ${logs.total_cost || '0.00'}
                            </Text>
                          </Well>
                          <Well UNSAFE_style={{ backgroundColor: 'var(--spectrum-global-color-gray-75)' }}>
                            <Heading level={3}>Processing Time</Heading>
                            <Text UNSAFE_style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--spectrum-global-color-purple-600)' }}>
                              {logs.processing_time || 'N/A'}
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
                            isDisabled={loading}
                            variant="accent"
                          >
                            {loading ? (
                              <ProgressCircle size="S" isIndeterminate />
                            ) : (
                              <Play />
                            )}
                            <Text>Run Pipeline</Text>
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
                <LivePipelineView campaignId={campaign.campaign_id} />
              </View>
            </Item>
          </TabPanels>
          </Tabs>
        </View>
      </View>
    </View>
  );
};