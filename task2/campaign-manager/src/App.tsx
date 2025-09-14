import React, { useState, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Provider, defaultTheme } from '@adobe/react-spectrum';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import CampaignsPage from './pages/CampaignsPage';
import CampaignDetailPage from './pages/CampaignDetailPage';
import CampaignEditPage from './pages/CampaignEditPage';
import CampaignCreatePage from './pages/CampaignCreatePage';
import './App.css';

// Error boundary component
class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean}> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div style={{padding: '20px'}}>
        <h1>Something went wrong.</h1>
        <p>Check the console for errors.</p>
      </div>;
    }

    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <Provider theme={defaultTheme} colorScheme="light" scale="medium">
        <Layout>
          <Suspense fallback={<div style={{padding: '20px'}}>Loading...</div>}>
            <Routes>
              <Route path="/" element={<CampaignsPage />} />
              <Route path="/campaigns" element={<CampaignsPage />} />
              <Route path="/campaigns/new" element={<CampaignCreatePage />} />
              <Route path="/campaigns/:id" element={<CampaignDetailPage />} />
              <Route path="/campaigns/:id/edit" element={<CampaignEditPage />} />
              <Route path="*" element={<CampaignsPage />} />
            </Routes>
          </Suspense>
        </Layout>
      </Provider>
    </ErrorBoundary>
  );
}

export default App;