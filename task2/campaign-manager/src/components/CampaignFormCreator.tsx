'use client';

import React, { useState } from 'react';
import {
  View, Flex, Heading, Text, TextField, TextArea, Button, Picker, Item,
  Well, ActionButton, Form, Divider, NumberField, TagGroup, TagList,
  ProgressCircle, StatusLight, AlertDialog, DialogTrigger
} from '@adobe/react-spectrum';
import Add from '@spectrum-icons/workflow/Add';
import Delete from '@spectrum-icons/workflow/Delete';
import { Campaign } from '../types/Campaign';

interface CampaignFormCreatorProps {
  onSave: (campaign: Campaign) => Promise<void>;
  onCancel: () => void;
}

export default function CampaignFormCreator({ onSave, onCancel }: CampaignFormCreatorProps) {
  const [saving, setSaving] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);

  const [campaign, setCampaign] = useState<Campaign>({
    campaign_id: '',
    campaign_name: '',
    client: '',
    campaign_start_date: '',
    campaign_end_date: '',
    campaign_message: {
      primary_headline: '',
      secondary_headline: '',
      brand_voice: '',
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
        {
          name: 'square',
          dimensions: '1080x1080',
          platform: 'Instagram Post',
          usage: 'Main feed posts'
        },
        {
          name: 'story',
          dimensions: '1080x1920',
          platform: 'Instagram/Facebook Stories',
          usage: 'Vertical stories'
        },
        {
          name: 'landscape',
          dimensions: '1920x1080',
          platform: 'Facebook/YouTube Ads',
          usage: 'Horizontal video ads'
        }
      ],
      brand_requirements: {
        logo_placement: 'bottom-right',
        color_compliance: '',
        typography: '',
        messaging: ''
      }
    },
    budget_allocation: {
      total_budget: '',
      genai_budget: '',
      estimated_assets: 0,
      cost_per_asset: ''
    },
    success_metrics: {
      primary_kpis: [],
      target_metrics: {
        awareness_lift: '',
        engagement_rate: '',
        seasonal_conversion: '',
        global_reach: ''
      }
    },
    deliverables: {
      total_assets: 0,
      breakdown: {},
      formats_per_product: {}
    }
  });

  const handleSave = async () => {
    if (!campaign.campaign_id) {
      setErrors(['Campaign ID is required']);
      return;
    }
    
    try {
      setSaving(true);
      setErrors([]);
      await onSave(campaign);
    } catch (error) {
      console.error('Error saving campaign:', error);
      setErrors(['Failed to save campaign']);
    } finally {
      setSaving(false);
    }
  };

  const updateField = (path: string, value: any) => {
    const keys = path.split('.');
    const newCampaign = { ...campaign };
    let current = newCampaign as any;
    
    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) current[keys[i]] = {};
      current = current[keys[i]];
    }
    
    current[keys[keys.length - 1]] = value;
    setCampaign(newCampaign);
  };

  const addProduct = () => {
    const newProduct = {
      id: `product_${Date.now()}`,
      name: '',
      category: '',
      description: '',
      key_benefits: [],
      target_price: '',
      messaging: { primary: '', secondary: '' },
      existing_assets: []
    };
    
    setCampaign({
      ...campaign,
      products: [...campaign.products, newProduct]
    });
  };

  const removeProduct = (index: number) => {
    const products = [...campaign.products];
    products.splice(index, 1);
    setCampaign({ ...campaign, products });
  };

  const addRegion = () => {
    const newRegion = {
      region: '',
      countries: [],
      languages: [],
      cultural_notes: '',
      messaging_adaptation: {
        tone: '',
        themes: [],
        local_context: ''
      }
    };
    
    setCampaign({
      ...campaign,
      target_regions: [...campaign.target_regions, newRegion]
    });
  };

  const removeRegion = (index: number) => {
    const regions = [...campaign.target_regions];
    regions.splice(index, 1);
    setCampaign({ ...campaign, target_regions: regions });
  };

  return (
    <View padding="size-400" maxWidth="800px" marginX="auto">
      <Flex justifyContent="space-between" alignItems="center" marginBottom="size-400">
        <Heading level={2}>Create New Campaign</Heading>
        <Flex gap="size-200">
          <Button variant="secondary" onPress={onCancel}>Cancel</Button>
          <Button 
            variant="accent" 
            onPress={handleSave} 
            isDisabled={saving}
          >
            {saving ? 'Creating...' : 'Create Campaign'}
          </Button>
        </Flex>
      </Flex>

      {errors.length > 0 && (
        <Well marginBottom="size-400">
          <StatusLight variant="negative">Validation errors</StatusLight>
          {errors.map((error, i) => (
            <Text key={i} UNSAFE_style={{ color: 'var(--spectrum-global-color-red-600)' }}>
              {error}
            </Text>
          ))}
        </Well>
      )}

      <Form maxWidth="none">
        {/* Basic Information */}
        <Well marginBottom="size-400">
          <Heading level={3} marginBottom="size-200">Basic Information</Heading>
          
          <TextField
            label="Campaign ID"
            value={campaign.campaign_id}
            onChange={(value) => updateField('campaign_id', value)}
            marginBottom="size-200"
            isRequired
          />
          
          <TextField
            label="Campaign Name"
            value={campaign.campaign_name}
            onChange={(value) => updateField('campaign_name', value)}
            marginBottom="size-200"
          />
          
          <TextField
            label="Client"
            value={campaign.client}
            onChange={(value) => updateField('client', value)}
            marginBottom="size-200"
          />
          
          <Flex gap="size-200" marginBottom="size-200">
            <TextField
              label="Start Date"
              value={campaign.campaign_start_date}
              onChange={(value) => updateField('campaign_start_date', value)}
              flex={1}
            />
            <TextField
              label="End Date"
              value={campaign.campaign_end_date}
              onChange={(value) => updateField('campaign_end_date', value)}
              flex={1}
            />
          </Flex>
        </Well>

        {/* Campaign Message */}
        <Well marginBottom="size-400">
          <Heading level={3} marginBottom="size-200">Campaign Message</Heading>
          
          <TextField
            label="Primary Headline"
            value={campaign.campaign_message.primary_headline}
            onChange={(value) => updateField('campaign_message.primary_headline', value)}
            marginBottom="size-200"
          />
          
          <TextField
            label="Secondary Headline"
            value={campaign.campaign_message.secondary_headline}
            onChange={(value) => updateField('campaign_message.secondary_headline', value)}
            marginBottom="size-200"
          />
          
          <TextField
            label="Brand Voice"
            value={campaign.campaign_message.brand_voice}
            onChange={(value) => updateField('campaign_message.brand_voice', value)}
            marginBottom="size-200"
          />
          
          <TextArea
            label="Seasonal Theme"
            value={campaign.campaign_message.seasonal_theme}
            onChange={(value) => updateField('campaign_message.seasonal_theme', value)}
          />
        </Well>

        {/* Target Audience */}
        <Well marginBottom="size-400">
          <Heading level={3} marginBottom="size-200">Target Audience</Heading>
          
          <TextArea
            label="Demographics"
            value={campaign.target_audience.primary.demographics}
            onChange={(value) => updateField('target_audience.primary.demographics', value)}
            marginBottom="size-200"
          />
          
          <TextArea
            label="Psychographics"
            value={campaign.target_audience.primary.psychographics}
            onChange={(value) => updateField('target_audience.primary.psychographics', value)}
            marginBottom="size-200"
          />
          
          <TextArea
            label="Behavior"
            value={campaign.target_audience.primary.behavior}
            onChange={(value) => updateField('target_audience.primary.behavior', value)}
          />
        </Well>

        {/* Products */}
        <Well marginBottom="size-400">
          <Flex justifyContent="space-between" alignItems="center" marginBottom="size-200">
            <Heading level={3}>Products ({campaign.products.length})</Heading>
            <ActionButton onPress={addProduct}>
              <Add />
              <Text>Add Product</Text>
            </ActionButton>
          </Flex>
          
          {campaign.products.map((product, index) => (
            <Well key={product.id} marginBottom="size-200">
              <Flex justifyContent="space-between" alignItems="center" marginBottom="size-200">
                <Heading level={4}>Product {index + 1}</Heading>
                <ActionButton 
                  onPress={() => removeProduct(index)}
                  UNSAFE_style={{ color: 'var(--spectrum-global-color-red-600)' }}
                >
                  <Delete />
                </ActionButton>
              </Flex>
              
              <Flex gap="size-200" marginBottom="size-200">
                <TextField
                  label="Product ID"
                  value={product.id}
                  onChange={(value) => updateField(`products.${index}.id`, value)}
                  flex={1}
                />
                <TextField
                  label="Name"
                  value={product.name}
                  onChange={(value) => updateField(`products.${index}.name`, value)}
                  flex={1}
                />
              </Flex>
              
              <Flex gap="size-200" marginBottom="size-200">
                <TextField
                  label="Category"
                  value={product.category}
                  onChange={(value) => updateField(`products.${index}.category`, value)}
                  flex={1}
                />
                <TextField
                  label="Target Price"
                  value={product.target_price}
                  onChange={(value) => updateField(`products.${index}.target_price`, value)}
                  flex={1}
                />
              </Flex>
              
              <TextArea
                label="Description"
                value={product.description}
                onChange={(value) => updateField(`products.${index}.description`, value)}
                marginBottom="size-200"
              />
              
              <Flex gap="size-200" marginBottom="size-200">
                <TextField
                  label="Primary Messaging"
                  value={product.messaging.primary}
                  onChange={(value) => updateField(`products.${index}.messaging.primary`, value)}
                  flex={1}
                />
                <TextField
                  label="Secondary Messaging"
                  value={product.messaging.secondary}
                  onChange={(value) => updateField(`products.${index}.messaging.secondary`, value)}
                  flex={1}
                />
              </Flex>
            </Well>
          ))}
        </Well>

        {/* Target Regions */}
        <Well marginBottom="size-400">
          <Flex justifyContent="space-between" alignItems="center" marginBottom="size-200">
            <Heading level={3}>Target Regions ({campaign.target_regions.length})</Heading>
            <ActionButton onPress={addRegion}>
              <Add />
              <Text>Add Region</Text>
            </ActionButton>
          </Flex>
          
          {campaign.target_regions.map((region, index) => (
            <Well key={index} marginBottom="size-200">
              <Flex justifyContent="space-between" alignItems="center" marginBottom="size-200">
                <Heading level={4}>Region {index + 1}</Heading>
                <ActionButton 
                  onPress={() => removeRegion(index)}
                  UNSAFE_style={{ color: 'var(--spectrum-global-color-red-600)' }}
                >
                  <Delete />
                </ActionButton>
              </Flex>
              
              <TextField
                label="Region Name"
                value={region.region}
                onChange={(value) => updateField(`target_regions.${index}.region`, value)}
                marginBottom="size-200"
              />
              
              <TextArea
                label="Cultural Notes"
                value={region.cultural_notes}
                onChange={(value) => updateField(`target_regions.${index}.cultural_notes`, value)}
                marginBottom="size-200"
              />
              
              <TextField
                label="Messaging Tone"
                value={region.messaging_adaptation.tone}
                onChange={(value) => updateField(`target_regions.${index}.messaging_adaptation.tone`, value)}
                marginBottom="size-200"
              />
              
              <TextArea
                label="Local Context"
                value={region.messaging_adaptation.local_context}
                onChange={(value) => updateField(`target_regions.${index}.messaging_adaptation.local_context`, value)}
              />
            </Well>
          ))}
        </Well>

        {/* Budget Information */}
        <Well marginBottom="size-400">
          <Heading level={3} marginBottom="size-200">Budget Allocation</Heading>
          
          <Flex gap="size-200" marginBottom="size-200">
            <TextField
              label="Total Budget"
              value={campaign.budget_allocation.total_budget}
              onChange={(value) => updateField('budget_allocation.total_budget', value)}
              flex={1}
            />
            <TextField
              label="GenAI Budget"
              value={campaign.budget_allocation.genai_budget}
              onChange={(value) => updateField('budget_allocation.genai_budget', value)}
              flex={1}
            />
          </Flex>
          
          <Flex gap="size-200">
            <NumberField
              label="Estimated Assets"
              value={campaign.budget_allocation.estimated_assets}
              onChange={(value) => updateField('budget_allocation.estimated_assets', value)}
              flex={1}
            />
            <TextField
              label="Cost Per Asset"
              value={campaign.budget_allocation.cost_per_asset}
              onChange={(value) => updateField('budget_allocation.cost_per_asset', value)}
              flex={1}
            />
          </Flex>
        </Well>

        {/* Creative Requirements */}
        <Well marginBottom="size-400">
          <Heading level={3} marginBottom="size-200">Brand Requirements</Heading>
          
          <TextField
            label="Logo Placement"
            value={campaign.creative_requirements.brand_requirements.logo_placement}
            onChange={(value) => updateField('creative_requirements.brand_requirements.logo_placement', value)}
            marginBottom="size-200"
          />
          
          <TextField
            label="Color Compliance"
            value={campaign.creative_requirements.brand_requirements.color_compliance}
            onChange={(value) => updateField('creative_requirements.brand_requirements.color_compliance', value)}
            marginBottom="size-200"
          />
          
          <TextField
            label="Typography"
            value={campaign.creative_requirements.brand_requirements.typography}
            onChange={(value) => updateField('creative_requirements.brand_requirements.typography', value)}
            marginBottom="size-200"
          />
          
          <TextField
            label="Messaging Guidelines"
            value={campaign.creative_requirements.brand_requirements.messaging}
            onChange={(value) => updateField('creative_requirements.brand_requirements.messaging', value)}
          />
        </Well>
      </Form>
    </View>
  );
}