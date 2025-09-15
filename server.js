const express = require('express');
const path = require('path');
const fs = require('fs').promises;
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);
const app = express();
const PORT = process.env.PORT || 3001;

// Detect if running in development
const isDevelopment = process.env.NODE_ENV !== 'production';

app.use(express.json());

// CORS for development
if (isDevelopment) {
  app.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', 'http://localhost:3000');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
    if (req.method === 'OPTIONS') {
      return res.sendStatus(200);
    }
    next();
  });
}

// Campaigns directory - in current directory now
const campaignsDir = path.join(__dirname, 'campaigns');

// API Routes
app.get('/api/campaigns', async (req, res) => {
  try {
    console.log(`[LOCAL] Loading campaigns from: ${campaignsDir}`);
    
    const files = await fs.readdir(campaignsDir);
    const jsonFiles = files.filter(f => f.endsWith('.json'));
    
    const campaigns = await Promise.all(
      jsonFiles.map(async (file) => {
        const content = await fs.readFile(path.join(campaignsDir, file), 'utf8');
        return JSON.parse(content);
      })
    );
    
    console.log(`Loaded ${campaigns.length} campaigns`);
    res.json(campaigns);
  } catch (error) {
    console.error('Error loading campaigns:', error);
    res.status(500).json({ error: 'Failed to load campaigns' });
  }
});

app.get('/api/campaigns/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const filePath = path.join(campaignsDir, `${id}.json`);
    
    const content = await fs.readFile(filePath, 'utf8');
    const campaign = JSON.parse(content);
    
    res.json(campaign);
  } catch (error) {
    console.error('Error loading campaign:', error);
    res.status(404).json({ error: 'Campaign not found' });
  }
});

app.post('/api/campaigns', async (req, res) => {
  try {
    const campaign = req.body;
    const filePath = path.join(campaignsDir, `${campaign.campaign_id}.json`);
    
    await fs.writeFile(filePath, JSON.stringify(campaign, null, 2));
    
    res.status(201).json(campaign);
  } catch (error) {
    console.error('Error creating campaign:', error);
    res.status(500).json({ error: 'Failed to create campaign' });
  }
});

app.put('/api/campaigns/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const campaign = req.body;
    const filePath = path.join(campaignsDir, `${id}.json`);
    
    // Ensure campaign_id matches URL
    campaign.campaign_id = id;
    
    await fs.writeFile(filePath, JSON.stringify(campaign, null, 2));
    
    res.json(campaign);
  } catch (error) {
    console.error('Error updating campaign:', error);
    res.status(500).json({ error: 'Failed to update campaign' });
  }
});

app.delete('/api/campaigns/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const filePath = path.join(campaignsDir, `${id}.json`);
    
    await fs.unlink(filePath);
    
    res.status(204).send();
  } catch (error) {
    console.error('Error deleting campaign:', error);
    res.status(500).json({ error: 'Failed to delete campaign' });
  }
});

// AI Generation endpoint
app.post('/api/campaigns/:id/generate', async (req, res) => {
  try {
    const { id } = req.params;
    const pythonScript = path.join(__dirname, 'integrated_pipeline.py');
    const command = `python3 "${pythonScript}" "${id}"`;
    
    console.log(`Executing AI generation for campaign: ${id}`);
    
    const { stdout, stderr } = await execAsync(command, {
      cwd: __dirname,
      env: {
        ...process.env,
        PYTHONPATH: __dirname
      }
    });
    
    if (stderr && !stderr.includes('WARNING') && !stderr.includes('INFO')) {
      console.error('Pipeline stderr:', stderr);
    }
    
    // Parse the output to find generated assets
    const result = JSON.parse(stdout.split('\n').find(line => line.startsWith('{')));
    
    res.json({
      success: true,
      campaign_id: id,
      message: 'Asset generation completed',
      assets: result.assets,
      logs: stdout
    });
    
  } catch (error) {
    console.error('Error generating assets:', error);
    res.status(500).json({ 
      error: 'Failed to generate assets',
      details: error.message 
    });
  }
});

// In production, also serve the React app
if (!isDevelopment) {
  app.use(express.static(path.join(__dirname, 'dist')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
  });
}

app.listen(PORT, () => {
  console.log(`
    ========================================
    Campaign Manager API Server
    ========================================
    Environment: ${isDevelopment ? 'DEVELOPMENT' : 'PRODUCTION'}
    Port: ${PORT}
    API Base: http://localhost:${PORT}/api
    ========================================
  `);
});