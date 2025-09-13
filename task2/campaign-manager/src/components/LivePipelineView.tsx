import React, { useState, useEffect } from 'react';
import {
  View,
  Flex,
  Heading,
  Text,
  Button,
  ProgressCircle,
  Badge,
  Grid,
  IllustratedMessage,
  Content,
  DialogTrigger,
  Dialog,
  ActionButton,
  Divider
} from '@adobe/react-spectrum';
import { Play, Image, CheckCircle, AlertCircle, Clock } from 'lucide-react';

interface LivePipelineViewProps {
  campaignId: string;
  onClose?: () => void;
  runningPipelines: Set<string>;
  onRunPipeline: (campaign: any) => Promise<void>;
  campaign: any;
}

interface GeneratedAsset {
  filename: string;
  url: string;
  timestamp: Date;
}

export const LivePipelineView: React.FC<LivePipelineViewProps> = ({ 
  campaignId, 
  onClose, 
  runningPipelines, 
  onRunPipeline, 
  campaign 
}) => {
  const [isRunning, setIsRunning] = useState(false);
  const [assets, setAssets] = useState<GeneratedAsset[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [currentStatus, setCurrentStatus] = useState('Ready to run pipeline');
  const [assetCount, setAssetCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const runPipeline = async () => {
    // Use the shared pipeline function
    await onRunPipeline(campaign);
    
    // Local state for live view updates
    setIsRunning(true);
    setAssets([]);
    setLogs([]);
    setError(null);
    setAssetCount(0);
    setCurrentStatus('Connecting to pipeline...');

    // Use Server-Sent Events for real-time updates
    const eventSource = new EventSource(
      `http://localhost:3001/api/campaigns/${campaignId}/generate-live`,
      { withCredentials: false }
    );

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'status':
            setCurrentStatus(data.message);
            break;
            
          case 'asset_generated':
            setAssets(prev => [...prev, {
              filename: data.filename,
              url: `http://localhost:3001${data.url}`,
              timestamp: new Date()
            }]);
            setAssetCount(data.count);
            setCurrentStatus(`Generated ${data.count} assets...`);
            break;
            
          case 'log':
            setLogs(prev => [...prev.slice(-50), data.message]); // Keep last 50 logs
            break;
            
          case 'complete':
            setCurrentStatus(`Pipeline complete! Generated ${data.totalAssets} assets`);
            setIsRunning(false);
            eventSource.close();
            break;
            
          case 'error':
            setError(data.message);
            setCurrentStatus('Pipeline failed');
            setIsRunning(false);
            eventSource.close();
            break;
        }
      } catch (e) {
        console.error('Error parsing SSE data:', e);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      setError('Connection lost');
      setIsRunning(false);
      setCurrentStatus('Connection error');
      eventSource.close();
    };

    // Alternative: Trigger via POST if SSE doesn't work
    fetch(`http://localhost:3001/api/campaigns/${campaignId}/generate-live`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }).catch(err => {
      console.error('Failed to start pipeline:', err);
    });
  };

  return (
    <View padding="size-400" minHeight="600px">
      <Flex direction="column" gap="size-300">
        {/* Header */}
        <Flex justifyContent="space-between" alignItems="center">
          <Heading level={2}>Live Pipeline Generation</Heading>
          <Flex gap="size-200" alignItems="center">
            <Badge variant={isRunning ? 'positive' : 'neutral'}>
              {isRunning ? 'Running' : 'Ready'}
            </Badge>
            {assetCount > 0 && (
              <Badge variant="info">
                {assetCount} Assets
              </Badge>
            )}
          </Flex>
        </Flex>

        {/* Status Bar */}
        <View backgroundColor="gray-100" padding="size-200" borderRadius="medium">
          <Flex alignItems="center" gap="size-200">
            {isRunning && <ProgressCircle size="S" isIndeterminate />}
            <Text>{currentStatus}</Text>
          </Flex>
        </View>

        {/* Control Buttons */}
        <Flex gap="size-200">
          <Button
            variant="cta"
            onPress={runPipeline}
            isDisabled={runningPipelines.has(campaignId)}
          >
            {runningPipelines.has(campaignId) ? (
              <ProgressCircle size="S" isIndeterminate />
            ) : (
              <Play size={16} />
            )}
            <Text>{runningPipelines.has(campaignId) ? 'Running...' : 'Run Pipeline'}</Text>
          </Button>
          {onClose && (
            <Button variant="secondary" onPress={onClose}>
              Close
            </Button>
          )}
        </Flex>

        <Divider />

        {/* Live Asset Grid */}
        <View>
          <Heading level={3} marginBottom="size-200">
            Generated Assets ({assets.length})
          </Heading>
          
          {assets.length === 0 ? (
            <View
              backgroundColor="gray-50"
              padding="size-400"
              borderRadius="medium"
              minHeight="200px"
            >
              <Flex justifyContent="center" alignItems="center" height="100%">
                <Text>No assets generated yet. Click "Run Pipeline" to start.</Text>
              </Flex>
            </View>
          ) : (
            <Grid
              columns={['1fr', '1fr', '1fr', '1fr']}
              gap="size-200"
              maxHeight="400px"
              UNSAFE_style={{ overflowY: 'auto' }}
            >
              {assets.map((asset, index) => (
                <View
                  key={index}
                  backgroundColor="gray-50"
                  borderRadius="medium"
                  padding="size-100"
                  UNSAFE_style={{
                    animation: 'fadeIn 0.5s ease-in',
                    border: '1px solid var(--spectrum-global-color-gray-200)'
                  }}
                >
                  <Flex direction="column" gap="size-100">
                    {/* Asset Preview */}
                    <View
                      height="size-2000"
                      backgroundColor="gray-100"
                      borderRadius="small"
                      UNSAFE_style={{
                        backgroundImage: `url(${asset.url})`,
                        backgroundSize: 'cover',
                        backgroundPosition: 'center'
                      }}
                    >
                      {/* Fallback icon if image doesn't load */}
                      <Flex justifyContent="center" alignItems="center" height="100%">
                        <Image size={24} color="gray" />
                      </Flex>
                    </View>
                    
                    {/* Asset Info */}
                    <Text UNSAFE_style={{ fontSize: '11px', wordBreak: 'break-all' }}>
                      {asset.filename.split('/').pop()}
                    </Text>
                    <Flex alignItems="center" gap="size-50">
                      <CheckCircle size={12} color="green" />
                      <Text UNSAFE_style={{ fontSize: '10px', color: 'var(--spectrum-global-color-gray-600)' }}>
                        {new Date(asset.timestamp).toLocaleTimeString()}
                      </Text>
                    </Flex>
                  </Flex>
                </View>
              ))}
            </Grid>
          )}
        </View>

        <Divider />

        {/* Live Logs */}
        <View>
          <Heading level={3} marginBottom="size-200">
            Pipeline Logs
          </Heading>
          <View
            backgroundColor="gray-900"
            padding="size-200"
            borderRadius="medium"
            maxHeight="200px"
            UNSAFE_style={{
              overflowY: 'auto',
              fontFamily: 'monospace',
              fontSize: '12px'
            }}
          >
            {logs.length === 0 ? (
              <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-400)' }}>
                Waiting for pipeline output...
              </Text>
            ) : (
              logs.map((log, index) => (
                <View key={index} marginBottom="size-50">
                  <Text UNSAFE_style={{ color: 'var(--spectrum-global-color-gray-100)' }}>
                    {log}
                  </Text>
                </View>
              ))
            )}
          </View>
        </View>

        {/* Error Display */}
        {error && (
          <View
            backgroundColor="negative"
            padding="size-200"
            borderRadius="medium"
          >
            <Flex alignItems="center" gap="size-200">
              <AlertCircle size={16} />
              <Text>{error}</Text>
            </Flex>
          </View>
        )}
      </Flex>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </View>
  );
};