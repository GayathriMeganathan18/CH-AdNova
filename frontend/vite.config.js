import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In docker-compose, the frontend is served by nginx (see Dockerfile/nginx.conf)
// which proxies /api to the backend service by container name. This vite
// config's proxy only matters for `npm run dev` outside Docker.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
      },
      "/health": {
        target: process.env.VITE_BACKEND_URL || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
