"""
Crisis-Language Detection & Safety Routing Service.
Strictly separated from general emotion classification and LLMs.
Runs before emotion analysis or RAG generation on submitted text only.

IMPORTANT SAFETY & PRIVACY CONSTRAINTS:
1. Never store raw crisis text in audit logs, application traces, or admin dashboards.
2. Output is classified as:
   - 'explicit_urgent_language': severe immediate self-harm / suicide intent -> trigger fixed support UI
   - 'ambiguous_distress': ambiguous deep hopelessness -> trigger optional calm support banner
   - 'no_signal_detected': no crisis indicators detected (does NOT guarantee safety)
3. Pause is not monitored, does not contact emergency services automatically, and cannot guarantee detection.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class CrisisDetectionResult(BaseModel):
    detected_class: str # "explicit_urgent_language", "ambiguous_distress", "no_signal_detected"
    confidence_label: str # "high", "moderate", "none"
    support_action: str # "urgent_modal", "optional_banner", "none"
    model_id: str = "pause-crisis-detector-ensemble"
    model_version: str = "2026.1-calibrated"
    matched_stems: List[str] = []
    is_negated: bool = False
    is_third_party: bool = False
    is_past_tense: bool = False
    is_quote: bool = False
    user_message: str
    helpline_contacts: List[Dict[str, str]] = []


# Explicit urgent phrase stems
EXPLICIT_URGENT_STEMS = [
    r"\bkill(ing)?\s+(my|one)?self\b",
    r"\bend(ing)?\s+(my|one'?s)?\s+life\b",
    r"\bsuicid(e|al)\b",
    r"\bwant\s+to\s+die\b",
    r"\bcommit(ting)?\s+suicide\b",
    r"\btak(e|ing)\s+my\s+(own\s+)?life\b",
    r"\bhang(ing)?\s+myself\b",
    r"\boverdos(e|ing)\s+on\s+pills\b",
    r"\bslit(ting)?\s+my\s+wrists\b",
    r"\bjump(ing)?\s+off(\s+(a\s+|the\s+)?(bridge|building|roof|cliff|ledge))?\b",
    r"\bbetter\s+off\s+dead\b",
    r"\bplan(ning)?\s+to\s+kill\s+myself\b",
    r"\bfeel\s+like\s+ending\s+my\s+life\b"
]

# Ambiguous deep distress stems
AMBIGUOUS_DISTRESS_STEMS = [
    r"\bno\s+reason\s+to\s+live\b",
    r"\bdon'?t\s+want\s+to\s+wake\s+up\b",
    r"\beveryone\s+(would\s+be\s+)?better\s+off\s+without\s+me\b",
    r"\bcan'?t\s+go\s+on\s+(any\s*more|with\s+this)\b",
    r"\bnothing\s+matters\s+any\s*more\b",
    r"\btired\s+of\s+(living|life|everything)\b",
    r"\bhopeless\s+and\s+trapped\b",
    r"\bwant\s+to\s+disappear\s+forever\b",
    r"\bcan'?t\s+take\s+this\s+(pain|burden)\b",
    r"\bwish\s+i\s+never\s+existed\b"
]

# Idiomatic non-crisis expressions (to prevent false alarms)
IDIOMATIC_NON_CRISIS = [
    r"\bdying\s+of\s+laughter\b",
    r"\bthis\s+(exam|homework|assignment|project|lab)\s+is\s+killing\s+me\b",
    r"\bdead\s+tired\b",
    r"\bkilling\s+time\b",
    r"\bi'?m\s+dead\s+after\s+that\s+workout\b",
    r"\bstarving\s+to\s+death\b"
]

# Specific crisis negation patterns (only negates when crisis phrase is directly negated)
CRISIS_NEGATION_PATTERNS = [
    r"\b(do\s+not|don'?t|did\s+not|didn'?t|never)\s+(want\s+to\s+)?(die|kill\s+myself|end\s+my\s+life|hurt\s+myself)\b",
    r"\b(not|never|no\s+longer)\s+suicid(e|al)\b",
    r"\bstopped\s+feeling\s+like\s+(i\s+wanted\s+to\s+)?(end\s+my\s+life|die|kill\s+myself)\b"
]

# Third party indicators
THIRD_PARTY_PATTERNS = [
    r"\b(my\s+friend|my\s+roommate|my\s+brother|my\s+sister|someone\s+else|he\s+said|she\s+said|they\s+said|heard\s+that)\b"
]

# Past-tense reflection indicators
PAST_TENSE_PATTERNS = [
    r"\b(years\s+ago|in\s+high\s+school|back\s+in\s+\d{4}|used\s+to\s+think|overcame|in\s+the\s+past|long\s+time\s+ago)\b"
]

# Standard India support contacts
DEFAULT_HELPLINE_CONTACTS = [
    {
        "name": "Tele-MANAS (Govt of India)",
        "contact": "14416 / 1800-89-14416",
        "description": "Toll-free, 24/7 mental health counseling in 20+ Indian languages."
    },
    {
        "name": "National Emergency Service",
        "contact": "112",
        "description": "24/7 emergency response (police, medical, fire)."
    },
    {
        "name": "KIRAN Helpline",
        "contact": "1800-599-0019",
        "description": "Ministry of Social Justice 24/7 counseling support."
    },
    {
        "name": "Vandrevala Foundation",
        "contact": "+91 9999 666 555",
        "description": "Free, confidential 24/7 mental wellness support."
    }
]


class CrisisDetectionService:
    def __init__(self):
        self.model_id = "pause-crisis-detector-ensemble"
        self.model_version = "2026.1-calibrated"

    def evaluate_text(self, text: str) -> CrisisDetectionResult:
        """
        Evaluate submitted text for crisis signals.
        Returns CrisisDetectionResult with detected class, confidence, and action.
        """
        if not text or not text.strip():
            return CrisisDetectionResult(
                detected_class="no_signal_detected",
                confidence_label="none",
                support_action="none",
                user_message="No crisis signal detected.",
                helpline_contacts=[]
            )

        t_lower = text.lower().strip()

        # 1. Check for idioms (e.g. "dying of laughter", "exam is killing me")
        for idiom in IDIOMATIC_NON_CRISIS:
            if re.search(idiom, t_lower):
                # Check if there is an explicit suicide phrase as well
                has_explicit = any(re.search(pat, t_lower) for pat in EXPLICIT_URGENT_STEMS)
                if not has_explicit:
                    return CrisisDetectionResult(
                        detected_class="no_signal_detected",
                        confidence_label="none",
                        support_action="none",
                        user_message="No crisis signal detected.",
                        helpline_contacts=[]
                    )

        # 2. Check for quotes / song lyrics
        is_quote = ('"' in text or "“" in text or "lyrics" in t_lower or "song" in t_lower or "poem" in t_lower)

        # 3. Check for third-party concern ("my friend is suicidal")
        is_third_party = any(re.search(pat, t_lower) for pat in THIRD_PARTY_PATTERNS)

        # 4. Check for past-tense reflection ("years ago I felt like ending things, but now I'm doing well")
        is_past_tense = any(re.search(pat, t_lower) for pat in PAST_TENSE_PATTERNS)

        # 5. Check for targeted crisis negation ("I do not want to die", "I am not suicidal")
        is_negated = any(re.search(npat, t_lower) for npat in CRISIS_NEGATION_PATTERNS)

        # Check explicit urgent stems
        matched_explicit = []
        for pat in EXPLICIT_URGENT_STEMS:
            if re.search(pat, t_lower):
                matched_explicit.append(pat)

        if matched_explicit and not is_negated:
            if is_third_party:
                return CrisisDetectionResult(
                    detected_class="ambiguous_distress",
                    confidence_label="moderate",
                    support_action="optional_banner",
                    matched_stems=["third_party_concern"],
                    is_third_party=True,
                    is_quote=is_quote,
                    user_message="It sounds like you may be concerned about someone close to you. Here are resources you can share with them.",
                    helpline_contacts=DEFAULT_HELPLINE_CONTACTS
                )

            if is_past_tense and not any(k in t_lower for k in ["now", "today", "currently", "still"]):
                return CrisisDetectionResult(
                    detected_class="no_signal_detected",
                    confidence_label="none",
                    support_action="none",
                    matched_stems=matched_explicit,
                    is_past_tense=True,
                    user_message="Past reflection noted. No current crisis signal detected.",
                    helpline_contacts=[]
                )

            return CrisisDetectionResult(
                detected_class="explicit_urgent_language",
                confidence_label="high",
                support_action="urgent_modal",
                matched_stems=matched_explicit,
                is_quote=is_quote,
                user_message="It sounds like you may be carrying overwhelming pain right now. Please know that free, confidential human support is available to you right now.",
                helpline_contacts=DEFAULT_HELPLINE_CONTACTS
            )

        # Check ambiguous distress stems
        matched_ambiguous = []
        for pat in AMBIGUOUS_DISTRESS_STEMS:
            if re.search(pat, t_lower):
                matched_ambiguous.append(pat)

        if matched_ambiguous and not is_negated:
            return CrisisDetectionResult(
                detected_class="ambiguous_distress",
                confidence_label="moderate",
                support_action="optional_banner",
                matched_stems=matched_ambiguous,
                is_third_party=is_third_party,
                is_quote=is_quote,
                user_message="You mentioned feeling exhausted or that things feel very difficult. If you want to talk to someone, confidential support is always available.",
                helpline_contacts=DEFAULT_HELPLINE_CONTACTS
            )

        return CrisisDetectionResult(
            detected_class="no_signal_detected",
            confidence_label="none",
            support_action="none",
            matched_stems=[],
            is_negated=is_negated,
            is_third_party=is_third_party,
            is_past_tense=is_past_tense,
            user_message="No crisis signal detected. (Note: Pause cannot guarantee risk detection or replace human counseling.)",
            helpline_contacts=[]
        )


crisis_service = CrisisDetectionService()
