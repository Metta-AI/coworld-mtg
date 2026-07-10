import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  expect: {
    timeout: 10_000
  },
  use: {
    ...devices["Desktop Chrome"],
    trace: "on-first-retry"
  },
  workers: 1
});
