import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      // Backend runs on :8010 locally (the meeting-ai project owns :8000 on this host).
      '/api': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
      '/token': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
      // Cookie-auth endpoints: /auth/me (rehydrate), /auth/logout, OIDC callbacks.
      '/auth': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8010',
        ws: true,
      },
      '/health': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    chunkSizeWarningLimit: 600,
  },
})
