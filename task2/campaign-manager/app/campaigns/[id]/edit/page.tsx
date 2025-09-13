'use client';

import { useRouter } from 'next/navigation';
import { Provider, defaultTheme } from '@adobe/react-spectrum';
import CampaignFormEditor from '../../../../src/components/CampaignFormEditor';
import { Campaign } from '../../../../src/types/Campaign';

export default function EditCampaignPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const campaignId = params.id;

  const handleSave = async (campaign: Campaign) => {
    const response = await fetch(`/api/campaigns/${campaignId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(campaign)
    });

    if (!response.ok) {
      throw new Error('Failed to save campaign');
    }

    router.push(`/campaigns/${campaignId}`);
  };

  const handleCancel = () => {
    router.push(`/campaigns/${campaignId}`);
  };

  return (
    <Provider theme={defaultTheme}>
      <CampaignFormEditor
        campaignId={campaignId}
        onSave={handleSave}
        onCancel={handleCancel}
      />
    </Provider>
  );
}