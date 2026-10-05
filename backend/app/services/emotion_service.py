"""
Pause AI Student Wellness Companion — Emotion Analysis Service
Implements candidate RoBERTa model and TF-IDF + Logistic Regression baseline.
"""

import os
import re
from typing import List, Dict, Optional, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.services.emotion_taxonomy import (
    TAXONOMY_TAGS,
    GO_EMOTIONS_MAPPING,
    STRESS_OVERWHELMED_PHRASES,
    LONELY_DISCONNECTED_PHRASES,
    ABSTENTION_THRESHOLD,
    SECONDARY_THRESHOLD,
    get_confidence_band,
    extract_explanation_spans
)

# Benchmark seed training data for the TF-IDF Baseline (student journal domain)
BASELINE_TRAINING_CORPUS: List[Tuple[str, str]] = [
    # stress/overwhelmed
    ("I have three assignments due tomorrow and haven't started compiler design. I feel completely overwhelmed and swamped.", "stress/overwhelmed"),
    ("My screen fatigue was intense today, so much pressure from my thesis advisor.", "stress/overwhelmed"),
    ("Too much coursework to keep up with, I feel like I am drowning in work.", "stress/overwhelmed"),
    ("Burnout is really catching up to me, exhausted from nonstop project work.", "stress/overwhelmed"),
    ("The lab went for five hours straight and I just could not handle the workload.", "stress/overwhelmed"),
    
    # worry/tense
    ("I am so anxious and nervous about the midterm exam next Monday.", "worry/tense"),
    ("My heart is racing thinking about the presentation in front of the seminar cohort.", "worry/tense"),
    ("I feel tense and jittery, worried I will lose my scholarship funding.", "worry/tense"),
    ("Kept waking up in the night worrying about whether my code submission will compile.", "worry/tense"),
    
    # sad/disappointed
    ("Got back my exam results today and they were much worse than I worked for. Really disappointed.", "sad/disappointed"),
    ("Feeling down and disheartened, missing my home and family so much today.", "sad/disappointed"),
    ("It feels gloomy and discouraging today, nothing went according to plan.", "sad/disappointed"),
    ("Grieving a family situation while trying to study is really hard.", "sad/disappointed"),
    
    # frustrated
    ("My project partner did not submit their part of the repository again, so annoyed and frustrated.", "frustrated"),
    ("The lab server crashed right before the deadline and erased my changes. I am furious.", "frustrated"),
    ("Angry at how disorganized the department schedule is this semester.", "frustrated"),
    ("So irritated by all the noise in the student hostel tonight.", "frustrated"),
    
    # lonely/disconnected
    ("Spent the entire weekend in my dorm room with nobody to speak to. Feeling so isolated.", "lonely/disconnected"),
    ("Everyone else seems to have their friend groups figured out, I feel completely disconnected.", "lonely/disconnected"),
    ("Eating alone in the campus mess again, feeling distant from everyone.", "lonely/disconnected"),
    
    # calm/relieved
    ("Finally submitted the final year project report. Big sigh of relief, feeling peaceful.", "calm/relieved"),
    ("Took a slow quiet walk around the university lake this morning, feeling calm and at ease.", "calm/relieved"),
    ("Sat in the library with a cup of warm tea and my pulse finally slowed down.", "calm/relieved"),
    
    # positive/hopeful
    ("Great lecture today! Really proud that our machine learning model reached 92% accuracy.", "positive/hopeful"),
    ("Grateful for my flatmates who helped me debug my database code tonight.", "positive/hopeful"),
    ("Looking forward with optimism to the weekend hackathon with the team.", "positive/hopeful"),
    ("Had a joyful afternoon chatting with my classmates after a long week.", "positive/hopeful"),
    
    # neutral
    ("Attended lectures from 9am to 3pm, then went to the library to review notes.", "neutral"),
    ("Submitted the attendance sheet and bought stationary from the campus shop.", "neutral"),
    ("Installed Python 3.12 and set up my virtual environment for the lab.", "neutral"),
    ("The weather was cloudy today. Had rice and dal for lunch.", "neutral"),
]

class TfIdfEmotionBaseline:
    """
    Transparent TF-IDF + Logistic Regression baseline classifier for student reflections.
    Used for comparative benchmark against neural transformers and fast offline inference.
    """
    def __init__(self):
        self.model_id = "tfidf-logistic-regression"
        self.model_version = "1.0-baseline"
        self._is_trained = False
        self._pipeline = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=1200, stop_words="english")),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=300, random_state=42))
        ])
        self._train()

    def _train(self):
        texts, labels = zip(*BASELINE_TRAINING_CORPUS)
        self._pipeline.fit(texts, labels)
        self._is_trained = True

    def predict_scores(self, text: str) -> Dict[str, float]:
        if not self._is_trained:
            self._train()
        classes = self._pipeline.classes_
        probs = self._pipeline.predict_proba([text])[0]
        return {cls_name: float(prob) for cls_name, prob in zip(classes, probs)}


class RobertaGoEmotionsClassifier:
    """
    Candidate neural model: SamLowe/roberta-base-go_emotions pinned to reviewed revision.
    """
    def __init__(self):
        self.model_id = "SamLowe/roberta-base-go_emotions"
        self.model_version = "1895400d2daef02be65e8f3c24559e0aa09d5d25"
        self._pipeline = None
        self._failed_load = False

    def _load_model(self):
        if self._pipeline is not None or self._failed_load:
            return
        try:
            from transformers import pipeline
            self._pipeline = pipeline(
                "text-classification",
                model=self.model_id,
                revision=self.model_version,
                top_k=None,
                device=-1 # CPU
            )
        except Exception as e:
            # Document load failure and degrade to baseline
            self._failed_load = True

    def predict_scores(self, text: str) -> Optional[Dict[str, float]]:
        self._load_model()
        if self._pipeline is None:
            return None
        
        try:
            # Run inference (truncate to max 512 tokens)
            results = self._pipeline(text[:1000])[0]
            # Aggregate probabilities into Pause's 9 non-clinical taxonomy classes
            aggregated: Dict[str, float] = {tag: 0.0 for tag in TAXONOMY_TAGS}
            
            for item in results:
                raw_label = item["label"]
                prob = float(item["score"])
                mapped_tag = GO_EMOTIONS_MAPPING.get(raw_label, "mixed/uncertain")
                aggregated[mapped_tag] += prob

            # Also incorporate phrase signals for student stress / loneliness
            text_lower = text.lower()
            if any(p in text_lower for p in STRESS_OVERWHELMED_PHRASES):
                aggregated["stress/overwhelmed"] = max(aggregated["stress/overwhelmed"], 0.45)
            if any(p in text_lower for p in LONELY_DISCONNECTED_PHRASES):
                aggregated["lonely/disconnected"] = max(aggregated["lonely/disconnected"], 0.45)

            # Normalize so scores are well-behaved
            total = sum(aggregated.values())
            if total > 0:
                aggregated = {k: v / total for k, v in aggregated.items()}

            return aggregated
        except Exception:
            return None


class EmotionAnalysisService:
    """
    Main Emotion Service coordinating model selection, language validation,
    abstention gating, and structured non-clinical explanation generation.
    """
    def __init__(self):
        self.baseline = TfIdfEmotionBaseline()
        self.roberta = RobertaGoEmotionsClassifier()

    def is_english(self, text: str) -> bool:
        """Simple heuristic check for English text."""
        if not text.strip():
            return True
        # Check percentage of standard ASCII / latin letters
        letters = re.findall(r'[a-zA-Z]', text)
        if len(letters) < 3 and len(text.strip()) > 5:
            return False
        return True

    def analyze(self, text: str, language: str = "en", prefer_roberta: bool = True) -> Dict[str, Any]:
        """
        Analyze a submitted journal entry.
        Returns strictly validated schema with qualitative confidence and abstention.
        """
        if not text or not text.strip():
            return {
                "status": "empty",
                "model_id": self.baseline.model_id,
                "model_version": self.baseline.model_version,
                "labels": [],
                "confidence_bands": [],
                "explanation_spans": [],
                "user_facing_explanation": "No text provided for analysis.",
                "abstained": True
            }

        # 1. Language gate (English only for Release 1 per specification)
        if language != "en" or not self.is_english(text):
            return {
                "status": "unsupported_language",
                "model_id": "language-filter",
                "model_version": "1.0",
                "labels": [],
                "confidence_bands": [],
                "explanation_spans": [],
                "user_facing_explanation": "Emotion analysis is currently evaluated only for English entries. Your entry has been saved privately without language analysis.",
                "abstained": True
            }

        # 2. Model inference
        scores = None
        model_id = self.baseline.model_id
        model_version = self.baseline.model_version

        if prefer_roberta:
            roberta_scores = self.roberta.predict_scores(text)
            if roberta_scores:
                scores = roberta_scores
                model_id = self.roberta.model_id
                model_version = self.roberta.model_version

        # Fallback to TF-IDF baseline if RoBERTa is unavailable
        if scores is None:
            scores = self.baseline.predict_scores(text)
            # Check student stress / loneliness phrases on baseline too
            text_lower = text.lower()
            if any(p in text_lower for p in STRESS_OVERWHELMED_PHRASES):
                scores["stress/overwhelmed"] = max(scores.get("stress/overwhelmed", 0.0), 0.45)
            if any(p in text_lower for p in LONELY_DISCONNECTED_PHRASES):
                scores["lonely/disconnected"] = max(scores.get("lonely/disconnected", 0.0), 0.45)

        # 3. Rank and filter scores
        sorted_classes = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_class, top_score = sorted_classes[0]

        # 4. Abstention decision: If confidence below threshold, return "I'm not sure"
        if top_score < ABSTENTION_THRESHOLD or (top_class == "neutral" and top_score < 0.35):
            return {
                "status": "uncertain",
                "model_id": model_id,
                "model_version": model_version,
                "labels": [],
                "confidence_bands": ["uncertain"],
                "explanation_spans": [],
                "user_facing_explanation": "I'm not sure. The language in this entry was too subtle or mixed to suggest a confident label.",
                "abstained": True
            }

        # Up to 3 labels above secondary threshold
        selected_labels = [str(top_class)]
        for cls_name, score in sorted_classes[1:3]:
            cls_str = str(cls_name)
            if score >= SECONDARY_THRESHOLD and cls_str not in selected_labels:
                selected_labels.append(cls_str)

        confidence_bands = [get_confidence_band(top_score) for _ in selected_labels]
        explanation_spans = extract_explanation_spans(text, selected_labels)

        # Non-clinical respectful wording per specification:
        # "The model tentatively tagged this entry as frustration. Does that feel right?"
        tags_str = " and ".join(selected_labels)
        explanation_msg = f"The model tentatively suggested: '{tags_str}'. Does that feel right to you?"

        return {
            "status": "success",
            "model_id": model_id,
            "model_version": model_version,
            "labels": selected_labels,
            "confidence_bands": confidence_bands,
            "explanation_spans": explanation_spans,
            "user_facing_explanation": explanation_msg,
            "abstained": False
        }

# Global singleton service
emotion_service = EmotionAnalysisService()
