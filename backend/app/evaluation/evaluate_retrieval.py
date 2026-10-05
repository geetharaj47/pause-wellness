"""
Pause AI Student Wellness Companion — Retrieval Evaluation Benchmark
Empirically measures Recall@5, Precision@5, No-Match Accuracy, and Latency
using candidate sentence-transformers/all-MiniLM-L6-v2 on a fixed student query-entry suite.
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Tuple, Set
import numpy as np

from app.services.embedding_service import embedding_service, RELEVANCE_THRESHOLD

# 1. Fixed fictional student journal corpus
BENCHMARK_ENTRIES: List[Dict[str, str]] = [
    {
        "id": "entry-01",
        "date": "2026-09-10",
        "text": "Before the digital circuits exam, doing four rounds of box breathing by the fountain slowed my pulse and cleared my head."
    },
    {
        "id": "entry-02",
        "date": "2026-09-14",
        "text": "When the compiler project felt completely overwhelming, breaking it down into 10-line coding slices made it manageable."
    },
    {
        "id": "entry-03",
        "date": "2026-09-18",
        "text": "Could not sleep because of racing thoughts. Dimming all hostel room lights and putting my phone in my desk drawer helped me fall asleep."
    },
    {
        "id": "entry-04",
        "date": "2026-09-22",
        "text": "Felt really lonely on Sunday. Sent a low-pressure text message to Ananya and we ended up having tea at the student mess."
    },
    {
        "id": "entry-05",
        "date": "2026-09-25",
        "text": "Long 4-hour programming lab today. My neck and eyes hurt from screen fatigue. Taking a 15-minute screen-free walk helped reset my focus."
    },
    {
        "id": "entry-06",
        "date": "2026-09-28",
        "text": "Reviewing previous years' exam papers with Rohan at the central library was much less stressful than studying alone."
    },
    {
        "id": "entry-07",
        "date": "2026-10-01",
        "text": "Tried chamomile herbal tea 30 minutes before bed. Slept uninterrupted for 7 hours."
    },
    {
        "id": "entry-08",
        "date": "2026-10-02",
        "text": "Feeling anxious about the viva. Writing down my talking points on an index card gave me something concrete to hold."
    },
    {
        "id": "entry-09",
        "date": "2026-10-03",
        "text": "Joined the campus badminton group for an hour in the evening. The physical exercise really lifted my low mood."
    },
    {
        "id": "entry-10",
        "date": "2026-10-04",
        "text": "Attended lecture on operating systems virtual memory architecture and took handwritten notes."
    }
]

# 2. Benchmark Queries (Positive and Negative Controls)
BENCHMARK_QUERIES: List[Dict] = [
    {
        "query": "What helped when I had exam anxiety or nervousness?",
        "expected_ids": {"entry-01", "entry-08", "entry-06"},
        "is_negative_control": False
    },
    {
        "query": "What did I do when my coding project was overwhelming?",
        "expected_ids": {"entry-02"},
        "is_negative_control": False
    },
    {
        "query": "What bedtime routine or habits helped me fall asleep?",
        "expected_ids": {"entry-03", "entry-07"},
        "is_negative_control": False
    },
    {
        "query": "What helped when I felt isolated or wanted to reconnect with someone?",
        "expected_ids": {"entry-04", "entry-09"},
        "is_negative_control": False
    },
    {
        "query": "How did I handle screen fatigue after hours of lab work?",
        "expected_ids": {"entry-05"},
        "is_negative_control": False
    },
    {
        "query": "Did studying with a peer help with revision?",
        "expected_ids": {"entry-06"},
        "is_negative_control": False
    },
    {
        "query": "What physical activity lifted my energy or mood?",
        "expected_ids": {"entry-09", "entry-05"},
        "is_negative_control": False
    },
    # Negative controls (queries with NO relevant evidence in corpus)
    {
        "query": "Cryptocurrency Bitcoin blockchain wallet trading strategy",
        "expected_ids": set(),
        "is_negative_control": True
    },
    {
        "query": "Car engine repair and transmission replacement manual",
        "expected_ids": set(),
        "is_negative_control": True
    },
    {
        "query": "Quantum gravity and general relativity mathematical proofs",
        "expected_ids": set(),
        "is_negative_control": True
    }
]

def run_retrieval_benchmark():
    print("=" * 65)
    print("RUNNING RETRIEVAL EVALUATION BENCHMARK (sentence-transformers/all-MiniLM-L6-v2)")
    print("=" * 65)

    # Pre-embed corpus entries
    print(f"1. Pre-indexing {len(BENCHMARK_ENTRIES)} benchmark journal entries...")
    embedded_corpus = []
    for item in BENCHMARK_ENTRIES:
        vec = embedding_service.embed_text(item["text"])
        embedded_corpus.append({
            "id": item["id"],
            "date": item["date"],
            "text": item["text"],
            "vector": vec
        })

    # Evaluate queries
    print(f"2. Running {len(BENCHMARK_QUERIES)} benchmark queries...")
    latencies = []
    recall_at_5_hits = 0
    total_positive_queries = 0
    precision_scores = []
    correct_abstentions = 0
    total_negative_queries = 0

    query_evaluations = []

    for q_item in BENCHMARK_QUERIES:
        query_text = q_item["query"]
        expected = q_item["expected_ids"]
        is_neg = q_item["is_negative_control"]

        start_time = time.perf_counter()
        q_vec = embedding_service.embed_text(query_text)

        # Score all corpus items
        scored = []
        for item in embedded_corpus:
            cosine_sim = embedding_service.cosine_similarity(q_vec, item["vector"])
            lexical_score = embedding_service.lexical_keyword_score(query_text, item["text"])
            combined = (0.75 * cosine_sim) + (0.25 * lexical_score)
            if combined >= RELEVANCE_THRESHOLD:
                scored.append({
                    "id": item["id"],
                    "score": round(combined, 4)
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        top_5 = scored[:5]
        top_5_ids = [s["id"] for s in top_5]
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        latencies.append(elapsed_ms)

        # Evaluation metrics
        if is_neg:
            total_negative_queries += 1
            if len(top_5_ids) == 0:
                correct_abstentions += 1
                abstention_status = "CORRECT_ABSTAIN"
            else:
                abstention_status = "FALSE_POSITIVE"
        else:
            total_positive_queries += 1
            # Check Recall@5: was at least one expected document retrieved?
            hits = expected.intersection(set(top_5_ids))
            if hits:
                recall_at_5_hits += 1
            # Precision@5: fraction of retrieved that were expected
            p = len(hits) / max(len(top_5_ids), 1)
            precision_scores.append(p)
            abstention_status = "RETRIEVED" if top_5_ids else "FALSE_ABSTAIN"

        query_evaluations.append({
            "query": query_text,
            "expected_ids": list(expected),
            "retrieved_ids": top_5_ids,
            "status": abstention_status,
            "latency_ms": round(elapsed_ms, 2)
        })

    # Summary numbers
    recall_at_5 = recall_at_5_hits / total_positive_queries if total_positive_queries > 0 else 0.0
    mean_precision = float(np.mean(precision_scores)) if precision_scores else 0.0
    no_match_accuracy = correct_abstentions / total_negative_queries if total_negative_queries > 0 else 0.0
    p50_latency = float(np.percentile(latencies, 50))
    p95_latency = float(np.percentile(latencies, 95))

    results = {
        "evaluation_timestamp": datetime.utcnow().isoformat(),
        "model_id": embedding_service.model_id,
        "model_version": embedding_service.model_version,
        "relevance_threshold": RELEVANCE_THRESHOLD,
        "corpus_size": len(BENCHMARK_ENTRIES),
        "total_queries": len(BENCHMARK_QUERIES),
        "positive_queries": total_positive_queries,
        "negative_queries": total_negative_queries,
        "recall_at_5": round(recall_at_5, 4),
        "precision_at_5": round(mean_precision, 4),
        "no_match_accuracy": round(no_match_accuracy, 4),
        "p50_latency_ms": round(p50_latency, 2),
        "p95_latency_ms": round(p95_latency, 2),
        "query_details": query_evaluations
    }

    output_path = "backend/app/evaluation/results_retrieval.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 65)
    print("RETRIEVAL BENCHMARK RESULTS (MEASURED EMPIRICAL DATA)")
    print("=" * 65)
    print(f"{'Metric':<30} | {'Measured Value':<25}")
    print("-" * 65)
    print(f"{'Recall@5 (Positive Queries)':<30} | {round(recall_at_5 * 100, 2)}%")
    print(f"{'Precision@5 (Mean)':<30} | {round(mean_precision * 100, 2)}%")
    print(f"{'No-Match Accuracy (Negatives)':<30} | {round(no_match_accuracy * 100, 2)}%")
    print(f"{'Relevance Gate Threshold':<30} | {RELEVANCE_THRESHOLD}")
    print(f"{'p50 Latency (ms)':<30} | {round(p50_latency, 2)} ms")
    print(f"{'p95 Latency (ms)':<30} | {round(p95_latency, 2)} ms")
    print("=" * 65)
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    run_retrieval_benchmark()
