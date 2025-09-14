import { BlobServiceClient, ContainerClient } from '@azure/storage-blob';

export class AzureCampaignStorage {
  private blobServiceClient: BlobServiceClient;
  private campaignsContainer: ContainerClient;
  private assetsContainer: ContainerClient;
  
  constructor() {
    const connectionString = process.env.AZURE_STORAGE_CONNECTION_STRING;
    if (!connectionString) {
      throw new Error('AZURE_STORAGE_CONNECTION_STRING environment variable is required');
    }
    
    this.blobServiceClient = BlobServiceClient.fromConnectionString(connectionString);
    this.campaignsContainer = this.blobServiceClient.getContainerClient('campaigns');
    this.assetsContainer = this.blobServiceClient.getContainerClient('assets');
  }

  async listCampaigns(): Promise<any[]> {
    const campaigns = [];
    
    for await (const blob of this.campaignsContainer.listBlobsFlat()) {
      if (blob.name.endsWith('.json')) {
        const blobClient = this.campaignsContainer.getBlobClient(blob.name);
        const downloadResponse = await blobClient.download();
        const content = await this.streamToString(downloadResponse.readableStreamBody!);
        const campaignData = JSON.parse(content);
        
        campaigns.push({
          ...campaignData,
          id: campaignData.campaign_id || blob.name.replace('.json', ''),
          name: campaignData.campaign_name,
          status: this.determineStatus(campaignData),
          created_date: blob.properties.lastModified?.toISOString()
        });
      }
    }
    
    return campaigns;
  }

  async getCampaign(campaignId: string): Promise<any> {
    const blobName = `${campaignId}.json`;
    const blobClient = this.campaignsContainer.getBlobClient(blobName);
    
    try {
      const downloadResponse = await blobClient.download();
      const content = await this.streamToString(downloadResponse.readableStreamBody!);
      return JSON.parse(content);
    } catch (error: any) {
      if (error.statusCode === 404) {
        throw new Error('Campaign not found');
      }
      throw error;
    }
  }

  async saveCampaign(campaignId: string, campaignData: any): Promise<void> {
    const blobName = `${campaignId}.json`;
    const blobClient = this.campaignsContainer.getBlobClient(blobName);
    
    // Ensure campaign_id matches the file name
    campaignData.campaign_id = campaignId;
    
    const content = JSON.stringify(campaignData, null, 2);
    
    await blobClient.upload(content, Buffer.byteLength(content), {
      blobHTTPHeaders: {
        blobContentType: 'application/json'
      }
    });
  }

  async deleteCampaign(campaignId: string): Promise<void> {
    const blobName = `${campaignId}.json`;
    const blobClient = this.campaignsContainer.getBlobClient(blobName);
    await blobClient.deleteIfExists();
  }

  async uploadAsset(fileName: string, data: Buffer, contentType: string): Promise<string> {
    const blobClient = this.assetsContainer.getBlobClient(fileName);
    
    await blobClient.upload(data, data.length, {
      blobHTTPHeaders: {
        blobContentType: contentType
      }
    });

    return blobClient.url;
  }

  async getAssetUrl(fileName: string): Promise<string> {
    const blobClient = this.assetsContainer.getBlobClient(fileName);
    return blobClient.url;
  }

  // Helper methods
  private async streamToString(readableStream: NodeJS.ReadableStream): Promise<string> {
    return new Promise((resolve, reject) => {
      const chunks: Buffer[] = [];
      readableStream.on('data', (data) => {
        chunks.push(data instanceof Buffer ? data : Buffer.from(data));
      });
      readableStream.on('end', () => {
        resolve(Buffer.concat(chunks).toString());
      });
      readableStream.on('error', reject);
    });
  }

  private determineStatus(campaign: any): 'pending' | 'active' | 'completed' {
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
}