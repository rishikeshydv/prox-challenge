"use client";

import ReactMarkdown from "react-markdown";
import { Message, WorkbenchItem } from "../types";

interface Props {
  message: Message;
  onOpenWorkbench?: (item?: WorkbenchItem | null) => void;
}

function WorkbenchSummary({
  item,
  onOpenWorkbench,
}: {
  item: WorkbenchItem;
  onOpenWorkbench?: (item?: WorkbenchItem | null) => void;
}) {
  const modeLabel =
    item.view === "manual_page" ? `Manual page ${item.pageNumber}` : "Opened in workbench";
  const kindLabel =
    item.view === "manual_page"
      ? "Manual reference"
      : item.kind === "polarity_diagram"
        ? "Setup diagram"
        : item.kind === "troubleshooting_flow"
          ? "Troubleshooting flow"
          : item.kind === "settings_configurator"
            ? "Settings panel"
            : item.kind === "duty_cycle_calculator"
              ? "Duty cycle tool"
              : "Visual output";

  return (
    <div className="mt-4 overflow-hidden rounded-[22px] border border-[rgba(21,32,48,0.1)] bg-[linear-gradient(180deg,#ffffff,#f4f7fb)] shadow-[0_14px_34px_rgba(15,23,42,0.08)]">
      <div className="flex items-start justify-between gap-3 border-b border-[rgba(15,23,42,0.07)] px-4 py-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#b85c16]">
            {kindLabel}
          </div>
          <div className="mt-1 text-sm font-semibold text-[#152030]">{item.title}</div>
          <div className="mt-1 text-xs text-[#637287]">{modeLabel}</div>
        </div>
        <button
          onClick={() => onOpenWorkbench?.(item)}
          className="rounded-full border border-[rgba(44,93,176,0.18)] bg-[rgba(54,113,201,0.08)] px-3 py-1.5 text-[11px] font-semibold text-[#2455a6] transition hover:bg-[rgba(54,113,201,0.16)]"
        >
          Focus
        </button>
      </div>

      <div className="flex items-center justify-between gap-3 px-4 py-3 text-xs text-[#6b7789]">
        <span>
          Source: {item.sourcePages.length > 0 ? `pages ${item.sourcePages.join(", ")}` : "manual-backed"}
        </span>
        <span className="rounded-full bg-[rgba(15,23,42,0.05)] px-2.5 py-1 font-medium text-[#516072]">
          Latest visual pinned
        </span>
      </div>
    </div>
  );
}

export function MessageBubble({ message, onOpenWorkbench }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`mb-4 flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={
          isUser
            ? "max-w-[82%] rounded-[24px] rounded-br-[8px] border border-[rgba(16,66,141,0.16)] bg-[linear-gradient(180deg,#3773c9,#2558a8)] px-4 py-3 text-sm leading-relaxed text-white shadow-[0_16px_36px_rgba(37,88,168,0.24)]"
            : "max-w-[88%] rounded-[24px] rounded-bl-[8px] border border-[rgba(21,32,48,0.08)] bg-[linear-gradient(180deg,#ffffff,#f9fbfd)] px-4 py-3 text-sm leading-relaxed text-[#152030] shadow-[0_14px_34px_rgba(15,23,42,0.06)]"
        }
      >
        {/* Typing indicator — shown while waiting for first token, but not if a workbench card already arrived */}
        {!isUser && message.isStreaming && !message.content && !message.workbenchItem && (
          <span className="inline-flex items-center justify-center gap-1.5 rounded-full border border-[rgba(54,113,201,0.18)] bg-[rgba(54,113,201,0.06)] px-3 py-2">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="h-2 w-2 rounded-full bg-[#2b63bd]"
                style={{ animation: `typingBounce 1.3s ease-in-out ${i * 0.18}s infinite` }}
              />
            ))}
          </span>
        )}

        {message.content && (
          <div className={isUser ? "prose prose-invert max-w-none" : "prose prose-slate max-w-none"}>
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="mb-2 list-disc space-y-1 pl-5">{children}</ul>,
                ol: ({ children }) => <ol className="mb-2 list-decimal space-y-1 pl-5">{children}</ol>,
                li: ({ children }) => <li>{children}</li>,
                strong: ({ children }) => (
                  <strong className={isUser ? "font-semibold text-white" : "font-semibold text-[#111827]"}>
                    {children}
                  </strong>
                ),
                code: ({ children }) => (
                  <code
                    className={
                      isUser
                        ? "rounded-md bg-white/20 px-1.5 py-0.5 text-[12px]"
                        : "rounded-md bg-[#eef2f7] px-1.5 py-0.5 text-[12px] text-[#233248]"
                    }
                  >
                    {children}
                  </code>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        )}

        {message.isStreaming && message.content && (
          <span className="ml-1 inline-block h-3.5 w-1.5 animate-pulse rounded-sm bg-[#2b63bd] align-middle" />
        )}

        {!isUser && message.workbenchItem && (
          <WorkbenchSummary item={message.workbenchItem} onOpenWorkbench={onOpenWorkbench} />
        )}
      </div>
    </div>
  );
}
