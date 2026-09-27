import path from "node:path";
import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import vue from "@vitejs/plugin-vue";

const apiPort = process.env.TUNALO_API_PORT?.trim() || "38417";

export default defineConfig({
  base: "./",
  plugins: [vue(), tailwindcss()],
  server: {
    proxy: {
      "/api": {
        target: `http://127.0.0.1:${apiPort}`,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
});
