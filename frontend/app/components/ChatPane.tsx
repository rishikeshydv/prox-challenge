"use client";

import { useEffect, useRef, useState } from "react";
import { Message, WorkbenchItem } from "../types";
import { LoadingIndicator } from "./LoadingIndicator";
import { MessageBubble } from "./MessageBubble";
import { WelcomeScreen } from "./WelcomeScreen";

interface Props {
  messages: Message[];
  isStreaming: boolean;
  toolInProgress: string | null;
  currentWorkbenchItem: WorkbenchItem | null;
  onSend: (text: string) => void;
  onOpenWorkbench: (item?: WorkbenchItem | null) => void;
}

export function ChatPane({
  messages,
  isStreaming,
  toolInProgress,
  currentWorkbenchItem,
  onSend,
  onOpenWorkbench,
}: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, toolInProgress]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput("");
    onSend(text);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`;
  };

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-[30px] border border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,rgba(250,251,253,0.98),rgba(241,244,248,0.98))] shadow-[0_24px_80px_rgba(15,23,42,0.12)]">
      <div className="border-b border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,#ffffff,#f4f7fb)] px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center rounded-full border border-[rgba(184,92,22,0.16)] bg-[rgba(247,178,103,0.12)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-[#b85c16]">
              Workshop Assistant
            </div>
            <h1 className="mt-3 text-[26px] font-semibold tracking-[-0.02em] text-[#152030]">
              Vulcan OmniPro 220
            </h1>
            <p className="mt-1 max-w-xl text-sm leading-6 text-[#64748b]">
              Ask for setup help, troubleshooting, settings, or exact manual visuals.
              The latest diagram or page stays pinned in the workbench while the chat keeps moving.
            </p>
          </div>

          {currentWorkbenchItem && (
            <button
              onClick={() => onOpenWorkbench(currentWorkbenchItem)}
              className="lg:hidden rounded-full border border-[rgba(44,93,176,0.16)] bg-[rgba(54,113,201,0.08)] px-4 py-2 text-[12px] font-semibold text-[#2455a6] transition hover:bg-[rgba(54,113,201,0.16)]"
            >
              Open workbench
            </button>
          )}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-5">
        {messages.length === 0 ? (
          <WelcomeScreen onQuestion={onSend} />
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onOpenWorkbench={onOpenWorkbench}
              />
            ))}
            {toolInProgress && <LoadingIndicator label={toolInProgress} />}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,#ffffff,#f5f7fa)] px-4 py-4 sm:px-5">
        <div className="rounded-[24px] border border-[rgba(15,23,42,0.08)] bg-[#fbfcfd] p-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
          <div className="flex items-end gap-3">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask about setup, duty cycle, wire feed, front panel controls, or troubleshooting..."
              rows={1}
              disabled={isStreaming}
              className="min-h-[28px] max-h-[160px] flex-1 resize-none bg-transparent px-1 text-[15px] leading-relaxed text-[#152030] outline-none placeholder:text-[#8a97aa] disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || isStreaming}
              className="inline-flex h-11 items-center justify-center rounded-[16px] bg-[linear-gradient(180deg,#3773c9,#2558a8)] px-4 text-sm font-semibold text-white shadow-[0_14px_24px_rgba(37,88,168,0.26)] transition hover:translate-y-[-1px] hover:shadow-[0_16px_28px_rgba(37,88,168,0.3)] disabled:translate-y-0 disabled:opacity-35 disabled:shadow-none"
              aria-label="Send"
            >
              Send
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-[#708096]">
            <span className="rounded-full bg-[rgba(15,23,42,0.05)] px-2.5 py-1">
              Grounded in the owner&apos;s manual
            </span>
            <span className="rounded-full bg-[rgba(15,23,42,0.05)] px-2.5 py-1">
              Best for setup and visual questions
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
