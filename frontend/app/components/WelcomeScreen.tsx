"use client";

const WORKFLOWS = [
  {
    label: "Set Up",
    eyebrow: "Connections and polarity",
    description: "Get the right socket, cable routing, gas notes, and process setup before you strike an arc.",
    prompt: "What polarity do I need for TIG welding?",
  },
  {
    label: "Troubleshoot",
    eyebrow: "Defects and symptoms",
    description: "Walk through porosity, spatter, arc instability, bird-nesting, and other garage-floor problems.",
    prompt: "I'm getting porosity in my flux-cored welds. What should I check?",
  },
  {
    label: "Find Settings",
    eyebrow: "Material and thickness",
    description: "Surface recommended settings for wire, gas, voltage, amperage, and thickness-dependent choices.",
    prompt: 'What settings should I use for 1/8" mild steel with MIG?',
  },
  {
    label: "Inspect Manual",
    eyebrow: "Exact manual pages",
    description: "Pin the front panel, wire feed mechanism, diagrams, and troubleshooting pages in the workbench.",
    prompt: "Show me the front panel controls.",
  },
];

const QUICK_PROMPTS = [
  "Show me how to set up the wire feed",
  "What's the duty cycle at 200A on 240V?",
  "Surface the manual page for the front panel",
];

interface Props {
  onQuestion: (q: string) => void;
}

export function WelcomeScreen({ onQuestion }: Props) {
  return (
    <div className="px-1 py-2">
      <div className="rounded-[30px] border border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,#ffffff,#f6f8fb)] p-6 shadow-[0_24px_60px_rgba(15,23,42,0.08)]">
        <div className="max-w-3xl">
          <div className="inline-flex items-center rounded-full border border-[rgba(184,92,22,0.16)] bg-[rgba(247,178,103,0.12)] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-[#b85c16]">
            Start With a Workflow
          </div>
          <h2 className="mt-4 text-3xl font-semibold tracking-[-0.03em] text-[#152030]">
            Built for the moment when you&apos;re standing in the garage and need the answer fast.
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-[#657487]">
            This assistant is strongest when the answer needs a diagram, an exact manual page,
            or a grounded troubleshooting path. Pick a lane below or fire off your own question.
          </p>
        </div>

        <div className="mt-8 grid gap-4 lg:grid-cols-2">
          {WORKFLOWS.map((workflow) => (
            <button
              key={workflow.label}
              onClick={() => onQuestion(workflow.prompt)}
              className="group rounded-[24px] border border-[rgba(15,23,42,0.08)] bg-[linear-gradient(180deg,#ffffff,#f8fafc)] p-5 text-left transition hover:border-[rgba(54,113,201,0.18)] hover:shadow-[0_18px_40px_rgba(37,88,168,0.08)]"
            >
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-[#6d7d90]">
                {workflow.eyebrow}
              </div>
              <div className="mt-2 text-xl font-semibold text-[#152030]">{workflow.label}</div>
              <p className="mt-3 text-sm leading-6 text-[#627185]">{workflow.description}</p>
              <div className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#2455a6]">
                Try this prompt
                <span className="transition group-hover:translate-x-1">→</span>
              </div>
              <div className="mt-3 rounded-[18px] bg-[rgba(36,85,166,0.06)] px-4 py-3 text-sm text-[#25415f]">
                {workflow.prompt}
              </div>
            </button>
          ))}
        </div>

        <div className="mt-8 flex flex-wrap gap-3">
          {QUICK_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => onQuestion(prompt)}
              className="rounded-full border border-[rgba(15,23,42,0.08)] bg-white px-4 py-2 text-sm font-medium text-[#334155] transition hover:border-[rgba(54,113,201,0.18)] hover:bg-[rgba(54,113,201,0.05)] hover:text-[#2455a6]"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
