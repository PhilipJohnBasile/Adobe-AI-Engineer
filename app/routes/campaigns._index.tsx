import { Link, useLoaderData } from 'react-router';
import type { loader } from './campaigns';
import { 
  View, 
  Heading, 
  Text, 
  Button, 
  Flex,
  Well,
  Badge,
  ButtonGroup
} from '@adobe/react-spectrum';
import ViewDetail from '@spectrum-icons/workflow/ViewDetail';
import Edit from '@spectrum-icons/workflow/Edit';

function getStatusColor(status: string) {
  switch (status) {
    case 'active':
      return 'positive';
    case 'pending':
      return 'notice';
    case 'completed':
      return 'neutral';
    default:
      return 'neutral';
  }
}

export default function CampaignsIndex() {
  const { campaigns } = useLoaderData<typeof loader>();
  
  if (campaigns.length === 0) {
    return (
      <View padding="size-400" minHeight="40vh">
        <Flex direction="column" alignItems="center" justifyContent="center" gap="size-200">
          <Text>No campaigns found.</Text>
          <Button variant="primary" elementType="a" href="/campaigns/new">
            Create Your First Campaign
          </Button>
        </Flex>
      </View>
    );
  }
  
  return (
    <View>
      <Flex direction="column" gap="size-300">
        {campaigns.map((campaign) => (
          <Well key={campaign.id}>
            <Flex direction="row" justifyContent="space-between" alignItems="flex-start" gap="size-200">
              <View flex="1">
                <Flex direction="column" gap="size-100">
                  <Flex direction="row" alignItems="center" gap="size-200">
                    <Heading level={3} margin={0}>
                      <Link to={`/campaigns/${campaign.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                        {campaign.name || campaign.campaign_name}
                      </Link>
                    </Heading>
                    <Badge variant={getStatusColor(campaign.status)}>
                      {campaign.status}
                    </Badge>
                  </Flex>
                  <Text>{campaign.client}</Text>
                  <Flex direction="row" gap="size-400">
                    <Text UNSAFE_style={{ fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)' }}>
                      <strong>Start:</strong> {new Date(campaign.campaign_start_date).toLocaleDateString()}
                    </Text>
                    <Text UNSAFE_style={{ fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)' }}>
                      <strong>End:</strong> {new Date(campaign.campaign_end_date).toLocaleDateString()}
                    </Text>
                  </Flex>
                </Flex>
              </View>
              <ButtonGroup>
                <Button variant="secondary" elementType={Link} href={`/campaigns/${campaign.id}`}>
                  <ViewDetail />
                  <Text>View</Text>
                </Button>
                <Button variant="primary" elementType={Link} href={`/campaigns/${campaign.id}/edit`}>
                  <Edit />
                  <Text>Edit</Text>
                </Button>
              </ButtonGroup>
            </Flex>
          </Well>
        ))}
      </Flex>
    </View>
  );
}