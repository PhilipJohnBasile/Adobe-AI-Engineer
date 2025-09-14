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
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type"
    }
  };

  if (req.method === 'OPTIONS') {
    context.res.status = 200;
    context.res.body = '';
    return;
  }

  try {
    if (req.method === 'GET') {
      // List campaigns from api/data folder
      const dataPath = path.join(__dirname, '../data');
      const files = fs.readdirSync(dataPath).filter(file => file.endsWith('.json'));
      
      const campaigns = [];
      
      for (const file of files) {
        try {
          const filePath = path.join(dataPath, file);
          const content = fs.readFileSync(filePath, 'utf8');
          const campaign = JSON.parse(content);
          
          // Add computed status
          campaign.status = determineStatus(campaign);
          campaigns.push(campaign);
          
        } catch (error) {
          context.log(`Error reading campaign file ${file}:`, error);
        }
      }
      
      // Sort by campaign name
      campaigns.sort((a, b) => (a.campaign_name || '').localeCompare(b.campaign_name || ''));
      
      context.res.status = 200;
      context.res.body = JSON.stringify(campaigns);
      
    } else if (req.method === 'POST') {
      // Create new campaign
      if (!req.body || !req.body.campaign_name) {
        context.res.status = 400;
        context.res.body = JSON.stringify({ error: 'Campaign name is required' });
        return;
      }
      
      const campaign = req.body;
      campaign.id = campaign.id || campaign.campaign_name.replace(/\s+/g, '_').toUpperCase();
      campaign.status = determineStatus(campaign);
      campaign.created_date = new Date().toISOString();
      
      const fileName = `${campaign.id}.json`;
      const filePath = path.join(__dirname, '../data', fileName);
      
      fs.writeFileSync(filePath, JSON.stringify(campaign, null, 2));
      
      context.res.status = 201;
      context.res.body = JSON.stringify(campaign);
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