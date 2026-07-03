import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  publicDir: mode === "development" ? "public" : false,
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/ws": {
        target: "ws://127.0.0.1:8000",
        ws: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
}));
