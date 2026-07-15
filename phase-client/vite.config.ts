import path from "node:path";
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

function trimManaFont(): Plugin {
  return {
    name: "coworld-trim-mana-font",
    enforce: "pre",
    transform(code, id) {
      if (!id.replace(/\\/g, "/").endsWith("mana-font/css/mana.css")) return;
      const classes = code.replace(/@font-face\s*\{[^}]*\}/g, "");
      return {
        code:
          '@font-face{font-family:"Mana";src:url("../fonts/mana.woff2") format("woff2");' +
          `font-weight:normal;font-style:normal;}\n${classes}`,
        map: null,
      };
    },
  };
}

const emptyUrl = JSON.stringify("");
const defines = Object.fromEntries(
  [
    "__AUDIO_BASE_URL__",
    "__CARD_DATA_META_URL__",
    "__CARD_DATA_URL__",
    "__CARD_NAMES_URL__",
    "__CHANGELOG_META_URL__",
    "__CHANGELOG_URL__",
    "__COVERAGE_DATA_URL__",
    "__COVERAGE_SUMMARY_URL__",
    "__DECKS_URL__",
    "__DEFAULT_MULTIPLAYER_SERVER_URL__",
    "__DRAFT_POOLS_URL__",
    "__PREVIEW_SITE_URL__",
    "__SCRYFALL_DATA_URL__",
    "__SCRYFALL_PRINTINGS_URL__",
    "__SCRYFALL_SETS_URL__",
    "__SCRYFALL_TOKEN_IMAGES_URL__",
    "__SET_LIST_URL__",
    "__SUPABASE_ANON_KEY__",
    "__SUPABASE_URL__",
    "__TELEMETRY_URL__",
  ].map((name) => [name, emptyUrl]),
);

export default defineConfig({
  base: "/client/",
  publicDir: false,
  define: {
    ...defines,
    __SCRYFALL_DATA_URL__: JSON.stringify("https://data.phase-rs.dev/scryfall-data.json"),
    __SCRYFALL_PRINTINGS_URL__: JSON.stringify(
      "https://data.phase-rs.dev/scryfall-printings.json",
    ),
    __SCRYFALL_SETS_URL__: JSON.stringify("https://data.phase-rs.dev/scryfall-sets.json"),
    __SCRYFALL_TOKEN_IMAGES_URL__: JSON.stringify(
      "https://data.phase-rs.dev/scryfall-token-images.json",
    ),
    __APP_VERSION__: JSON.stringify("coworld"),
    __BUILD_HASH__: JSON.stringify(process.env.PHASE_REVISION?.slice(0, 12) ?? "dev"),
    __CARD_DATA_LOCALE_URL_TEMPLATE__: emptyUrl,
    __GIT_REPO_URL__: JSON.stringify("https://github.com/phase-rs/phase"),
    __IS_RELEASE_BUILD__: "false",
    __TAURI_INTERNALS__: "undefined",
    "import.meta.env.VITE_WS_URL": JSON.stringify("coworld://current-origin"),
  },
  resolve: {
    alias: [
      {
        find: /^.*[/\\]adapter[/\\]ws-adapter(?:\.ts)?$/,
        replacement: path.resolve(__dirname, "src/coworld/coworld-ws-adapter.ts"),
      },
      {
        find: "@wasm/engine",
        replacement: path.resolve(__dirname, "src/coworld/wasm-engine-stub.ts"),
      },
      {
        find: "@wasm/draft",
        replacement: path.resolve(__dirname, "src/coworld/wasm-draft-stub.ts"),
      },
    ],
  },
  plugins: [trimManaFont(), react(), tailwindcss()],
  build: {
    outDir: "coworld-dist",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        player: path.resolve(__dirname, "player.html"),
        global: path.resolve(__dirname, "global.html"),
        replay: path.resolve(__dirname, "replay.html"),
      },
    },
  },
});
