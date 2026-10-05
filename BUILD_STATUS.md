# Pause AI Student Wellness Companion — Build Status

## 1. Completed Work (Milestone 1: Foundation, DB, Auth, Consent & Private Flows)

- **Application Architecture & Branding**: Aligned the project to the Pause Product & Engineering Specification and Build Brief, adopting the calm visual aesthetic (warm paper `#fbf9f5`, forest green text `#1e3a2f`, soft sage action states `#2d5a47`).
- **Database & Persistence**:
  - Local PostgreSQL 17 cluster configured on port `5434` with database `pause_wellness` (user-space trust configuration, non-blocking and local).
  - Production Docker Compose configuration created with `pgvector/pgvector:pg16` on port `5432`.
  - Schema created: `users`, `consent_records`, `check_ins`, `journal_entries`, `daily_plans`, `wellness_actions`, `saved_actions`, `action_events`, `support_resources`, `audit_events`, and schema hooks for `emotion_analyses` and `entry_embeddings`.
- **Security & Cryptography**:
  - Sensitive journal content is encrypted at rest using application-level AES-256 Fernet envelope encryption (`PAUSE_JOURNAL_ENCRYPTION_KEY`). Decrypted only for the authenticated owner.
  - PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations and 16-byte random salts.
  - JWT token-based session authentication with strict server-derived `user_id` context.
  - Audit logging strictly records security actions (login, export, deletion) without logging journal text, prompts, embeddings, emotion labels, or crisis text.
- **Granular Consent & Onboarding**:
  - Purpose separation: `save_journal` (opt-in), `emotion_analysis` (explicit action only), `embeddings_rag` (explicit opt-in), and `external_inference` (default OFF).
  - Age gating: registration enforces university students aged 18 and older. Minors are barred in this release.
- **Private Core Features**:
  - **Today Check-in**: 5 plain-language moods (Great, Good, Okay, Uneasy, Difficult), 1–5 energy scale, context tags (study, sleep, relationships, health, finances, other), and optional private note.
  - **One-Thing Daily Plan**: Single gentle focus and up to 3 editable, checkable steps with no streaks, productivity scores, or guilt copy.
  - **Reviewed Wellness Catalog**: Seeded 6 reviewed activities (Box Breathing, Micro-Step Task Slicing, 5-4-3-2-1 Grounding, Study-to-Rest Ritual, Reconnect Message, Calm Wind-Down) with accessibility notes, source review versions, context matching, and outcome logging ('helped', 'about the same', 'did not try', 'skip').
  - **Reflections & Trends**: 7-day and 30-day views with visible check-in counts, non-causal language ("In X check-ins tagged Study, you chose Uneasy Y times. This only describes what you recorded"), and insufficient data empty state.
  - **Support Resources**: Verified Indian emergency and mental health helplines: Tele-MANAS (`14416` / `1800-89-14416`), National Emergency (`112`), KIRAN (`1800-599-0019`), and Vandrevala Foundation with verification timestamps and explicit non-monitored notice.
  - **Privacy & Portability**: Machine-readable JSON data export (`/api/v1/privacy/export`) and permanent transactional account deletion (`/api/v1/account`).
  - **Fictional Reviewer Demo**: One-click demo sign-in and seed endpoint (`/api/v1/demo/seed`) generating safe synthetic entries for evaluators (`demo@pause-wellness.local`).
- **Next.js App Router Frontend**:
  - Built with Next.js 14, React 18, TypeScript, and Tailwind CSS.
  - All 12 routes compiled with static optimization: `/`, `/plan`, `/journal`, `/actions`, `/reflections`, `/support`, `/privacy`, `/login`, `/register`.
  - Persistent "Get support now" button visible at all times in the header without needing login or AI.

---

## 2. Run & Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 20+ (Node 24 supported)
- PostgreSQL 17 or Docker

### Local Running (Native Host)

1. **Database**:
   The local PostgreSQL 17 cluster is installed at `c:\finalyearPro\.pgdata` on port `5434`.
   To start it manually if stopped:
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" -D "c:\finalyearPro\.pgdata" -o "-p 5434" -l "c:\finalyearPro\.pgdata\server.log" start
   ```

2. **Backend API**:
   From the repository root:
   ```powershell
   $env:PYTHONPATH="backend"
   .\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   OpenAPI documentation available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

3. **Frontend Application**:
   From the `frontend` directory:
   ```powershell
   cd frontend
   npm run dev
   ```
   Open the application in your browser at [http://localhost:3000](http://localhost:3000).

4. **Reviewer Demo Mode**:
   Click **"One-Click Reviewer Demo Sign In"** on the login screen to automatically seed and log in with safe fictional reflection data.

### Docker Compose Deployment
```bash
docker compose up --build
```
This launches `pause_postgres` (pgvector/pgvector:pg16 on 5432), `pause_backend` (port 8000), and `pause_frontend` (port 3000).

---

## 3. Checks Performed

- **Database Connection**: `asyncpg` connection verified to `postgresql+asyncpg://postgres@localhost:5434/pause_wellness`. Table metadata creation and seed scripts verified.
- **Frontend Production Build**: `npm run build` executed successfully across all 12 Next.js App Router pages with zero syntax, webpack, or static generation errors.
- **Backend Automated Test Suite**:
  - Command: `$env:PYTHONPATH="backend"; .\venv\Scripts\pytest.exe tests/ -v`
  - Results: **8 passed in 5.04s (100% pass rate)**.
  - Tests verified:
    1. `test_health_check`: Operational status without sensitive data leaks.
    2. `test_18_plus_enforcement_and_registration`: Strict age gating rejecting minors and accepting adults.
    3. `test_checkin_flow`: Plain language mood, energy, and context tags.
    4. `test_journal_encryption_and_deletion`: AES-256 Fernet encryption at rest, owner decryption, and cascading deletion.
    5. `test_daily_plan_flow`: One-thing plan with 3 non-punitive steps.
    6. `test_support_resources`: Tele-MANAS, 112, and non-monitored notice.
    7. `test_demo_seed_and_export_and_account_delete`: Fictional data seed, complete JSON export, and full account wipe.
    8. `test_cross_tenant_isolation`: Security attack defense proving User B cannot read, modify, delete, or export User A's data.

---

## 4. Blockers
- **None**: All dependencies, database services, API routes, and frontend compilation succeeded locally without paid APIs.

---

## 5. Next Milestone
- **Milestone 2: Emotion AI Analysis & Evaluation**:
  - Implement server-side English emotion classification adapter (`SamLowe/roberta-base-go_emotions` vs TF-IDF + Logistic Regression baseline).
  - Enforce non-clinical taxonomy (stress/overwhelmed, worry/tense, sad/disappointed, frustrated, lonely/disconnected, calm/relieved, positive/hopeful, neutral, mixed/uncertain).
  - Implement confidence thresholding ("I'm not sure" abstention) and phrase explanation extraction.
  - Add user correction, hiding, and independent deletion UI.
  - Scripted evaluation on held-out student reflection benchmarks.
