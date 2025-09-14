'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import CampaignDetailV2 from '../../../src/components/CampaignDetailV2';

export default function CampaignDetailPage() {
  const params = useParams();
  
  if (!params.id) {
    return <div>Campaign not found</div>;
  }

  return <CampaignDetailV2 campaignId={params.id as string} />;
}