"use client";

import { ArtifactPane } from "./components/ArtifactPane";
import { ChatPane } from "./components/ChatPane";
import { useAgentStream } from "./hooks/useAgentStream";

export default function Home() {
  const {
    messages,
    isStreaming,
    toolInProgress,
    currentWorkbenchItem,
    isWorkbenchOpen,
    isMobileArtifactSheetOpen,
    sendMessage,
    focusWorkbench,
    closeWorkbench,
    closeMobileArtifactSheet,
  } = useAgentStream();

  const desktopWorkbenchVisible = Boolean(currentWorkbenchItem) && isWorkbenchOpen;

  return (
    <main className="h-[100dvh] overflow-hidden bg-[radial-gradient(circle_at_top_left,rgba(54,113,201,0.08),transparent_28%),radial-gradient(circle_at_top_right,rgba(247,178,103,0.14),transparent_24%),linear-gradient(180deg,#eef2f6,#e6ebf1)] px-3 py-3 text-[#152030] sm:px-4 sm:py-4">
      <div
        className={`mx-auto h-full min-h-0 max-w-[1600px] ${
          desktopWorkbenchVisible
            ? "lg:grid lg:grid-cols-[minmax(0,1.1fr)_minmax(380px,0.9fr)] lg:gap-5"
            : "w-full"
        }`}
      >
        <div className="h-full min-h-0 w-full">
          <ChatPane
            messages={messages}
            isStreaming={isStreaming}
            toolInProgress={toolInProgress}
            currentWorkbenchItem={currentWorkbenchItem}
            onSend={sendMessage}
            onOpenWorkbench={focusWorkbench}
          />
        </div>

        {desktopWorkbenchVisible && (
          <div className="relative hidden h-full min-h-0 lg:block">
            <ArtifactPane item={currentWorkbenchItem} onClose={closeWorkbench} className="h-full" />
          </div>
        )}
      </div>

      {currentWorkbenchItem && isMobileArtifactSheetOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            className="absolute inset-0 bg-[rgba(15,23,42,0.45)] backdrop-blur-[2px]"
            onClick={closeMobileArtifactSheet}
            aria-label="Close workbench sheet"
          />
          <div className="absolute inset-x-0 bottom-0 h-[82dvh] rounded-t-[28px] p-2">
            <ArtifactPane
              item={currentWorkbenchItem}
              onClose={closeMobileArtifactSheet}
              className="h-full rounded-t-[28px]"
            />
          </div>
        </div>
      )}
    </main>
  );
}
