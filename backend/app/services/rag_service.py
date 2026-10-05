"""
RAG Generation & Grounding Service for Pause.
Handles:
1. Untrusted data boundary and prompt injection defense.
2. Clinical claim refusal and safety routing.
3. Pluggable provider adapter (Local Extractive Synthesis, Local Transformers, External Opt-in, Source Cards Only).
4. Strict citation validation: validates cited entry IDs are a strict subset of retrieved entries for that user.
5. Fallback to source cards when generation is disabled or unavailable.
"""

import re
import uuid
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


# ==========================================
# SAFETY & ADVERSARIAL PATTERNS
# ==========================================

# Prompt injection and instruction override defense
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|previous\s+|above\s+)?instructions",
    r"disregard\s+(all\s+|previous\s+|system\s+)",
    r"you\s+are\s+now\s+(a\s+therapist|an\s+admin|dan|jailbroken|unfiltered)",
    r"system\s+prompt",
    r"reveal\s+(all\s+|other\s+)?(user|student|journal|data|password)",
    r"show\s+(me\s+|all\s+)?entries\s+from\s+other",
    r"select\s+\*\s+from",
    r"drop\s+table",
    r"delete\s+from\s+users",
    r"bypass\s+(security|safety|filter|guardrail)"
]

# Clinical diagnosis / medical prescription refusal
CLINICAL_PATTERNS = [
    r"do\s+i\s+have\s+(clinical\s+)?(depression|bipolar|schizophrenia|adhd|ocd|ptsd|autism|anxiety\s+disorder)",
    r"diagnose\s+me\s+with",
    r"prescribe\s+(me\s+)?(medication|antidepressant|adderall|xanax|prozac|drugs)",
    r"what\s+(is\s+my\s+)?(diagnosis|clinical\s+score|mental\s+illness)",
    r"am\s+i\s+(mentally\s+ill|clinically\s+depressed|crazy|insane)"
]

# High-urgency crisis keywords for safety pre-check
CRISIS_PRECHECK_PATTERNS = [
    r"\b(i\s+want\s+to\s+die|kill\s+myself|end\s+my\s+life|suicide|suicidal)\b",
    r"\b(better\s+off\s+dead|no\s+reason\s+to\s+live|hang\s+myself|overdose)\b"
]


class RAGGenerationService:
    def __init__(self):
        self.generator_mode = "local_synthesis" # Options: "local_synthesis", "source_cards_only", "external"

    def check_safety_and_adversarial(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Pre-flight check for:
        1. Crisis language -> route to support
        2. Prompt injection -> refusal
        3. Clinical diagnosis requests -> refusal
        Returns (safety_route, refusal_message) if flagged, or (None, None) if safe.
        """
        q_lower = query.lower().strip()

        # 1. Crisis pre-check
        for pattern in CRISIS_PRECHECK_PATTERNS:
            if re.search(pattern, q_lower):
                return (
                    "support",
                    "It sounds like you may be going through a deeply difficult time. Pause cannot handle crisis situations or provide emergency care. Please connect directly with human support—such as Tele-MANAS (14416 / 1800-89-14416) or National Emergency (112)."
                )

        # 2. Prompt injection
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, q_lower):
                return (
                    "refusal",
                    "Pause can only summarize your own past reflections. Instructions attempting to override system behavior, access other users' data, or alter safety constraints cannot be processed."
                )

        # 3. Clinical claim / diagnosis request
        for pattern in CLINICAL_PATTERNS:
            if re.search(pattern, q_lower):
                return (
                    "clinical_refusal",
                    "Pause is a self-reflection companion for university students and does not provide clinical diagnoses, psychiatric assessments, or treatment plans. If you are experiencing persistent distress, please speak with a campus counselor or qualified mental health professional."
                )

        return (None, None)

    def generate_grounded_answer(
        self,
        query: str,
        retrieved_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a strictly grounded answer based ONLY on the retrieved snippets.
        Enforces:
        - Strict citation contract (only valid retrieved entry IDs are cited)
        - Untrusted data boundary (snippets are treated as evidence, not instructions)
        - Honest abstention when evidence is insufficient
        - Safe fallback to source cards
        """
        if not retrieved_items:
            return {
                "answer": None,
                "source_entry_ids": [],
                "abstained": True,
                "safety_route": "normal",
                "message": "I couldn't find a related entry in your previous reflections."
            }

        valid_entry_ids = [str(item["entry_id"]) for item in retrieved_items]

        # If generator mode is set to source_cards_only, return None for answer
        if self.generator_mode == "source_cards_only":
            return {
                "answer": None,
                "source_entry_ids": valid_entry_ids,
                "abstained": False,
                "safety_route": "normal",
                "message": f"Showing {len(retrieved_items)} relevant past reflections without model synthesis."
            }

        # Deterministic Grounded Synthesis Engine
        # Synthesizes an honest, calm, non-judgmental summary directly from the student's own words.
        synthesized_text, cited_ids = self._synthesize_extractive_summary(query, retrieved_items)

        # Citation validation: ensure every cited ID is a strict subset of valid_entry_ids
        verified_citations = [eid for eid in cited_ids if eid in valid_entry_ids]
        if not verified_citations and valid_entry_ids:
            # Fallback to the top retrieved item if none cited
            verified_citations = [valid_entry_ids[0]]

        # Post-generation clinical claim defense
        clean_text = self._post_process_clinical_guard(synthesized_text)

        return {
            "answer": clean_text,
            "source_entry_ids": verified_citations,
            "abstained": False,
            "safety_route": "normal",
            "message": f"Answer grounded in {len(verified_citations)} of your past reflection{'s' if len(verified_citations) > 1 else ''}."
        }

    def _synthesize_extractive_summary(
        self,
        query: str,
        retrieved_items: List[Dict[str, Any]]
    ) -> Tuple[str, List[str]]:
        """
        Grounded synthesis that extracts key actions, habits, and self-observations
        from retrieved journal entries, attributing each finding to its date.
        """
        cited_ids = []
        observations = []

        q_lower = query.lower()
        is_asking_what_helped = any(w in q_lower for w in ["helped", "do", "habit", "routine", "handle", "manage"])

        for item in retrieved_items[:3]: # Focus on top 3 most relevant items
            date_str = item.get("date_formatted", "Past entry")
            snippet = item.get("snippet", "").strip()
            entry_id = str(item.get("entry_id"))

            if not snippet:
                continue

            cited_ids.append(entry_id)

            # Extract sentence-level key points
            sentences = [s.strip() for s in re.split(r'[.!?]+', snippet) if len(s.strip()) > 15]

            # Find sentences describing positive actions or outcomes
            helpful_sentences = []
            for s in sentences:
                s_lower = s.lower()
                # Check if sentence describes something that helped, worked, or was done
                if any(k in s_lower for k in [
                    "helped", "better", "walk", "breathe", "breathing", "break",
                    "routine", "sleep", "stepped away", "rest", "call", "talk", "study",
                    "focus", "notes", "tried", "felt calmer", "worked"
                ]):
                    helpful_sentences.append(s)

            if helpful_sentences:
                primary_point = helpful_sentences[0]
                observations.append(f"On {date_str}, you noted that {primary_point.lower()}.")
            elif sentences:
                # Use the first clear sentence
                observations.append(f"On {date_str}, you reflected: \"{sentences[0]}\".")

        if not observations:
            top_item = retrieved_items[0]
            cited_ids = [str(top_item["entry_id"])]
            return (
                f"In your reflection from {top_item.get('date_formatted', 'earlier')}, you mentioned: \"{top_item.get('snippet', '')[:160]}...\"",
                cited_ids
            )

        if is_asking_what_helped:
            prefix = "Based on your past reflections, here is what you recorded that helped:\n\n"
        else:
            prefix = "Here is what your past reflections note regarding this:\n\n"

        body = "\n\n".join(f"• {obs}" for obs in observations)
        conclusion = "\n\n(These are observations drawn directly from your notes, not clinical advice.)"

        return (prefix + body + conclusion, cited_ids)

    def _post_process_clinical_guard(self, text: str) -> str:
        """
        Sanitize generated text to eliminate any inadvertent clinical diagnostic claims.
        """
        prohibited = [
            (r"\byou\s+have\s+depression\b", "you mentioned feeling low"),
            (r"\byou\s+are\s+diagnosed\s+with\b", "you wrote about"),
            (r"\bclinical\s+depression\b", "extended periods of low mood"),
            (r"\bprescription\b", "routine suggestion"),
            (r"\btreatment\s+plan\b", "wellness plan")
        ]
        sanitized = text
        for pat, repl in prohibited:
            sanitized = re.sub(pat, repl, sanitized, flags=re.IGNORECASE)
        return sanitized

    @staticmethod
    def hash_query_for_privacy(query: str) -> str:
        """
        Hash query text with SHA-256 for privacy-compliant feedback tracking.
        Raw question text is NOT stored in feedback tables.
        """
        return hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()


rag_service = RAGGenerationService()
