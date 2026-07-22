import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Em dev, o /api é proxyado pro backend (porta 8004 do docker-compose).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8004',
    },
  },
})
