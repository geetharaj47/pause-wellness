# MindTrace Research Methodology

This document outlines the research framework, experimental design, datasets, evaluation metrics, and statistical analysis plans for the MindTrace project.

---

## 1. Research Question

> **Primary Question:** Can personalized longitudinal modeling identify meaningful changes in an individual's wellness-related patterns more accurately, earlier, and with fewer false alarms than a generic population-level approach?

---

## 2. Experimental Setup & Hypotheses

### 2.1. Models under Comparison
*   **Model A (Generic Baseline):** A static threshold model. Flags a deviation if a signal $X_t > T_{\text{static}}$ for $k=3$ consecutive days. The threshold $T_{\text{static}}$ is determined by taking the $90\text{th}$ percentile of the training population data.
*   **Model B (Personalized Model):** An individualized baseline model. Calculates a rolling mean ($\mu_t$) and standard deviation ($\sigma_t$) over a window $W=14$. Flags a deviation if the current signal $X_t > \mu_{t-1} + Z_{\text{thresh}} \cdot \sigma_{t-1}$ (where $Z_{\text{thresh}} = 1.96$). We also test a CUSUM version.

### 2.2. Core Hypotheses
1.  **Hypothesis 1:** Model B will demonstrate a significantly lower False Positive Rate (FPR) compared to Model A, especially for users with high or low baseline stress levels.
2.  **Hypothesis 2:** Model B will detect injected wellness deviations with a shorter Lead Time (days between shift onset and model detection) than Model A.
3.  **Hypothesis 3:** Integrating multi-modal features (daily factors + emotions + topics) in the Personalized Model will yield a higher F1-score than using sentiment signals alone.

---

## 3. Data Strategy & Simulation

### 3.1. GoEmotions (NLP Layer Verification)
For evaluating the NLP signal extraction accuracy:
*   We utilize the **GoEmotions** dataset (58,000 Reddit comments labeled with 27 emotions).
*   We map these emotions into positive affect, negative affect, and stress categories.
*   We train a local classification head (e.g., Logistic Regression or a PyTorch Multi-layer Perceptron) on top of frozen `all-MiniLM-L6-v2` embeddings, and report Standard Classification Metrics (Accuracy, Precision, Recall, Macro-F1).

### 3.2. Synthetic Longitudinal Cohort (Engine Verification)
Since collecting longitudinal wellness data from real human participants requires institutional ethics approval (IRB) and takes months, we develop a **Longitudinal Simulator**:
*   **Cohort Size:** $N = 100$ simulated users.
*   **Duration:** $T = 60$ days of daily check-ins and journal entries per user.
*   **Base Behaviors:** Users are simulated with varying baseline profiles:
    *   *Profile 1 (High-baseline Stress):* College student with high average academic pressure but high resilience (high sleep quality).
    *   *Profile 2 (Highly Variable Mood):* High emotional variance, sensitive to weekend vs. weekday factors.
    *   *Profile 3 (Low Expression):* Muted emotional peaks, subtle verbal shifts.
*   **Anomaly Injection:** For each user, we programmatically inject a "wellness shift" (e.g., sleep drops, stress scores increase, positive experiences decrease) at a random day $t_{\text{shift}} \in [30, 45]$ lasting for 7 to 10 days.
*   **Ground Truth:** Since we control the injection day $t_{\text{shift}}$, we have exact ground-truth labels for when a real deviation occurred, allowing precise calculation of precision, recall, and detection latency.

---

## 4. Proposed Experiments

```
               ┌─────────────────────────────────────────────────────────┐
               │                     MINDTRACE STUDY                     │
               └─────────────────────────────────────────────────────────┘
                                            │
       ┌────────────────────┬───────────────┴───────────────┬────────────────────┐
       ▼                    ▼                               ▼                    ▼
┌──────────────┐     ┌──────────────┐                ┌──────────────┐     ┌──────────────┐
│ Experiment 1 │     │ Experiment 2 │                │ Experiment 3 │     │ Experiment 4 │
│  Generic vs  │     │   Ablation   │                │   Feature    │     │ Calibration  │
│ Personalized │     │ Window Size  │                │   Ablation   │     │ & Conformal  │
└──────────────┘     └──────────────┘                └──────────────┘     └──────────────┘
```

### Experiment 1: Generic vs. Personalized Performance
*   **Objective:** Compare Model A and Model B on the simulated cohort.
*   **Metrics:**
    *   **Precision:** $\frac{TP}{TP + FP}$ (percentage of flagged alerts that correspond to true injected shifts).
    *   **Recall (Sensitivity):** $\frac{TP}{TP + FN}$ (percentage of injected shifts successfully flagged).
    *   **F1-Score:** Harmonic mean of Precision and Recall.
    *   **False Positive Rate (FPR):** $\frac{FP}{FP + TN}$ (rate of false alarms during baseline periods).
    *   **Detection Lead Time (Latency):** $\Delta t = t_{\text{detected}} - t_{\text{shift}}$ (number of days taken to raise a flag after the shift was injected).

### Experiment 2: History Window Size Ablation
*   **Objective:** Analyze the impact of the baseline window size $W$ on Model B's performance.
*   **Configurations:** Test $W \in \{5, 10, 14, 20, 30\}$ days.
*   **Goal:** Find the optimal trade-off point between model responsiveness (smaller $W$) and statistical stability (larger $W$).

### Experiment 3: Feature Ablation
*   **Objective:** Measure how different signal combinations affect deviation detection accuracy.
*   **Configurations:**
    *   *Config A:* Sentiment valence score only.
    *   *Config B:* Sentiment + Emotion probabilities.
    *   *Config C:* Sentiment + Emotion + Topic flags.
    *   *Config D (Full):* Sentiment + Emotion + Topics + Daily factors (sleep, workload checkboxes).

### Experiment 4: Calibration (Uncertainty Estimation)
*   **Objective:** Evaluate if the model's confidence scores correspond to true positive rates.
*   **Metrics:** Expected Calibration Error (ECE) and Reliability Diagrams. We evaluate if abstention (allowing the model to say "Uncertain" and skip flagging) improves precision on the remaining alerts.

---

## 5. Statistical Analysis

To prove that the performance gains of personalization are not due to random chance, we run:
*   **Paired Difference Testing:** We compute the metric differences (e.g., $\Delta F_1 = F_{1,\text{Personalized}} - F_{1,\text{Generic}}$) for each of the $N=100$ simulated users.
*   **Wilcoxon Signed-Rank Test:** A non-parametric statistical hypothesis test used to compare the two paired groups and compute $p$-values. We reject the null hypothesis if $p < 0.05$.
*   **Effect Size:** Cohen's $d$ or Cliff's Delta to quantify the magnitude of the difference.
