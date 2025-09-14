# Azure Functions Deployment Guide

## Overview

This guide explains how to deploy the Campaign Manager API as Azure Functions instead of using the built-in Static Web Apps API hosting.

## Prerequisites

1. Azure Account with active subscription
2. Azure Functions Core Tools installed
3. Azure CLI installed and configured
4. Node.js 18+ installed

## Install Azure Functions Core Tools

```bash
# Install Azure Functions Core Tools
npm install -g azure-functions-core-tools@4 --unsafe-perm true
```

## Step 1: Create Azure Function App

### Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group (if not already created)
az group create --name rg-campaign-manager --location eastus

# Create storage account for Functions (different from campaign storage)
az storage account create \
    --name campaignfuncstorage \
    --location eastus \
    --resource-group rg-campaign-manager \
    --sku Standard_LRS

# Create Function App
az functionapp create \
    --resource-group rg-campaign-manager \
    --consumption-plan-location eastus \
    --runtime node \
    --runtime-version 18 \
    --functions-version 4 \
    --name campaign-manager-functions \
    --storage-account campaignfuncstorage \
    --disable-app-insights false
```

## Step 2: Configure Environment Variables

Set the Azure Storage connection string in your Function App:

```bash
# Set campaign storage connection string
az functionapp config appsettings set \
    --name campaign-manager-functions \
    --resource-group rg-campaign-manager \
    --settings AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=campaignmanagerstorage;AccountKey=YOUR_ACCOUNT_KEY;EndpointSuffix=core.windows.net"
```

## Step 3: Deploy Functions

### Option A: Deploy via Azure CLI

```bash
# Navigate to the api directory
cd api

# Install dependencies
npm install

# Deploy to Azure
func azure functionapp publish campaign-manager-functions
```

### Option B: Deploy via VS Code

1. Install Azure Functions extension for VS Code
2. Open the `api` folder in VS Code
3. Click on Azure icon in sidebar
4. Sign in to Azure
5. Right-click on Function Apps
6. Select "Deploy to Function App"
7. Choose your function app

## Step 4: Update Static Web App Configuration

If using Azure Functions separately, update the Static Web App workflow to not deploy the API:

```yaml
# .github/workflows/azure-static-web-apps.yml
- name: Build And Deploy
  uses: Azure/static-web-apps-deploy@v1
  with:
    azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
    repo_token: ${{ secrets.GITHUB_TOKEN }}
    action: "upload"
    app_location: "/task2/campaign-manager"
    api_location: "" # Empty - using separate Function App
    output_location: "dist"
```

## Step 5: Update Frontend API Base URL

Update the React app to use the Function App URL instead of relative `/api` paths:

```javascript
// In your React components or config
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://campaign-manager-functions.azurewebsites.net/api'
  : '/api';
```

## Step 6: Configure CORS

Enable CORS for your Static Web App domain:

```bash
az functionapp cors add \
    --name campaign-manager-functions \
    --resource-group rg-campaign-manager \
    --allowed-origins "https://your-static-web-app.azurestaticapps.net"
```

## Testing the Functions

Test your deployed functions:

```bash
# Test health endpoint
curl https://campaign-manager-functions.azurewebsites.net/api/health

# Test campaigns list
curl https://campaign-manager-functions.azurewebsites.net/api/campaigns
```

## Architecture Comparison

### Option 1: Static Web Apps with Built-in API (Recommended for simplicity)
```
Static Web App
├── Frontend (React build)
└── API (Node.js) → Auto-deployed as Functions
```

### Option 2: Separate Function App (More control)
```
Static Web App (React build) 
    ↓ HTTP requests
Function App (Azure Functions)
    ↓ Storage calls
Azure Blob Storage
```

## Local Development with Functions

To test functions locally:

```bash
# Navigate to api directory
cd api

# Install dependencies
npm install

# Start local Functions runtime
func start

# Functions will be available at:
# http://localhost:7071/api/campaigns
# http://localhost:7071/api/health
```

## Monitoring and Logs

- View function logs in Azure Portal → Function App → Functions → Monitor
- Use Application Insights for detailed telemetry
- Monitor performance and errors in Azure Portal

## Cost Considerations

Azure Functions Consumption Plan:
- **Free tier**: 1M requests/month, 400,000 GB-s/month
- **Pay-per-use**: $0.20 per 1M executions, $0.000016/GB-s
- **Typical cost**: $0-5/month for small to medium usage

## Troubleshooting

### Common Issues

1. **CORS errors**: Ensure CORS is configured for your Static Web App domain
2. **Storage connection**: Verify `AZURE_STORAGE_CONNECTION_STRING` is set correctly
3. **Function timeout**: Default timeout is 5 minutes (configurable in host.json)

### Debug Commands

```bash
# Check function app settings
az functionapp config appsettings list --name campaign-manager-functions --resource-group rg-campaign-manager

# View function app logs
az webapp log tail --name campaign-manager-functions --resource-group rg-campaign-manager

# Test function locally
func start --verbose
```

## Next Steps

1. Deploy the Function App using the commands above
2. Test all endpoints to ensure they work correctly
3. Update your Static Web App to use the Function App URLs
4. Monitor performance and costs in Azure Portal