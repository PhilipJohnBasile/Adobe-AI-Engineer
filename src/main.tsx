import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from '@adobe/react-spectrum';
import { defaultTheme } from '@adobe/react-spectrum';
import { RouterProvider, createBrowserRouter } from 'react-router-dom';
import { routes } from './routes';
import './index.css';

const router = createBrowserRouter(routes);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Provider theme={defaultTheme}>
      <RouterProvider router={router} />
    </Provider>
  </React.StrictMode>
);