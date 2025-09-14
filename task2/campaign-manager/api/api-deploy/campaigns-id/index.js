const fs = require('fs');
const path = require('path');

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

module.exports = async function (context, req) {
  context.log('HTTP trigger function processed a request.');

  // Set CORS headers
  context.res = {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    }
  };

  if (req.method === 'OPTIONS') {
    context.res.status = 200;
    context.res.body = '';
    return;
  }

  const campaignId = req.params.id;
  const fileName = `${campaignId}.json`;
  const filePath = path.join(__dirname, '../data', fileName);

  try {
    if (req.method === 'GET') {
      // Get single campaign
      if (!fs.existsSync(filePath)) {
        context.res.status = 404;
        context.res.body = JSON.stringify({ error: 'Campaign not found' });
        return;
      }
      
      const content = fs.readFileSync(filePath, 'utf8');
      const campaign = JSON.parse(content);
      campaign.status = determineStatus(campaign);
      
      context.res.status = 200;
      context.res.body = JSON.stringify(campaign);
      
    } else if (req.method === 'PUT') {
      // Update campaign
      if (!req.body) {
        context.res.status = 400;
        context.res.body = JSON.stringify({ error: 'Request body is required' });
        return;
      }
      
      const campaign = req.body;
      campaign.id = campaignId;
      campaign.status = determineStatus(campaign);
      campaign.updated_date = new Date().toISOString();
      
      fs.writeFileSync(filePath, JSON.stringify(campaign, null, 2));
      
      context.res.status = 200;
      context.res.body = JSON.stringify(campaign);
      
    } else if (req.method === 'DELETE') {
      // Delete campaign
      if (!fs.existsSync(filePath)) {
        context.res.status = 404;
        context.res.body = JSON.stringify({ error: 'Campaign not found' });
        return;
      }
      
      fs.unlinkSync(filePath);
      
      context.res.status = 204;
      context.res.body = '';
    }
    
  } catch (error) {
    context.log('Error:', error);
    context.res.status = 500;
    context.res.body = JSON.stringify({ 
      error: 'Internal server error',
      message: error.message 
    });
  }
};