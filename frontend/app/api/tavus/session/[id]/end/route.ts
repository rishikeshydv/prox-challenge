import { NextRequest, NextResponse } from "next/server";
import { endTavusConversation, getTavusEnvStatus } from "@/lib/tavus/client";

export async function POST(
  _request: NextRequest,
  { params }: { params: { id: string } },
) {
  try {
    const envStatus = getTavusEnvStatus();

    if (!envStatus.ready) {
      return NextResponse.json(
        {
          error: `Tavus is not configured. Missing: ${envStatus.missing.join(", ")}`,
        },
        { status: 500 },
      );
    }

    await endTavusConversation(params.id);
    return NextResponse.json({ status: "ended" });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Failed to end Tavus specialist session.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
