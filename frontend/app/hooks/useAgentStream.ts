"use client";

import { useCallback, useRef, useState } from "react";
import { Message, SSEEvent, WorkbenchItem } from "../types";

const TOOL_LABELS: Record<string, string> = {
  search_manual: "Inspecting the manual and cross-checking the right section...",
  render_polarity_diagram: "Building a connection diagram for your setup...",
  render_duty_cycle_calculator: "Preparing the duty cycle workbench...",
  render_troubleshooting_flow: "Laying out a troubleshooting path...",
  render_settings_configurator: "Assembling recommended settings...",
  get_manual_page_image: "Loading the exact manual page into the workbench...",
};

function parseSSEBuffer(buffer: string): { events: SSEEvent[]; rest: string } {
  const blocks = buffer.split("\n\n");
  const rest = blocks.pop() ?? "";

  const events = blocks
    .filter((block) => block.startsWith("data: "))
    .map((block) => {
      try {
        return JSON.parse(block.slice(6)) as SSEEvent;
      } catch {
        return null;
      }
    })
    .filter(Boolean) as SSEEvent[];

  return { events, rest };
}

export function useAgentStream() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toolInProgress, setToolInProgress] = useState<string | null>(null);
  const [currentWorkbenchItem, setCurrentWorkbenchItem] = useState<WorkbenchItem | null>(null);
  const [isWorkbenchOpen, setIsWorkbenchOpen] = useState(false);
  const [isMobileArtifactSheetOpen, setIsMobileArtifactSheetOpen] = useState(false);

  const conversationIdRef = useRef<string | null>(null);
  const sseBufferRef = useRef("");
  const currentAssistantIdRef = useRef<string | null>(null);
  const currentUserQuestionRef = useRef("");
  const idCounterRef = useRef(0);

  const createId = useCallback((prefix: string) => {
    idCounterRef.current += 1;
    return `${prefix}-${Date.now()}-${idCounterRef.current}`;
  }, []);

  const updateLastAssistantMessage = useCallback((update: Partial<Message>) => {
    setMessages((prev) => {
      const updated = [...prev];
      const last = updated[updated.length - 1];
      if (last?.role === "assistant") {
        updated[updated.length - 1] = { ...last, ...update };
      }
      return updated;
    });
  }, []);

  const syncActiveWorkbenchNarrative = useCallback((text: string) => {
    const activeAssistantId = currentAssistantIdRef.current;
    if (!activeAssistantId) return;

    setMessages((prev) =>
      prev.map((message) => {
        if (message.id !== activeAssistantId || !message.workbenchItem) {
          return message;
        }

        return {
          ...message,
          workbenchItem: {
            ...message.workbenchItem,
            narrativeText: text,
          },
        };
      }),
    );

    setCurrentWorkbenchItem((prev) => {
      if (!prev || prev.sourceMessageId !== activeAssistantId) {
        return prev;
      }

      return {
        ...prev,
        narrativeText: text,
      };
    });
  }, []);

  const attachWorkbenchItemToLastAssistant = useCallback((item: WorkbenchItem) => {
    updateLastAssistantMessage({ workbenchItem: item });
    setCurrentWorkbenchItem(item);
    setIsWorkbenchOpen(true);
    setIsMobileArtifactSheetOpen(true);
  }, [updateLastAssistantMessage]);

  const handleEvent = useCallback((event: SSEEvent, assistantContent: string) => {
    switch (event.type) {
      case "text_delta": {
        const nextContent = assistantContent + event.content;
        updateLastAssistantMessage({ content: nextContent });
        syncActiveWorkbenchNarrative(nextContent);
        return nextContent;
      }

      case "tool_start":
        setToolInProgress(TOOL_LABELS[event.tool] ?? "Working through the next step...");
        return assistantContent;

      case "artifact": {
        const sourceMessageId = currentAssistantIdRef.current ?? createId("assistant");
        const item: WorkbenchItem = {
          id: createId("workbench"),
          sourceMessageId,
          view: "artifact",
          html: event.html,
          title: event.title,
          sourcePages: event.pages,
          kind: event.kind ?? "artifact",
          narrativeText: assistantContent,
          currentQuestion: currentUserQuestionRef.current,
          process: event.metadata?.process,
          polarity: event.metadata?.polarity,
          symptom: event.metadata?.symptom,
        };
        attachWorkbenchItemToLastAssistant(item);
        setToolInProgress(null);
        return assistantContent;
      }

      case "manual_page": {
        const sourceMessageId = currentAssistantIdRef.current ?? createId("assistant");
        const item: WorkbenchItem = {
          id: createId("workbench"),
          sourceMessageId,
          view: "manual_page",
          imageBase64: event.image_b64,
          pageNumber: event.page,
          highlight: event.highlight,
          title: `Manual Page ${event.page}`,
          sourcePages: [event.page],
          kind: "manual_page",
          narrativeText: assistantContent,
          currentQuestion: currentUserQuestionRef.current,
        };
        attachWorkbenchItemToLastAssistant(item);
        setToolInProgress(null);
        return assistantContent;
      }

      case "done":
        setIsStreaming(false);
        setToolInProgress(null);
        updateLastAssistantMessage({ isStreaming: false });
        currentAssistantIdRef.current = null;
        currentUserQuestionRef.current = "";
        return assistantContent;

      case "error":
        setIsStreaming(false);
        setToolInProgress(null);
        currentAssistantIdRef.current = null;
        currentUserQuestionRef.current = "";
        return assistantContent;
    }
  }, [
    attachWorkbenchItemToLastAssistant,
    createId,
    syncActiveWorkbenchNarrative,
    updateLastAssistantMessage,
  ]);

  const sendMessage = useCallback(async (text: string) => {
    if (isStreaming) return;

    const userMessageId = createId("user");
    const assistantMessageId = createId("assistant");
    currentAssistantIdRef.current = assistantMessageId;
    currentUserQuestionRef.current = text;
    sseBufferRef.current = "";

    setMessages((prev) => [
      ...prev,
      { id: userMessageId, role: "user", content: text },
      { id: assistantMessageId, role: "assistant", content: "", isStreaming: true },
    ]);
    setIsStreaming(true);
    setToolInProgress(null);

    let assistantContent = "";

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationIdRef.current,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const convId = response.headers.get("X-Conversation-Id");
      if (convId) conversationIdRef.current = convId;

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) {
        throw new Error("Missing response stream");
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        sseBufferRef.current += decoder.decode(value, { stream: true });
        const { events, rest } = parseSSEBuffer(sseBufferRef.current);
        sseBufferRef.current = rest;

        for (const event of events) {
          assistantContent = handleEvent(event, assistantContent);
        }
      }

      if (sseBufferRef.current.trim().startsWith("data: ")) {
        const { events } = parseSSEBuffer(`${sseBufferRef.current}\n\n`);
        sseBufferRef.current = "";
        for (const event of events) {
          assistantContent = handleEvent(event, assistantContent);
        }
      }
    } catch (err) {
      console.error("Stream error:", err);
      updateLastAssistantMessage({
        content: "Something went wrong. Please try again.",
        isStreaming: false,
      });
      currentAssistantIdRef.current = null;
      currentUserQuestionRef.current = "";
    } finally {
      setIsStreaming(false);
      setToolInProgress(null);
    }
  }, [createId, handleEvent, isStreaming, updateLastAssistantMessage]);

  const focusWorkbench = useCallback((item?: WorkbenchItem | null) => {
    if (item) {
      setCurrentWorkbenchItem(item);
    }
    setIsWorkbenchOpen(true);
    setIsMobileArtifactSheetOpen(true);
  }, []);

  const closeWorkbench = useCallback(() => {
    setIsWorkbenchOpen(false);
  }, []);

  const closeMobileArtifactSheet = useCallback(() => {
    setIsMobileArtifactSheetOpen(false);
  }, []);

  const clearConversation = useCallback(() => {
    setMessages([]);
    setCurrentWorkbenchItem(null);
    setIsWorkbenchOpen(false);
    setIsMobileArtifactSheetOpen(false);
    conversationIdRef.current = null;
    currentAssistantIdRef.current = null;
    currentUserQuestionRef.current = "";
  }, []);

  return {
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
    clearConversation,
  };
}
