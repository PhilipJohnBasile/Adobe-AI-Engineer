import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CampaignForm } from '../components/CampaignForm';
import { CampaignService } from '../services/CampaignService';
import { Campaign } from '../types/Campaign';
import { View, Text, ProgressCircle, AlertDialog, DialogTrigger, Button, Flex } from '@adobe/react-spectrum';

export default function CampaignEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadCampaign(id);
    }
  }, [id]);

  const loadCampaign = async (campaignId: string) => {
    try {
      setLoading(true);
      const campaignData = await CampaignService.getCampaign(campaignId);
      setCampaign(campaignData);
      setError(null);
    } catch (err) {
      console.error('Error loading campaign:', err);
      setError('Failed to load campaign for editing');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (updatedCampaign: Campaign) => {
    try {
      await CampaignService.updateCampaign(id!, updatedCampaign);
      // Update local state with saved campaign
      setCampaign(updatedCampaign);
    } catch (err) {
      console.error('Error saving campaign:', err);
    }
  };

  const handleCancel = () => {
    navigate(`/campaigns/${id}`);
  };

  if (loading) {
    return (
      <View padding="size-800">
        <Flex direction="column" alignItems="center" gap="size-200">
          <ProgressCircle aria-label="Loading campaign" isIndeterminate />
          <Text>Loading campaign for editing...</Text>
        </Flex>
      </View>
    );
  }

  if (error || !campaign) {
    return (
      <View padding="size-800">
        <DialogTrigger isDismissable>
          <Button variant="primary">Show Error</Button>
          <AlertDialog
            title="Error Loading Campaign"
            variant="error"
            primaryActionLabel="Go Back"
            onPrimaryAction={() => navigate('/campaigns')}
          >
            {error || 'Campaign not found'}
          </AlertDialog>
        </DialogTrigger>
      </View>
    );
  }

  return (
    <CampaignForm
      campaign={campaign}
      onSave={handleSave}
      onCancel={handleCancel}
    />
  );
}