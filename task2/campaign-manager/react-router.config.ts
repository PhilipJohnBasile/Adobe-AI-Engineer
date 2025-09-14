import type { Config } from '@react-router/dev/config';

export default {
  // Build configuration
  appDirectory: 'app',
  buildDirectory: 'build',
  publicPath: '/',
  serverBuildPath: 'build/server/index.js',
  
  // Enable SSR and pre-rendering
  ssr: true,
  async prerender() {
    return ["/", "/campaigns"];
  },
} satisfies Config;