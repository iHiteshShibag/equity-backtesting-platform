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
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        // Heavy, not-always-needed vendor libs get their own chunk so they
        // load in parallel with (not blocking) the main bundle, and so
        // browsers can cache them independently of app code.
        manualChunks(id) {
          if (!id.includes('node_modules')) return undefined
          if (id.includes('recharts') || id.includes('d3-')) return 'vendor-charts'
          if (id.includes('xlsx') || id.includes('file-saver')) return 'vendor-export'
          if (id.includes('@sentry')) return 'vendor-sentry'
          return 'vendor'
        },
      },
    },
  },
})
