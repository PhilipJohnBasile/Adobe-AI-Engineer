import { Link } from 'react-router';

export default function Home() {
  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', lineHeight: '1.8' }}>
      <h1>Adobe Creative Automation - Campaign Manager</h1>
      <p>Welcome to the AI-powered creative automation platform for multi-brand campaigns.</p>
      <nav>
        <Link to="/campaigns" style={{ 
          display: 'inline-block', 
          padding: '10px 20px', 
          backgroundColor: '#007bff', 
          color: 'white', 
          textDecoration: 'none', 
          borderRadius: '5px' 
        }}>
          Manage Campaigns
        </Link>
      </nav>
    </div>
  );
}