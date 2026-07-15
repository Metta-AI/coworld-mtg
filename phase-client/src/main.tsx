import "../polyfills/cryptoRandomUUID";
import { Suspense } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter, Route, Routes } from "react-router";
import "@fontsource-variable/newsreader";
import "@fontsource-variable/jetbrains-mono";
import "mana-font/css/mana.css";
import "../index.css";
import "../i18n";

import { ErrorBoundary } from "../components/ErrorBoundary";
import { AppToast } from "../components/chrome/AppToast";
import { EngineLostModal } from "../components/modal/EngineLostModal";
import { NonFatalPanicToast } from "../components/modal/NonFatalPanicToast";
import { StuckDecisionToast } from "../components/modal/StuckDecisionToast";
import { GamePage } from "../pages/GamePage";
import { CoworldChrome } from "./coworld-chrome";

const role = document.body.dataset.coworldRole;
const mode = role === "player" ? "host" : "spectate";
const entry = `/game/coworld?mode=${mode}`;

function CoworldPhaseApp() {
  return (
    <MemoryRouter initialEntries={[entry]}>
      <div className="min-h-screen bg-gray-950 text-white">
        <ErrorBoundary>
          <Suspense
            fallback={
              <div className="flex min-h-screen items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-500 border-t-white" />
              </div>
            }
          >
            <Routes>
              <Route path="/game/:id" element={<GamePage />} />
            </Routes>
          </Suspense>
        </ErrorBoundary>
        <AppToast />
        <EngineLostModal />
        <NonFatalPanicToast />
        <StuckDecisionToast />
        <CoworldChrome />
      </div>
    </MemoryRouter>
  );
}

createRoot(document.getElementById("root")!).render(<CoworldPhaseApp />);
