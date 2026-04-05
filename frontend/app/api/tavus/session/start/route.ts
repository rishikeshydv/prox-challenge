import { NextRequest, NextResponse } from "next/server";
import {
  createTavusConversation,
  getTavusEnvStatus,
} from "@/lib/tavus/client";

interface StartSpecialistRequest {
  currentQuestion?: string;
  title?: string;
  sourcePages?: number[];
  process?: string;
  polarity?: string;
  symptom?: string;
  narrativeText?: string;
}

interface SpecialistContextResponse {
  query: string;
  process_filter?: string;
  topic_filter?: string;
  source_pages: number[];
  section_titles: string[];
  facts?: string[];
  snippets: Array<{
    page?: number;
    section?: string;
    content: string;
    type?: string;
  }>;
  tables: Array<{
    page?: number;
    section?: string;
    title?: string;
    preview?: string;
  }>;
}

async function fetchKnowledgeContext(input: StartSpecialistRequest) {
  const backendBaseUrl =
    process.env.BACKEND_API_BASE_URL ?? "http://127.0.0.1:8000";

  const response = await fetch(`${backendBaseUrl}/api/specialist-context`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_question: input.currentQuestion,
      title: input.title,
      source_pages: input.sourcePages,
      process: input.process,
      polarity: input.polarity,
      symptom: input.symptom,
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    const details = await response.text();
    throw new Error(`Knowledge context failed: ${response.status} ${details}`);
  }

  return (await response.json()) as SpecialistContextResponse;
}

function buildConversationalContext(
  input: StartSpecialistRequest,
  knowledge: SpecialistContextResponse,
) {
  const lines = [
    "You are a workshop integration specialist helping a welder understand the current setup or troubleshooting artifact.",
    "Be practical, concise, and explain things like you are standing next to the machine.",
    "Use the grounded manual evidence below as the primary source of truth. Do not invent details beyond that evidence.",
  ];

  if (input.currentQuestion) {
    lines.push(`Current user question: ${input.currentQuestion}`);
  }
  if (input.title) {
    lines.push(`Current workbench item: ${input.title}`);
  }
  if (input.process) {
    lines.push(`Process: ${input.process}`);
  }
  if (input.polarity) {
    lines.push(`Polarity: ${input.polarity}`);
  }
  if (input.symptom) {
    lines.push(`Troubleshooting symptom: ${input.symptom}`);
  }
  if (knowledge.source_pages.length > 0) {
    lines.push(`Grounded manual pages: ${knowledge.source_pages.join(", ")}`);
  }
  if (knowledge.section_titles.length > 0) {
    lines.push(`Relevant manual sections: ${knowledge.section_titles.join(", ")}`);
  }
  if (knowledge.process_filter) {
    lines.push(`Grounded process scope: ${knowledge.process_filter}`);
  }
  if (knowledge.topic_filter) {
    lines.push(`Grounded topic scope: ${knowledge.topic_filter}`);
  }

  if (knowledge.facts && knowledge.facts.length > 0) {
    lines.push("Canonical manual facts:");
    knowledge.facts.forEach((fact, index) => {
      lines.push(`${index + 1}. ${fact}`);
    });
  }

  if (knowledge.snippets.length > 0) {
    lines.push("Manual evidence snippets:");
    knowledge.snippets.forEach((snippet, index) => {
      lines.push(
        `${index + 1}. [page ${snippet.page ?? "?"}${snippet.section ? ` · ${snippet.section}` : ""}] ${snippet.content}`,
      );
    });
  }

  if (knowledge.tables.length > 0) {
    lines.push("Manual table evidence:");
    knowledge.tables.forEach((table, index) => {
      lines.push(
        `${index + 1}. [page ${table.page ?? "?"}${table.section ? ` · ${table.section}` : ""}] ${table.title || "Table"}: ${table.preview || ""}`,
      );
    });
  }

  lines.push(
    "If the user is asking for setup help, talk them through the highlighted connections one step at a time.",
  );
  lines.push(
    "If the user seems uncertain, restate only the next concrete action instead of repeating a long lecture.",
  );
  lines.push(
    "Treat the assistant explanation summary as secondary context only when it agrees with the manual evidence.",
  );

  if (input.narrativeText) {
    lines.push(`Assistant explanation summary: ${input.narrativeText.slice(0, 1200)}`);
  }

  return lines.join("\n");
}

export async function POST(request: NextRequest) {
  try {
    const body = (await request.json()) as StartSpecialistRequest;
    const envStatus = getTavusEnvStatus();

    if (!envStatus.ready) {
      return NextResponse.json(
        {
          error: `Tavus is not configured. Missing: ${envStatus.missing.join(", ")}`,
        },
        { status: 500 },
      );
    }

    const knowledge = await fetchKnowledgeContext(body);

    const conversation = await createTavusConversation({
      personaId: process.env.TAVUS_PERSONA_ID ?? "",
      replicaId: process.env.TAVUS_REPLICA_ID ?? "",
      callbackUrl: process.env.TAVUS_CALLBACK_URL,
      memoryStore: process.env.TAVUS_MEMORY_STORE,
      documentIds: process.env.TAVUS_DOCUMENT_IDS
        ? process.env.TAVUS_DOCUMENT_IDS.split(",").map((id) => id.trim()).filter(Boolean)
        : undefined,
      conversationName: `${body.title ?? "Workbench"} Specialist Session`,
      conversationalContext: buildConversationalContext(body, knowledge),
      customGreeting:
        "I can help talk you through what is open in the workbench. What part would you like to go through first?",
    });

    return NextResponse.json(conversation);
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to start Tavus specialist session.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
