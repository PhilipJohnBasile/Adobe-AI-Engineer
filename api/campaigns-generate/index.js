const { exec } = require('child_process');
const { promisify } = require('util');
const path = require('path');

const execAsync = promisify(exec);

module.exports = async function (context, req) {
  const id = context.bindingData.id;
  
  if (!id) {
    context.res = {
      status: 400,
      body: { error: 'Campaign ID is required' }
    };
    return;
  }
  
  try {
    // In Azure, the Python script should be in the wwwroot directory
    const pythonScript = process.env.WEBSITE_INSTANCE_ID 
      ? path.join(process.env.HOME, 'site', 'wwwroot', 'integrated_pipeline.py')
      : path.join(__dirname, '..', '..', 'integrated_pipeline.py');
    
    const command = `python3 "${pythonScript}" "${id}"`;
    
    context.log(`Executing AI generation for campaign: ${id}`);
    
    const { stdout, stderr } = await execAsync(command, {
      cwd: process.env.WEBSITE_INSTANCE_ID 
        ? path.join(process.env.HOME, 'site', 'wwwroot')
        : path.join(__dirname, '..', '..'),
      env: {
        ...process.env,
        PYTHONPATH: process.env.WEBSITE_INSTANCE_ID 
          ? path.join(process.env.HOME, 'site', 'wwwroot')
          : path.join(__dirname, '..', '..')
      },
      timeout: 60000 // 1 minute timeout
    });
    
    if (stderr && !stderr.includes('WARNING') && !stderr.includes('INFO')) {
      context.log.error('Pipeline stderr:', stderr);
    }
    
    // Parse the output to find generated assets
    let result;
    try {
      result = JSON.parse(stdout.split('\\n').find(line => line.startsWith('{')));
    } catch {
      // If parsing fails, return a basic success response
      result = { assets: [], message: 'Generation completed' };
    }
    
    context.res = {
      status: 200,
      body: {
        success: true,
        campaign_id: id,
        message: 'Asset generation completed',
        assets: result.assets || [],
        logs: stdout
      },
      headers: { 'Content-Type': 'application/json' }
    };
    
  } catch (error) {
    context.log.error('Error generating assets:', error);
    context.res = {
      status: 500,
      body: { 
        error: 'Failed to generate assets',
        details: error.message 
      },
      headers: { 'Content-Type': 'application/json' }
    };
  }
};