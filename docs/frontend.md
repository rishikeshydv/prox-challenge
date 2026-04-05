# Frontend

## Layout

### Desktop (≥1024px)
```
┌─────────────────┬────────────────────────┐
│                 │                        │
│   Chat Pane     │   Artifact Pane        │
│   (60% width)   │   (40% width)          │
│                 │                        │
│   Messages      │   Rendered artifact    │
│   + input bar   │   in sandboxed iframe  │
│                 │                        │
│                 │   Source: Pages 14-15   │
└─────────────────┴────────────────────────┘
```

### Mobile (<1024px)
Chat pane full width. Artifact slides up from bottom as a drawer/sheet when generated. Close button to dismiss.

## Components

### ChatPane.tsx
- Scrollable message list
- Auto-scroll to bottom on new messages
- Input bar fixed at bottom with send button
- Loading states during tool execution

### MessageBubble.tsx
- User messages: right-aligned, accent background
- Assistant messages: left-aligned, subtle background
- Streaming text: renders incrementally as SSE tokens arrive
- Tool status badges: "Searching manual..." / "Building diagram..."

### ArtifactPane.tsx
```tsx
function ArtifactPane({ artifact }: { artifact: Artifact | null }) {
  if (!artifact) return <EmptyArtifactState />;

  return (
    <div className="artifact-pane">
      <div className="artifact-header">
        <h3>{artifact.title}</h3>
        <button onClick={onClose}>×</button>
      </div>
      <iframe
        srcDoc={artifact.html}
        sandbox="allow-scripts"
        style={{ width: "100%", height: "100%", border: "none" }}
        title={artifact.title}
      />
      <div className="source-badge">
        Based on pages {artifact.sourcePages.join(", ")}
      </div>
    </div>
  );
}
```

Key: `sandbox="allow-scripts"` allows JS execution but blocks navigation, form submission, and access to parent frame.

### SourceBadge.tsx
- Small pill/badge showing "Pages 14-15"
- Positioned below the artifact
- Muted styling, informational

### WelcomeScreen.tsx
Shown when no messages exist. Contains:
- Product name and brief description
- Clickable example questions that auto-send:
  - "What polarity do I need for TIG welding?"
  - "What's the duty cycle at 200A on 240V?"
  - "I'm getting porosity in my flux-cored welds"
  - "What settings for 1/8" mild steel with MIG?"
  - "Show me how to set up the wire feed"

### LoadingIndicator.tsx
- Shown during tool execution
- Displays tool-specific messages:
  - `search_manual` → "Searching manual..."
  - `render_polarity_diagram` → "Building setup diagram..."
  - `render_duty_cycle_calculator` → "Building duty cycle calculator..."
  - `render_troubleshooting_flow` → "Building troubleshooting guide..."
  - `render_settings_configurator` → "Building settings recommendation..."
  - `get_manual_page_image` → "Loading manual page..."
- Subtle animation (pulsing dot or spinner)

## SSE Protocol

### Endpoint
`POST /api/chat`

Request body:
```json
{
  "message": "What polarity do I need for TIG?",
  "conversation_id": "uuid-optional"
}
```

### Event Types

```typescript
type SSEEvent =
  | { type: "text_delta"; content: string }
  | { type: "tool_start"; tool: string }
  | { type: "artifact"; html: string; title: string; pages: number[] }
  | { type: "manual_page"; image_b64: string; page: number }
  | { type: "done" }
  | { type: "error"; message: string }
```

### Hook: useAgentStream.ts

```typescript
function useAgentStream() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentArtifact, setCurrentArtifact] = useState<Artifact | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toolInProgress, setToolInProgress] = useState<string | null>(null);

  async function sendMessage(text: string) {
    // Add user message
    setMessages(prev => [...prev, { role: "user", content: text }]);
    setIsStreaming(true);

    // Start assistant message
    let assistantContent = "";
    setMessages(prev => [...prev, { role: "assistant", content: "" }]);

    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const events = parseSSE(chunk);

      for (const event of events) {
        switch (event.type) {
          case "text_delta":
            assistantContent += event.content;
            updateLastMessage(assistantContent);
            break;
          case "tool_start":
            setToolInProgress(event.tool);
            break;
          case "artifact":
            setCurrentArtifact({
              html: event.html,
              title: event.title,
              sourcePages: event.pages
            });
            setToolInProgress(null);
            break;
          case "manual_page":
            // Handle manual page display
            setToolInProgress(null);
            break;
          case "done":
            setIsStreaming(false);
            setToolInProgress(null);
            break;
          case "error":
            setIsStreaming(false);
            setToolInProgress(null);
            break;
        }
      }
    }
  }

  return { messages, currentArtifact, isStreaming, toolInProgress, sendMessage };
}
```

## State Types

```typescript
interface Message {
  role: "user" | "assistant";
  content: string;
  artifact?: Artifact;
  manualPage?: ManualPage;
}

interface Artifact {
  html: string;
  title: string;
  sourcePages: number[];
}

interface ManualPage {
  imageBase64: string;
  pageNumber: number;
  highlight?: string;
}
```

## Styling

- Use Tailwind CSS for layout and spacing
- Dark theme matching artifact design system:
  - App background: `#0a0a0a` or `#0d1117`
  - Chat background: slightly lighter `#111`
  - User bubbles: accent blue `#1e3a5f`
  - Assistant bubbles: `#1a1a2e`
  - Input bar: `#1a1a2e` with `#333` border
- Smooth transitions for artifact pane appearing/disappearing
- Responsive breakpoint at 1024px

## Animations

- Artifact pane: slide in from right (desktop) or bottom (mobile)
- Messages: subtle fade-in
- Loading indicator: pulsing opacity
- Text streaming: no animation needed, just append
