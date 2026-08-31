# MindTrace Data Dictionary & Schema Design

This document defines the relational database schema, tables, datatypes, descriptions, relationships, and privacy data classifications for the MindTrace application.

---

## 1. Data Classification Levels
To enforce privacy-by-design, columns are categorized into four sensitivity levels:
*   **[CRITICAL]:** Highly sensitive personal narrative data (PHI/PII). Must be encrypted at rest, excluded from standard application logging, and hidden from the researcher dashboard.
*   **[IDENTIFIABLE]:** Basic user identifiers. Must be protected by secure hashes and isolated.
*   **[SENSITIVE]:** Individual daily check-ins or raw anomaly scores. Protected via authorization gates.
*   **[PUBLIC/SYSTEM]:** General system metadata, system-level lookup values, or aggregated analytics.

---

## 2. Table Definitions

### 2.1. `users`
Stores user authentication details.
*   **Primary Key:** `id` (UUID)
*   **Relations:** One-to-One with `user_preferences`, One-to-Many with `journal_entries`, `daily_checkins`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | **[IDENTIFIABLE]** | Unique identifier for the user. |
| `email` | VARCHAR(255) | **[IDENTIFIABLE]** | User's email address (unique). |
| `password_hash` | VARCHAR(255) | **[IDENTIFIABLE]** | Salted bcrypt password hash. |
| `created_at` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Account creation timestamp. |
| `timezone` | VARCHAR(50) | **[PUBLIC/SYSTEM]** | User's timezone (default: UTC). |

### 2.2. `consent_records`
Logs user privacy consents.
*   **Primary Key:** `id` (INT)
*   **Relations:** Many-to-One with `users`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | **[PUBLIC/SYSTEM]** | Auto-incrementing primary key. |
| `user_id` | UUID | **[IDENTIFIABLE]** | Foreign key linking to `users.id`. |
| `consent_given` | BOOLEAN | **[SENSITIVE]** | True if user accepted the privacy terms. |
| `consent_version` | VARCHAR(10) | **[PUBLIC/SYSTEM]** | Version of the privacy policy accepted. |
| `timestamp` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Timestamp of user consent selection. |

### 2.3. `journal_entries`
Stores user journal texts.
*   **Primary Key:** `id` (UUID)
*   **Relations:** Many-to-One with `users`. One-to-One with `wellness_signals`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | **[PUBLIC/SYSTEM]** | Unique identifier for the journal. |
| `user_id` | UUID | **[IDENTIFIABLE]** | Foreign key linking to `users.id`. |
| `journal_text` | TEXT | **[CRITICAL]** | The raw journal text. Encrypted at rest. |
| `created_at` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Entry creation timestamp. |
| `updated_at` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Last entry modification timestamp. |

### 2.4. `daily_checkins`
Stores daily mood and optional metric ratings.
*   **Primary Key:** `id` (UUID)
*   **Relations:** Many-to-One with `users`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | **[PUBLIC/SYSTEM]** | Unique identifier for the check-in. |
| `user_id` | UUID | **[IDENTIFIABLE]** | Foreign key linking to `users.id`. |
| `mood` | INTEGER | **[SENSITIVE]** | Rated mood score (1: Very Difficult to 5: Very Good). |
| `sleep` | INTEGER | **[SENSITIVE]** | Optional rated sleep score (1-5) or NULL. |
| `academic_work` | BOOLEAN | **[SENSITIVE]** | Checked if work/academic concerns were active. |
| `relationships` | BOOLEAN | **[SENSITIVE]** | Checked if relationship factors were active. |
| `social_life` | BOOLEAN | **[SENSITIVE]** | Checked if social connection factors were active. |
| `health` | BOOLEAN | **[SENSITIVE]** | Checked if health concerns were active. |
| `created_at` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Timestamp of check-in entry. |

### 2.5. `wellness_signals`
Stores NLP-derived features extracted from journals.
*   **Primary Key:** `id` (UUID)
*   **Relations:** Many-to-One with `users`, One-to-One with `journal_entries`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | **[PUBLIC/SYSTEM]** | Unique identifier. |
| `user_id` | UUID | **[IDENTIFIABLE]** | Foreign key linking to `users.id`. |
| `journal_entry_id` | UUID | **[PUBLIC/SYSTEM]** | Foreign key linking to `journal_entries.id`. |
| `sentiment` | FLOAT | **[SENSITIVE]** | Valence score in range [-1.0, 1.0]. |
| `joy` | FLOAT | **[SENSITIVE]** | Probability of Joy emotion [0.0, 1.0]. |
| `sadness` | FLOAT | **[SENSITIVE]** | Probability of Sadness emotion [0.0, 1.0]. |
| `anger` | FLOAT | **[SENSITIVE]** | Probability of Anger emotion [0.0, 1.0]. |
| `fear` | FLOAT | **[SENSITIVE]** | Probability of Fear emotion [0.0, 1.0]. |
| `work_pressure` | FLOAT | **[SENSITIVE]** | Derived workload topic strength [0.0, 1.0]. |
| `sleep_issues` | FLOAT | **[SENSITIVE]** | Derived sleep concerns topic strength [0.0, 1.0]. |
| `social_support` | FLOAT | **[SENSITIVE]** | Derived social support topic strength [0.0, 1.0]. |
| `fatigue` | FLOAT | **[SENSITIVE]** | Derived tiredness topic strength [0.0, 1.0]. |
| `created_at` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Processed timestamp. |

### 2.6. `personal_baselines`
Stores user-specific historical rolling baseline distributions.
*   **Primary Key:** `id` (INTEGER)
*   **Relations:** Many-to-One with `users`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | **[PUBLIC/SYSTEM]** | Primary Key. |
| `user_id` | UUID | **[IDENTIFIABLE]** | Foreign key linking to `users.id`. |
| `signal_name` | VARCHAR(50) | **[PUBLIC/SYSTEM]** | Column name of signal (e.g., 'work_pressure'). |
| `rolling_mean` | FLOAT | **[SENSITIVE]** | Calculated mean ($\mu$) over window $W$. |
| `rolling_std` | FLOAT | **[SENSITIVE]** | Calculated standard deviation ($\sigma$) over window $W$. |
| `window_size` | INTEGER | **[PUBLIC/SYSTEM]** | Size of sliding window (e.g., 14). |
| `updated_at` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Timestamp of last metric update. |

### 2.7. `detected_changes`
Logs deviation alerts raised by the models.
*   **Primary Key:** `id` (UUID)
*   **Relations:** Many-to-One with `users`. One-to-One with `explanations`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | **[PUBLIC/SYSTEM]** | Unique ID. |
| `user_id` | UUID | **[IDENTIFIABLE]** | Foreign key linking to `users.id`. |
| `model_type` | VARCHAR(20) | **[PUBLIC/SYSTEM]** | Model ID: 'Generic' (A) or 'Personalized' (B). |
| `signal_name` | VARCHAR(50) | **[PUBLIC/SYSTEM]** | Flagged signal (e.g., 'fatigue'). |
| `baseline_value` | FLOAT | **[SENSITIVE]** | Rolling baseline average or static threshold. |
| `current_value` | FLOAT | **[SENSITIVE]** | Measured signal value on trigger day. |
| `deviation_score` | FLOAT | **[SENSITIVE]** | Z-score or difference score. |
| `is_flagged` | BOOLEAN | **[SENSITIVE]** | True if deviation crossed flag threshold. |
| `detected_at` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Detection timestamp. |

### 2.8. `explanations`
Stores explainability details for flags.
*   **Primary Key:** `id` (INTEGER)
*   **Relations:** One-to-One with `detected_changes`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | **[PUBLIC/SYSTEM]** | Primary Key. |
| `change_id` | UUID | **[PUBLIC/SYSTEM]** | Foreign key linking to `detected_changes.id`. |
| `explanation_text` | TEXT | **[SENSITIVE]** | Human-readable statistical explanation. |
| `reflection_prompt` | TEXT | **[SENSITIVE]** | Suggestive prompt mapping to user's shift. |
| `created_at` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Compilation timestamp. |

### 2.9. `user_preferences`
User privacy and contact configuration.
*   **Primary Key:** `id` (INTEGER)
*   **Relations:** One-to-One with `users`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | **[PUBLIC/SYSTEM]** | Primary Key. |
| `user_id` | UUID | **[IDENTIFIABLE]** | Foreign key linking to `users.id`. |
| `enable_analysis` | BOOLEAN | **[PUBLIC/SYSTEM]** | True if NLP processing is allowed. |
| `trusted_contact_name` | VARCHAR(100) | **[CRITICAL]** | Optional contact name for emergency resource. |
| `trusted_contact_phone` | VARCHAR(20) | **[CRITICAL]** | Optional contact phone for emergency resource. |
| `trusted_contact_email` | VARCHAR(255) | **[CRITICAL]** | Optional contact email for emergency resource. |

### 2.10. `safety_events`
Audit logs of keyword safety interceptions.
*   **Primary Key:** `id` (INTEGER)
*   **Relations:** Many-to-One with `users`.

| Column | Type | Sensitive Level | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | **[PUBLIC/SYSTEM]** | Primary Key. |
| `user_id` | UUID | **[IDENTIFIABLE]** | Foreign key linking to `users.id`. |
| `triggered_keyword` | VARCHAR(50) | **[SENSITIVE]** | Redacted keyword category that matched. |
| `action_taken` | VARCHAR(100) | **[PUBLIC/SYSTEM]** | Action log (e.g., 'Helpline modal displayed'). |
| `triggered_at` | TIMESTAMP | **[PUBLIC/SYSTEM]** | Timestamp of interception. |
