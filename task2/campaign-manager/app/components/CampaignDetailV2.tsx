import React, { useState } from 'react';
import {
  View,
  Heading,
  Text,
  Flex,
  Button,
  Grid,
  TabList,
  TabPanels,
  Item,
  Tabs,
  Badge,
  StatusLight,
  SearchField,
  Picker
} from '@adobe/react-spectrum';
import { Campaign } from '../types/Campaign';

interface CampaignDetailV2Props {
  campaign: Campaign;
  onBack: () => void;
  onEdit: (campaign: Campaign) => void;
}

// Mock campaign data to ensure we show the detailed content
const mockCampaign: Campaign = {
  campaign_id: "SPRING_REFRESH_2026",
  campaign_name: "Spring Refresh - Coca-Cola Global",
  client: "The Coca-Cola Company",
  status: "Upcoming",
  campaign_start_date: "2026-03-01",
  campaign_end_date: "2026-05-31",
  campaign_message: {
    primary_headline: "Refresh Your Spring",
    secondary_headline: "New Beginnings Start Here",
    brand_voice: "energetic, optimistic, fresh, inspiring"
  },
  products: [
    {
      id: "coca_cola_classic",
      name: "Coca-Cola Classic",
      category: "Cola",
      description: "The original and iconic cola taste perfect for spring celebrations",
      key_benefits: ["Classic refreshing taste", "Perfect for spring gatherings", "Iconic brand heritage", "Social connection"],
      target_price: "$1.50"
    },
    {
      id: "coca_cola_zero",
      name: "Coca-Cola Zero Sugar", 
      category: "Zero Sugar Cola",
      description: "Great Coke taste with zero sugar for active spring lifestyles",
      key_benefits: ["Zero sugar", "Great taste", "Active lifestyle friendly", "No compromise refreshment"],
      target_price: "$1.75"
    },
    {
      id: "sprite",
      name: "Sprite",
      category: "Lemon-Lime Soda", 
      description: "Crisp, clear lemon-lime taste that refreshes spring moments",
      key_benefits: ["Clear refreshment", "Lemon-lime twist", "Spring-perfect taste", "Natural clarity"],
      target_price: "$1.50"
    },
    {
      id: "vitaminwater",
      name: "vitaminwater",
      category: "Enhanced Water",
      description: "Nutrient-enhanced water with vitamins for spring wellness goals", 
      key_benefits: ["Vitamin enhanced", "Functional hydration", "Wellness support", "Spring nutrition"],
      target_price: "$2.50"
    }
  ],
  target_regions: [
    {
      region: "North America",
      countries: ["United States", "Canada", "Mexico"],
      languages: ["en", "es", "fr"],
      cultural_notes: "Spring break season, outdoor activities resuming, fitness culture, spring training"
    },
    {
      region: "Latin America", 
      countries: ["Brazil", "Argentina", "Chile", "Colombia", "Peru", "Venezuela", "Costa Rica"],
      languages: ["pt", "es"],
      cultural_notes: "Autumn season (southern hemisphere), harvest festivals, cooler weather refreshment"
    },
    {
      region: "Europe",
      countries: ["United Kingdom", "France", "Spain", "Italy", "Germany", "Netherlands", "Greece", "Portugal"], 
      languages: ["en", "fr", "es", "it", "de", "nl", "el"],
      cultural_notes: "Spring awakening, café culture, outdoor dining season, Easter celebrations"
    },
    {
      region: "Asia Pacific",
      countries: ["Australia", "Japan", "South Korea", "Thailand", "Philippines", "Indonesia", "Malaysia", "Singapore"],
      languages: ["en", "ja", "ko", "th", "tl", "id", "ms", "zh"],
      cultural_notes: "Autumn season (southern hemisphere), spring season (northern), cherry blossoms, monsoon preparation"
    },
    {
      region: "Middle East & Africa",
      countries: ["South Africa", "Nigeria", "Kenya", "UAE", "Saudi Arabia", "Egypt", "Morocco"],
      languages: ["en", "ar", "fr", "sw", "zu", "am"], 
      cultural_notes: "Autumn harvest (southern), spring warmth (northern), Ramadan season, outdoor gathering season"
    },
    {
      region: "Greater China",
      countries: ["China", "Hong Kong", "Taiwan"],
      languages: ["zh", "en"],
      cultural_notes: "Spring festival aftermath, outdoor activity season, business renewal period"
    },
    {
      region: "India & South Asia",
      countries: ["India", "Bangladesh", "Sri Lanka", "Pakistan"],
      languages: ["hi", "en", "bn", "ta", "te", "ur"],
      cultural_notes: "Spring festivals (Holi), pre-summer season, outdoor celebration time, cricket season"
    },
    {
      region: "Eastern Europe", 
      countries: ["Russia", "Poland", "Czech Republic", "Hungary", "Romania", "Ukraine"],
      languages: ["ru", "pl", "cs", "hu", "ro", "uk"],
      cultural_notes: "Spring awakening after winter, Easter traditions, outdoor season beginning, garden culture"
    }
  ],
  budget_allocation: {
    total_budget: "$98000",
    genai_budget: "$1960"
  }
};

export function CampaignDetailV2({ campaign, onBack, onEdit }: CampaignDetailV2Props) {
  console.log('🚀 CampaignDetailV2 component rendering with campaign:', campaign.campaign_id);
  const [loading] = useState(false);
  const [selectedTab, setSelectedTab] = useState('overview');

  console.log('🔍 Render state:', { loading, campaign: !!campaign });

  if (loading) {
    console.log('📝 Rendering loading state');
    return (
      <View maxWidth="size-7000" marginX="auto" paddingX="size-300" paddingY="size-300">
        <Heading level={2}>Loading Campaign...</Heading>
        <Text>Loading campaign...</Text>
      </View>
    );
  }

  if (!campaign) {
    console.log('📝 No campaign data');
    return (
      <View maxWidth="size-7000" marginX="auto" paddingX="size-300" paddingY="size-300">
        <Heading level={2}>No Campaign Found</Heading>
        <Text>Campaign not found</Text>
      </View>
    );
  }

  console.log('📝 Rendering full campaign detail view');

  return (
    <View maxWidth="size-7000" marginX="auto" paddingX="size-300" paddingY="size-300">
        
        {/* Header with Back Button and Campaign Info */}
        <Flex direction="column" gap="size-300" marginBottom="size-400">
          <Flex alignItems="center" gap="size-200">
            <Button variant="secondary" onPress={onBack}>
              ← Back to Campaigns  
            </Button>
            <View backgroundColor="positive" borderRadius="medium" paddingX="size-100" paddingY="size-50">
              <Text UNSAFE_style={{ color: 'white', fontSize: '12px', fontWeight: '600' }}>
                {campaign.status || 'Upcoming'}
              </Text>
            </View>
            <Button variant="secondary">Edit</Button>
            <Button variant="accent">Run Pipeline</Button>
          </Flex>

          <View>
            <Heading level={1} margin={0}>{campaign.campaign_name}</Heading>
            <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)', fontSize: '16px' }}>
              {campaign.client}
            </Text>
          </View>
        </Flex>

        {/* Navigation Tabs */}
        <Tabs selectedKey={selectedTab} onSelectionChange={(key) => setSelectedTab(key as string)}>
          <TabList>
            <Item key="overview">Overview</Item>
            <Item key="compliance">Compliance & Validation</Item>  
            <Item key="logs">Generation Logs</Item>
            <Item key="pipeline">Live Pipeline</Item>
          </TabList>
          
          <TabPanels>
            <Item key="overview">
              <View marginTop="size-400">
                
                {/* Main Content Grid */}
                <Grid columns="2fr 1fr" gap="size-400" marginBottom="size-500">
                  
                  {/* Left Column - Campaign Details */}
                  <View>
                    <Heading level={3} marginBottom="size-300">Campaign Details</Heading>
                    <View backgroundColor="gray-50" borderRadius="large" padding="size-300" marginBottom="size-400">
                      <Grid columns="repeat(2, 1fr)" gap="size-200" marginBottom="size-300">
                        <View>
                          <Text UNSAFE_style={{ fontSize: '14px', fontWeight: '600', color: 'var(--spectrum-global-color-gray-600)' }}>
                            Start Date
                          </Text>
                          <Text>{campaign.campaign_start_date}</Text>
                        </View>
                        <View>
                          <Text UNSAFE_style={{ fontSize: '14px', fontWeight: '600', color: 'var(--spectrum-global-color-gray-600)' }}>
                            End Date  
                          </Text>
                          <Text>{campaign.campaign_end_date}</Text>
                        </View>
                      </Grid>
                      
                      <View marginTop="size-300">
                        <Text UNSAFE_style={{ fontSize: '14px', fontWeight: '600', color: 'var(--spectrum-global-color-gray-600)' }}>
                          Campaign Message
                        </Text>
                        <Heading level={4} margin="size-100 0">{campaign.campaign_message?.primary_headline}</Heading>
                        <Text marginBottom="size-200">{campaign.campaign_message?.secondary_headline}</Text>
                        <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>
                          Brand Voice: {campaign.campaign_message?.brand_voice}
                        </Text>
                      </View>
                    </View>

                    {/* Target Audience */}
                    <View backgroundColor="gray-50" borderRadius="large" padding="size-300">
                      <Heading level={4} marginBottom="size-200">Target Audience</Heading>
                      <Text size="S" marginBottom="size-100">
                        <strong>Demographics:</strong> 18-35 year olds, active lifestyle, young professionals
                      </Text>
                      <Text size="S" marginBottom="size-100">
                        <strong>Psychographics:</strong> health-conscious, social, optimistic
                      </Text>
                      <Text size="S">
                        <strong>Behavior:</strong> outdoor enthusiasts, fitness-oriented, social media active
                      </Text>
                    </View>
                  </View>

                  {/* Right Column - Campaign Stats */}
                  <View>
                    <Heading level={3} marginBottom="size-300">Campaign Stats</Heading>
                    <View backgroundColor="gray-50" borderRadius="large" padding="size-300" marginBottom="size-300">
                      <Grid columns="repeat(2, 1fr)" gap="size-200" marginBottom="size-300">
                        <View>
                          <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Products</Text>
                          <Text UNSAFE_style={{ fontSize: '24px', fontWeight: '700' }}>7</Text>
                        </View>
                        <View>
                          <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Regions</Text>
                          <Text UNSAFE_style={{ fontSize: '24px', fontWeight: '700' }}>8</Text>
                        </View>
                      </Grid>
                      <Grid columns="repeat(2, 1fr)" gap="size-200" marginBottom="size-300">
                        <View>
                          <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Total Assets</Text>
                          <Text UNSAFE_style={{ fontSize: '24px', fontWeight: '700' }}>168</Text>
                        </View>
                        <View>
                          <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Budget</Text>
                          <Text UNSAFE_style={{ fontSize: '24px', fontWeight: '700' }}>$98000</Text>
                        </View>
                      </Grid>
                      <View>
                        <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Cost per Asset</Text>
                        <Text UNSAFE_style={{ fontSize: '24px', fontWeight: '700' }}>$25.00</Text>
                      </View>
                    </View>

                    {/* Compliance Status */}
                    <View>
                      <Heading level={3} marginBottom="size-300">Compliance Status</Heading>
                      <View backgroundColor="gray-50" borderRadius="large" padding="size-300">
                        <Flex justifyContent="space-between" alignItems="center" marginBottom="size-200">
                          <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Overall Score</Text>
                          <Text UNSAFE_style={{ fontSize: '18px', fontWeight: '700', color: 'var(--spectrum-global-color-orange-600)' }}>80%</Text>
                        </Flex>
                        <Flex justifyContent="space-between" alignItems="center" marginBottom="size-200">
                          <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Brand Checks</Text>
                          <Text size="S">2/3</Text>
                        </Flex>
                        <Flex justifyContent="space-between" alignItems="center">
                          <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Legal Checks</Text>
                          <Text size="S">2/3</Text>
                        </Flex>
                      </View>
                    </View>
                  </View>
                </Grid>

                {/* Products Section */}
                <View marginBottom="size-500">
                  <Heading level={3} marginBottom="size-300">Products</Heading>
                  <Grid columns="repeat(auto-fill, minmax(350px, 1fr))" gap="size-300">
                    {campaign.products?.map((product, index) => (
                      <View key={index} backgroundColor="gray-50" borderRadius="large" padding="size-300">
                        <Flex direction="column" gap="size-200">
                          <Flex justifyContent="space-between" alignItems="flex-start">
                            <Heading level={4} margin={0}>{product.name}</Heading>
                            <View backgroundColor="gray-200" borderRadius="medium" paddingX="size-100" paddingY="size-50">
                              <Text UNSAFE_style={{ fontSize: '12px', fontWeight: '600' }}>{product.category}</Text>
                            </View>
                          </Flex>
                          
                          <Text size="S">{product.description}</Text>

                          <View>
                            <Text UNSAFE_style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px' }}>Key Benefits:</Text>
                            {product.key_benefits?.map((benefit, i) => (
                              <Text key={i} size="XS" UNSAFE_style={{ display: 'block', marginBottom: '4px' }}>
                                • {benefit}
                              </Text>
                            ))}
                          </View>

                          <Flex justifyContent="space-between" alignItems="center" marginTop="size-200">
                            <Text UNSAFE_style={{ fontWeight: '600', fontSize: '16px' }}>
                              Price: {product.target_price}
                            </Text>
                            <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>
                              Assets: 3
                            </Text>
                          </Flex>
                        </Flex>
                      </View>
                    ))}
                  </Grid>
                </View>

                {/* Target Regions Section */}
                <View>
                  <Heading level={3} marginBottom="size-300">Target Regions</Heading>
                  <Grid columns="repeat(auto-fill, minmax(400px, 1fr))" gap="size-300">
                    {campaign.target_regions?.map((region, index) => (
                      <View key={index} backgroundColor="gray-50" borderRadius="large" padding="size-300">
                        <Flex direction="column" gap="size-200">
                          <Heading level={4} margin={0}>{region.region}</Heading>
                          
                          <Text size="S">
                            <strong>Countries:</strong> {region.countries?.join(', ')}
                          </Text>
                          
                          <Text size="S">
                            <strong>Languages:</strong> {region.languages?.join(', ')}
                          </Text>
                          
                          <Text size="S">{region.cultural_notes}</Text>

                          <Text size="XS" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)', marginTop: '8px' }}>
                            <strong>Messaging Tone:</strong> sophisticated and refreshing
                          </Text>
                        </Flex>
                      </View>
                    ))}
                  </Grid>
                </View>
              </View>
            </Item>
            
            <Item key="compliance">
              <View marginTop="size-400">
                
                {/* Brand Voice Section */}
                <View backgroundColor="yellow-100" borderRadius="large" padding="size-300" marginBottom="size-400" borderLeftColor="yellow-600" borderLeftWidth="thick">
                  <Flex alignItems="center" gap="size-200" marginBottom="size-200">
                    <StatusLight variant="notice">Brand Voice</StatusLight>
                  </Flex>
                  <Text size="M" marginBottom="size-100">Brand voice alignment: 0/6 keywords match0</Text>
                </View>

                {/* Legal Content Checks */}
                <Heading level={3} marginBottom="size-300">Legal Content Checks</Heading>

                {/* Forbidden Words Check */}
                <View backgroundColor="green-100" borderRadius="large" padding="size-300" marginBottom="size-300" borderLeftColor="green-600" borderLeftWidth="thick">
                  <Flex alignItems="center" gap="size-200" marginBottom="size-200">
                    <StatusLight variant="positive">Forbidden Words</StatusLight>
                  </Flex>
                  <Text size="M">No prohibited words detected</Text>
                  <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Score: 100%</Text>
                </View>

                {/* Health Claims Check */}
                <View backgroundColor="yellow-100" borderRadius="large" padding="size-300" marginBottom="size-300" borderLeftColor="yellow-600" borderLeftWidth="thick">
                  <Flex alignItems="center" gap="size-200" marginBottom="size-200">
                    <StatusLight variant="notice">Health Claims</StatusLight>
                  </Flex>
                  <Text size="M">Potential health claims require review: vitamin</Text>
                  <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Score: 80%</Text>
                </View>

                {/* Age Appropriate Check */}
                <View backgroundColor="green-100" borderRadius="large" padding="size-300" marginBottom="size-300" borderLeftColor="green-600" borderLeftWidth="thick">
                  <Flex alignItems="center" gap="size-200" marginBottom="size-200">
                    <StatusLight variant="positive">Age Appropriate</StatusLight>
                  </Flex>
                  <Text size="M">Content is age-appropriate</Text>
                  <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>Score: 100%</Text>
                </View>

              </View>
            </Item>
            
            <Item key="logs">
              <View marginTop="size-400">
                
                {/* Generation Stats */}
                <Flex justifyContent="space-between" alignItems="center" marginBottom="size-400">
                  <Heading level={3}>Generation Logs & Reports</Heading>
                  <Flex gap="size-200">
                    <Button variant="secondary">Export Report</Button>
                    <Button variant="secondary">Refresh Logs</Button>
                  </Flex>
                </Flex>

                {/* Stats Cards */}
                <Grid columns="repeat(3, 1fr)" gap="size-300" marginBottom="size-400">
                  <View backgroundColor="green-100" borderRadius="large" padding="size-300" textAlign="center">
                    <Text UNSAFE_style={{ fontSize: '32px', fontWeight: '700', color: 'var(--spectrum-global-color-green-700)' }}>81</Text>
                    <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}>Assets Generated</Text>
                  </View>
                  <View backgroundColor="blue-100" borderRadius="large" padding="size-300" textAlign="center">
                    <Text UNSAFE_style={{ fontSize: '16px', fontWeight: '700', color: 'var(--spectrum-global-color-blue-700)' }}>APPROVED_WITH</Text>
                    <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}>Status</Text>
                  </View>
                  <View backgroundColor="gray-100" borderRadius="large" padding="size-300" textAlign="center">
                    <Text UNSAFE_style={{ fontSize: '16px', fontWeight: '600' }}>SERVICE METADATA</Text>
                    <Text size="S" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-700)' }}>Details</Text>
                  </View>
                </Grid>

                {/* Asset Gallery Controls */}
                <Flex justifyContent="space-between" alignItems="center" marginBottom="size-300">
                  <Heading level={4}>Asset Gallery</Heading>
                  <Flex gap="size-200" alignItems="center">
                    <SearchField placeholder="Search assets..." width="size-2400" />
                    <Picker placeholder="All Products" width="size-1600">
                      <Item key="all">All Products</Item>
                      <Item key="coca_cola">Coca-Cola</Item>
                      <Item key="sprite">Sprite</Item>
                      <Item key="fanta">Fanta</Item>
                    </Picker>
                  </Flex>
                </Flex>

                <Text size="S" marginBottom="size-300">Page 1 of 1 · 1 of 81 ·</Text>

                {/* Generated Assets Grid */}
                <Grid columns="repeat(5, 1fr)" gap="size-200">
                  {/* Red Assets - Coca-Cola Classic */}
                  {Array.from({length: 20}).map((_, i) => (
                    <View key={`red-${i}`} backgroundColor="red-600" borderRadius="medium" padding="size-150" minHeight="size-1200" position="relative">
                      <Badge variant="positive" position="absolute" top="size-100" left="size-100">APPROVED</Badge>
                      <View position="absolute" bottom="size-100" left="size-100">
                        <Text UNSAFE_style={{ color: 'white', fontSize: '10px' }}>
                          coca_cola_classic_{i + 1}_square_North America
                        </Text>
                      </View>
                    </View>
                  ))}
                  
                  {/* Green Assets - Sprite */}
                  {Array.from({length: 20}).map((_, i) => (
                    <View key={`green-${i}`} backgroundColor="green-600" borderRadius="medium" padding="size-150" minHeight="size-1200" position="relative">
                      <Badge variant="positive" position="absolute" top="size-100" left="size-100">APPROVED</Badge>
                      <View position="absolute" bottom="size-100" left="size-100">
                        <Text UNSAFE_style={{ color: 'white', fontSize: '10px' }}>
                          sprite_{i + 1}_square_Europe
                        </Text>
                      </View>
                    </View>
                  ))}

                  {/* Blue Assets - Zero Sugar */}
                  {Array.from({length: 15}).map((_, i) => (
                    <View key={`blue-${i}`} backgroundColor="blue-600" borderRadius="medium" padding="size-150" minHeight="size-1200" position="relative">
                      <Badge variant="positive" position="absolute" top="size-100" left="size-100">APPROVED</Badge>
                      <View position="absolute" bottom="size-100" left="size-100">
                        <Text UNSAFE_style={{ color: 'white', fontSize: '10px' }}>
                          coca_cola_zero_{i + 1}_landscape_Asia
                        </Text>
                      </View>
                    </View>
                  ))}

                  {/* Orange Assets - Fanta */}
                  {Array.from({length: 26}).map((_, i) => (
                    <View key={`orange-${i}`} backgroundColor="orange-600" borderRadius="medium" padding="size-150" minHeight="size-1200" position="relative">
                      <Badge variant="positive" position="absolute" top="size-100" left="size-100">APPROVED</Badge>
                      <View position="absolute" bottom="size-100" left="size-100">
                        <Text UNSAFE_style={{ color: 'white', fontSize: '10px' }}>
                          fanta_orange_{i + 1}_story_Global
                        </Text>
                      </View>
                    </View>
                  ))}
                </Grid>

              </View>
            </Item>
            
            <Item key="pipeline">
              <View marginTop="size-400">
                
                {/* Pipeline Header */}
                <Flex justifyContent="space-between" alignItems="center" marginBottom="size-400">
                  <Heading level={3}>Live Pipeline Generation</Heading>
                  <Badge variant="positive">Ready</Badge>
                </Flex>

                {/* Pipeline Controls */}
                <View backgroundColor="gray-50" borderRadius="large" padding="size-400" marginBottom="size-500">
                  <Text marginBottom="size-300">Ready to run pipeline</Text>
                  <Button variant="accent">▷ Run Pipeline</Button>
                </View>

                {/* Generated Assets Section */}
                <View borderTopWidth="thin" borderTopColor="gray-300" paddingTop="size-400">
                  <Heading level={4} marginBottom="size-300">Generated Assets (0)</Heading>
                  
                  <View textAlign="center" paddingY="size-800">
                    <Text size="M" UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-600)' }}>
                      No assets generated yet. Click "Run Pipeline" to start.
                    </Text>
                  </View>
                </View>

                {/* Pipeline Logs Section */}
                <View borderTopWidth="thin" borderTopColor="gray-300" paddingTop="size-400" marginTop="size-500">
                  <Heading level={4} marginBottom="size-300">Pipeline Logs</Heading>
                  
                  <View backgroundColor="gray-900" borderRadius="medium" padding="size-300" minHeight="size-1000">
                    <Text UNSAFE_style={{ color: 'white', fontFamily: 'monospace', fontSize: '12px' }}>
                      Waiting for pipeline output...
                    </Text>
                  </View>
                </View>

              </View>
            </Item>
          </TabPanels>
        </Tabs>
      </View>
    );
}

