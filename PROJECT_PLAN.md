# MindTrace Project Plan

MindTrace is a personalized AI system for longitudinal mental wellness monitoring and self-reflection. This document details the development roadmap, MVP priorities, phase-by-phase deliverables, and success milestones to ensure a successful final-year B.Tech Computer Science project and a publication-grade research paper.

---

## 1. Project Objectives
*   **Goal 1 (Product):** A polished, calm, privacy-first web application for daily mood check-in, free-form journaling, trend tracking, and low-risk wellness reflection.
*   **Goal 2 (Technical):** A robust FastAPI + React stack, SQL database with a clean schema, secure authentication, and a reproducible local ML/NLP pipeline.
*   **Goal 3 (Research):** A rigorous comparison of a population-level (generic) baseline model versus an individualized (personalized) baseline model for detecting wellness-related deviations, backed by feature ablation studies and statistical testing.

---

## 2. MVP vs. Future Scope

To ensure completion within the academic timeline, features are classified as follows:

| Category | Priority | Features |
| :--- | :--- | :--- |
| **Must Have (MVP)** | High | Secure Auth, Privacy Consent, Journaling, Daily Check-in, local NLP Signal Extraction (Sentiment/Emotion/Topics), Generic Baseline, Personalized Baseline (rolling statistical deviation), Personal Trend Dashboard, "What's Changing?", Explainability Layer, and the Research Evaluation Pipeline. |
| **Should Have** | Medium | Weekly Reflection summaries, Curated Support Activity Library, Uncertainty Calibration (Selective Prediction/Conformal Prediction), Safety Gateway (crisis-word overlay), Researcher/Admin Dashboard, and Simulated User Study. |
| **Optional (Future)** | Low | Voice-to-text journal input, advanced large language model (LLM) summaries, wearable device integrations (sleep/heart rate), and clinician/therapist portal. |

---

## 3. Development Roadmap (Phases 0–12)

The project will proceed in thirteen distinct phases:

### Phase 0: Project Discovery (Current)
*   **Focus:** Workspace analysis, environmental checks, architecture design, schema definition, and methodology alignment.
*   **Deliverables:** `PROJECT_PLAN.md`, `ARCHITECTURE.md`, `PROJECT_RULES.md`, `RESEARCH_METHODOLOGY.md`, `DATA_DICTIONARY.md`.

### Phase 1: Foundation & Setup
*   **Focus:** Backend and frontend structure, database connections, user authentication, and basic tests.
*   **Deliverables:**
    *   Vite + React frontend with Tailwind CSS and routing.
    *   FastAPI backend with directory layout.
    *   SQLAlchemy ORM configured with dual-support (SQLite for local dev, PostgreSQL for production).
    *   JWT auth, user registration, login, and consent workflow.
    *   Docker configuration (`docker-compose.yml`, Dockerfiles) and API health checks.

### Phase 2: Journaling & Check-Ins
*   **Focus:** CRUD operations for journals and daily check-ins, database persistence, and validation.
*   **Deliverables:**
    *   Daily check-in UI (mood slider, checkboxes for optional sleep/work/relationship factors).
    *   Free-form journal entry editor with autosave.
    *   Journal history list with date filters.
    *   Encrypted storage functions for journal texts.

### Phase 3: NLP Pipeline & Signal Extraction
*   **Focus:** Processing journal texts to extract embeddings, emotions, sentiments, and topics locally.
*   **Deliverables:**
    *   Local pipeline loading `sentence-transformers/all-MiniLM-L6-v2` for embeddings.
    *   Classifier model (Scikit-Learn/PyTorch) mapping embeddings to GoEmotions categories.
    *   PII-aware text preprocessing script (redacting names, phone numbers, emails before analysis).
    *   Database storing derived signals separately from raw text.

### Phase 4: Generic Baseline (Model A)
*   **Focus:** Designing and implementing the population-level deviation detection model.
*   **Deliverables:**
    *   Model A processor implementing static thresholds (e.g., flag if work stress > 0.70).
    *   API endpoint returning generic deviation flags.
    *   Unit tests validating model behaviour on dummy data.

### Phase 5: Personalized Model (Model B)
*   **Focus:** Designing and implementing the individualized baseline model.
*   **Deliverables:**
    *   Model B processor implementing sliding-window means ($\mu_i$), standard deviations ($\sigma_i$), and rolling Z-score / CUSUM calculations per user.
    *   Dynamic deviation detection that flags outliers relative to user-specific baselines.
    *   API endpoint returning personalized deviation flags.

### Phase 6: Research & Evaluation Pipeline
*   **Focus:** Creating a reproducible environment to run experiments, log results, and perform statistical evaluations.
*   **Deliverables:**
    *   Dedicated `research/` directory.
    *   Synthetic dataset generation/loading scripts to simulate longitudinal journal histories.
    *   Evaluation scripts running Experiments 1, 2, and 3 (Generic vs. Personalized, window size ablation, feature ablation).
    *   Statistical test executor (t-test / Wilcoxon signed-rank, calibration curve plotter).

### Phase 7: Explainability Layer
*   **Focus:** Generating human-readable, grounded explanations for why a deviation was flagged.
*   **Deliverables:**
    *   Explanation generator that compiles statistical differences (e.g., "Your stress level is 2.1x higher than your last 14-day average").
    *   UI components showing the "What's Changing?" insights panel with bar charts.

### Phase 8: Weekly Reflection & Support Library
*   **Focus:** Compiling weekly summaries and displaying curated support exercises.
*   **Deliverables:**
    *   Weekly reflection aggregator (combining daily factors and text trends).
    *   Support Library interface offering specific exercises (e.g., Box Breathing, Thought Journaling) based on the flagged deviation categories.

### Phase 9: Safety Gateway
*   **Focus:** Implementing a secure keyword-based crisis detection system that displays immediate resource lists.
*   **Deliverables:**
    *   Deterministic, high-recall safety regex and keyword scanner.
    *   Safety resource overlay UI with national helplines and trusted contact cards.
    *   Opt-in trusted contact registration form.

### Phase 10: UI/UX Polish & Refinement
*   **Focus:** Polishing CSS styles, adding animations, handling loading states, and ensuring mobile responsiveness.
*   **Deliverables:**
    *   Tailwind styling audit, color palette verification (calm, accessible greens/blues).
    *   Responsive layouts for mobile viewports.
    *   Detailed error boundaries and fallback states.

### Phase 11: Researcher Dashboard
*   **Focus:** Building a separate, password-protected administrative route for displaying aggregated research metrics.
*   **Deliverables:**
    *   Anonymized, aggregate dashboard showing overall model accuracy, false-positive rates, and ablation charts.
    *   *Zero raw text leakage policy* enforced by design.

### Phase 12: Final Validation
*   **Focus:** End-to-end testing, security checks, and final performance reporting.
*   **Deliverables:**
    *   Full test suite coverage (frontend, backend, ML).
    *   `FINAL_VALIDATION.md` containing final metrics, system performance, known limitations, and viva-ready Q&As.

---

## 4. Key Milestones & Timeline

```
Milestone 1: Project Plan & Arch Approved ──> [Completed]
Milestone 2: Foundation & Journaling Auth ──> Weeks 1-2
Milestone 3: Local NLP & Baseline Models  ──> Weeks 3-4
Milestone 4: Evaluation & Research Run    ──> Weeks 5-6
Milestone 5: Reflection, Safety & Polish   ──> Weeks 7-8
Milestone 6: Final Validation & Thesis    ──> Week 9
```

---

## 5. Risk Assessment & Mitigation

1.  **Risk:** PostgreSQL configuration difficulties on local development machines or within the evaluation environment.
    *   *Mitigation:* Utilize SQLAlchemy with an abstraction layer that uses local SQLite (`mindtrace.db`) for local development and PostgreSQL for production.
2.  **Risk:** Sensitive participant data collection and IRB/Ethics approval delays.
    *   *Mitigation:* Base the research paper evaluation on a combination of a public, anonymized NLP dataset (e.g., GoEmotions for signal extraction validation) and a programmatically simulated synthetic longitudinal dataset modeling user behavior patterns over time. Real participant evaluation can be marked as opt-in/future work.
3.  **Risk:** Computational resource limitations on local machines when running large models.
    *   *Mitigation:* Restrict the embedding model to `all-MiniLM-L6-v2` (384-dimensional vectors, ~80MB disk size), which runs extremely fast even on older laptop CPUs. Avoid LLMs for primary signal extraction.
4.  **Risk:** False positives causing alarm.
    *   *Mitigation:* Build a calibration layer that requires minimum duration (e.g., 3 consecutive days of high stress) and statistical confidence before triggering wellness warnings, and present all flags as suggestions for self-reflection rather than diagnostic claims.
