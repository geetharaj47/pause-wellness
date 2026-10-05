"""
Pause AI Student Wellness Companion — Emotion Evaluation Benchmark
Runs a rigorous, empirical head-to-head comparison of:
  Model A: TF-IDF + Logistic Regression (Transparent baseline)
  Model B: SamLowe/roberta-base-go_emotions (Candidate neural model, mapped to Pause taxonomy)
On a held-out test suite of student reflection scenarios.

Outputs real, measured metrics (Precision, Recall, F1, Macro-F1, Abstention Rate, Latency).
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score

from app.services.emotion_service import emotion_service
from app.services.emotion_taxonomy import TAXONOMY_TAGS

# Held-out student reflection test suite (distinct authors/contexts from training)
HELD_OUT_BENCHMARK: List[Tuple[str, str]] = [
    # stress/overwhelmed
    ("Midterms start tomorrow and I haven't slept more than 3 hours. Too many deadlines at once, feeling completely crushed.", "stress/overwhelmed"),
    ("My thesis proposal feedback was brutally heavy. Feeling swamped and mentally burned out.", "stress/overwhelmed"),
    ("So much homework piled up over the weekend, can't keep up with both research and classes.", "stress/overwhelmed"),
    ("The lab demo is in two hours and my partner never uploaded their modules. Extreme workload pressure.", "stress/overwhelmed"),
    
    # worry/tense
    ("Waiting for the scholarship interview call. My chest feels tight and I'm very anxious.", "worry/tense"),
    ("What if I fail the compiler design viva? I feel so nervous thinking about standing before the professor.", "worry/tense"),
    ("Restless and tense tonight, wondering if my internship application was rejected.", "worry/tense"),
    
    # sad/disappointed
    ("Got an F on the math quiz after studying for days. Feeling so defeated and disheartened.", "sad/disappointed"),
    ("My flatmate moved out today. The room feels very empty and sad tonight.", "sad/disappointed"),
    ("Missed my sister's birthday back home because of lab attendance. Really down today.", "sad/disappointed"),
    
    # frustrated
    ("The university wifi has been down all afternoon during assignment submission. So furious.", "frustrated"),
    ("Tired of group projects where one person does all the work. It is deeply annoying.", "frustrated"),
    ("Professor changed the syllabus format the day before the test. Completely aggravated.", "frustrated"),
    
    # lonely/disconnected
    ("Walked through the campus student center and realized I have no one to sit with. Feeling very isolated.", "lonely/disconnected"),
    ("It feels like everyone has made lifelong friends already and I'm just here alone in my dorm.", "lonely/disconnected"),
    ("No messages all weekend. Feeling totally disconnected from my peers.", "lonely/disconnected"),
    
    # calm/relieved
    ("Turned in my major project report! Sitting by the library lawn listening to the breeze, feeling peaceful.", "calm/relieved"),
    ("Took a long hot shower after finishing exams. The relief feels immense and relaxing.", "calm/relieved"),
    ("Finally sorted out my course registration. A calm and gentle evening ahead.", "calm/relieved"),
    
    # positive/hopeful
    ("Our presentation went amazingly well! The faculty panel even complimented our design. So happy!", "positive/hopeful"),
    ("Got accepted into the student research internship! Thrilled and excited for the semester.", "positive/hopeful"),
    ("Had such a warm dinner with classmates tonight. Really grateful for this group.", "positive/hopeful"),
    
    # neutral
    ("Read chapter 4 of the database systems book from 2pm to 4pm.", "neutral"),
    ("Purchased bus tickets for the weekend and did laundry in the morning.", "neutral"),
    ("Campus bookstore was closed today. Will go back on Tuesday.", "neutral"),
    
    # mixed/uncertain (subtle / borderline cases designed to test abstention)
    ("The day was somewhat strange. A mix of different feelings that I cannot really articulate.", "mixed/uncertain"),
    ("Not sure how I feel about the grade. It is neither good nor bad.", "mixed/uncertain"),
    ("Things happened today, felt busy but also strangely detached.", "mixed/uncertain"),
]

def evaluate_model(use_roberta: bool) -> Dict:
    model_name = "RoBERTa-GoEmotions (Mapped Candidate)" if use_roberta else "TF-IDF + Logistic Regression (Baseline)"
    y_true = []
    y_pred = []
    latencies = []
    abstained_count = 0

    for text, true_label in HELD_OUT_BENCHMARK:
        start_time = time.perf_counter()
        result = emotion_service.analyze(text, language="en", prefer_roberta=use_roberta)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        latencies.append(elapsed_ms)

        y_true.append(true_label)
        if result["abstained"] or not result["labels"]:
            abstained_count += 1
            y_pred.append("mixed/uncertain") # Default evaluation bin for abstained/uncertain
        else:
            y_pred.append(result["labels"][0])

    # Calculate metrics
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    precision_macro = precision_score(y_true, y_pred, average="macro", zero_division=0)
    recall_macro = recall_score(y_true, y_pred, average="macro", zero_division=0)
    
    # Per-class report
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    p50_latency = float(np.percentile(latencies, 50))
    p95_latency = float(np.percentile(latencies, 95))

    return {
        "model_name": model_name,
        "sample_count": len(HELD_OUT_BENCHMARK),
        "macro_f1": round(float(macro_f1), 4),
        "macro_precision": round(float(precision_macro), 4),
        "macro_recall": round(float(recall_macro), 4),
        "abstention_rate": round(float(abstained_count / len(HELD_OUT_BENCHMARK)), 4),
        "p50_latency_ms": round(p50_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "per_class": {
            cls: {
                "precision": round(report[cls]["precision"], 3),
                "recall": round(report[cls]["recall"], 3),
                "f1": round(report[cls]["f1-score"], 3),
                "support": report[cls]["support"]
            }
            for cls in TAXONOMY_TAGS if cls in report
        }
    }

def main():
    print("=" * 60)
    print("RUNNING EMOTION MODEL BENCHMARK (TF-IDF vs RoBERTa Candidate)")
    print("=" * 60)
    
    print("\n1. Evaluating Model A: TF-IDF + Logistic Regression Baseline...")
    baseline_results = evaluate_model(use_roberta=False)
    
    print("2. Evaluating Model B: RoBERTa-GoEmotions Classifier...")
    roberta_results = evaluate_model(use_roberta=True)

    summary = {
        "evaluation_timestamp": datetime.utcnow().isoformat(),
        "dataset": "Pause Held-Out Student Reflection Benchmark",
        "sample_size": len(HELD_OUT_BENCHMARK),
        "baseline_tfidf": baseline_results,
        "candidate_roberta": roberta_results
    }

    output_path = "backend/app/evaluation/results_emotion.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS (MEASURED EMPIRICAL DATA)")
    print("=" * 60)
    print(f"Sample Count: {len(HELD_OUT_BENCHMARK)} student reflections")
    print(f"{'Metric':<25} | {'TF-IDF Baseline':<18} | {'RoBERTa Candidate':<18}")
    print("-" * 65)
    print(f"{'Macro-F1':<25} | {baseline_results['macro_f1']:<18} | {roberta_results['macro_f1']:<18}")
    print(f"{'Macro-Precision':<25} | {baseline_results['macro_precision']:<18} | {roberta_results['macro_precision']:<18}")
    print(f"{'Macro-Recall':<25} | {baseline_results['macro_recall']:<18} | {roberta_results['macro_recall']:<18}")
    print(f"{'Abstention Rate':<25} | {baseline_results['abstention_rate']:<18} | {roberta_results['abstention_rate']:<18}")
    print(f"{'p50 Latency (ms)':<25} | {baseline_results['p50_latency_ms']:<18} | {roberta_results['p50_latency_ms']:<18}")
    print(f"{'p95 Latency (ms)':<25} | {baseline_results['p95_latency_ms']:<18} | {roberta_results['p95_latency_ms']:<18}")
    print("=" * 60)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
