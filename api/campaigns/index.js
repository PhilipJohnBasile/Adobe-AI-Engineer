const fs = require('fs').promises;
const path = require('path');

// Get campaigns directory - in Azure this will be relative to the deployment
const getCampaignsDir = () => {
  // In Azure, campaigns should be in the wwwroot/data directory
  if (process.env.WEBSITE_INSTANCE_ID) {
    return path.join(process.env.HOME, 'site', 'wwwroot', 'data');
  }
  // Locally, use the campaigns directory in the root
  return path.join(__dirname, '..', '..', 'campaigns');
};

module.exports = async function (context, req) {
  const method = req.method;
  
  try {
    if (method === 'GET') {
      // Get all campaigns
      const campaignsDir = getCampaignsDir();
      const files = await fs.readdir(campaignsDir);
      const jsonFiles = files.filter(f => f.endsWith('.json'));
      
      const campaigns = await Promise.all(
        jsonFiles.map(async (file) => {
          const content = await fs.readFile(path.join(campaignsDir, file), 'utf8');
          return JSON.parse(content);
        })
      );
      
      context.res = {
        status: 200,
        body: campaigns,
        headers: { 'Content-Type': 'application/json' }
      };
    } else if (method === 'POST') {
      // Create new campaign
      const campaign = req.body;
      if (!campaign || !campaign.campaign_id) {
        context.res = {
          status: 400,
          body: { error: 'Invalid campaign data' }
        };
        return;
      }
      
      const campaignsDir = getCampaignsDir();
      const filePath = path.join(campaignsDir, `${campaign.campaign_id}.json`);
      
      await fs.writeFile(filePath, JSON.stringify(campaign, null, 2));
      
      context.res = {
        status: 201,
        body: campaign,
        headers: { 'Content-Type': 'application/json' }
      };
    }
  } catch (error) {
    context.log.error('Error in campaigns function:', error);
    context.res = {
      status: 500,
      body: { error: 'Internal server error' }
    };
  }
};