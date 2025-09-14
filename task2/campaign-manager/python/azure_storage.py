#!/usr/bin/env python3
"""
Azure Blob Storage helper for Python campaign pipeline.
This allows the Python pipeline to read campaigns from Azure Blob Storage.
"""

import json
import os
from azure.storage.blob import BlobServiceClient, BlobClient
from typing import Dict, Any, Optional

class AzureCampaignStorage:
    """Helper class for accessing campaign data from Azure Blob Storage."""
    
    def __init__(self):
        """Initialize Azure Blob Storage client."""
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not self.connection_string:
            raise ValueError('AZURE_STORAGE_CONNECTION_STRING environment variable is required')
        
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.campaigns_container = 'campaigns'
        self.assets_container = 'assets'
        self.brand_container = 'brand'
    
    def download_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Download a campaign JSON from Azure Blob Storage.
        
        Args:
            campaign_id: The campaign ID (without .json extension)
            
        Returns:
            Dict containing the campaign data
            
        Raises:
            FileNotFoundError: If the campaign doesn't exist
        """
        blob_name = f"{campaign_id}.json"
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.campaigns_container, 
                blob=blob_name
            )
            
            # Download the blob content
            blob_data = blob_client.download_blob()
            content = blob_data.readall().decode('utf-8')
            
            return json.loads(content)
            
        except Exception as e:
            if "BlobNotFound" in str(e):
                raise FileNotFoundError(f"Campaign '{campaign_id}' not found in Azure Blob Storage")
            raise e
    
    def upload_campaign(self, campaign_id: str, campaign_data: Dict[str, Any]) -> None:
        """
        Upload a campaign JSON to Azure Blob Storage.
        
        Args:
            campaign_id: The campaign ID (without .json extension)
            campaign_data: The campaign data dictionary
        """
        blob_name = f"{campaign_id}.json"
        
        # Ensure campaign_id matches the filename
        campaign_data['campaign_id'] = campaign_id
        
        # Convert to JSON string
        json_content = json.dumps(campaign_data, indent=2)
        
        blob_client = self.blob_service_client.get_blob_client(
            container=self.campaigns_container, 
            blob=blob_name
        )
        
        # Upload the blob
        blob_client.upload_blob(
            json_content, 
            overwrite=True,
            content_settings={'content_type': 'application/json'}
        )
    
    def upload_asset(self, asset_path: str, local_file_path: str, content_type: str = 'application/octet-stream') -> str:
        """
        Upload a generated asset to Azure Blob Storage.
        
        Args:
            asset_path: The path in the assets container (e.g., 'CAMPAIGN_ID/image.png')
            local_file_path: Path to the local file to upload
            content_type: MIME type of the file
            
        Returns:
            The URL of the uploaded asset
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.assets_container, 
            blob=asset_path
        )
        
        # Upload the file
        with open(local_file_path, 'rb') as data:
            blob_client.upload_blob(
                data, 
                overwrite=True,
                content_settings={'content_type': content_type}
            )
        
        return blob_client.url
    
    def download_brand_asset(self, asset_name: str, local_path: str) -> None:
        """
        Download a brand asset from Azure Blob Storage.
        
        Args:
            asset_name: Name of the brand asset (e.g., 'guidelines.json')
            local_path: Local path to save the file
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.brand_container, 
            blob=asset_name
        )
        
        # Download the blob
        with open(local_path, 'wb') as download_file:
            blob_data = blob_client.download_blob()
            download_file.write(blob_data.readall())


def load_campaign_from_azure(campaign_id: str) -> Dict[str, Any]:
    """
    Convenience function to load a campaign from Azure Blob Storage.
    
    This function can be used as a drop-in replacement for loading
    campaigns from local JSON files.
    
    Args:
        campaign_id: The campaign ID (without .json extension)
        
    Returns:
        Dict containing the campaign data
    """
    storage = AzureCampaignStorage()
    return storage.download_campaign(campaign_id)


def load_campaign_from_file_or_azure(file_path: str) -> Dict[str, Any]:
    """
    Load campaign from file path or Azure if environment variable is set.
    
    This allows the pipeline to work with both local files and Azure storage
    based on environment configuration.
    
    Args:
        file_path: Original file path (e.g., 'campaigns/CAMPAIGN_ID.json')
        
    Returns:
        Dict containing the campaign data
    """
    # Check if Azure storage should be used
    if os.getenv('AZURE_STORAGE_CONNECTION_STRING'):
        # Extract campaign ID from file path
        campaign_id = os.path.basename(file_path).replace('.json', '')
        return load_campaign_from_azure(campaign_id)
    else:
        # Fall back to local file loading
        with open(file_path, 'r') as f:
            return json.load(f)


if __name__ == "__main__":
    # Test the Azure storage functionality
    storage = AzureCampaignStorage()
    
    # List available campaigns
    container_client = storage.blob_service_client.get_container_client(storage.campaigns_container)
    print("Available campaigns in Azure Blob Storage:")
    for blob in container_client.list_blobs():
        if blob.name.endswith('.json'):
            print(f"  - {blob.name}")