import { Outlet, useLoaderData } from 'react-router';

export async function loader() {
  // In framework mode, loaders run server-side when SSR/prerender is on,
  // or client-side when ssr: false. Either way: no filesystem in prod.
  // Always use API in production - no filesystem access
  
  try {
    console.log('Loader: Fetching /api/campaigns');
    const response = await fetch('/api/campaigns', { 
      headers: { accept: "application/json" } 
    });
    console.log('Loader: Response status:', response.status, response.ok);
    if (!response.ok) {
      const body = await response.text().catch(() => "");
      console.error('Loader: API error:', response.status, body);
      throw new Response(`Failed to load campaigns from API: ${response.status} ${body}`, { 
        status: response.status 
      });
    }
    let campaigns = await response.json();
    // Map campaign_id to id for frontend compatibility
    if (Array.isArray(campaigns)) {
      campaigns = campaigns.map(c => ({ ...c, id: c.campaign_id }));
    }
    console.log('Loader: Received campaigns:', Array.isArray(campaigns) ? campaigns.length : 'Not an array', typeof campaigns);
    const result = { campaigns };
    console.log('Loader: Returning:', result);
    return result;
  } catch (error) {
    console.error('Loader: Error loading campaigns:', error);
    // Return empty array to prevent destructuring errors
    const errorResult = { campaigns: [] };
    console.log('Loader: Error result:', errorResult);
    return errorResult;
  }
}

import { View, Heading, Text, Flex, Button } from '@adobe/react-spectrum';
import Add from '@spectrum-icons/workflow/Add';

export default function CampaignsLayout() {
  const loaderData = useLoaderData() as { campaigns?: any[] } | undefined;
  console.log('Component: Received loaderData:', loaderData);
  const campaigns = loaderData && Array.isArray(loaderData.campaigns) ? loaderData.campaigns : [];
  console.log('Component: campaigns array:', Array.isArray(campaigns) ? campaigns.length : 'Not an array', typeof campaigns);
  if (!loaderData || !Array.isArray(loaderData.campaigns)) {
    return (
      <View padding="size-400" maxWidth="1200px" marginX="auto">
        <Heading level={1} margin={0}>Campaign Manager</Heading>
        <Text>Failed to load campaigns. Please try again later.</Text>
      </View>
    );
  }
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