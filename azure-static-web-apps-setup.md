# Azure Static Web Apps Deployment Guide

## Overview

This guide explains how to deploy the Campaign Manager React application to Azure Static Web Apps with the API server running as Azure Functions.

## Prerequisites

1. Azure Account with active subscription
2. GitHub repository with the campaign-manager code
3. Azure CLI installed and configured

## Step 1: Create Azure Static Web App

### Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group (if not already created)
az group create --name rg-campaign-manager --location eastus

# Create Static Web App
az staticwebapp create \
    --name campaign-manager-app \
    --resource-group rg-campaign-manager \
    --source https://github.com/YOUR_USERNAME/YOUR_REPO_NAME \
    --location eastus2 \
    --branch main \
    --app-location "/task2/campaign-manager" \
    --api-location "server" \
    --output-location "dist" \
    --login-with-github
```

### Using Azure Portal

1. Go to Azure Portal (portal.azure.com)
2. Search for "Static Web Apps" and create new resource
3. Fill in the details:
   - **Resource Group**: rg-campaign-manager
   - **Name**: campaign-manager-app
   - **Plan type**: Free
   - **Region**: East US 2
   - **Source**: GitHub
   - **GitHub Account**: Your GitHub account
   - **Organization**: Your username/organization
   - **Repository**: Your repository name
   - **Branch**: main
   - **Build Presets**: React
   - **App location**: `/task2/campaign-manager`
   - **Api location**: `server`
   - **Output location**: `dist`

## Step 2: Configure Environment Variables

After deployment, configure environment variables in Azure:

```bash
# Set Azure Storage connection string for production
az staticwebapp appsettings set \
    --name campaign-manager-app \
    --resource-group rg-campaign-manager \
    --setting-names AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=campaignmanagerstorage;AccountKey=YOUR_ACCOUNT_KEY;EndpointSuffix=core.windows.net"
```

Or set via Azure Portal:
1. Go to your Static Web App resource
2. Click "Configuration" in the left menu
3. Add application settings:
   - `AZURE_STORAGE_CONNECTION_STRING`: Your storage connection string

## Step 3: Build Configuration

The GitHub workflow (`.github/workflows/azure-static-web-apps.yml`) is already configured with:

- **App location**: `/task2/campaign-manager` (React app source)
- **API location**: `server` (Node.js API source)  
- **Output location**: `dist` (Vite build output)
- **App build command**: `npm run build`
- **API build command**: `npm install`

## Step 4: Route Configuration

The Static Web App is configured via `public/staticwebapp.config.json`:

- **API routes**: `/api/*` - proxied to Azure Functions
- **SPA routes**: All other routes serve `/index.html` for client-side routing
- **Security headers**: CSP, X-Frame-Options, etc.
- **MIME types**: Proper JSON content-type handling

## Step 5: Testing the Deployment

1. After deployment, Azure will provide a URL like: `https://campaign-manager-app.azurestaticapps.net`

2. Test the following:
   - Frontend loads correctly
   - API endpoints work: `/api/campaigns`
   - Client-side routing works for all React Router routes
   - Campaign data loads from Azure Blob Storage

## Step 6: Custom Domain (Optional)

To add a custom domain:

```bash
az staticwebapp hostname set \
    --name campaign-manager-app \
    --resource-group rg-campaign-manager \
    --hostname your-domain.com
```

## Architecture Overview

```
GitHub Repository
    ↓ (Push to main)
GitHub Actions Workflow
    ↓ (Build & Deploy)
Azure Static Web Apps
    ├── Frontend (React + Vite) → Static Files
    └── API (Node.js) → Azure Functions
            ↓ (Reads/Writes)
    Azure Blob Storage (campaigns, assets, brand)
```

## Costs (Free Tier Limits)

Azure Static Web Apps Free Tier includes:
- **Bandwidth**: 100 GB/month
- **API requests**: 125,000/month  
- **Storage**: 0.5 GB
- **Custom domains**: 2
- **Staging environments**: 3

## Environment Variables for Local Development

For local development with Azure backend:

```bash
# .env.local
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=campaignmanagerstorage;AccountKey=YOUR_KEY;EndpointSuffix=core.windows.net"
```

## Monitoring and Logs

- View deployment logs in GitHub Actions
- Monitor app performance in Azure Portal → Static Web Apps → Overview
- View API logs in Azure Portal → Static Web Apps → Functions

## Next Steps

1. Push your code to GitHub to trigger the first deployment
2. Configure the Azure Storage connection string
3. Test all functionality on the deployed app
4. Set up custom domain if needed