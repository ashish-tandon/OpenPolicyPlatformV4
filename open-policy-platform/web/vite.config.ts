import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://api-gateway:9000',
        changeOrigin: true,
      },
    },
    cors: true,
    // Force binding to all interfaces
    strictPort: true,
    // Allow external access
    hmr: {
      host: '0.0.0.0',
    },
    // Additional settings for Docker
    watch: {
      usePolling: true,
    },
    // Force network binding
    network: '0.0.0.0',
  },
});
