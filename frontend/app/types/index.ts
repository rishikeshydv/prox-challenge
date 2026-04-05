export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  workbenchItem?: WorkbenchItem;
  isStreaming?: boolean;
}

export interface WorkbenchItemBase {
  id: string;
  sourceMessageId: string;
  title: string;
  sourcePages: number[];
  kind: string;
  narrativeText?: string;
  currentQuestion?: string;
  process?: string;
  polarity?: string;
  symptom?: string;
}

export interface ArtifactWorkbenchItem extends WorkbenchItemBase {
  view: "artifact";
  html: string;
}

export interface ManualPageWorkbenchItem extends WorkbenchItemBase {
  view: "manual_page";
  imageBase64: string;
  pageNumber: number;
  highlight?: string;
}

export type WorkbenchItem = ArtifactWorkbenchItem | ManualPageWorkbenchItem;

export type SSEEvent =
  | { type: "text_delta"; content: string }
  | { type: "tool_start"; tool: string }
  | {
      type: "artifact";
      html: string;
      title: string;
      pages: number[];
      kind?: string;
      metadata?: {
        process?: string;
        polarity?: string;
        symptom?: string;
      };
    }
  | { type: "manual_page"; image_b64: string; page: number; highlight?: string }
  | { type: "done" }
  | { type: "error"; message: string };
