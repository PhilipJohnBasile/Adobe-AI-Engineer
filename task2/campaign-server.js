#!/usr/bin/env node
/**
 * Campaign Management Backend Server
 * 
 * Provides REST API for campaign CRUD operations, validation, and pipeline integration
 */

const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');
const { spawn } = require('child_process');

const app = express();
const PORT = 3001;

// Middleware
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3001', 'http://localhost:3002', 'http://localhost:3003', 'http://localhost:3004', 'http://localhost:3005'],
  credentials: true
}));
app.use(express.json());

// Campaign directory
const CAMPAIGNS_DIR = path.join(__dirname, 'campaigns');

// Ensure campaigns directory exists
async function ensureCampaignsDir() {
  try {
    await fs.access(CAMPAIGNS_DIR);
  } catch {
    await fs.mkdir(CAMPAIGNS_DIR, { recursive: true });
  }
}

// Helper function to get campaign file path
const getCampaignPath = (campaignId) => {
  return path.join(CAMPAIGNS_DIR, `${campaignId.toLowerCase().replace(/[^a-z0-9]/g, '_')}.json`);
};

// GET /api/campaigns - List all campaigns
app.get('/api/campaigns', async (req, res) => {
  try {
    await ensureCampaignsDir();
    const files = await fs.readdir(CAMPAIGNS_DIR);
    const campaigns = [];

    for (const file of files) {
      if (file.endsWith('.json')) {
        try {
          const filePath = path.join(CAMPAIGNS_DIR, file);
          const content = await fs.readFile(filePath, 'utf8');
          const campaign = JSON.parse(content);
          campaigns.push(campaign);
        } catch (error) {
          console.error(`Error reading campaign file ${file}:`, error);
        }
      }
    }

    campaigns.sort((a, b) => new Date(b.campaign_start_date) - new Date(a.campaign_start_date));
    res.json(campaigns);
  } catch (error) {
    console.error('Error listing campaigns:', error);
    res.status(500).json({ error: 'Failed to list campaigns' });
  }
});

// GET /api/campaigns/:id - Get specific campaign
app.get('/api/campaigns/:id', async (req, res) => {
  try {
    const campaignPath = getCampaignPath(req.params.id);
    const content = await fs.readFile(campaignPath, 'utf8');
    const campaign = JSON.parse(content);
    res.json(campaign);
  } catch (error) {
    if (error.code === 'ENOENT') {
      res.status(404).json({ error: 'Campaign not found' });
    } else {
      console.error('Error reading campaign:', error);
      res.status(500).json({ error: 'Failed to read campaign' });
    }
  }
});

// POST /api/campaigns - Create new campaign
app.post('/api/campaigns', async (req, res) => {
  try {
    const campaign = req.body;
    
    // Generate campaign ID if not provided
    if (!campaign.campaign_id) {
      campaign.campaign_id = `CAMPAIGN_${Date.now()}`;
    }

    // Add timestamps
    campaign.created_at = new Date().toISOString();
    campaign.updated_at = new Date().toISOString();

    const campaignPath = getCampaignPath(campaign.campaign_id);
    await fs.writeFile(campaignPath, JSON.stringify(campaign, null, 2));

    console.log(`Campaign created: ${campaign.campaign_id}`);
    res.status(201).json(campaign);
  } catch (error) {
    console.error('Error creating campaign:', error);
    res.status(500).json({ error: 'Failed to create campaign' });
  }
});

// PUT /api/campaigns/:id - Update campaign
app.put('/api/campaigns/:id', async (req, res) => {
  try {
    const campaign = req.body;
    campaign.updated_at = new Date().toISOString();

    const campaignPath = getCampaignPath(req.params.id);
    await fs.writeFile(campaignPath, JSON.stringify(campaign, null, 2));

    console.log(`Campaign updated: ${req.params.id}`);
    res.json(campaign);
  } catch (error) {
    console.error('Error updating campaign:', error);
    res.status(500).json({ error: 'Failed to update campaign' });
  }
});

// DELETE /api/campaigns/:id - Delete campaign
app.delete('/api/campaigns/:id', async (req, res) => {
  try {
    const campaignPath = getCampaignPath(req.params.id);
    await fs.unlink(campaignPath);

    console.log(`Campaign deleted: ${req.params.id}`);
    res.status(204).send();
  } catch (error) {
    if (error.code === 'ENOENT') {
      res.status(404).json({ error: 'Campaign not found' });
    } else {
      console.error('Error deleting campaign:', error);
      res.status(500).json({ error: 'Failed to delete campaign' });
    }
  }
});

// POST /api/campaigns/generate - Generate campaign idea using AI
app.post('/api/campaigns/generate', async (req, res) => {
  try {
    const { prompt } = req.body;
    
    // Mock AI generation for demo (replace with actual OpenAI integration)
    const generatedIdea = {
      campaign_name: `${prompt.includes('fall') ? 'Fall' : 'Seasonal'} Campaign ${new Date().getFullYear()}`,
      campaign_message: {
        primary_headline: "Experience the Season",
        secondary_headline: "Refreshing Moments",
        brand_voice: "uplifting, inclusive, joyful, authentic",
        seasonal_theme: prompt.includes('fall') ? "autumn comfort, warm gatherings" : "seasonal celebrations"
      },
      target_audience: {
        primary: {
          demographics: "18-45 year olds, families, working professionals",
          psychographics: "value tradition, seek comfort, enjoy seasonal moments",
          behavior: "social media active, brand loyal, seasonal purchasers"
        }
      },
      products: [
        {
          id: "coca_cola_classic",
          name: "Coca-Cola Classic",
          category: "Cola",
          description: "The original and iconic Coca-Cola taste",
          key_benefits: ["Classic refreshing taste", "Perfect for sharing moments"],
          target_price: "$1.99",
          messaging: { primary: "Classic Comfort", secondary: "Share the Tradition" },
          existing_assets: []
        }
      ]
    };

    console.log(`AI idea generated for prompt: ${prompt}`);
    res.json(generatedIdea);
  } catch (error) {
    console.error('Error generating campaign idea:', error);
    res.status(500).json({ error: 'Failed to generate campaign idea' });
  }
});

// POST /api/campaigns/validate - Validate campaign compliance
app.post('/api/campaigns/validate', async (req, res) => {
  try {
    const campaign = req.body;
    
    // Perform brand compliance validation
    const brandChecks = [];
    const legalChecks = [];

    // Brand color compliance
    const hasCokeRed = campaign.creative_requirements?.brand_requirements?.color_compliance?.includes('#DA020E');
    brandChecks.push({
      type: 'brand_color',
      status: hasCokeRed ? 'passed' : 'failed',
      message: hasCokeRed ? 'Coca-Cola red color compliance verified' : 'Missing required Coca-Cola red #DA020E',
      score: hasCokeRed ? 100 : 0
    });

    // Logo placement
    const logoPlacement = campaign.creative_requirements?.brand_requirements?.logo_placement || '';
    const validPlacements = ['bottom-right', 'top-left', 'bottom-left', 'top-right'];
    const hasValidPlacement = validPlacements.some(placement => logoPlacement.includes(placement));
    
    brandChecks.push({
      type: 'logo_placement',
      status: hasValidPlacement ? 'passed' : 'warning',
      message: hasValidPlacement ? 'Logo placement follows guidelines' : 'Logo placement needs review',
      score: hasValidPlacement ? 100 : 70
    });

    // Forbidden words check
    const forbiddenWords = ['pepsi', 'mountain dew', 'dr pepper', 'alcohol', 'beer', 'wine'];
    const allText = JSON.stringify(campaign).toLowerCase();
    const foundForbidden = forbiddenWords.filter(word => allText.includes(word));

    legalChecks.push({
      type: 'forbidden_words',
      status: foundForbidden.length === 0 ? 'passed' : 'failed',
      message: foundForbidden.length === 0 ? 'No prohibited words detected' : `Prohibited words: ${foundForbidden.join(', ')}`,
      score: foundForbidden.length === 0 ? 100 : 0
    });

    const allChecks = [...brandChecks, ...legalChecks];
    const overallScore = Math.round(allChecks.reduce((sum, check) => sum + check.score, 0) / allChecks.length);

    const validation = {
      overall_score: overallScore,
      compliance_checks: allChecks,
      brand_checks: brandChecks,
      legal_checks: legalChecks
    };

    console.log(`Campaign validation completed: ${overallScore}%`);
    res.json(validation);
  } catch (error) {
    console.error('Error validating campaign:', error);
    res.status(500).json({ error: 'Failed to validate campaign' });
  }
});

// POST /api/campaigns/:id/generate-live - Run pipeline with live updates
app.post('/api/campaigns/:id/generate-live', async (req, res) => {
  // Set up Server-Sent Events
  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Access-Control-Allow-Origin': 'http://localhost:3000'
  });

  try {
    const campaignId = req.params.id;
    const campaignPath = getCampaignPath(campaignId);
    
    await fs.access(campaignPath);
    
    // Send initial status
    res.write(`data: ${JSON.stringify({ type: 'status', message: 'Starting pipeline...' })}\n\n`);
    
    // Run pipeline
    const pythonProcess = spawn('python3', ['src/pipeline.py', campaignPath], {
      cwd: __dirname,
      stdio: 'pipe'
    });
    
    let generatedAssets = [];
    
    // Process stdout line by line for real-time updates
    pythonProcess.stdout.on('data', (data) => {
      const lines = data.toString().split('\n');
      for (const line of lines) {
        if (line.includes('Saved:') || line.includes('Generated:')) {
          // Extract filename from the log
          const match = line.match(/Saved:\s+(.+\.png)|Generated:\s+(.+\.png)/);
          if (match) {
            const filename = match[1] || match[2];
            generatedAssets.push(filename);
            
            // Send real-time update
            res.write(`data: ${JSON.stringify({
              type: 'asset_generated',
              filename: filename,
              url: `/api/assets/FALL_COKE_2025_001/${filename}`,
              count: generatedAssets.length
            })}\n\n`);
          }
        }
        
        // Send log updates
        if (line.trim()) {
          res.write(`data: ${JSON.stringify({
            type: 'log',
            message: line.trim()
          })}\n\n`);
        }
      }
    });
    
    pythonProcess.stderr.on('data', (data) => {
      const lines = data.toString().split('\n');
      for (const line of lines) {
        if (line.includes('INFO') && (line.includes('Saved') || line.includes('Generated'))) {
          const match = line.match(/Saved:\s+(.+\.png)|Generated:\s+(.+\.png)/);
          if (match) {
            const filename = match[1] || match[2];
            generatedAssets.push(filename);
            res.write(`data: ${JSON.stringify({
              type: 'asset_generated',
              filename: filename,
              url: `/api/assets/output/${filename}`,
              count: generatedAssets.length
            })}\n\n`);
          }
        }
      }
    });
    
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        res.write(`data: ${JSON.stringify({
          type: 'complete',
          success: true,
          totalAssets: generatedAssets.length,
          assets: generatedAssets
        })}\n\n`);
      } else {
        res.write(`data: ${JSON.stringify({
          type: 'error',
          message: 'Pipeline failed'
        })}\n\n`);
      }
      res.end();
    });
    
  } catch (error) {
    res.write(`data: ${JSON.stringify({
      type: 'error',
      message: error.message
    })}\n\n`);
    res.end();
  }
});

// POST /api/campaigns/:id/generate - Run pipeline for campaign
app.post('/api/campaigns/:id/generate', async (req, res) => {
  try {
    const campaignId = req.params.id;
    const campaignPath = getCampaignPath(campaignId);
    
    // Check if campaign exists
    await fs.access(campaignPath);

    console.log(`Running pipeline for campaign: ${campaignId}`);

    // Run the Python pipeline
    const pythonProcess = spawn('python3', ['src/pipeline.py', campaignPath], {
      cwd: __dirname,
      stdio: 'pipe'
    });

    let output = '';
    let errorOutput = '';

    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    pythonProcess.on('close', async (code) => {
      if (code === 0) {
        console.log(`Pipeline completed successfully for ${campaignId}`);
        
        // Read actual results from output directory
        try {
          // Find the most recent campaign report
          const outputDir = path.join(__dirname, 'output');
          const files = await fs.readdir(outputDir);
          const reportFiles = files.filter(f => f.startsWith('campaign_report_') && f.endsWith('.json'));
          
          let assets_generated = [];
          let reportData = null;
          
          if (reportFiles.length > 0) {
            // Get the most recent report
            const latestReport = reportFiles.sort().pop();
            const reportPath = path.join(outputDir, latestReport);
            const reportContent = await fs.readFile(reportPath, 'utf-8');
            reportData = JSON.parse(reportContent);
          }
          
          // Scan output directories for actual generated assets
          const productDirs = files.filter(f => !f.includes('.json') && !f.includes('.'));
          for (const productDir of productDirs) {
            const productPath = path.join(outputDir, productDir);
            try {
              const stats = await fs.stat(productPath);
              if (stats.isDirectory()) {
                const assetFiles = await fs.readdir(productPath);
                for (const assetFile of assetFiles) {
                  if (assetFile.endsWith('.png') || assetFile.endsWith('.jpg')) {
                    assets_generated.push({
                      filename: assetFile,
                      product: productDir.replace(/_/g, ' '),
                      path: path.join('output', productDir, assetFile),
                      format: assetFile.includes('square') ? 'square' : 
                              assetFile.includes('story') ? 'story' : 
                              assetFile.includes('landscape') ? 'landscape' : 'unknown'
                    });
                  }
                }
              }
            } catch (e) {
              // Skip if not a directory
            }
          }
          
          const result = {
            success: true,
            campaign_id: campaignId,
            assets_generated: assets_generated.slice(0, 50), // Limit to 50 for display
            total_assets: assets_generated.length,
            total_cost: reportData?.total_cost || 0,
            processing_time: reportData?.processing_time || 'N/A',
            timestamp: new Date().toISOString(),
            output_directory: outputDir
          };
          
          res.json(result);
        } catch (error) {
          console.error('Error reading pipeline results:', error);
          // Fallback to basic success message
          res.json({
            success: true,
            campaign_id: campaignId,
            message: 'Pipeline completed but could not read detailed results',
            timestamp: new Date().toISOString()
          });
        }
      } else {
        console.error(`Pipeline failed for ${campaignId}:`, errorOutput);
        res.status(500).json({ 
          error: 'Pipeline execution failed', 
          details: errorOutput || 'Unknown error' 
        });
      }
    });

  } catch (error) {
    if (error.code === 'ENOENT') {
      res.status(404).json({ error: 'Campaign not found' });
    } else {
      console.error('Error running pipeline:', error);
      res.status(500).json({ error: 'Failed to run pipeline' });
    }
  }
});

// GET /api/campaigns/:id/assets - List existing assets
app.get('/api/campaigns/:id/assets', async (req, res) => {
  try {
    const campaignId = req.params.id;
    const outputDir = path.join(__dirname, 'output');
    const assets = [];

    // Check multiple possible output directories
    const possibleDirs = [
      path.join(outputDir, campaignId.toUpperCase()),
      path.join(outputDir, `${campaignId.toUpperCase()}_001`),
      path.join(outputDir, 'FALL_COKE_2025_001'), // Hardcoded for demo
      outputDir // Also check root output dir
    ];

    for (const dir of possibleDirs) {
      try {
        const files = await fs.readdir(dir);
        for (const file of files) {
          if (file.endsWith('.png') || file.endsWith('.jpg')) {
            const filePath = path.join(dir, file);
            const stats = await fs.stat(filePath);
            
            // Parse filename for metadata
            const parts = file.replace('.png', '').replace('.jpg', '').split('_');
            
            assets.push({
              filename: file,
              path: path.relative(outputDir, filePath),
              url: `/api/assets/${path.relative(outputDir, filePath)}`,
              size: stats.size,
              created: stats.birthtime,
              modified: stats.mtime,
              product: parts[0] + (parts[1] ? '_' + parts[1] : ''),
              format: parts.includes('square') ? 'square' : 
                      parts.includes('story') ? 'story' : 
                      parts.includes('landscape') ? 'landscape' : 'unknown',
              region: parts.find(p => ['usa', 'germany', 'japan', 'canada', 'uk'].includes(p.toLowerCase())) || 'unknown'
            });
          }
        }
        break; // Stop at first successful directory
      } catch (error) {
        // Directory doesn't exist, try next one
        continue;
      }
    }

    res.json({
      campaign_id: campaignId,
      total_assets: assets.length,
      assets: assets.sort((a, b) => b.modified - a.modified) // Most recent first
    });

  } catch (error) {
    console.error('Error listing assets:', error);
    res.status(500).json({ error: 'Failed to list assets' });
  }
});

// GET /api/campaigns/:id/logs - Get generation logs
app.get('/api/campaigns/:id/logs', async (req, res) => {
  try {
    const campaignId = req.params.id;
    
    // Try to read logs from output directory
    const outputDir = path.join(__dirname, 'output', campaignId.toUpperCase());
    const reportFiles = [];
    
    try {
      const files = await fs.readdir(outputDir);
      for (const file of files) {
        if (file.includes('campaign_report') && file.endsWith('.json')) {
          const reportPath = path.join(outputDir, file);
          const content = await fs.readFile(reportPath, 'utf8');
          reportFiles.push(JSON.parse(content));
        }
      }
    } catch (error) {
      // No logs available yet
    }

    if (reportFiles.length > 0) {
      // Return the most recent report
      const latestReport = reportFiles.sort((a, b) => 
        new Date(b.processing_timestamp) - new Date(a.processing_timestamp)
      )[0];
      
      res.json(latestReport);
    } else {
      res.status(404).json({ error: 'No logs available for this campaign' });
    }
  } catch (error) {
    console.error('Error reading logs:', error);
    res.status(500).json({ error: 'Failed to read logs' });
  }
});

// Serve generated assets
app.use('/api/assets', express.static(path.join(__dirname, 'output')));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Campaign Management Server running on http://localhost:${PORT}`);
  console.log(`📁 Campaigns directory: ${CAMPAIGNS_DIR}`);
  console.log(`🔥 Ready to manage Coca-Cola campaigns!`);
});

module.exports = app;