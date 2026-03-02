// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    // Add this section below:
    allowedHosts: [
      'prova.bitssand.blog',
      'localhost'
    ],
    watch: {
       usePolling: true,
    },
  },
})
