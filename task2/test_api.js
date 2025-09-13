const axios = require('axios');

async function testAPI() {
  try {
    console.log('Testing API connection to http://localhost:3001/api/campaigns');

    const response = await axios.get('http://localhost:3001/api/campaigns', {
      headers: {
        'Origin': 'http://localhost:3005'
      },
      timeout: 5000
    });

    console.log('SUCCESS: API responded with status:', response.status);
    console.log('Number of campaigns:', response.data.length);
    console.log('First campaign:', response.data[0]?.campaign_name || 'None');

  } catch (error) {
    console.error('ERROR connecting to API:');
    console.error('Message:', error.message);
    console.error('Code:', error.code);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
  }
}

testAPI();