import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Heading, Text, ActionButton, Flex, View } from '@adobe/react-spectrum';
import Add from '@spectrum-icons/workflow/Add';

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <Flex direction="column" gap="size-400" alignItems="center" justifyContent="center" minHeight="400px">
      <Heading level={1} marginBottom="size-200">
        Welcome to Campaign Manager
      </Heading>
      <Text marginBottom="size-300">
        Manage your creative automation campaigns with Adobe Experience Cloud
      </Text>
      <Flex gap="size-200">
        <ActionButton 
          variant="accent" 
          onPress={() => navigate('/campaigns')}
        >
          View Campaigns
        </ActionButton>
        <ActionButton 
          variant="primary"
          onPress={() => navigate('/campaigns/new')}
        >
          <Add />
          <Text>Create Campaign</Text>
        </ActionButton>
      </Flex>
    </Flex>
  );
}