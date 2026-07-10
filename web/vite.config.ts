import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  root: resolve(import.meta.dirname),
  base: "/client/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        player: resolve(import.meta.dirname, "player.html"),
        global: resolve(import.meta.dirname, "global.html"),
        replay: resolve(import.meta.dirname, "replay.html")
      }
    }
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"]
  }
});
