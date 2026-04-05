# Testing

## Challenge Questions

These must all be answered correctly. They come directly from the challenge brief or test cross-referencing, visual understanding, and response mode selection.

### Tier 1 — Direct Challenge Questions

```
"What's the duty cycle for MIG welding at 200A on 240V?"
→ Expected: exact number from manual + duty cycle calculator artifact

"I'm getting porosity in my flux-cored welds. What should I check?"
→ Expected: troubleshooting flow artifact with diagnostic steps from manual

"What polarity setup do I need for TIG welding? Which socket does the ground clamp go in?"
→ Expected: polarity diagram showing DCEN, torch to negative, clamp to positive
```

### Tier 2 — Cross-Referencing

```
"Can I run this welder on a 15-amp household circuit?"
→ Must cross-reference input power specs + circuit breaker requirements

"What's the difference in setup between MIG and flux-cored on this machine?"
→ Must compare polarity, gas requirements, wire type across two process sections

"If I switch from MIG to TIG, what do I need to change on the machine?"
→ Must cover polarity swap, lead connections, gas setup, process selection
```

### Tier 3 — Visual/Diagram Questions

```
"Show me how to thread the wire through the drive rolls"
→ Should show manual page or diagram of wire feed mechanism

"Where do I connect the gas line?"
→ Polarity diagram with gas connection highlighted

"What does the front panel look like?"
→ Manual page showing front panel
```

### Tier 4 — Settings Questions

```
"What settings should I use for welding 16-gauge sheet metal with MIG?"
→ Settings configurator with manual-backed values

"I'm welding 1/4 inch steel plate — what process and settings do you recommend?"
→ Should recommend process + settings configurator

"What wire size should I use for thin sheet metal?"
→ Text answer or settings configurator depending on specificity
```

### Tier 5 — Troubleshooting

```
"The wire keeps bird-nesting at the drive rolls, what's wrong?"
→ Troubleshooting flow: tension, liner, tip size, feed roll alignment

"My arc keeps cutting out, what should I check?"
→ Troubleshooting flow: power, ground connection, wire feed, tip contact

"Welds are spattering excessively, how do I fix this?"
→ Troubleshooting flow: voltage, wire speed, gas flow, contact tip
```

### Tier 6 — Ambiguous (Should Trigger Clarification)

```
"My welds look bad"
→ Should ask: what process, what does the defect look like

"This thing isn't working right"
→ Should ask: what specifically is happening

"What settings should I use?"
→ Should ask: what process, material, thickness
```

## Quality Checklist

For each response, verify:

### Accuracy
- [ ] Answer is factually correct per the manual
- [ ] No hallucinated specifications, settings, or part names
- [ ] Numbers match the manual exactly (duty cycles, amperages, voltages)
- [ ] Connection/polarity information matches manual diagrams
- [ ] Source pages cited are the correct pages

### Response Mode
- [ ] Appropriate mode chosen (text vs diagram vs calculator vs flow)
- [ ] Artifacts generated when they should be (not text-only for visual questions)
- [ ] Text-only used appropriately (not generating artifacts for simple questions)
- [ ] Clarification asked when question is genuinely ambiguous

### Artifact Quality
- [ ] Artifact renders correctly in iframe
- [ ] Interactive elements work (dropdowns, buttons, navigation)
- [ ] Data displayed matches what was retrieved from manual
- [ ] Source pages badge is visible and accurate
- [ ] Visual design is clean and consistent with design system

### Tone and Helpfulness
- [ ] Direct and specific language
- [ ] No unnecessary hedging or filler
- [ ] Safety warnings surfaced when relevant
- [ ] Practical enough for someone in their garage
- [ ] Text alongside artifacts is concise (artifact is the main payload)

### Edge Cases
- [ ] Handles questions outside the manual scope gracefully ("I don't have info on that")
- [ ] Doesn't crash on unusual inputs
- [ ] Multiple tool calls in sequence work correctly
- [ ] Conversation context maintained across turns
- [ ] Follow-up questions work ("What about for TIG?" after a MIG answer)

## Test Script

```python
# scripts/test_queries.py

import asyncio
import httpx

QUERIES = [
    "What's the duty cycle for MIG welding at 200A on 240V?",
    "What polarity setup do I need for TIG welding?",
    "I'm getting porosity in my flux-cored welds. What should I check?",
    "What settings should I use for 1/8 inch mild steel with MIG?",
    "Show me the wire feed mechanism",
    "My welds look bad",
]

async def test_query(client: httpx.AsyncClient, query: str):
    print(f"\n{'='*60}")
    print(f"QUERY: {query}")
    print(f"{'='*60}")

    async with client.stream("POST", "http://localhost:8000/api/chat",
                             json={"message": query}) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                if data["type"] == "text_delta":
                    print(data["content"], end="", flush=True)
                elif data["type"] == "artifact":
                    print(f"\n[ARTIFACT: {data['title']} | Pages: {data['pages']}]")
                elif data["type"] == "tool_start":
                    print(f"\n[TOOL: {data['tool']}]")

    print()

async def main():
    async with httpx.AsyncClient(timeout=60) as client:
        for query in QUERIES:
            await test_query(client, query)

asyncio.run(main())
```
