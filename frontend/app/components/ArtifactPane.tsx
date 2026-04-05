"use client";

import { useCallback, useEffect, useState } from "react";
import { WorkbenchItem } from "../types";

interface Props {
  item: WorkbenchItem | null;
  onClose?: () => void;
  className?: string;
}

interface SpecialistSession {
  conversationId: string;
  conversationUrl: string;
}

function LiveSpecialistModal({
  title,
  session,
  onClose,
  isClosing,
}: {
  title: string;
  session: SpecialistSession;
  onClose: () => void;
  isClosing: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[rgba(15,23,42,0.62)] p-4 backdrop-blur-[3px]">
      <div className="flex h-[min(760px,88vh)] w-full max-w-5xl flex-col overflow-hidden rounded-[28px] border border-[rgba(255,255,255,0.12)] bg-[linear-gradient(180deg,#152030,#0f172a)] shadow-[0_30px_90px_rgba(15,23,42,0.38)]">
        <div className="flex items-start justify-between gap-4 border-b border-[rgba(255,255,255,0.08)] px-5 py-4">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#f7b267]">
              Live Specialist
            </div>
            <h3 className="mt-2 text-lg font-semibold text-white">{title}</h3>
            <p className="mt-1 text-xs text-[#91a0b6]">
              Tavus specialist embedded alongside your current workbench context.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <a
              href={session.conversationUrl}
              target="_blank"
              rel="noreferrer"
              className="rounded-full border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.05)] px-3 py-1.5 text-[11px] font-semibold text-[#d9e3f0] transition hover:bg-[rgba(255,255,255,0.12)]"
            >
              Open externally
            </a>
            <button
              onClick={onClose}
              disabled={isClosing}
              className="rounded-full border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.05)] px-3 py-1.5 text-[11px] font-semibold text-[#d9e3f0] transition hover:bg-[rgba(255,255,255,0.12)]"
            >
              {isClosing ? "Ending..." : "Close"}
            </button>
          </div>
        </div>

        <div className="flex-1 p-3">
          <div className="h-full overflow-hidden rounded-[22px] border border-[rgba(255,255,255,0.08)] bg-black/20">
            <iframe
              key={session.conversationUrl}
              src={session.conversationUrl}
              title="Tavus live specialist"
              className="h-full w-full bg-slate-950"
              allow="camera; microphone; autoplay; clipboard-write"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full flex-col justify-between rounded-[28px] border border-[rgba(255,255,255,0.08)] bg-[linear-gradient(180deg,rgba(30,41,59,0.98),rgba(15,23,42,0.98))] p-6 text-[#d5dbe5]">
      <div>
        <div className="inline-flex items-center rounded-full border border-[rgba(251,146,60,0.32)] bg-[rgba(251,146,60,0.08)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.28em] text-[#f7b267]">
          Workbench
        </div>
        <h3 className="mt-5 text-2xl font-semibold text-white">
          Visual guidance shows up here.
        </h3>
        <p className="mt-3 max-w-md text-sm leading-6 text-[#98a4b8]">
          Connection diagrams, troubleshooting flows, calculators, and exact manual
          pages stay pinned so you can keep working while the chat continues.
        </p>
      </div>

      <div className="grid gap-3 text-sm text-[#b8c2d1]">
        <div className="rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)] p-4">
          Setup questions open cable routing and polarity visuals.
        </div>
        <div className="rounded-2xl border border-[rgba(255,255,255,0.08)] bg-[rgba(255,255,255,0.03)] p-4">
          Manual-image requests pin the exact page so the assistant can point to it.
        </div>
      </div>
    </div>
  );
}

export function ArtifactPane({ item, onClose, className = "" }: Props) {
  const [specialistSessions, setSpecialistSessions] = useState<Record<string, SpecialistSession>>({});
  const [activeSpecialistItemId, setActiveSpecialistItemId] = useState<string | null>(null);
  const [isLaunchingSpecialist, setIsLaunchingSpecialist] = useState(false);
  const [isClosingSpecialist, setIsClosingSpecialist] = useState(false);
  const [specialistError, setSpecialistError] = useState<string | null>(null);

  const shouldOfferSpecialist = Boolean(
    item &&
      (
        item.kind === "polarity_diagram" ||
        item.kind === "duty_cycle_calculator" ||
        item.kind === "troubleshooting_flow" ||
        item.view === "manual_page"
      ),
  );

  const activeSpecialistSession =
    activeSpecialistItemId ? specialistSessions[activeSpecialistItemId] : null;

  const openSpecialist = useCallback(async () => {
    if (!item) return;

    const existing = specialistSessions[item.id];
    setSpecialistError(null);

    if (existing) {
      setActiveSpecialistItemId(item.id);
      return;
    }

    setIsLaunchingSpecialist(true);
    try {
      const response = await fetch("/api/tavus/session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          currentQuestion: item.currentQuestion,
          title: item.title,
          sourcePages: item.sourcePages,
          process: item.process,
          polarity: item.polarity,
          symptom: item.symptom,
          narrativeText: item.narrativeText,
        }),
      });

      const data = (await response.json()) as
        | SpecialistSession
        | { error?: string };

      if (!response.ok || !("conversationUrl" in data)) {
        const message =
          "error" in data && data.error
            ? data.error
            : `Failed to start specialist (${response.status})`;
        throw new Error(message);
      }

      setSpecialistSessions((prev) => ({
        ...prev,
        [item.id]: data,
      }));
      setActiveSpecialistItemId(item.id);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to open the Tavus specialist.";
      setSpecialistError(message);
    } finally {
      setIsLaunchingSpecialist(false);
    }
  }, [item, specialistSessions]);

  const closeSpecialist = useCallback(async () => {
    if (!activeSpecialistItemId) return;

    const session = specialistSessions[activeSpecialistItemId];
    setSpecialistError(null);
    setIsClosingSpecialist(true);

    try {
      if (session?.conversationId) {
        const response = await fetch(
          `/api/tavus/session/${session.conversationId}/end`,
          { method: "POST" },
        );
        const data = (await response.json()) as { error?: string };
        if (!response.ok) {
          throw new Error(data.error || `Failed to end specialist (${response.status})`);
        }
      }

      setSpecialistSessions((prev) => {
        const next = { ...prev };
        delete next[activeSpecialistItemId];
        return next;
      });
      setActiveSpecialistItemId(null);
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Unable to end the Tavus specialist session.";
      setSpecialistError(message);
    } finally {
      setIsClosingSpecialist(false);
    }
  }, [activeSpecialistItemId, specialistSessions]);

  useEffect(() => {
    setSpecialistError(null);
  }, [item?.id]);

  const sourceLabel =
    item && item.sourcePages.length > 0
      ? `Manual pages ${item.sourcePages.join(", ")}`
      : "Grounded response";

  return (
    <div
      className={`flex h-full flex-col overflow-hidden rounded-[28px] border border-[rgba(15,23,42,0.12)] bg-[linear-gradient(180deg,#253246,#151e2b)] shadow-[0_20px_80px_rgba(15,23,42,0.28)] ${className}`}
    >
      <div className="flex items-start justify-between gap-4 border-b border-[rgba(255,255,255,0.08)] px-5 py-4">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.26em] text-[#f7b267]">
            Live Workbench
          </div>
          <h3 className="mt-2 text-base font-semibold text-white">
            {item?.title ?? "Awaiting visual output"}
          </h3>
          <p className="mt-1 text-xs text-[#91a0b6]">{sourceLabel}</p>
        </div>

        <div className="flex items-center gap-2">
          {item && shouldOfferSpecialist && (
            <button
              onClick={openSpecialist}
              disabled={isLaunchingSpecialist}
              className="rounded-full border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.05)] px-3 py-1.5 text-[11px] font-semibold text-[#d9e3f0] transition hover:bg-[rgba(255,255,255,0.12)] disabled:opacity-50"
            >
              {isLaunchingSpecialist
                ? "Opening specialist..."
                : specialistSessions[item.id]
                  ? "Open live specialist"
                  : "Talk me through this"}
            </button>
          )}
          {onClose && (
            <button
              onClick={onClose}
              className="rounded-full border border-[rgba(255,255,255,0.12)] bg-[rgba(255,255,255,0.05)] px-3 py-1.5 text-[11px] font-semibold text-[#c8d2df] transition hover:bg-[rgba(255,255,255,0.11)]"
              aria-label="Close workbench"
            >
              Close
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-hidden bg-[radial-gradient(circle_at_top,rgba(74,158,255,0.08),transparent_42%),linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.02))] p-4">
        {specialistError && (
          <div className="mb-3 rounded-[18px] border border-[rgba(248,113,113,0.24)] bg-[rgba(127,29,29,0.2)] px-4 py-3 text-sm text-[#ffd3d3]">
            {specialistError}
          </div>
        )}
        {!item ? (
          <EmptyState />
        ) : item.view === "artifact" ? (
          <div className="h-full overflow-hidden rounded-[24px] border border-[rgba(255,255,255,0.08)] bg-[#dfe6ef]">
            <iframe
              srcDoc={item.html}
              sandbox="allow-scripts"
              className="h-full w-full border-none"
              title={item.title}
            />
          </div>
        ) : (
          <div className="flex h-full flex-col overflow-hidden rounded-[24px] border border-[rgba(255,255,255,0.08)] bg-[rgba(236,241,247,0.96)]">
            <div className="flex items-center justify-between border-b border-[rgba(15,23,42,0.08)] px-4 py-3">
              <div>
                <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#7c8aa0]">
                  Manual Snapshot
                </div>
                <div className="mt-1 text-sm font-semibold text-[#152030]">
                  Page {item.pageNumber}
                </div>
              </div>
              <div className="rounded-full bg-[rgba(251,146,60,0.12)] px-3 py-1 text-[11px] font-semibold text-[#9a4a13]">
                Pinch or browser-zoom for detail
              </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
              <img
                src={`data:image/png;base64,${item.imageBase64}`}
                alt={`Manual page ${item.pageNumber}`}
                className="mx-auto block w-full max-w-[940px] rounded-[20px] border border-[rgba(15,23,42,0.08)] bg-white shadow-[0_14px_40px_rgba(15,23,42,0.12)]"
              />
            </div>
          </div>
        )}
      </div>

      {activeSpecialistSession && item && activeSpecialistItemId === item.id && (
        <LiveSpecialistModal
          title={item.title}
          session={activeSpecialistSession}
          onClose={closeSpecialist}
          isClosing={isClosingSpecialist}
        />
      )}
    </div>
  );
}
