import { json, type LoaderFunctionArgs } from "react-router";
import { Outlet, useLoaderData, useRouteError, isRouteErrorResponse } from 'react-router';
import type { Campaign } from "~/types/Campaign";
import { View, Heading, Text, Flex, Button } from '@adobe/react-spectrum';
import Add from '@spectrum-icons/workflow/Add';

export async function loader(_args: LoaderFunctionArgs) {
  // Dev-only fallback (optional): read local JSON when running vite dev
  if (import.meta.env.DEV) {
    try {
      const mods = import.meta.glob("/api/data/*.json", { eager: true });
      const list = Object.values(mods).map((m: any) => m.default) as Campaign[];
      return json({ campaigns: list });
    } catch {
      // fall through to API
    }
  }

  // Production (and dev fallback): use the API
  const res = await fetch("/api/campaigns", { headers: { accept: "application/json" } });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Response(`Failed to load campaigns from API: ${res.status} ${body}`, { status: res.status });
  }
  const data = (await res.json()) as Campaign[];
  return json({ campaigns: data });
}

export default function CampaignsLayout() {
  const { campaigns } = useLoaderData<typeof loader>(); // <-- now always defined
  
  // Render empty state safely if needed:
  if (!campaigns?.length) {
    return (
      <View padding="size-400" maxWidth="1200px" marginX="auto">
        <Flex direction="row" justifyContent="space-between" alignItems="center" marginBottom="size-400">
          <View>
            <Heading level={1} margin={0}>Campaign Manager</Heading>
            <Text>No campaigns yet.</Text>
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

export function ErrorBoundary() {
  const err = useRouteError();
  if (isRouteErrorResponse(err)) {
    return <div>Failed to load campaigns ({err.status}).</div>;
  }
  return <div>Something went wrong loading campaigns.</div>;
}