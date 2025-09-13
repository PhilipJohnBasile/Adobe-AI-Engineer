import React, { useState, useEffect } from 'react';
import { Campaign, Product, Region, CreativeFormat } from '../types/Campaign';
import { CampaignService, ComplianceService } from '../services/CampaignService';
import {
  ActionButton,
  Button,
  ButtonGroup,
  Content,
  Dialog,
  DialogTrigger,
  Divider,
  Flex,
  Form,
  Heading,
  IllustratedMessage,
  Item,
  Label,
  NumberField,
  Picker,
  ProgressCircle,
  Section,
  Text,
  TextArea,
  TextField,
  View,
  Well
} from '@adobe/react-spectrum';
import Add from '@spectrum-icons/workflow/Add';
import Close from '@spectrum-icons/workflow/Close';
import SaveFloppy from '@spectrum-icons/workflow/SaveFloppy';
import MagicWand from '@spectrum-icons/workflow/MagicWand';
import Alert from '@spectrum-icons/workflow/Alert';
import CheckmarkCircle from '@spectrum-icons/workflow/CheckmarkCircle';
import Clock from '@spectrum-icons/workflow/Clock';
import Remove from '@spectrum-icons/workflow/Remove';

interface CampaignFormProps {
  campaign?: Campaign;
  onSave: (campaign: Campaign) => void;
  onCancel: () => void;
}

export const CampaignForm: React.FC<CampaignFormProps> = ({
  campaign,
  onSave,
  onCancel
}) => {
  const getInitialFormData = () => {
    if (campaign) {
      return campaign;
    }
    return {
      campaign_id: '',
      campaign_name: '',
      client: 'The Coca-Cola Company',
      campaign_start_date: '',
      campaign_end_date: '',
      campaign_message: {
        primary_headline: '',
        secondary_headline: '',
        brand_voice: 'uplifting, inclusive, joyful, authentic',
        seasonal_theme: ''
      },
      target_audience: {
        primary: {
          demographics: '',
          psychographics: '',
          behavior: ''
        }
      },
      products: [],
      target_regions: [],
      creative_requirements: {
        formats: [
          { name: 'square', dimensions: '1080x1080', platform: 'Instagram Post', usage: 'Main feed posts' },
          { name: 'story', dimensions: '1080x1920', platform: 'Instagram/Facebook Stories', usage: 'Vertical stories' },
          { name: 'landscape', dimensions: '1920x1080', platform: 'Facebook/YouTube Ads', usage: 'Horizontal video ads' }
        ],
        brand_requirements: {
          logo_placement: 'bottom-right or top-left',
          color_compliance: 'must use coca_cola_red #DA020E',
          typography: 'Spencerian Script for headlines, Gotham for body',
          messaging: 'uplifting, inclusive, joyful tone'
        }
      },
      budget_allocation: {
        total_budget: '',
        genai_budget: '',
        estimated_assets: 0,
        cost_per_asset: '$18.50'
      },
      success_metrics: {
        primary_kpis: ['Brand awareness lift', 'Purchase intent', 'Social engagement rate'],
        target_metrics: {
          awareness_lift: '',
          engagement_rate: '',
          seasonal_conversion: ''
        }
      },
      deliverables: {
        total_assets: 0,
        breakdown: {},
        formats_per_product: {}
      }
    };
  };

  const [formData, setFormData] = useState<Partial<Campaign>>(getInitialFormData());

  // Update form data when campaign prop changes
  useEffect(() => {
    if (campaign) {
      setFormData(campaign);
    }
  }, [campaign]);

  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [validation, setValidation] = useState<any>(null);
  const [showValidation, setShowValidation] = useState(false);

  const handleInputChange = (path: string, value: any) => {
    setFormData(prev => {
      const newData = { ...prev };
      const keys = path.split('.');
      let current: any = newData;
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = {};
        current = current[keys[i]];
      }
      
      current[keys[keys.length - 1]] = value;
      return newData;
    });
  };

  const handleArrayChange = (path: string, index: number, field: string, value: any) => {
    setFormData(prev => {
      const newData = { ...prev };
      const keys = path.split('.');
      let current: any = newData;
      
      for (let i = 0; i < keys.length - 1; i++) {
        if (!current[keys[i]]) current[keys[i]] = [];
        current = current[keys[i]];
      }
      
      const array = current[keys[keys.length - 1]] || [];
      array[index] = { ...array[index], [field]: value };
      current[keys[keys.length - 1]] = array;
      return newData;
    });
  };

  const addProduct = () => {
    const newProduct: Product = {
      id: `product_${Date.now()}`,
      name: '',
      category: '',
      description: '',
      key_benefits: [''],
      target_price: '',
      messaging: { primary: '', secondary: '' },
      existing_assets: []
    };

    setFormData(prev => ({
      ...prev,
      products: [...(prev.products || []), newProduct]
    }));
  };

  const removeProduct = (index: number) => {
    setFormData(prev => ({
      ...prev,
      products: prev.products?.filter((_, i) => i !== index) || []
    }));
  };

  const addRegion = () => {
    const newRegion: Region = {
      region: '',
      countries: [''],
      languages: ['en'],
      cultural_notes: '',
      messaging_adaptation: {
        tone: '',
        themes: [''],
        local_context: ''
      }
    };

    setFormData(prev => ({
      ...prev,
      target_regions: [...(prev.target_regions || []), newRegion]
    }));
  };

  const removeRegion = (index: number) => {
    setFormData(prev => ({
      ...prev,
      target_regions: prev.target_regions?.filter((_, i) => i !== index) || []
    }));
  };

  const generateCampaignIdea = async () => {
    setGenerating(true);
    try {
      const prompt = `Generate a creative campaign idea for ${formData.client} with theme: ${formData.campaign_message?.seasonal_theme}`;
      const idea = await CampaignService.generateCampaignIdea(prompt);
      
      setFormData(prev => ({
        ...prev,
        ...idea
      }));
    } catch (error) {
      alert('Failed to generate campaign idea. Using AI generation requires backend setup.');
    } finally {
      setGenerating(false);
    }
  };

  const validateCampaign = () => {
    if (!formData.campaign_name || !formData.products?.length) {
      alert('Please fill in required fields before validation.');
      return;
    }

    const brandChecks = ComplianceService.validateBrandCompliance(formData as Campaign);
    const legalChecks = ComplianceService.validateLegalContent(formData as Campaign);
    
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
    setShowValidation(true);
  };

  const handleSave = async () => {
    if (!formData.campaign_name || !formData.products?.length) {
      alert('Please fill in required fields.');
      return;
    }

    setSaving(true);
    try {
      const campaignData = {
        ...formData,
        campaign_id: formData.campaign_id || `CAMPAIGN_${Date.now()}`
      } as Campaign;

      let savedCampaign;
      if (campaign?.campaign_id) {
        savedCampaign = await CampaignService.updateCampaign(campaign.campaign_id, campaignData);
      } else {
        savedCampaign = await CampaignService.createCampaign(campaignData);
      }

      onSave(savedCampaign);
    } catch (error) {
      alert('Failed to save campaign. Check console for details.');
      console.error(error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <View
      backgroundColor="gray-50"
      borderRadius="medium"
      borderWidth="thin"
      borderColor="gray-300"
      maxWidth="size-6000"
      margin="auto"
    >
      <View
        backgroundColor="gray-75"
        paddingX="size-300"
        paddingY="size-200"
        borderBottomWidth="thin"
        borderBottomColor="gray-300"
      >
        <Flex direction="row" justifyContent="space-between" alignItems="center">
          <View>
            <Heading level={2} margin={0}>
              {campaign ? 'Edit Campaign' : 'Create New Campaign'}
            </Heading>
            <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>
              Adobe Creative Automation Platform
            </Text>
          </View>
          <ButtonGroup>
            <ActionButton
              onPress={generateCampaignIdea}
              isDisabled={generating}
              variant="secondary"
            >
              {generating ? (
                <ProgressCircle
                  size="S"
                  isIndeterminate
                  UNSAFE_style={{ marginRight: '8px' }}
                />
              ) : (
                <MagicWand />
              )}
              <Text>AI Generate</Text>
            </ActionButton>
            <ActionButton onPress={validateCampaign} variant="secondary">
              <Alert />
              <Text>Validate</Text>
            </ActionButton>
            <ActionButton onPress={onCancel} variant="secondary">
              <Close />
              <Text>Cancel</Text>
            </ActionButton>
            <ActionButton
              onPress={handleSave}
              isDisabled={saving}
              variant="accent"
            >
              {saving ? (
                <ProgressCircle
                  size="S"
                  isIndeterminate
                  UNSAFE_style={{ marginRight: '8px' }}
                />
              ) : (
                <SaveFloppy />
              )}
              <Text>Save Campaign</Text>
            </ActionButton>
          </ButtonGroup>
        </Flex>
      </View>

      <View padding="size-300">
        {/* Simple test to see if data is loading */}
        <Heading level={3}>Campaign Editor</Heading>
        <Text>Campaign Name: {formData.campaign_name || 'NOT LOADED'}</Text>
        <Text>Number of Products: {formData.products?.length || 0}</Text>
        <Text>Number of Regions: {formData.target_regions?.length || 0}</Text>

        {/* Simple form fields */}
        <View marginTop="size-200">
          <TextField
            label="Campaign Name"
            value={formData.campaign_name || ''}
            onChange={(value) => handleInputChange('campaign_name', value)}
          />
        </View>

        <View marginTop="size-200">
          <TextField
            label="Client"
            value={formData.client || ''}
            onChange={(value) => handleInputChange('client', value)}
          />
        </View>

        <Section>
          <Heading level={3}>Campaign Message</Heading>
          <Flex direction="column" gap="size-200">
            <Flex direction="row" gap="size-200" wrap>
              <View flex={1} minWidth="size-2400">
                <TextField
                  label="Primary Headline"
                  value={formData.campaign_message?.primary_headline || ''}
                  onChange={(value) => handleInputChange('campaign_message.primary_headline', value)}
                  placeholder="Main campaign headline"
                />
              </View>
              <View flex={1} minWidth="size-2400">
                <TextField
                  label="Secondary Headline"
                  value={formData.campaign_message?.secondary_headline || ''}
                  onChange={(value) => handleInputChange('campaign_message.secondary_headline', value)}
                  placeholder="Supporting headline"
                />
              </View>
            </Flex>
            <TextField
              label="Seasonal Theme"
              value={formData.campaign_message?.seasonal_theme || ''}
              onChange={(value) => handleInputChange('campaign_message.seasonal_theme', value)}
              placeholder="e.g., autumn comfort, warm gatherings, back-to-routine energy"
            />
          </Flex>
        </Section>

        <Section>
          <Flex direction="row" justifyContent="space-between" alignItems="center">
            <Heading level={3}>Products</Heading>
            <ActionButton onPress={addProduct} variant="accent">
              <Add />
              <Text>Add Product</Text>
            </ActionButton>
          </Flex>
          {formData.products?.map((product, index) => (
            <Well key={index} marginY="size-200">
              <Flex direction="column" gap="size-150">
                <Flex direction="row" justifyContent="space-between" alignItems="center">
                  <Heading level={4}>Product {index + 1}</Heading>
                  <ActionButton
                    onPress={() => removeProduct(index)}
                    variant="negative"
                    isQuiet
                  >
                    <Remove />
                  </ActionButton>
                </Flex>
                <Flex direction="row" gap="size-200" wrap>
                  <View flex={1} minWidth="size-2400">
                    <TextField
                      label="Name"
                      value={product.name}
                      onChange={(value) => handleArrayChange('products', index, 'name', value)}
                      placeholder="Product name"
                    />
                  </View>
                  <View flex={1} minWidth="size-2400">
                    <TextField
                      label="Category"
                      value={product.category}
                      onChange={(value) => handleArrayChange('products', index, 'category', value)}
                      placeholder="Product category"
                    />
                  </View>
                </Flex>
                <TextArea
                  label="Description"
                  value={product.description}
                  onChange={(value) => handleArrayChange('products', index, 'description', value)}
                  placeholder="Product description"
                  height="size-800"
                />
              </Flex>
            </Well>
          ))}
        </Section>

        <Section>
          <Flex direction="row" justifyContent="space-between" alignItems="center">
            <Heading level={3}>Target Regions</Heading>
            <ActionButton onPress={addRegion} variant="accent">
              <Add />
              <Text>Add Region</Text>
            </ActionButton>
          </Flex>
          {formData.target_regions?.map((region, index) => (
            <Well key={index} marginY="size-200">
              <Flex direction="column" gap="size-150">
                <Flex direction="row" justifyContent="space-between" alignItems="center">
                  <Heading level={4}>Region {index + 1}</Heading>
                  <ActionButton
                    onPress={() => removeRegion(index)}
                    variant="negative"
                    isQuiet
                  >
                    <Remove />
                  </ActionButton>
                </Flex>
                <Flex direction="row" gap="size-200" wrap>
                  <View flex={1} minWidth="size-2400">
                    <TextField
                      label="Region Name"
                      value={region.region}
                      onChange={(value) => handleArrayChange('target_regions', index, 'region', value)}
                      placeholder="e.g., North America, Europe"
                    />
                  </View>
                  <View flex={1} minWidth="size-2400">
                    <TextField
                      label="Cultural Notes"
                      value={region.cultural_notes}
                      onChange={(value) => handleArrayChange('target_regions', index, 'cultural_notes', value)}
                      placeholder="Cultural context and considerations"
                    />
                  </View>
                </Flex>
              </Flex>
            </Well>
          ))}
        </Section>
      </View>

      <DialogTrigger isOpen={showValidation} onOpenChange={setShowValidation}>
        <ActionButton>Hidden Trigger</ActionButton>
        <Dialog>
          <Heading>Campaign Validation</Heading>
          <Divider />
          <Content>
            {validation && (
              <Flex direction="column" gap="size-200">
                <Well>
                  <Flex direction="row" alignItems="center" gap="size-150">
                    <View
                      width="size-400"
                      height="size-400"
                      borderRadius="small"
                      UNSAFE_style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        backgroundColor:
                          validation.overall_score >= 85 ? '#D4EDDA' :
                          validation.overall_score >= 70 ? '#FFF3CD' : '#F8D7DA'
                      }}
                    >
                      {validation.overall_score >= 85 ? (
                        <CheckmarkCircle color="positive" />
                      ) : validation.overall_score >= 70 ? (
                        <Clock color="notice" />
                      ) : (
                        <Alert color="negative" />
                      )}
                    </View>
                    <View>
                      <Heading level={4}>Overall Score: {validation.overall_score}%</Heading>
                      <Text>
                        {validation.overall_score >= 85 ? 'Campaign meets all compliance requirements' :
                         validation.overall_score >= 70 ? 'Campaign needs minor improvements' :
                         'Campaign requires significant changes'}
                      </Text>
                    </View>
                  </Flex>
                </Well>

                <View>
                  {validation.compliance_checks.map((check: any, index: number) => (
                    <Well key={index} marginY="size-100">
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
                          <Heading level={5}>{check.type.replace('_', ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}</Heading>
                          <Text>{check.message}</Text>
                          {check.score && (
                            <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>
                              Score: {check.score}%
                            </Text>
                          )}
                        </View>
                      </Flex>
                    </Well>
                  ))}
                </View>
              </Flex>
            )}
          </Content>
          <ButtonGroup>
            <Button variant="secondary" onPress={() => setShowValidation(false)}>
              Close
            </Button>
          </ButtonGroup>
        </Dialog>
      </DialogTrigger>
    </View>
  );
};