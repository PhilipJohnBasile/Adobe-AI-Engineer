import React, { useState, useEffect } from 'react';
import { Campaign, CampaignValidation } from '../types/Campaign';
import { CampaignService, ComplianceService } from '../services/CampaignService';
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
import ViewIcon from '@spectrum-icons/workflow/View';

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
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'validation' | 'logs'>('overview');

  useEffect(() => {
    runValidation();
    loadLogs();
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

  const getStatusColor = () => {
    const now = new Date();
    const startDate = new Date(campaign.campaign_start_date);
    const endDate = new Date(campaign.campaign_end_date);

    if (now < startDate) return 'bg-blue-100 text-blue-800';
    if (now > endDate) return 'bg-gray-100 text-gray-800';
    return 'bg-green-100 text-green-800';
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
    if (score >= 85) return <CheckCircle className="w-5 h-5 text-green-600" />;
    if (score >= 70) return <Clock className="w-5 h-5 text-yellow-600" />;
    return <AlertTriangle className="w-5 h-5 text-red-600" />;
  };

  const getValidationColor = (score: number) => {
    if (score >= 85) return 'bg-green-100 text-green-800';
    if (score >= 70) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
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
          padding="size-300"
          borderBottomWidth="thin"
          borderBottomColor="gray-300"
        >
          <Flex direction="row" justifyContent="space-between" alignItems="center">
            <Flex direction="row" alignItems="center" gap="size-200">
              <ActionButton onPress={onBack} isQuiet>
                <ArrowLeft />
                <Text>Back to Campaigns</Text>
              </ActionButton>
              <View>
                <Heading level={1} margin={0}>{campaign.campaign_name}</Heading>
                <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>
                  {campaign.client}
                </Text>
              </View>
            </Flex>
            <Flex direction="row" alignItems="center" gap="size-150">
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

        <Tabs aria-label="Campaign Details" selectedKey={activeTab} onSelectionChange={(key) => setActiveTab(key as any)}>
          <TabList>
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
              <View paddingY="size-300">
                <Well>
                  <Flex direction="row" justifyContent="space-between" alignItems="center">
                    <Heading level={2}>Generation Logs & Reports</Heading>
                    {logs && (
                      <ActionButton variant="secondary">
                        <Download />
                        <Text>Download Report</Text>
                      </ActionButton>
                    )}
                  </Flex>
                  <Divider size="S" />

                  {logs ? (
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
                    <View textAlign="center" paddingY="size-600">
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
                  )}
                </Well>
              </View>
            </Item>
          </TabPanels>
        </Tabs>
      </View>
    </View>
  );
};