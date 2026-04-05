"""
tools.py — Tool definitions (Anthropic API schema format).
"""

TOOLS = [
    {
        "name": "search_manual",
        "description": (
            "Search the Vulcan OmniPro 220 owner's manual. "
            "ALWAYS call this first before answering any technical question. "
            "Returns relevant text, tables, and page references."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Natural language search query. Be specific: "
                        "'TIG polarity setup connections' not just 'TIG'."
                    ),
                },
                "process_filter": {
                    "type": "string",
                    "enum": ["MIG", "TIG", "Stick", "Flux-Cored"],
                    "description": "Optional: filter results to a specific welding process.",
                },
                "topic_filter": {
                    "type": "string",
                    "enum": [
                        "setup",
                        "polarity",
                        "troubleshooting",
                        "safety",
                        "duty-cycle",
                        "specifications",
                        "parts",
                        "maintenance",
                        "wiring",
                    ],
                    "description": "Optional: filter results to a specific topic.",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_manual_page_image",
        "description": (
            "Retrieve and display a specific manual page as an image. "
            "Use when the user explicitly asks to see the manual page or when the manual image carries "
            "unique visual detail that a generated artifact cannot replace. "
            "Also use for parts diagrams, wiring schematics, and weld diagnosis photos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "page_number": {
                    "type": "integer",
                    "description": "The manual page number to retrieve.",
                },
                "highlight_region": {
                    "type": "string",
                    "description": "Optional: describe the region to highlight.",
                },
            },
            "required": ["page_number"],
        },
    },
    {
        "name": "render_polarity_diagram",
        "description": (
            "Generate an SVG diagram showing cable-to-socket connections for a welding process. "
            "Use when the user asks about setup, polarity, connections, or 'where does X go'. "
            "ALL connection data must come from search_manual results."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "process": {
                    "type": "string",
                    "enum": ["MIG", "TIG", "Stick", "Flux-Cored"],
                },
                "polarity": {
                    "type": "string",
                    "description": "e.g. 'DCEP (DC Electrode Positive)' or 'DCEN (DC Electrode Negative)'",
                },
                "connections": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "from_component": {"type": "string"},
                            "to_socket": {"type": "string"},
                            "cable_color": {"type": "string"},
                        },
                        "required": ["from_component", "to_socket"],
                    },
                },
                "gas_required": {"type": "boolean"},
                "gas_type": {"type": "string"},
                "notes": {"type": "array", "items": {"type": "string"}},
                "focus_component": {
                    "type": "string",
                    "description": (
                        "Optional: the component the user most cares about, e.g. "
                        "'Ground Clamp' or 'TIG Torch'. Use this when the user asks "
                        "where a specific lead or cable goes."
                    ),
                },
                "focus_socket": {
                    "type": "string",
                    "description": (
                        "Optional: the exact socket that should be visually emphasized."
                    ),
                },
                "focus_note": {
                    "type": "string",
                    "description": (
                        "Optional short callout for the highlighted connection, e.g. "
                        "'Ground clamp goes to the positive (+) Dinse connector'."
                    ),
                },
                "source_pages": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["process", "polarity", "connections", "source_pages"],
        },
    },
    {
        "name": "render_duty_cycle_calculator",
        "description": (
            "Generate an interactive duty cycle lookup widget. "
            "Use when users ask about duty cycle, how long they can weld, or amperage limits. "
            "ALL data must come from manual's duty cycle tables."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "duty_cycle_data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "voltage_input": {"type": "string", "enum": ["120V", "240V"]},
                            "process": {"type": "string"},
                            "amperage": {"type": "number"},
                            "voltage_output": {"type": "number"},
                            "duty_cycle_percent": {"type": "number"},
                        },
                        "required": ["voltage_input", "process", "amperage", "duty_cycle_percent"],
                    },
                },
                "source_pages": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["duty_cycle_data", "source_pages"],
        },
    },
    {
        "name": "render_troubleshooting_flow",
        "description": (
            "Generate an interactive troubleshooting flowchart. "
            "Use when users describe weld defects, problems, or symptoms. "
            "Build the decision tree from the manual's troubleshooting section."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "symptom": {"type": "string"},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "type": {"type": "string", "enum": ["question", "fix", "check"]},
                            "text": {"type": "string"},
                            "yes_next": {"type": "string"},
                            "no_next": {"type": "string"},
                            "fix_text": {"type": "string"},
                        },
                        "required": ["id", "type", "text"],
                    },
                },
                "source_pages": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["symptom", "steps", "source_pages"],
        },
    },
    {
        "name": "render_settings_configurator",
        "description": (
            "Generate a settings recommendation widget. "
            "Use when users ask what settings for a material, thickness, or process. "
            "ALL values must come from the manual."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "process": {"type": "string"},
                "material": {"type": "string"},
                "thickness_range": {"type": "string"},
                "settings_options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "voltage": {"type": "string"},
                            "wire_speed": {"type": "string"},
                            "amperage": {"type": "string"},
                            "gas_type": {"type": "string"},
                            "gas_flow_rate": {"type": "string"},
                            "wire_type": {"type": "string"},
                            "wire_diameter": {"type": "string"},
                        },
                    },
                },
                "tips": {"type": "array", "items": {"type": "string"}},
                "source_pages": {"type": "array", "items": {"type": "integer"}},
            },
            "required": ["process", "settings_options", "source_pages"],
        },
    },
]
