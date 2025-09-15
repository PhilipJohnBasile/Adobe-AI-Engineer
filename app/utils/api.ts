// API configuration that detects local vs Azure environment
export function getApiUrl(): string {
  // Check if we're in development
  if (import.meta.env.DEV) {
    return 'http://localhost:3001/api';
  }
  
  // In production, use relative URLs (works for both Azure and local builds)
  return '/api';
}

export async function fetchApi(endpoint: string, options?: RequestInit) {
  const baseUrl = getApiUrl();
  const url = `${baseUrl}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      accept: 'application/json',
      ...options?.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.text().catch(() => 'Unknown error');
    throw new Error(`API request failed: ${response.status} - ${error}`);
  }
  
  return response;
}

// Campaign-specific API functions with fallback to static files
export async function fetchCampaigns() {
  if (import.meta.env.DEV) {
    // In development, use the API server
    const response = await fetchApi('/campaigns');
    return response.json();
  } else {
    // In production, fetch from static files
    try {
      // First try to use API if available
      const response = await fetchApi('/campaigns');
      return response.json();
    } catch {
      // Fallback to static files
      const campaigns = [];
      const campaignFiles = [
        'BAILEYS_HOLIDAY_INDULGENCE_2025.json',
        'CAPTAIN_MORGAN_SUMMER_2025.json',
        'FALL_COKE_2025.json',
        'GUINNESS_ST_PATRICKS_2026.json',
        'JOHNNIE_WALKER_HOLIDAY_2025.json',
        'SMIRNOFF_NIGHTLIFE_2025.json',
        'SPRING_REFRESH_2026.json',
        'SUMMER_VIBES_2025.json',
        'TEST_CAMPAIGN_2025.json'
      ];
      
      for (const file of campaignFiles) {
        try {
          const response = await fetch(`/data/${file}`);
          if (response.ok) {
            const campaign = await response.json();
            campaigns.push(campaign);
          }
        } catch (e) {
          console.warn(`Failed to load campaign file: ${file}`);
        }
      }
      
      return campaigns;
    }
  }
}

export async function fetchCampaign(id: string) {
  if (import.meta.env.DEV) {
    // In development, use the API server
    const response = await fetchApi(`/campaigns/${id}`);
    return response.json();
  } else {
    // In production, try API first, then static file
    try {
      const response = await fetchApi(`/campaigns/${id}`);
      return response.json();
    } catch {
      // Fallback to static file
      const response = await fetch(`/data/${id}.json`);
      if (!response.ok) {
        throw new Error(`Campaign ${id} not found`);
      }
      return response.json();
    }
  }
}

// Campaign CRUD operations (always use API)
export async function createCampaign(campaign: any) {
  const response = await fetchApi('/campaigns', {
    method: 'POST',
    body: JSON.stringify(campaign),
  });
  return response.json();
}

export async function updateCampaign(id: string, campaign: any) {
  const response = await fetchApi(`/campaigns/${id}`, {
    method: 'PUT',
    body: JSON.stringify(campaign),
  });
  return response.json();
}

export async function deleteCampaign(id: string) {
  const response = await fetchApi(`/campaigns/${id}`, {
    method: 'DELETE',
  });
  return response.ok;
}

export async function generateAssets(id: string) {
  const response = await fetchApi(`/campaigns/${id}/generate`, {
    method: 'POST',
  });
  return response.json();
}