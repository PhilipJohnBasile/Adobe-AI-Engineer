import { Outlet, useLoaderData } from 'react-router';
import type { Route } from './+types/campaigns';

export async function loader(): Promise<Route.LoaderData> {
  try {
    const response = await fetch('http://localhost:3002/api/campaigns');
    if (!response.ok) {
      throw new Error('Failed to load campaigns');
    }
    
    const campaigns = await response.json();
    
    console.log(`Loaded ${campaigns.length} campaigns from API`);
    
    return { campaigns };
  } catch (error) {
    console.error('Error loading campaigns:', error);
    return { campaigns: [] };
  }
}

import { View, Heading, Text, Flex, Button } from '@adobe/react-spectrum';
import Add from '@spectrum-icons/workflow/Add';

export default function CampaignsLayout() {
  const { campaigns } = useLoaderData<typeof loader>();
  
  return (
    <View padding="size-400" maxWidth="1200px" marginX="auto">
      <Flex direction="row" justifyContent="space-between" alignItems="center" marginBottom="size-400">
        <View>
          <Heading level={1} margin={0}>Campaign Manager</Heading>
          <Text>Found {campaigns.length} campaigns</Text>
        </View>
        <Button variant="primary" elementType="a" href="/campaigns/new">
          <Add />
          <Text>New Campaign</Text>
        </Button>
      </Flex>
      <Outlet />
    </View>
  );
}