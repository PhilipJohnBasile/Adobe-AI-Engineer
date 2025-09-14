const { app } = require('@azure/functions');
const { BlobServiceClient } = require('@azure/storage-blob');

// Azure Blob Storage setup
let blobServiceClient;
let campaignsContainer;

try {
  const connectionString = process.env.AZURE_STORAGE_CONNECTION_STRING;
  if (connectionString) {
    blobServiceClient = BlobServiceClient.fromConnectionString(connectionString);
    campaignsContainer = blobServiceClient.getContainerClient('campaigns');
    console.log('Azure Blob Storage initialized');
  }
} catch (error) {
  console.warn('Azure storage initialization failed:', error.message);
}

// Helper function to determine campaign status
function determineStatus(campaign) {
  const now = new Date();
  const startDate = new Date(campaign.campaign_start_date || '');
  const endDate = new Date(campaign.campaign_end_date || '');
  
  if (now < startDate) {
    return 'pending';
  } else if (now >= startDate && now <= endDate) {
    return 'active';
  } else {
    return 'completed';
  }
}

// Helper to convert readable stream to string
async function streamToString(readableStream) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    readableStream.on('data', (data) => {
      chunks.push(data instanceof Buffer ? data : Buffer.from(data));
    });
    readableStream.on('end', () => {
      resolve(Buffer.concat(chunks).toString());
    });
    readableStream.on('error', reject);
  });
}

// GET /api/campaigns - List all campaigns
app.http('campaigns-list', {
  methods: ['GET'],
  route: 'campaigns',
  handler: async (request, context) => {
    try {
      if (!campaignsContainer) {
        return {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Azure storage not configured' })
        };
      }

      context.log('Loading campaigns from Azure Blob Storage...');
      const campaigns = [];
      
      for await (const blob of campaignsContainer.listBlobsFlat()) {
        if (blob.name.endsWith('.json')) {
          try {
            const blobClient = campaignsContainer.getBlobClient(blob.name);
            const downloadResponse = await blobClient.download();
            const content = await streamToString(downloadResponse.readableStreamBody);
            const campaignData = JSON.parse(content);
            
            campaigns.push({
              ...campaignData,
              id: campaignData.campaign_id || blob.name.replace('.json', ''),
              name: campaignData.campaign_name,
              status: determineStatus(campaignData),
              created_date: blob.properties.lastModified?.toISOString()
            });
          } catch (error) {
            context.log.warn(`Failed to load ${blob.name}:`, error);
          }
        }
      }
      
      context.log(`Loaded ${campaigns.length} campaigns from Azure`);
      
      return {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(campaigns)
      };
      
    } catch (error) {
      context.log.error('Error loading campaigns:', error);
      return {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Failed to load campaigns' })
      };
    }
  }
});

// GET /api/campaigns/:id - Get specific campaign
app.http('campaigns-get', {
  methods: ['GET'],
  route: 'campaigns/{id}',
  handler: async (request, context) => {
    try {
      if (!campaignsContainer) {
        return {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Azure storage not configured' })
        };
      }

      const campaignId = request.params.id;
      const blobName = `${campaignId}.json`;
      const blobClient = campaignsContainer.getBlobClient(blobName);
      
      context.log(`Loading campaign ${campaignId} from Azure...`);
      
      const downloadResponse = await blobClient.download();
      const content = await streamToString(downloadResponse.readableStreamBody);
      const campaignData = JSON.parse(content);
      
      return {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(campaignData)
      };
      
    } catch (error) {
      context.log.error('Error loading campaign:', error);
      
      if (error.statusCode === 404) {
        return {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Campaign not found' })
        };
      }
      
      return {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Failed to load campaign' })
      };
    }
  }
});

// POST /api/campaigns - Create new campaign
app.http('campaigns-create', {
  methods: ['POST'],
  route: 'campaigns',
  handler: async (request, context) => {
    try {
      if (!campaignsContainer) {
        return {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Azure storage not configured' })
        };
      }

      const campaignData = await request.json();
      
      // Generate campaign ID if not provided
      if (!campaignData.campaign_id) {
        campaignData.campaign_id = `CAMPAIGN_${Date.now()}`;
      }
      
      const campaignId = campaignData.campaign_id;
      const blobName = `${campaignId}.json`;
      const blobClient = campaignsContainer.getBlobClient(blobName);
      
      // Check if campaign already exists
      try {
        await blobClient.getProperties();
        return {
          status: 409,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Campaign already exists' })
        };
      } catch (error) {
        // Campaign doesn't exist, which is what we want for creation
      }
      
      const content = JSON.stringify(campaignData, null, 2);
      
      await blobClient.upload(content, Buffer.byteLength(content), {
        blobHTTPHeaders: {
          blobContentType: 'application/json'
        }
      });
      
      context.log(`Created new campaign ${campaignId} in Azure`);
      
      return {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: true, campaign: campaignData })
      };
      
    } catch (error) {
      context.log.error('Error creating campaign:', error);
      return {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Failed to create campaign' })
      };
    }
  }
});

// PUT /api/campaigns/:id - Update campaign
app.http('campaigns-update', {
  methods: ['PUT'],
  route: 'campaigns/{id}',
  handler: async (request, context) => {
    try {
      if (!campaignsContainer) {
        return {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Azure storage not configured' })
        };
      }

      const campaignId = request.params.id;
      const campaignData = await request.json();
      
      // Ensure the campaign_id matches the URL parameter
      campaignData.campaign_id = campaignId;
      
      const blobName = `${campaignId}.json`;
      const blobClient = campaignsContainer.getBlobClient(blobName);
      const content = JSON.stringify(campaignData, null, 2);
      
      await blobClient.upload(content, Buffer.byteLength(content), {
        blobHTTPHeaders: {
          blobContentType: 'application/json'
        }
      });
      
      context.log(`Saved campaign ${campaignId} to Azure`);
      
      return {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ success: true, campaign: campaignData })
      };
      
    } catch (error) {
      context.log.error('Error saving campaign:', error);
      return {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Failed to save campaign' })
      };
    }
  }
});

// POST /api/campaigns/:id/upload - Upload campaign data
app.http('campaigns-upload', {
  methods: ['POST'],
  route: 'campaigns/{id}/upload',
  handler: async (request, context) => {
    try {
      if (!campaignsContainer) {
        return {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Azure storage not configured' })
        };
      }

      const campaignId = request.params.id;
      const campaignData = await request.json();
      
      if (!campaignData) {
        return {
          status: 400,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'No campaign data provided' })
        };
      }
      
      // Ensure the campaign_id matches the URL parameter
      campaignData.campaign_id = campaignId;
      
      const blobName = `${campaignId}.json`;
      const blobClient = campaignsContainer.getBlobClient(blobName);
      const content = JSON.stringify(campaignData, null, 2);
      
      await blobClient.upload(content, Buffer.byteLength(content), {
        blobHTTPHeaders: {
          blobContentType: 'application/json'
        }
      });
      
      context.log(`Uploaded and saved campaign ${campaignId} to Azure`);
      
      return {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(campaignData)
      };
      
    } catch (error) {
      context.log.error('Error uploading campaign:', error);
      return {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Failed to upload campaign' })
      };
    }
  }
});

// GET /api/campaigns/:id/export - Export campaign
app.http('campaigns-export', {
  methods: ['GET'],
  route: 'campaigns/{id}/export',
  handler: async (request, context) => {
    try {
      if (!campaignsContainer) {
        return {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Azure storage not configured' })
        };
      }

      const campaignId = request.params.id;
      const blobName = `${campaignId}.json`;
      const blobClient = campaignsContainer.getBlobClient(blobName);
      
      const downloadResponse = await blobClient.download();
      const content = await streamToString(downloadResponse.readableStreamBody);
      const campaignData = JSON.parse(content);
      
      context.log(`Exporting campaign ${campaignId} as JSON download`);
      
      return {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Content-Disposition': `attachment; filename="${campaignId}.json"`
        },
        body: JSON.stringify(campaignData, null, 2)
      };
      
    } catch (error) {
      context.log.error('Error exporting campaign:', error);
      
      if (error.statusCode === 404) {
        return {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ error: 'Campaign not found' })
        };
      }
      
      return {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Failed to export campaign' })
      };
    }
  }
});

// GET /api/health - Health check
app.http('health', {
  methods: ['GET'],
  route: 'health',
  handler: async (request, context) => {
    return {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        status: 'ok', 
        timestamp: new Date().toISOString(),
        azureStorage: !!campaignsContainer
      })
    };
  }
});