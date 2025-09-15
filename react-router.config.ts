import type { Config } from '@react-router/dev/config';

export default {
  // Build configuration
  appDirectory: 'app',
  buildDirectory: 'build',
  publicPath: '/',
  
  // Disable SSR for client-side only app
  ssr: false,
} satisfies Config;