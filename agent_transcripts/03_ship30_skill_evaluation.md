# Agent Transcript 03: Ship 30 for 30 Skill Engine & Artifact Sandbox
**Date:** 2026-09-05  
**Component:** Ship 30 for 30 Skill Framework, Claude-Style Artifact Protocol, Sandboxed Iframe  
**Agent:** Antigravity (Google DeepMind Advanced Agentic Coding)

---

## 1. Challenge: Translating Unstructured Transcripts into Ship 30 for 30 Format
A common failure mode with naive LLM prompts is producing generic, bulleted summaries that fail to capture the high-retention mechanics of the *Ship 30 for 30* methodology (Dickie Bush & Nicolas Cole).
The prompt required:
- ~1,250 words
- A strong, tension-filled hook in the first 2–3 lines
- Skimmable, short 1-to-3 sentence paragraphs
- Bold anchor words initiating bullets
- Deep tactical grounding in Lenny's guests
- An actionable framework/checklist ending

---

## 2. Iteration on Prompt Engineering & Heuristic Constraints
### Attempt 1 (Baseline):
Standard instruction: "Write a 1250-word essay using Ship 30 for 30 principles."
*Issue:* The model output fluctuated between 400 and 700 words, used long paragraphs, and didn't clearly attribute ideas to specific guests.

### Attempt 2 (Structured Scaffold & Explicit Heuristics):
We updated the prompt template in `backend/app/skills/ship30_writer.py` with explicit structural guardrails:
1. **The Hook:** Start with a counterintuitive growth myth or operational tension.
2. **The Progression:**
   - Section 1: The Invisible Trap (Why standard tactics fail)
   - Section 2: Core Mental Shift (The guest's foundational insight)
   - Section 3: The Step-by-Step Playbook (Tactical implementation)
   - Section 4: Operational Checklist (Immediate execution checklist)
3. **Format Mandates:**
   - Maximum 3 sentences per paragraph.
   - Every bullet must begin with **Bold Anchor Words**.
   - Every major claim must reference the guest (e.g., `As Adam Fishman proved at Lyft...`).
4. **Artifact Wrapping:**
   The output is wrapped in `<artifact type="markdown" title="...">` or `<artifact type="html" title="...">` so the streaming parser automatically routes the essay to the side-by-side Claude-style viewer.

---

## 3. Sandboxed Artifact Security Isolation
Generated HTML/CSS snippets are treated as untrusted user-supplied content:
- **Sanitization:** All raw HTML is passed through `DOMPurify.sanitize()` prior to rendering.
- **Iframe Sandboxing:** Rendered using `sandbox="allow-scripts"` while strictly omitting `allow-same-origin`.
- **Security Invariant:** Even if an artifact executes malicious JavaScript or attempts cross-site scripting, it executes within an opaque, unique null origin and cannot access parent `localStorage`, cookies, or DOM.
