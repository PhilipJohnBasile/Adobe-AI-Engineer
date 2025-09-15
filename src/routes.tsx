import React from 'react';
import { Root } from './root';
import CampaignsLayout from './routes/campaigns';
import CampaignsList from './routes/campaigns._index';
import CampaignDetail from './routes/campaigns.$id';
import CampaignEdit from './routes/campaigns.$id.edit';
import Home from './routes/home';

export const routes = [
  {
    path: '/',
    element: <Root />,
    children: [
      {
        index: true,
        element: <Home />
      },
      {
        path: 'campaigns',
        element: <CampaignsLayout />,
        children: [
          {
            index: true,
            element: <CampaignsList />
          },
          {
            path: ':id',
            element: <CampaignDetail />
          },
          {
            path: ':id/edit',
            element: <CampaignEdit />
          }
        ]
      }
    ]
  }
];