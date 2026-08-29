import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8790',
        changeOrigin: true,
      },
      '/api/explain': {
        target: 'http://localhost:9001',
        changeOrigin: true,
      },
      '/mcp': {
        target: 'http://localhost:9001',
        changeOrigin: true,
      },
    },
  },
});
