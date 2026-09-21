import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      // Direct proxy for endpoints
      '/products': 'http://127.0.0.1:8000',
      '/keywords': 'http://127.0.0.1:8000',
      '/content': 'http://127.0.0.1:8000',
      '/existing-content': 'http://127.0.0.1:8000',
      '/store-profile': 'http://127.0.0.1:8000',
      '/research-runs': 'http://127.0.0.1:8000',
      '/opportunities': 'http://127.0.0.1:8000',
      '/content-opportunities': 'http://127.0.0.1:8000',
      '/content-briefs': 'http://127.0.0.1:8000',
      '/briefs': 'http://127.0.0.1:8000',
      '/content-drafts': 'http://127.0.0.1:8000',
      '/published-content': 'http://127.0.0.1:8000',
      '/blog': 'http://127.0.0.1:8000',
      '/dashboard': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000'
    }
  }
});
