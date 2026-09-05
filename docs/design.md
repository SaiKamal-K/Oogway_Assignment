# Design Specification
## Project: The Lenny Growth Assistant
**Framework:** Next.js 14 App Router, Tailwind CSS, Lucide Icons, DOMPurify

---

## 1. Design Philosophy & Aesthetic Principles

1. **Executive Clarity & Focus:** Designed for growth leaders and product executives who need dense, actionable insights quickly. Clean typography, generous white-space, subtle borders, and harmonious neutrals (`slate-900`, `zinc-800`, `amber-500` accents).
2. **Dual-Pane Workstation:** A side-by-side split layout inspired by modern AI work environments (e.g., Claude Artifacts). Chat on the left for contextual dialogue; Artifact drawer on the right for long-form essays, checklists, and rendered HTML/CSS tools.
3. **Transparent Grounding:** Every claim is explicitly backed by citation chips. Clicking a citation chip expands a drawer revealing exact timestamp references, podcast title, guest bio, and source transcript excerpts.
4. **Live Visual Artifacts:** Real-time rendering of generated artifacts with preview vs. code toggling, one-click copying, and file export.

---

## 2. Layout Structure & Breakpoints

```
+-----------------------------------------------------------------------------------------+
| [Header] Lenny Growth Assistant | Model Toggle: [Ollama: llama3.1:8b v] | Health: [● Active] |
+-----------------------+------------------------------------+----------------------------+
| [Sidebar]             | [Chat Workspace]                   | [Artifact Viewer (Claude)] |
|                       |                                    |                            |
| + New Session         | Mode: [● QA] [★ Ship 30 Essay]     | [Tab: Preview] [Tab: Code] |
|                       |                                    |                            |
| Sessions:             | User: "How does Adam Fishman..."   | [Title: The 100% Onboarding|
| - Onboarding Growth   |                                    |         Leverage Framework]|
| - PLG vs Sales-Led    | Lenny Assistant:                   |                            |
| - PM Competency Model | "According to Adam Fishman..."     | [Sandboxed Iframe or       |
|                       | [Sources: Adam Fishman (00:00:00)] |  Formatted Markdown Essay] |
|                       |                                    |                            |
|                       | [ Input Prompt Box               ] | [Actions: Copy | Download] |
+-----------------------+------------------------------------+----------------------------+
```

### 2.1 Responsive Breakpoints
- **Desktop ($\ge 1280\text{px}$):** Three-column layout (Collapsible Sidebar, Chat Workspace 50%, Artifact Viewer 50%).
- **Laptop ($1024\text{px} - 1279\text{px}$):** Two-column layout with sidebar tucked into a slide-over drawer; Chat and Artifact viewer split 50/50.
- **Tablet & Mobile ($< 1024\text{px}$):** Full-width chat view with artifact opening as an animated bottom drawer or full-screen overlay tab.

---

## 3. Component Hierarchy & Design Tokens

### 3.1 Design Tokens
- **Font Stack:** Primary: `Inter`, system-ui, -apple-system. Monospace: `JetBrains Mono`, `Fira Code`, monospace.
- **Colors:**
  - Background Base: `#0f172a` (Slate 950) / `#ffffff` (Light Mode)
  - Surface Card: `#1e293b` (Slate 800) / `#f8fafc` (Slate 50)
  - Primary Accent: `#f59e0b` (Amber 500 - Lenny's signature yellow/amber branding)
  - Secondary Accent: `#10b981` (Emerald 500 - Verification & Grounding indicators)
  - Border: `#334155` (Slate 700) / `#e2e8f0` (Slate 200)

### 3.2 Key Components
1. **`Header`**: Displays branding, model routing dropdown (Ollama vs. Claude 3.5 Sonnet vs. OpenAI), and real-time backend/database/vector health indicator badge.
2. **`Sidebar`**: Manages session state (New chat, historical sessions, delete sessions).
3. **`ChatPane`**: Renders message bubbles, streaming cursor indicator, citation pills, and prompt composition input.
4. **`ModelSelector`**: Dropdown showing available models, local Ollama latency estimates, and cloud fallback options.
5. **`ArtifactViewer`**:
   - Header with artifact title, type badge (`Markdown` or `HTML`), preview/code tabs, copy button, and close toggle.
   - Body hosting either `react-markdown` with code syntax highlighting or `SandboxedIframe`.
6. **`SandboxedIframe`**: Uses `DOMPurify` to sanitize HTML/CSS, embedded with `sandbox="allow-scripts"` to strictly prohibit parent window access.

---

## 4. Accessibility & Interaction States

1. **Keyboard Accessibility:**
   - `Enter` submits prompt; `Shift + Enter` inserts newline.
   - `Esc` closes expanded citation drawer or artifact modal.
2. **Screen Reader Support:**
   - ARIA roles on all interactive tabs (`role="tablist"`, `role="tab"`).
   - Clear accessible labels on model dropdowns and action buttons.
3. **Loading & Streaming States:**
   - Animated pulse on citation badge during retrieval phase.
   - Smooth token-by-token character streaming with blinking caret.
   - Error toast notifications when Ollama connection or cloud keys are invalid.
