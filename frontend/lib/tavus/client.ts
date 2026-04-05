const TAVUS_API_BASE = "https://tavusapi.com/v2";

export interface TavusConversationPayload {
  personaId: string;
  replicaId?: string;
  callbackUrl?: string;
  conversationName?: string;
  conversationalContext?: string;
  customGreeting?: string;
  memoryStore?: string;
  documentIds?: string[];
}

export interface TavusConversationResponse {
  conversationId: string;
  conversationUrl: string;
  metadata?: Record<string, unknown>;
}

function getEnvStatus() {
  const hasApiKey = Boolean(process.env.TAVUS_API_KEY);
  const hasPersonaId = Boolean(process.env.TAVUS_PERSONA_ID);
  const hasReplicaId = Boolean(process.env.TAVUS_REPLICA_ID);

  const missing = [
    !hasApiKey ? "TAVUS_API_KEY" : null,
    !hasPersonaId ? "TAVUS_PERSONA_ID" : null,
    !hasReplicaId ? "TAVUS_REPLICA_ID" : null,
  ].filter(Boolean) as string[];

  return {
    ready: missing.length === 0,
    missing,
  };
}

export function getTavusEnvStatus() {
  return getEnvStatus();
}

export async function createTavusConversation(
  payload: TavusConversationPayload,
): Promise<TavusConversationResponse> {
  const envStatus = getEnvStatus();

  if (!envStatus.ready || !process.env.TAVUS_API_KEY) {
    throw new Error(
      `Tavus real mode is not ready. Missing: ${envStatus.missing.join(", ")}`,
    );
  }

  const response = await fetch(`${TAVUS_API_BASE}/conversations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": process.env.TAVUS_API_KEY,
    },
    body: JSON.stringify({
      persona_id: payload.personaId,
      replica_id: payload.replicaId,
      callback_url: payload.callbackUrl,
      conversation_name:
        payload.conversationName ?? "Workshop Specialist Session",
      conversational_context: payload.conversationalContext,
      custom_greeting: payload.customGreeting,
      memory_stores: payload.memoryStore ? [payload.memoryStore] : undefined,
      document_ids:
        payload.documentIds && payload.documentIds.length > 0
          ? payload.documentIds
          : undefined,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    const details = await response.text();
    throw new Error(`Tavus API returned ${response.status}: ${details}`);
  }

  const data = (await response.json()) as Record<string, unknown>;

  return {
    conversationId: String(
      data.conversation_id ??
        data.conversationId ??
        data.id ??
        `tavus-${crypto.randomUUID()}`,
    ),
    conversationUrl: String(data.conversation_url ?? data.conversationUrl ?? ""),
    metadata: data,
  };
}

export async function endTavusConversation(conversationId: string): Promise<void> {
  const envStatus = getEnvStatus();

  if (!envStatus.ready || !process.env.TAVUS_API_KEY) {
    throw new Error(
      `Tavus real mode is not ready. Missing: ${envStatus.missing.join(", ")}`,
    );
  }

  const response = await fetch(
    `${TAVUS_API_BASE}/conversations/${conversationId}/end`,
    {
      method: "POST",
      headers: {
        "x-api-key": process.env.TAVUS_API_KEY,
      },
      cache: "no-store",
    },
  );

  if (!response.ok) {
    const details = await response.text();
    throw new Error(`Tavus end conversation returned ${response.status}: ${details}`);
  }
}
