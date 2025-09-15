import { readCampaign, writeCampaign } from './lib/campaignFs.ts';
import { CampaignSchema } from './lib/campaignSchema.ts';
import * as fs from 'fs';
import * as path from 'path';

const CAMPAIGN_DIR = path.join(process.cwd(), "..", "campaigns");

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

export function apiMiddleware() {
  return {
    name: 'api-middleware',
    configureServer(server) {
      server.middlewares.use('/api/campaigns', async (req, res, next) => {
        try {
          const url = new URL(req.url, `http://${req.headers.host}`);
          const pathParts = url.pathname.split('/').filter(Boolean);
          
          // GET /api/campaigns - List all campaigns
          if (req.method === 'GET' && pathParts.length === 2) {
            const files = fs.readdirSync(CAMPAIGN_DIR);
            const jsonFiles = files.filter(file => file.endsWith('.json'));
            
            const campaigns = await Promise.all(
              jsonFiles.map(async (filename) => {
                try {
                  const campaignId = path.basename(filename, '.json');
                  const campaignData = await readCampaign(campaignId);
                  const validatedCampaign = CampaignSchema.parse(campaignData);
                  
                  const filePath = path.join(CAMPAIGN_DIR, filename);
                  return {
                    ...validatedCampaign,
                    id: validatedCampaign.campaign_id || campaignId,
                    name: validatedCampaign.campaign_name,
                    status: determineStatus(validatedCampaign),
                    created_date: fs.statSync(filePath).ctime.toISOString()
                  };
                } catch (error) {
                  console.warn(`Failed to load ${filename}:`, error);
                  return null;
                }
              })
            );
            
            const validCampaigns = campaigns.filter(campaign => campaign !== null);
            console.log(`Loaded ${validCampaigns.length} campaigns from filesystem`);
            
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify(validCampaigns));
            return;
          }
          
          // GET /api/campaigns/[id] - Get specific campaign
          if (req.method === 'GET' && pathParts.length === 3) {
            const campaignId = pathParts[2];
            
            try {
              const campaignData = await readCampaign(campaignId);
              const validatedCampaign = CampaignSchema.parse(campaignData);
              
              console.log(`Loaded campaign ${campaignId} from filesystem`);
              
              res.setHeader('Content-Type', 'application/json');
              res.end(JSON.stringify(validatedCampaign));
              return;
            } catch (error) {
              console.error('Error loading campaign:', error);
              if (error.message.includes('ENOENT')) {
                res.statusCode = 404;
                res.end(JSON.stringify({ error: 'Campaign not found' }));
              } else {
                res.statusCode = 500;
                res.end(JSON.stringify({ error: 'Failed to load campaign' }));
              }
              return;
            }
          }
          
          // PUT /api/campaigns/[id] - Update campaign
          if (req.method === 'PUT' && pathParts.length === 3) {
            const campaignId = pathParts[2];
            
            let body = '';
            req.on('data', chunk => {
              body += chunk.toString();
            });
            
            req.on('end', async () => {
              try {
                const campaignData = JSON.parse(body);
                campaignData.campaign_id = campaignId;
                
                const validatedCampaign = CampaignSchema.parse(campaignData);
                await writeCampaign(campaignId, validatedCampaign);
                
                console.log(`Saved campaign ${campaignId} to filesystem`);
                
                res.setHeader('Content-Type', 'application/json');
                res.end(JSON.stringify({ success: true, campaign: validatedCampaign }));
              } catch (error) {
                console.error('Error saving campaign:', error);
                res.statusCode = 500;
                res.end(JSON.stringify({ error: 'Failed to save campaign' }));
              }
            });
            return;
          }
          
          // POST /api/campaigns - Create new campaign
          if (req.method === 'POST' && pathParts.length === 2) {
            let body = '';
            req.on('data', chunk => {
              body += chunk.toString();
            });
            
            req.on('end', async () => {
              try {
                const campaignData = JSON.parse(body);
                
                if (!campaignData.campaign_id) {
                  campaignData.campaign_id = `CAMPAIGN_${Date.now()}`;
                }
                
                const campaignId = campaignData.campaign_id;
                const filePath = path.join(CAMPAIGN_DIR, `${campaignId}.json`);
                
                if (fs.existsSync(filePath)) {
                  res.statusCode = 409;
                  res.end(JSON.stringify({ error: 'Campaign already exists' }));
                  return;
                }
                
                const validatedCampaign = CampaignSchema.parse(campaignData);
                await writeCampaign(campaignId, validatedCampaign);
                
                console.log(`Created new campaign ${campaignId} in filesystem`);
                
                res.statusCode = 201;
                res.setHeader('Content-Type', 'application/json');
                res.end(JSON.stringify({ success: true, campaign: validatedCampaign }));
              } catch (error) {
                console.error('Error creating campaign:', error);
                res.statusCode = 500;
                res.end(JSON.stringify({ error: 'Failed to create campaign' }));
              }
            });
            return;
          }
          
        } catch (error) {
          console.error('API middleware error:', error);
          res.statusCode = 500;
          res.end(JSON.stringify({ error: 'Internal server error' }));
          return;
        }
        
        next();
      });
    }
  };
}