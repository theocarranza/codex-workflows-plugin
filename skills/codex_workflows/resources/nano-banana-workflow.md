---
description: Nano Banana Workflow: Visual Synthesis & Cognitive Anchoring
---

# Nano Banana Workflow: Visual Synthesis & Cognitive Anchoring

## 🍌 Overview
Nano Banana (Gemini 2.5 Flash Image) is the primary engine for visual synthesis within the Antigravity IDE. It is used to generate UI mockups, architectural diagrams, and cognitive anchors to improve system comprehension.

## 🛠️ Tooling
- **Primary Tool:** `generate_image`
- **Sub-Agent:** Nano Banana (invoked via `generate_image`)
- **Integration:** Cross-model synergy (e.g., Claude/Gemini Pro reasoning + Nano Banana visualization)

## 📋 Operational Rules

### 1. Visual Triggering Protocol
- **Trigger Condition:** Generate a visual asset when a technical description exceeds 3 interpretation paths or involves complex UI/UX transitions.
- **Prompt Engineering:** The reasoning model (Gemini/Claude) must formulate a high-fidelity, descriptive prompt for the `generate_image` tool.
- **Context Injection:** Include specific project themes (colors, typography) from `docs/design-system.md` in the image prompt.

### 2. Cognitive Style-Locking
To optimize long-term mental retrieval, use the following style-locks:
- **Database/Backend:** *Retro Print / Heritage* (Historical Detachment Protocol).
- **Frontend/UI:** *Classic / High-Fidelity* (Modern Aesthetic).
- **Conceptual/Roadmap:** *Watercolor* (Fluidity and Abstract Thinking).
- **Complex Logic:** *Papercraft / Anime* (Cognitive Load Calibration).

### 3. Artifact Management
- **Verification:** All generated images must be visually verified by the agent using the Antigravity Browser Agent if they are part of a UI mockup.
- **Storage:** Save all generated visual assets to `AI_Codex/assets/` and link them in the corresponding Markdown documentation in the Obsidian vault.
- **Naming Convention:** `[YYYYMMDD]-[Project]-[Context]-[Style].png`

### 4. Cross-Style Concept Stress Test
When a core architectural component is modified, perform a "Concept Stress Test" by generating the same diagram across two incompatible styles (e.g., *Heritage* vs. *High-Fidelity*) to expose fragility in the current mental model.

## 🚀 Execution Flow
1. **Analyze:** Identify the need for a visual anchor.
2. **Draft:** Create the image generation prompt using project-specific design tokens.
3. **Execute:** Call `generate_image(prompt: "...")`.
4. **Link:** Insert the resulting artifact into the `.agent/outputs/` and the Obsidian vault.
5. **Verify:** Confirm the visual aligns with the textual architectural logic.
