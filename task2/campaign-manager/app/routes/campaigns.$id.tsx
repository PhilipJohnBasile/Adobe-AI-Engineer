import { useLoaderData, Link } from 'react-router';
import type { Route } from './+types/campaigns.$id';

export async function loader({ params }: Route.LoaderArgs): Promise<Route.LoaderData> {
  const { id } = params;
  
  try {
    // Use relative path for Azure deployment
    const response = await fetch(`/api/campaigns/${id}`);
    if (!response.ok) {
      throw new Response('Campaign not found', { status: 404 });
    }
    
    const campaign = await response.json();
    
    console.log(`Loaded campaign ${id} from API`);
    
    return { campaign };
  } catch (error) {
    console.error('Error loading campaign:', error);
    throw new Response('Campaign not found', { status: 404 });
  }
}

import { 
  View, 
  Heading, 
  Text, 
  Button, 
  Flex,
  Well,
  Divider,
  Badge
} from '@adobe/react-spectrum';
import Edit from '@spectrum-icons/workflow/Edit';
import ArrowLeft from '@spectrum-icons/workflow/ArrowLeft';

export default function CampaignDetail() {
  const { campaign } = useLoaderData<typeof loader>();
  
  return (
    <View padding="size-400" maxWidth="1200px" marginX="auto">
      {/* Header with actions */}
      <Flex direction="row" justifyContent="space-between" alignItems="center" marginBottom="size-400">
        <Heading level={1} margin={0}>{campaign.campaign_name}</Heading>
        <Flex direction="row" gap="size-150">
          <Button variant="primary" elementType={Link} href={`/campaigns/${campaign.campaign_id}/edit`}>
            <Edit />
            <Text>Edit Campaign</Text>
          </Button>
          <Button variant="secondary" elementType={Link} href="/campaigns">
            <ArrowLeft />
            <Text>Back to List</Text>
          </Button>
        </Flex>
      </Flex>

      <View
        backgroundColor="gray-50"
        borderRadius="medium"
        borderWidth="thin"
        borderColor="gray-300"
        padding="size-400"
      >
        <Flex direction="column" gap="size-400">
          
          {/* Basic Information */}
          <View>
            <Heading level={2}>Basic Information</Heading>
            <Divider size="S" />
            <Flex direction="row" wrap gap="size-300" marginTop="size-200">
              <View flex="1 1 45%">
                <Text><strong>Client:</strong> {campaign.client}</Text>
              </View>
              <View flex="1 1 45%">
                <Text><strong>Campaign ID:</strong> {campaign.campaign_id}</Text>
              </View>
              <View flex="1 1 45%">
                <Text><strong>Start Date:</strong> {new Date(campaign.campaign_start_date).toLocaleDateString()}</Text>
              </View>
              <View flex="1 1 45%">
                <Text><strong>End Date:</strong> {new Date(campaign.campaign_end_date).toLocaleDateString()}</Text>
              </View>
            </Flex>
          </View>

          {/* Campaign Message */}
          <View>
            <Heading level={2}>Campaign Message</Heading>
            <Divider size="S" />
            <Flex direction="column" gap="size-150" marginTop="size-200">
              <Text><strong>Primary Headline:</strong> {campaign.campaign_message.primary_headline}</Text>
              <Text><strong>Secondary Headline:</strong> {campaign.campaign_message.secondary_headline}</Text>
              <Text><strong>Brand Voice:</strong> {campaign.campaign_message.brand_voice}</Text>
              <Text><strong>Seasonal Theme:</strong> {campaign.campaign_message.seasonal_theme}</Text>
            </Flex>
          </View>

          {/* Target Audience */}
          <View>
            <Heading level={2}>Target Audience</Heading>
            <Divider size="S" />
            <Flex direction="column" gap="size-150" marginTop="size-200">
              <Text><strong>Demographics:</strong> {campaign.target_audience.primary.demographics}</Text>
              <Text><strong>Psychographics:</strong> {campaign.target_audience.primary.psychographics}</Text>
              <Text><strong>Behavior:</strong> {campaign.target_audience.primary.behavior}</Text>
            </Flex>
          </View>

          {/* Products */}
          <View>
            <Flex direction="row" alignItems="center" gap="size-150">
              <Heading level={2}>Products</Heading>
              <Badge variant="info">{campaign.products.length}</Badge>
            </Flex>
            <Divider size="S" />
            <Flex direction="column" gap="size-300" marginTop="size-200">
              {campaign.products.map((product, index) => (
                <Well key={index} marginY="size-100">
                  <Flex direction="column" gap="size-150">
                    <Heading level={4} margin={0}>{product.name}</Heading>
                    <Flex direction="row" wrap gap="size-200">
                      <Text><strong>Category:</strong> {product.category}</Text>
                      <Text><strong>Target Price:</strong> {product.target_price}</Text>
                    </Flex>
                    <Text><strong>Description:</strong> {product.description}</Text>
                    <Text><strong>Key Benefits:</strong> {product.key_benefits.join(', ')}</Text>
                  </Flex>
                </Well>
              ))}
            </Flex>
          </View>

          {/* Budget Allocation */}
          <View>
            <Heading level={2}>Budget Allocation</Heading>
            <Divider size="S" />
            <Flex direction="row" wrap gap="size-300" marginTop="size-200">
              <View flex="1 1 45%">
                <Text><strong>Total Budget:</strong> {campaign.budget_allocation.total_budget}</Text>
              </View>
              <View flex="1 1 45%">
                <Text><strong>GenAI Budget:</strong> {campaign.budget_allocation.genai_budget}</Text>
              </View>
              <View flex="1 1 45%">
                <Text><strong>Estimated Assets:</strong> {campaign.budget_allocation.estimated_assets}</Text>
              </View>
              <View flex="1 1 45%">
                <Text><strong>Cost per Asset:</strong> {campaign.budget_allocation.cost_per_asset}</Text>
              </View>
            </Flex>
          </View>

        </Flex>
      </View>
    </View>
  );
}