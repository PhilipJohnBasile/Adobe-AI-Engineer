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
  const id = context.bindingData.id;
  
  if (!id) {
    context.res = {
      status: 400,
      body: { error: 'Campaign ID is required' }
    };
    return;
  }
  
  try {
    const campaignsDir = getCampaignsDir();
    const filePath = path.join(campaignsDir, `${id}.json`);
    
    if (method === 'GET') {
      // Get specific campaign
      try {
        const content = await fs.readFile(filePath, 'utf8');
        const campaign = JSON.parse(content);
        
        context.res = {
          status: 200,
          body: campaign,
          headers: { 'Content-Type': 'application/json' }
        };
      } catch (error) {
        context.res = {
          status: 404,
          body: { error: 'Campaign not found' }
        };
      }
    } else if (method === 'PUT') {
      // Update campaign
      const campaign = req.body;
      if (!campaign) {
        context.res = {
          status: 400,
          body: { error: 'Invalid campaign data' }
        };
        return;
      }
      
      // Ensure campaign_id matches URL
      campaign.campaign_id = id;
      
      await fs.writeFile(filePath, JSON.stringify(campaign, null, 2));
      
      context.res = {
        status: 200,
        body: campaign,
        headers: { 'Content-Type': 'application/json' }
      };
    } else if (method === 'DELETE') {
      // Delete campaign
      try {
        await fs.unlink(filePath);
        context.res = {
          status: 204,
          body: ''
        };
      } catch (error) {
        context.res = {
          status: 404,
          body: { error: 'Campaign not found' }
        };
      }
    }
  } catch (error) {
    context.log.error('Error in campaigns-id function:', error);
    context.res = {
      status: 500,
      body: { error: 'Internal server error' }
    };
  }
};