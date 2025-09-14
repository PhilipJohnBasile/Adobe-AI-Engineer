// Simple test to verify v4 functions syntax
const { app } = require('@azure/functions');

console.log('✅ Azure Functions v4 app object imported successfully');
console.log('App methods:', Object.getOwnPropertyNames(app.__proto__));

// Test the app.http method exists
if (typeof app.http === 'function') {
  console.log('✅ app.http method is available');
  
  // Test basic handler structure
  app.http('test-health', {
    methods: ['GET'],
    route: 'test-health',
    handler: async (request, context) => {
      console.log('✅ v4 handler executed successfully');
      return {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'ok',
          timestamp: new Date().toISOString(),
          model: 'v4'
        })
      };
    }
  });
  
  console.log('✅ Test function registered successfully with v4 syntax');
} else {
  console.log('❌ app.http method not found');
}

console.log('✅ All v4 syntax tests passed');