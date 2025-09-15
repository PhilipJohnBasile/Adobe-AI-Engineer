import React from 'react';
import { Flex, View, Heading, Text } from '@adobe/react-spectrum';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <View UNSAFE_className="campaign-manager-container" minHeight="100vh">
      {/* Adobe.com style hero header */}
      <View
        UNSAFE_className="adobe-hero-gradient"
        paddingY="size-300"
        borderBottomWidth="thin"
        borderBottomColor="gray-300"
        UNSAFE_style={{
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
          backdropFilter: 'blur(10px)'
        }}
      >
        <Flex justifyContent="space-between" alignItems="center" width="100%" maxWidth="1200px" marginX="auto" paddingX="size-300">
          <Flex alignItems="center" gap="size-200">
            {/* Enhanced Adobe Logo */}
            <View
              width="size-600"
              height="size-600"
              borderRadius="medium"
              UNSAFE_className="adobe-logo"
              UNSAFE_style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '20px',
                fontWeight: '800',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              Ae
            </View>
            <Flex direction="column" gap="size-50">
              <Heading level={1} UNSAFE_style={{margin: 0, fontSize: '28px', fontWeight: '700', color: 'white', textShadow: '0 2px 4px rgba(0,0,0,0.3)'}}>
                Creative Automation
              </Heading>
              <Text UNSAFE_style={{fontSize: '16px', color: 'rgba(255,255,255,0.9)', fontWeight: '500'}}>
                Campaign Manager • Adobe Experience Cloud
              </Text>
            </Flex>
          </Flex>
        </Flex>
      </View>

      {/* Adobe.com style main content with glassmorphism */}
      <View maxWidth="1200px" marginX="auto" padding="size-400">
        <View
          UNSAFE_className="adobe-enhanced-card"
          borderRadius="large"
          padding="size-400"
          minHeight="80vh"
        >
          {children}
        </View>
      </View>

      {/* Adobe.com style footer */}
      <View
        backgroundColor="gray-100"
        paddingY="size-300"
        marginTop="size-600"
        borderTopWidth="thin"
        borderTopColor="gray-300"
      >
        <Flex direction="row" justifyContent="center" alignItems="center" gap="size-100">
          <Text UNSAFE_style={{fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)'}}>
            Powered by
          </Text>
          <Text UNSAFE_className="adobe-gradient-text" UNSAFE_style={{fontSize: '14px', fontWeight: '700'}}>
            Adobe Experience Cloud
          </Text>
          <Text UNSAFE_style={{fontSize: '14px', color: 'var(--spectrum-global-color-gray-600)'}}>
            • Creative Automation Platform
          </Text>
        </Flex>
      </View>
    </View>
  );
}