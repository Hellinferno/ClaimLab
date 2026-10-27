# ClaimLab — Meta Global AI Developer Hackathon Submission Kit

**Repository:** [https://github.com/Hellinferno/ClaimLab.git](https://github.com/Hellinferno/ClaimLab.git)  
**Branch:** `main`  
**License:** MIT  
**Target Model:** Meta `muse-spark-1.3` (Live Function Calling & Orchestration)  
**Verification Status:** 27/27 Pytest Tests Passed · 12/12 Behavioral Benchmark Cases Passed (100%)

---

## 1. Hackathon Portal Form Fields

### Project Name
**ClaimLab**

### Tagline / Short Pitch (under 120 chars)
*Source-grounded whiteboard teacher with live numerical attention experiments powered by Meta's muse-spark-1.3.*

### Track
*Meta Global AI Developer Hackathon — Developer Tools & Education Track*

### Primary Technology & Meta AI Backbone
- **Meta AI Model:** `muse-spark-1.3`
- **Model Role:** Bounded agentic teaching coordinator executing tool loops for citation retrieval (`get_source_excerpt`), numerical lab execution (`run_experiment`), and whiteboard state changes (`present_teaching_step`).
- **Backend:** Python 3.12, FastAPI, SQLite (WAL mode), SQLAlchemy 2.0, NumPy, PyPDF.
- **Frontend:** React 19, TypeScript, Vite, KaTeX, Tailwind/CSS custom cyber-matrix canvas.

---

## 2. Long Description & Technical Narrative

### The Problem
Most AI-assisted STEM learning systems suffer from two fatal flaws:
1. **Unverifiable Hallucinated Calculations:** When explaining complex neural mechanisms (e.g., softmax saturation or attention variance), LLMs generate plausible-looking prose or hardcoded numbers rather than actually computing the math.
2. **Passive, Unanchored Chat Interfaces:** Students scroll through endless text without spatial intuition, without grounding back to the original research papers, and without adaptive follow-up tasks that test genuine understanding.

### The ClaimLab Solution
ClaimLab transforms technical paper reading into an interactive, empirically verified research laboratory built around three foundational pillars:

1. **Source-Grounded Shared Whiteboard:**
   Students upload technical literature (such as *Attention Is All You Need*). ClaimLab performs page-bounded extraction, generates cryptographic character anchors, and builds an atomic SVG whiteboard where concepts, mathematical derivations (rendered in KaTeX), and empirical plots are linked directly to source quotes.

2. **Verified Numerical Attention Labs (No Hallucinated Math):**
   ClaimLab executes real, sandboxed numerical calculations across three canonical attention recipes:
   - **Recipe A (Softmax Sensitivity):** Proves shift invariance $\text{softmax}(z + c) = \text{softmax}(z)$ and entropy collapse under logit scaling.
   - **Recipe B (Dimension Scaling):** Proves $\text{Var}(q \cdot k^T) \approx d_k$ for $q, k \sim \mathcal{N}(0, I)$, and verifies how dividing by $\sqrt{d_k}$ stabilizes score variance to $\approx 1.0$.
   - **Recipe C (Causal Masking):** Proves strict future masking with lower-triangular probability distribution matrices.
   *Every single chart and metric shown to the student originates from retained NumPy execution outputs with independent mathematical oracle checks.*

3. **Evidence-Based Observation & Pedagogical Adaptation:**
   ClaimLab tracks semantic learner events (predictions, formula evaluations, connections). It implements the strict **Two-Variant Progression Rule**: a student cannot achieve `supported_independently` status without succeeding on two distinct application variants. When misconceptions or calculation errors occur, ClaimLab dynamically adapts, offering prerequisite scaffolding before advancing.

---

## 3. Meta AI Model Integration (`muse-spark-1.3`)

ClaimLab integrates Meta's `muse-spark-1.3` model through a bounded, stateful tool-dispatch loop:
- **`get_source_excerpt`:** Fetches verified quotes matching student selections to prevent paper hallucination.
- **`run_experiment`:** Triggers deterministic numerical recipes with strict input validation and parameter normalizations.
- **`present_teaching_step`:** Emits pedagogical explanations and atomic whiteboard patches (`add_object`, `highlight_objects`, `update_object`).
- **Budget & Safety Enforcements:** Every turn reserves and settles token usage against an isolated user budget, enforces lease heartbeats, and provides graceful fallback to deterministic fixtures if provider connectivity is lost.

---

## 4. Empirical Verification & Test Evidence

All acceptance criteria across the specification suite pass with 100% verification:

| Verification Suite | Result | Details |
| :--- | :--- | :--- |
| **Complete Pytest Suite** | **27/27 Passed** | Covers auth, atomic whiteboard engine, numerical invariants, CSRF, idempotency, data deletion, and live Meta API calls. |
| **Live Provider Probe (`T-META-01`)** | **PASSED** | Live Meta API round-trip completed in ~2.6s with autonomous tool execution. |
| **Live Orchestrator Loop (`T-META-02`)** | **PASSED** | End-to-end live tutor turn with tool call dispatch and session snapshot. |
| **Official Evaluation Benchmark** | **12/12 Passed (100%)** | All 12 behavioral cases from `docs/12_EVALUATION_HARNESS.md` verified in both live and offline modes. |
| **Ruff Code Quality** | **0 Errors** | Fully formatted and linted Python codebase. |
| **Frontend Production Build** | **0 Errors** | Optimized bundle compiled via Vite/TypeScript in <600ms. |

---

## 5. Three-Minute Demo Walkthrough Script

| Timestamp | Screen / Flow | Narration / Action |
| :--- | :--- | :--- |
| **0:00 – 0:35** | **The Problem & Document Grounding** | Show ClaimLab's cyber-matrix workspace. Guest session initializes automatically with encrypted cookie. Upload `claimlab_attention_lab.pdf`. Select the passage: *"Why do large dot products push softmax into regions with small gradients?"* Note how cryptographic source anchors link directly to the PDF text. |
| **0:35 – 1:30** | **The Live Meta Whiteboard Teacher** | Click *"Begin Lesson"*. Meta's `muse-spark-1.3` receives bounded context, retrieves the anchor quote, and autonomously issues whiteboard patches. An interactive SVG canvas renders Query/Key concept nodes, the LaTeX scaled attention equation, and real-time explanation cards. |
| **1:30 – 2:15** | **Executing the Numerical Lab** | Transition to the Experiment Panel. The tutor triggers **Recipe B (Attention Scaling)** across dimensions $d_k \in \{16, 32, 64, 128\}$. Show the live variance plot: unscaled variance spikes to $128$, while scaled variance remains perfectly stable at $\approx 1.0$. Point out the independent numerical oracle checks (weights sum to $1.0$, strictly finite). |
| **2:15 – 2:45** | **Evidence-Based Adaptation Loop** | The tutor presents an application task: *"A score is 12 and $d_k=16$. What is the scaled score?"* Deliberately submit the unscaled answer `12`. Show ClaimLab detecting the error, classifying the misconception, updating evidence to `needs_check`, and providing scaffolding. Submit the correct answer `3` across two variants to unlock `supported_independently`. |
| **2:45 – 3:00** | **Security & Privacy Purge** | Highlight that keys never enter client code, uploads are private per guest, and click *"Purge My Data"* to demonstrate complete cryptographic deletion of sessions, snapshots, and uploaded files. |

---

## 6. Local Quickstart Instructions

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/Hellinferno/ClaimLab.git
cd ClaimLab

# Python backend setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 2. Configure Environment Variables
Create `.env` in the project root:
```ini
APP_ENV=development
PUBLIC_ORIGIN=http://127.0.0.1:5173
DATABASE_URL=sqlite:///./data/claimlab.db
DATA_DIR=./data
SESSION_SECRET=dev-secret-change-in-production-min-32-chars-long!

MODEL_MODE=live
META_API_KEY=your_actual_meta_api_key
META_BASE_URL=https://api.meta.ai/v1
META_MODEL=muse-spark-1.3
```

### 3. Run Backend & Frontend
```bash
# Terminal 1: Backend API
python -m claimlab.api

# Terminal 2: Frontend Dev Server
cd frontend
npm install
npm run dev
```
Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

### 4. Run Full Verification Suite
```bash
# Pytest (27/27 tests including live Meta probe)
pytest backend/tests

# Behavioral Evaluation Benchmark (12/12 cases)
python -m claimlab.evaluation.benchmark
```
