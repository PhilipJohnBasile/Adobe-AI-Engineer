import {
  type RouteConfig,
  index,
  route,
  layout,
} from '@react-router/dev/routes';

export default [
  index('./routes/home.tsx'),
  layout('./routes/campaigns.tsx', [
    route('campaigns', './routes/campaigns._index.tsx'),
    route('campaigns/:id', './routes/campaigns.$id.tsx'),
    route('campaigns/:id/edit', './routes/campaigns.$id.edit.tsx'),
  ]),
] satisfies RouteConfig;