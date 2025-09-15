import { useLoaderData, useNavigate, Form } from 'react-router';
import type { Route } from './+types/campaigns.$id.edit';
import { CampaignSchema } from '~/lib/campaignSchema';
import type { Campaign } from '~/lib/campaignSchema';

export async function loader({ params }: Route.LoaderArgs): Promise<Route.LoaderData> {
  const { id } = params;
  
  try {
    // In framework mode, loaders run server-side when SSR/prerender is on,
    // or client-side when ssr: false. Either way: no filesystem in prod.
    // Always use the API in production (and dev)
    const response = await fetch(`/api/campaigns/${id}`, { 
      headers: { accept: "application/json" } 
    });
    
    if (!response.ok) {
      throw new Response('Campaign not found', { status: 404 });
    }
    
    const campaignData = await response.json();
    const validatedCampaign = CampaignSchema.parse(campaignData);
    
    console.log(`Loaded campaign ${id} for editing from API`);
    
    return { campaign: validatedCampaign };
  } catch (error) {
    console.error('Error loading campaign:', error);
    throw new Response('Campaign not found', { status: 404 });
  }
}

export async function action({ params, request }: Route.ActionArgs) {
  const { id } = params;
  const formData = await request.formData();
  
  try {
    // Get the JSON data from the form
    const campaignDataJson = formData.get('campaignData') as string;
    const campaignData = JSON.parse(campaignDataJson);
    
    // Ensure the campaign_id matches the URL parameter
    campaignData.campaign_id = id;
    
    // Validate with Zod schema
    const validatedCampaign = CampaignSchema.parse(campaignData);
    
    // Save via API instead of filesystem
    const response = await fetch(`/api/campaigns/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'accept': 'application/json'
      },
      body: JSON.stringify(validatedCampaign)
    });
    
    if (!response.ok) {
      throw new Error(`Failed to save campaign: ${response.status}`);
    }
    
    console.log(`Saved campaign ${id} via API`);
    
    return { success: true, campaign: validatedCampaign };
  } catch (error) {
    console.error('Error saving campaign:', error);
    return { success: false, error: 'Failed to save campaign' };
  }
}

export default function CampaignEdit() {
  const { campaign } = useLoaderData<typeof loader>();
  const navigate = useNavigate();
  
  const handleSave = (event: React.FormEvent<HTMLFormElement>) => {
    // The form will be handled by React Router's action function
    // We can add client-side validation here if needed
  };
  
  const handleCancel = () => {
    navigate(`/campaigns/${campaign.campaign_id}`);
  };
  
  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2>Edit Campaign: {campaign.campaign_name}</h2>
      </div>

      <Form method="post" onSubmit={handleSave}>
        <input 
          type="hidden" 
          name="campaignData" 
          value={JSON.stringify(campaign)} 
        />
        
        <div style={{ backgroundColor: 'white', border: '1px solid #ddd', borderRadius: '8px', padding: '20px' }}>
          <div style={{ display: 'grid', gap: '20px' }}>
            
            <section>
              <h3>Basic Information</h3>
              <div style={{ display: 'grid', gap: '15px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Campaign Name:</label>
                  <input 
                    type="text" 
                    name="campaign_name"
                    defaultValue={campaign.campaign_name}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    onChange={(e) => {
                      // Update the hidden JSON field
                      const form = e.target.form;
                      if (form) {
                        const hiddenInput = form.querySelector('input[name="campaignData"]') as HTMLInputElement;
                        const data = JSON.parse(hiddenInput.value);
                        data.campaign_name = e.target.value;
                        hiddenInput.value = JSON.stringify(data);
                      }
                    }}
                  />
                </div>
                
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Client:</label>
                  <input 
                    type="text" 
                    name="client"
                    defaultValue={campaign.client}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    onChange={(e) => {
                      const form = e.target.form;
                      if (form) {
                        const hiddenInput = form.querySelector('input[name="campaignData"]') as HTMLInputElement;
                        const data = JSON.parse(hiddenInput.value);
                        data.client = e.target.value;
                        hiddenInput.value = JSON.stringify(data);
                      }
                    }}
                  />
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Start Date:</label>
                    <input 
                      type="date" 
                      name="campaign_start_date"
                      defaultValue={campaign.campaign_start_date}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      onChange={(e) => {
                        const form = e.target.form;
                        if (form) {
                          const hiddenInput = form.querySelector('input[name="campaignData"]') as HTMLInputElement;
                          const data = JSON.parse(hiddenInput.value);
                          data.campaign_start_date = e.target.value;
                          hiddenInput.value = JSON.stringify(data);
                        }
                      }}
                    />
                  </div>
                  
                  <div>
                    <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>End Date:</label>
                    <input 
                      type="date" 
                      name="campaign_end_date"
                      defaultValue={campaign.campaign_end_date}
                      style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                      onChange={(e) => {
                        const form = e.target.form;
                        if (form) {
                          const hiddenInput = form.querySelector('input[name="campaignData"]') as HTMLInputElement;
                          const data = JSON.parse(hiddenInput.value);
                          data.campaign_end_date = e.target.value;
                          hiddenInput.value = JSON.stringify(data);
                        }
                      }}
                    />
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h3>Campaign Message</h3>
              <div style={{ display: 'grid', gap: '15px' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Primary Headline:</label>
                  <input 
                    type="text" 
                    name="primary_headline"
                    defaultValue={campaign.campaign_message.primary_headline}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    onChange={(e) => {
                      const form = e.target.form;
                      if (form) {
                        const hiddenInput = form.querySelector('input[name="campaignData"]') as HTMLInputElement;
                        const data = JSON.parse(hiddenInput.value);
                        data.campaign_message.primary_headline = e.target.value;
                        hiddenInput.value = JSON.stringify(data);
                      }
                    }}
                  />
                </div>
                
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Secondary Headline:</label>
                  <input 
                    type="text" 
                    name="secondary_headline"
                    defaultValue={campaign.campaign_message.secondary_headline}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    onChange={(e) => {
                      const form = e.target.form;
                      if (form) {
                        const hiddenInput = form.querySelector('input[name="campaignData"]') as HTMLInputElement;
                        const data = JSON.parse(hiddenInput.value);
                        data.campaign_message.secondary_headline = e.target.value;
                        hiddenInput.value = JSON.stringify(data);
                      }
                    }}
                  />
                </div>
                
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Brand Voice:</label>
                  <textarea 
                    name="brand_voice"
                    defaultValue={campaign.campaign_message.brand_voice}
                    rows={3}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', resize: 'vertical' }}
                    onChange={(e) => {
                      const form = e.target.form;
                      if (form) {
                        const hiddenInput = form.querySelector('input[name="campaignData"]') as HTMLInputElement;
                        const data = JSON.parse(hiddenInput.value);
                        data.campaign_message.brand_voice = e.target.value;
                        hiddenInput.value = JSON.stringify(data);
                      }
                    }}
                  />
                </div>
                
                <div>
                  <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Seasonal Theme:</label>
                  <input 
                    type="text" 
                    name="seasonal_theme"
                    defaultValue={campaign.campaign_message.seasonal_theme}
                    style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
                    onChange={(e) => {
                      const form = e.target.form;
                      if (form) {
                        const hiddenInput = form.querySelector('input[name="campaignData"]') as HTMLInputElement;
                        const data = JSON.parse(hiddenInput.value);
                        data.campaign_message.seasonal_theme = e.target.value;
                        hiddenInput.value = JSON.stringify(data);
                      }
                    }}
                  />
                </div>
              </div>
            </section>

            <div style={{ display: 'flex', gap: '10px', paddingTop: '20px', borderTop: '1px solid #eee' }}>
              <button 
                type="submit"
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#007bff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                Save Campaign
              </button>
              
              <button 
                type="button"
                onClick={handleCancel}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '5px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      </Form>
    </div>
  );
}