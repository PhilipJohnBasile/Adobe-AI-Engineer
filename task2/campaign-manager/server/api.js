const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

// Azure Blob Storage
const { AzureCampaignStorage } = require('../lib/azureStorage');

const app = express();
const PORT = 3002;

// Path to the campaigns directory (fallback for local development)
const CAMPAIGNS_DIR = '/Users/pjb/Git/Adobe-AI-Engineer/task2/campaigns';

// Initialize Azure storage (will fall back to filesystem if no connection string)
let azureStorage = null;
try {
  if (process.env.AZURE_STORAGE_CONNECTION_STRING) {
    azureStorage = new AzureCampaignStorage();
    console.log('Azure Blob Storage initialized');
  } else {
    console.log('Azure connection string not found - using filesystem');
  }
} catch (error) {
  console.warn('Azure storage initialization failed - using filesystem:', error.message);
}

// Middleware
app.use(cors());
app.use(express.json());

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

// GET /api/campaigns - List all campaigns
app.get('/api/campaigns', async (req, res) => {
  try {
    let campaigns = [];
    
    if (azureStorage) {
      console.log('Loading campaigns from Azure Blob Storage...');
      campaigns = await azureStorage.listCampaigns();
      console.log(`Loaded ${campaigns.length} campaigns from Azure`);
    } else {
      console.log('Loading campaigns from filesystem...');
      const files = fs.readdirSync(CAMPAIGNS_DIR);
      const jsonFiles = files.filter(file => file.endsWith('.json'));
      
      campaigns = jsonFiles.map(filename => {
        try {
          const filePath = path.join(CAMPAIGNS_DIR, filename);
          const fileContent = fs.readFileSync(filePath, 'utf-8');
          const campaignData = JSON.parse(fileContent);
          
          return {
            ...campaignData,
            id: campaignData.campaign_id || path.basename(filename, '.json'),
            name: campaignData.campaign_name,
            status: determineStatus(campaignData),
            created_date: fs.statSync(filePath).ctime.toISOString()
          };
        } catch (error) {
          console.warn(`Failed to load ${filename}:`, error);
          return null;
        }
      }).filter(campaign => campaign !== null);
      
      console.log(`Loaded ${campaigns.length} campaigns from filesystem`);
    }
    
    res.json(campaigns);
  } catch (error) {
    console.error('Error loading campaigns:', error);
    res.status(500).json({ error: 'Failed to load campaigns' });
  }
});

// GET /api/campaigns/:id - Get specific campaign
app.get('/api/campaigns/:id', async (req, res) => {
  try {
    const campaignId = req.params.id;
    let campaignData;
    
    if (azureStorage) {
      console.log(`Loading campaign ${campaignId} from Azure...`);
      campaignData = await azureStorage.getCampaign(campaignId);
    } else {
      const filePath = path.join(CAMPAIGNS_DIR, `${campaignId}.json`);
      
      if (!fs.existsSync(filePath)) {
        return res.status(404).json({ error: 'Campaign not found' });
      }
      
      const fileContent = fs.readFileSync(filePath, 'utf-8');
      campaignData = JSON.parse(fileContent);
      console.log(`Loaded campaign ${campaignId} from filesystem`);
    }
    
    res.json(campaignData);
  } catch (error) {
    console.error('Error loading campaign:', error);
    if (error.message.includes('not found')) {
      res.status(404).json({ error: 'Campaign not found' });
    } else {
      res.status(500).json({ error: 'Failed to load campaign' });
    }
  }
});

// POST /api/campaigns - Create new campaign
app.post('/api/campaigns', async (req, res) => {
  try {
    const campaignData = req.body;
    
    // Generate campaign ID if not provided
    if (!campaignData.campaign_id) {
      campaignData.campaign_id = `CAMPAIGN_${Date.now()}`;
    }
    
    const campaignId = campaignData.campaign_id;
    
    if (azureStorage) {
      // Check if campaign exists in Azure
      try {
        await azureStorage.getCampaign(campaignId);
        return res.status(409).json({ error: 'Campaign already exists' });
      } catch (error) {
        // Campaign doesn't exist, which is what we want for creation
      }
      
      await azureStorage.saveCampaign(campaignId, campaignData);
      console.log(`Created new campaign ${campaignId} in Azure`);
    } else {
      const filePath = path.join(CAMPAIGNS_DIR, `${campaignId}.json`);
      
      // Check if file already exists
      if (fs.existsSync(filePath)) {
        return res.status(409).json({ error: 'Campaign already exists' });
      }
      
      // Write the JSON file with pretty formatting
      const jsonContent = JSON.stringify(campaignData, null, 2);
      fs.writeFileSync(filePath, jsonContent, 'utf-8');
      console.log(`Created new campaign ${campaignId} in filesystem`);
    }
    
    res.status(201).json({ success: true, campaign: campaignData });
  } catch (error) {
    console.error('Error creating campaign:', error);
    res.status(500).json({ error: 'Failed to create campaign' });
  }
});

// PUT /api/campaigns/:id - Update campaign
app.put('/api/campaigns/:id', async (req, res) => {
  try {
    const campaignId = req.params.id;
    const campaignData = req.body;
    
    // Ensure the campaign_id matches the URL parameter
    campaignData.campaign_id = campaignId;
    
    if (azureStorage) {
      await azureStorage.saveCampaign(campaignId, campaignData);
      console.log(`Saved campaign ${campaignId} to Azure`);
    } else {
      const filePath = path.join(CAMPAIGNS_DIR, `${campaignId}.json`);
      const jsonContent = JSON.stringify(campaignData, null, 2);
      fs.writeFileSync(filePath, jsonContent, 'utf-8');
      console.log(`Saved campaign ${campaignId} to filesystem`);
    }
    
    res.json({ success: true, campaign: campaignData });
  } catch (error) {
    console.error('Error saving campaign:', error);
    res.status(500).json({ error: 'Failed to save campaign' });
  }
});

// POST /api/campaigns/:id/upload - Upload JSON data to replace campaign
app.post('/api/campaigns/:id/upload', async (req, res) => {
  try {
    const campaignId = req.params.id;
    const campaignData = req.body;
    
    if (!campaignData) {
      return res.status(400).json({ error: 'No campaign data provided' });
    }
    
    // Ensure the campaign_id matches the URL parameter
    campaignData.campaign_id = campaignId;
    
    if (azureStorage) {
      await azureStorage.saveCampaign(campaignId, campaignData);
      console.log(`Uploaded and saved campaign ${campaignId} to Azure`);
    } else {
      const filePath = path.join(CAMPAIGNS_DIR, `${campaignId}.json`);
      const jsonContent = JSON.stringify(campaignData, null, 2);
      fs.writeFileSync(filePath, jsonContent, 'utf-8');
      console.log(`Uploaded and saved campaign ${campaignId} to filesystem`);
    }
    
    res.json(campaignData);
  } catch (error) {
    console.error('Error uploading campaign:', error);
    res.status(500).json({ error: 'Failed to upload campaign' });
  }
});

// GET /api/campaigns/:id/export - Export campaign as downloadable JSON
app.get('/api/campaigns/:id/export', async (req, res) => {
  try {
    const campaignId = req.params.id;
    let campaignData;
    
    if (azureStorage) {
      campaignData = await azureStorage.getCampaign(campaignId);
    } else {
      const filePath = path.join(CAMPAIGNS_DIR, `${campaignId}.json`);
      
      if (!fs.existsSync(filePath)) {
        return res.status(404).json({ error: 'Campaign not found' });
      }
      
      const fileContent = fs.readFileSync(filePath, 'utf-8');
      campaignData = JSON.parse(fileContent);
    }
    
    // Set headers for file download
    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Content-Disposition', `attachment; filename="${campaignId}.json"`);
    
    console.log(`Exporting campaign ${campaignId} as JSON download`);
    res.send(JSON.stringify(campaignData, null, 2));
  } catch (error) {
    console.error('Error exporting campaign:', error);
    if (error.message.includes('not found')) {
      res.status(404).json({ error: 'Campaign not found' });
    } else {
      res.status(500).json({ error: 'Failed to export campaign' });
    }
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`Campaign API server running on http://localhost:${PORT}`);
  console.log(`Serving campaigns from: ${CAMPAIGNS_DIR}`);
});