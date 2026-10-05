"""
Pause AI Student Wellness Companion — Emotion Taxonomy & Mapping

Non-clinical language taxonomy per Product Specification:
1. stress/overwhelmed
2. worry/tense
3. sad/disappointed
4. frustrated
5. lonely/disconnected
6. calm/relieved
7. positive/hopeful
8. neutral
9. mixed/uncertain

PROHIBITED CLAIMS:
- Never output diagnostic labels, clinical severity scores, or depression/anxiety scales.
- Never output false-precision decimal percentages (e.g. '87.4% sad').
- Return qualitative confidence bands ('tentative', 'uncertain').
- If below confidence threshold, abstain with 'I am not sure'.
"""

from typing import List, Dict, Optional, Tuple

TAXONOMY_TAGS = [
    "stress/overwhelmed",
    "worry/tense",
    "sad/disappointed",
    "frustrated",
    "lonely/disconnected",
    "calm/relieved",
    "positive/hopeful",
    "neutral",
    "mixed/uncertain"
]

# Mapping from GoEmotions 28 categories to Pause's 9 non-clinical student reflection tags
GO_EMOTIONS_MAPPING: Dict[str, str] = {
    # Positive / Hopeful
    "admiration": "positive/hopeful",
    "amusement": "positive/hopeful",
    "approval": "positive/hopeful",
    "caring": "positive/hopeful",
    "desire": "positive/hopeful",
    "excitement": "positive/hopeful",
    "gratitude": "positive/hopeful",
    "joy": "positive/hopeful",
    "love": "positive/hopeful",
    "optimism": "positive/hopeful",
    "pride": "positive/hopeful",
    
    # Calm / Relieved
    "relief": "calm/relieved",
    
    # Worry / Tense
    "fear": "worry/tense",
    "nervousness": "worry/tense",
    
    # Sad / Disappointed
    "disappointment": "sad/disappointed",
    "embarrassment": "sad/disappointed",
    "grief": "sad/disappointed",
    "remorse": "sad/disappointed",
    "sadness": "sad/disappointed",
    
    # Frustrated
    "anger": "frustrated",
    "annoyance": "frustrated",
    "disapproval": "frustrated",
    "disgust": "frustrated",
    
    # Neutral / Ambiguous
    "neutral": "neutral",
    "curiosity": "neutral",
    "realization": "neutral",
    "surprise": "mixed/uncertain",
    "confusion": "mixed/uncertain"
}

# Context phrases indicating stress/overwhelm in student life
STRESS_OVERWHELMED_PHRASES = [
    "overwhelmed", "too much", "swamped", "burnout", "exhausted",
    "deadline", "crushed", "drowning", "can't keep up", "behind on",
    "pressure", "fatigue", "overload", "stressed", "hectic"
]

LONELY_DISCONNECTED_PHRASES = [
    "lonely", "alone", "isolated", "nobody to talk to", "disconnected",
    "left out", "homesick", "by myself", "distant", "alienated"
]

ABSTENTION_THRESHOLD = 0.28 # Below this score, return "I'm not sure"
SECONDARY_THRESHOLD = 0.22 # Score threshold for 2nd or 3rd tag

def get_confidence_band(score: float) -> str:
    """Return a qualitative confidence band without false-precision decimals."""
    if score >= 0.50:
        return "tentative"
    return "uncertain"

def extract_explanation_spans(text: str, detected_labels: List[str]) -> List[str]:
    """
    Extract short phrase snippets from the submitted text that contributed to the tag.
    Limits to 1-3 clear textual anchors.
    """
    if not text or not detected_labels:
        return []
    
    text_lower = text.lower()
    spans = []
    
    # 1. Check for specific student stress phrases
    if "stress/overwhelmed" in detected_labels:
        for p in STRESS_OVERWHELMED_PHRASES:
            if p in text_lower:
                spans.append(f"noticed: '{p}'")
                break
                
    if "lonely/disconnected" in detected_labels:
        for p in LONELY_DISCONNECTED_PHRASES:
            if p in text_lower:
                spans.append(f"noticed: '{p}'")
                break

    # 2. General phrase extraction (find clauses or sentences matching emotional tone)
    import re
    sentences = re.split(r'[\.\n;!?,]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 8]

    for s in sentences:
        s_lower = s.lower()
        if any(w in s_lower for w in ["feel", "felt", "worried", "tired", "happy", "calm", "rough", "hard", "heavy", "good"]):
            if len(spans) < 2:
                spans.append(f"phrase: '{s[:45]}...'")

    if not spans and sentences:
        spans.append(f"phrase: '{sentences[0][:40]}...'")

    return spans[:2]
