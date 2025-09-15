# Azure Setup Instructions

## 1. Create Azure Storage Account

```bash
# Login to Azure CLI
az login

# Create resource group
az group create --name rg-campaign-manager --location eastus

# Create storage account (free tier)
az storage account create \
  --name campaignmanagerstorage \
  --resource-group rg-campaign-manager \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2

# Get connection string
az storage account show-connection-string \
  --name campaignmanagerstorage \
  --resource-group rg-campaign-manager \
  --query connectionString --output tsv
```

## 2. Create Blob Containers

```bash
# Set connection string as environment variable
export AZURE_STORAGE_CONNECTION_STRING="<connection-string-from-above>"

# Create containers
az storage container create --name campaigns
az storage container create --name assets
az storage container create --name brand
```

## 3. Upload Campaign Files

```bash
# Upload all campaign JSON files
az storage blob upload-batch \
  --destination campaigns \
  --source ../../task2/campaigns \
  --pattern "*.json"

# Upload brand assets
az storage blob upload-batch \
  --destination brand \
  --source ../../task2/assets/brand \
  --pattern "*"
```

## 4. Environment Variables

Create `.env.azure` file:

```env
AZURE_STORAGE_CONNECTION_STRING=<your-connection-string>
AZURE_STORAGE_ACCOUNT_NAME=campaignmanagerstorage
AZURE_STORAGE_CONTAINER_CAMPAIGNS=campaigns
AZURE_STORAGE_CONTAINER_ASSETS=assets
AZURE_STORAGE_CONTAINER_BRAND=brand
```