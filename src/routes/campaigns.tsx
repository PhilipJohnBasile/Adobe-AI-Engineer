import { Outlet, useLoaderData } from 'react-router';

export async function loader() {
  // In framework mode, loaders run server-side when SSR/prerender is on,
  // or client-side when ssr: false. Either way: no filesystem in prod.
  // Always use API in production - no filesystem access
  
  try {
    const response = await fetch('/api/campaigns', { 
      headers: { accept: "application/json" } 
    });
    if (!response.ok) {
      const body = await response.text().catch(() => "");
      throw new Response(`Failed to load campaigns from API: ${response.status} ${body}`, { 
        status: response.status 
      });
    }
    const campaigns = await response.json();
    console.log(`Loaded ${campaigns.length} campaigns from API`);
    return { campaigns };
  } catch (error) {
    console.error('Error loading campaigns:', error);
    // Return empty array to prevent destructuring errors
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