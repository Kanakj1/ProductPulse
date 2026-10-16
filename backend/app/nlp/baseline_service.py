"""
ProductPulse — Deterministic Rule-Based Baseline NLP Service
Encapsulates domain-locked aspect detection and aspect-conditional sentiment classification.
Uses zero external dependencies (Python 3.12 standard library regex and collections).
Provides explainable aspect-based sentiment analysis for sentences and multi-sentence reviews.
"""
from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Tuple

from backend.app.nlp.schemas import AspectName, DetectionStatus, SentimentLabel
from backend.app.nlp.tokenizer import segment_sentences, SentenceSpan


# ==============================================================================
# 1. DOMAIN ASPECT LEXICONS & DISAMBIGUATION RULES
# ==============================================================================

ASPECT_PATTERNS: Dict[AspectName, List[str]] = {
    AspectName.BUILD_DURABILITY: [
        r"\bbuild\b", r"\bdurab\w*", r"\bsturd\w*", r"\bflims\w*", r"\bfragil\w*",
        r"\bscratch\w*", r"\bdrop\w*", r"\bmaterial\w*", r"\bplastic\b", r"\bmetal\w*",
        r"\baluminum\b", r"\brubber\w*", r"\bsilicone\b", r"\bhinge\w*", r"\bcrack\w*",
        r"\bcase\b", r"\bcases\b", r"\bcover\b", r"\bcovers\b", r"\bsleeve\w*", r"\bbumper\w*",
        r"\brugged\b", r"\bheavy[- ]duty\b", r"\bfinish\b",
        # Explicit protection & drop survival
        r"\bsaved?\s+(?:my\s+)?phone\b",
        r"\bprotect\w*\s+(?:the\s+|my\s+)?phone\b",
        r"\bdrop\s+protection\b",
        r"\bshock\s*proof\b",
        r"\bshatter\s*proof\b",
        # Case structural fit (requires case/cover/casing context)
        r"\b(?:case|cover|bumper|sleeve)\s+fits?\b|\bfits?\s+(?:the\s+)?(?:case|cover|bumper|sleeve)\b",
        r"\b(?:tight|snug)\s+(?:case|cover)\b|\b(?:case|cover)\s+(?:is\s+)?(?:tight|snug)\b"
    ],
    AspectName.BATTERY_CHARGING: [
        r"\bbatter\w*", r"\bcharg\w*", r"\bdrain\w*", r"\bmah\b", r"\brun[- ]?time\b",
        r"\bpower\s*bank\b", r"\brecharg\w*", r"\bcable\w*", r"\bcord\w*", r"\bwire\w*",
        r"\bplug\w*", r"\badapter\w*", r"\bwireless\s+charg\w*", r"\bfast\s+charg\w*",
        r"\bquick\s+charg\w*", r"\boverheat\w*", r"\bbattery\s+life\b", r"\bwatt\w*"
    ],
    AspectName.SCREEN_DISPLAY: [
        r"\bscreen\w*", r"\bdisplay\w*", r"\boled\b", r"\bamoled\b", r"\blcd\b",
        r"\bretina\b", r"\bbright\w*", r"\bresolution\b", r"\btouch\w*", r"\btouchscreen\w*",
        r"\brefresh\s+rate\b", r"\b\d+hz\b", r"\bpixel\w*", r"\bglare\b", r"\bviewing\s+angle\w*",
        r"\bdim\b", r"\bdimness\b", r"\bwashed\s+out\b", r"\bglass\b", r"\bgorilla\s+glass\b",
        r"\bscreen\s+protector\w*", r"\bbezel\w*", r"\bnotch\b"
    ],
    AspectName.CAMERA_OPTICS: [
        r"\bcamera\w*", r"\bphoto\w*", r"\bphotograph\w*", r"\bpicture\w*", r"\bpic\w*",
        r"\blens\w*", r"\bvideo\w*", r"\brecording\b", r"\bsensor\w*", r"\bmegapixel\w*",
        r"\b\d+mp\b", r"\bzoom\w*", r"\bfocus\w*", r"\bportrait\w*", r"\bselfie\w*",
        r"\bnight\s+mode\b", r"\bflash\b", r"\bsharpness\b", r"\bblur\w*", r"\bbokeh\b",
        r"\bmacro\b", r"\bwide[- ]angle\b", r"\btelephoto\b"
    ],
    AspectName.CONNECTIVITY_AUDIO: [
        r"\bbluetooth\b", r"\bwi[- ]?fi\b", r"\bsignal\w*", r"\breception\b", r"\b5g\b",
        r"\b4g\b", r"\blte\b", r"\bcellular\b", r"\bantenna\w*",
        r"\bdisconnect\w*", r"\bspeaker\w*", r"\baudio\b", r"\bsound\w*", r"\bvolume\b",
        r"\bloud\b", r"\bquiet\b", r"\b(?:mic|mics|microphone\w*)\b", r"\bcall\w*", r"\bcalling\b",
        r"\bvoice\b", r"\bstatic\b", r"\b(?:headphone|earphone|earbud|headset)\w*\b",
        r"\baux\b", r"\bjack\b",
        r"\b(?:bluetooth\s+)?pair(?:s|ed|ing)?\s+(?:with|to|via|up)\b|\bpairing\b",
        r"\b(?:bluetooth|wifi|wi-fi|wireless|cellular|network|audio|call|phone|stable|unstable|lost|drop(?:ped)?)\s+connection\w*\b|\bconnection\s+(?:is\s+like\s+having\s+a\s+headset|to\s+(?:bluetooth|wifi|the\s+network|my\s+car|the\s+phone|audio))\b|\b(?:internet|network|signal|bluetooth)\s+connection\b"
    ],
    AspectName.PERFORMANCE_SOFTWARE: [
        r"\blag\w*", r"\bslow\w*", r"\bsluggish\b", r"\bfast\b", r"\bspeed\w*",
        r"\bfreeze\w*", r"\bfroze\w*", r"\bfrozen\b", r"\bcrash\w*", r"\bbug\w*",
        r"\bsoftware\b", r"\bfirmware\b", r"\bupdate\w*", r"\bos\b", r"\bandroid\b",
        r"\bios\b", r"\bapp\b", r"\bapps\b", r"\bui\b", r"\binterface\b", r"\bsystem\b",
        r"\bprocessor\w*", r"\bcpu\b", r"\b(?:microchip|chipset|soc|(?:apple|bionic|snapdragon|tensor|processor|m\d)\s+chip)\b",
        r"\bram\b", r"\bmemory\b",
        r"\bglitch\w*", r"\bboot\w*", r"\breboot\w*", r"\brestart\w*", r"\bsnappy\b",
        r"\bsmooth\w*", r"\bstutter\w*", r"\bmultitask\w*"
    ]
}

IDIOM_EXCLUSIONS = {
    AspectName.BUILD_DURABILITY: re.compile(
        r"\bin\s+(?:my|this|that|any|each|every|either|some|most|all|no|such|which)?\s*cases?\b|"
        r"\bjust\s+in\s+case\b|\bcase\s+in\s+point\b|\bcase\s+of\b|\bas\s+(?:is\s+)?the\s+case\s+may\s+be\b",
        re.IGNORECASE
    ),
    AspectName.CONNECTIVITY_AUDIO: re.compile(
        r"\b(tough|close|good|bad)\s+call\b|\bsafe\s+and\s+sound\b",
        re.IGNORECASE
    ),
    AspectName.CAMERA_OPTICS: re.compile(
        r"\[\[VIDEOID:[^\]]+\]\]|\bVIDEOID:[a-zA-Z0-9]+\b|\bVIDEOID\b|"
        r"\b(picture|photo)\s+(?:included|shows|above|below)\b|"
        r"\b(?:included|see|shown\s+in|in)\s+(?:the\s+)?(picture|photo|pic)\b|"
        r"\bpicture\s+of\s+the\s+(?:case|phone\s+case|box|packaging)\b",
        re.IGNORECASE
    ),
}


# ==============================================================================
# 2. SENTIMENT LEXICONS & NEGATION RULES
# ==============================================================================

POSITIVE_WORDS = {
    "great", "excellent", "amazing", "love", "loved", "loves", "perfect", "perfectly",
    "good", "best", "sturdy", "fast", "crisp", "vibrant", "clear", "clearly",
    "impressive", "smooth", "well", "nice", "happy", "satisfied", "pleased",
    "recommend", "recommended", "recommends", "superb", "flawless", "solid",
    "durable", "awesome", "fantastic", "wonderful", "beautiful", "easy", "easily",
    "bright", "sharp", "snappy", "reliable", "protects", "protected", "protection",
    "protect", "fine", "decent", "adequate", "handy", "quality", "responsive"
}

NEGATIVE_WORDS = {
    "terrible", "horrible", "awful", "poor", "bad", "worst", "broken", "cracked",
    "crack", "cracks", "defect", "defective", "defects", "cheap", "flimsy",
    "fragile", "freeze", "freezes", "froze", "frozen", "drain", "drains",
    "draining", "drained", "slow", "sluggish", "lag", "laggy", "lagging",
    "useless", "waste", "wasted", "disappointed", "disappointing", "disappointment",
    "fail", "failed", "fails", "failing", "failure", "broke", "break", "breaks",
    "scratch", "scratches", "scratched", "blurry", "grainy", "washed out", "dim",
    "unusable", "horrid", "disaster", "junk", "trash", "garbage", "hate", "hated",
    "hates", "annoying", "annoyed", "frustrating", "frustrated", "pain", "problem",
    "problems", "issue", "issues", "died", "dead", "loose", "peeling", "overheat",
    "overheating", "hot", "static", "muffled", "quiet", "stopped", "stops"
}

NEGATION_WORDS = {
    "not", "no", "never", "hardly", "barely", "scarcely", "doesn't", "doesnt",
    "didn't", "didnt", "won't", "wont", "can't", "cant", "cannot", "couldn't",
    "couldnt", "isn't", "isnt", "aren't", "arent", "wasn't", "wasnt", "without"
}

CONTRASTIVE_CONJUNCTIONS = re.compile(r"\b(but|however|although|though|yet|except|while)\b", re.IGNORECASE)


# ==============================================================================
# 3. CORE PREDICTION FUNCTIONS
# ==============================================================================

def detect_aspect(text: str, aspect: AspectName) -> Tuple[Optional[bool], str, float]:
    """
    Deterministically detects whether an aspect is discussed in text.
    Returns: (presence: True | False | None, rationale: str, confidence: float)
    """
    text_clean = text.strip()
    if not text_clean:
        return None, "Empty text snippet", 0.0

    sanitized_text = text_clean
    if aspect in IDIOM_EXCLUSIONS:
        sanitized_text = IDIOM_EXCLUSIONS[aspect].sub("", text_clean)

    matched_keywords = []
    for pattern in ASPECT_PATTERNS[aspect]:
        matches = re.findall(pattern, sanitized_text, re.IGNORECASE)
        if matches:
            matched_keywords.extend(matches)

    # Disambiguation: "cord" / "cable" in audio context
    if aspect == AspectName.BATTERY_CHARGING and matched_keywords:
        if all(m.lower() in {"cord", "cords", "cable", "cables", "wire", "wires"} for m in matched_keywords):
            if re.search(r"\b(headphone|audio|earphone|sound|aux|mic)\b", text_clean, re.IGNORECASE):
                return False, "Cord/cable matched in audio context (disambiguated to audio)", 0.90

    # Disambiguation: "touch" as physical feel vs touchscreen
    if aspect == AspectName.SCREEN_DISPLAY and matched_keywords:
        if all(m.lower() in {"touch"} for m in matched_keywords):
            if re.search(r"\b(soft\s+touch|touch\s+of|feel|finish|texture)\b", text_clean, re.IGNORECASE) and not re.search(r"\b(screen|display|responsive)\b", text_clean, re.IGNORECASE):
                return False, "Touch matched as physical texture (disambiguated to build)", 0.85

    # Disambiguation: Camera "focus" in generic discourse context
    if aspect == AspectName.CAMERA_OPTICS and matched_keywords:
        if all(m.lower().startswith("focus") for m in matched_keywords):
            is_discourse_focus = bool(re.search(
                r"\b(?:going\s+to|want\s+to|will|let(?:'s)?|need\s+to|try\s+to|hard\s+to)\s+focus\s+(?:on|upon)\b|"
                r"\bfocus\s+(?:on|upon)\b|"
                r"\b(?:main|primary|sole)\s+focus\b",
                text_clean, re.IGNORECASE
            ))
            has_camera_context = bool(re.search(
                r"\b(camera|lens|autofocus|auto[- ]focus|blur|blurry|sharp|sharpness|macro|photo|photograph|picture|pic|zoom|shutter|optics)\b",
                text_clean, re.IGNORECASE
            ))
            if is_discourse_focus and not has_camera_context:
                return False, "Discourse usage of 'focus' without camera/optics context", 0.90

    # Disambiguation: Audio "mic" in micro-USB / micro-SD context
    if aspect == AspectName.CONNECTIVITY_AUDIO and matched_keywords:
        if all(m.lower() in {"mic", "mics"} for m in matched_keywords):
            is_micro_spec = bool(re.search(r"\bmicro[- ]?(?:usb|sd|sim|fiber)\b|\bmicro\b", text_clean, re.IGNORECASE))
            has_audio_context = bool(re.search(r"\b(audio|voice|record|listen|speak|headset|headphone|call|sound|speaker)\b", text_clean, re.IGNORECASE))
            if is_micro_spec and not has_audio_context:
                return False, "Micro matched as micro-USB/micro-SD without audio context", 0.90

    # Disambiguation: Bare accessory nouns ("case", "cover", "sleeve", "bumper") without build/durability context
    if aspect == AspectName.BUILD_DURABILITY and matched_keywords:
        if all(m.lower() in {"case", "cases", "cover", "covers", "sleeve", "sleeves", "bumper", "bumpers"} for m in matched_keywords):
            has_durability_context = bool(re.search(
                r"\b("
                r"sturd\w*|durab\w*|flims\w*|fragil\w*|solid|rugged|heavy[- ]duty|crack\w*|scratch\w*|"
                r"broke\w*|break\w*|peel\w*|chip\w*|bend\w*|bent|shatter\w*|defect\w*|loose|fall\w*\s+apart|fell\s+apart|"
                r"well[- ]made|well[- ]constructed|craftsmanship|build\w*|finish\w*|texture\w*|"
                r"material\w*|plastic|metal\w*|aluminum|rubber\w*|silicone|leather|hinge\w*|button\w*|"
                r"protect\w*|drop\w*|save\w*|shock\w*|damage\w*|safe\w*|"
                r"fits?\s+(?:tight|snug|well|secure|loose)\w*|tight\s+fit\w*|snug\s+fit\w*|loose\s+fit\w*"
                r")\b",
                text_clean, re.IGNORECASE
            ))
            if not has_durability_context:
                return False, "Bare mention of case/accessory noun without build, material, or durability context", 0.90

    # Disambiguation: Performance "smooth" in physical texture context
    if aspect == AspectName.PERFORMANCE_SOFTWARE and matched_keywords:
        if all(m.lower() in {"smooth", "smoothly", "smoothness"} for m in matched_keywords):
            is_physical_texture = bool(re.search(
                r"\b(texture|feel|hold|hands?|grip|slip|slips|slippery|finish|surface|back|leather|plastic|silicone|rubber|glitter|case)\b",
                text_clean, re.IGNORECASE
            ))
            has_software_context = bool(re.search(
                r"\b(app|apps|ui|os|software|game|gaming|scroll|scrolling|animation|transition|operation|performance|screen|display|responsive|fast|speed|lag)\b",
                text_clean, re.IGNORECASE
            ))
            if is_physical_texture and not has_software_context:
                return False, "Smooth matched as physical material texture (disambiguated to build)", 0.85

        if all(m.lower() in {"slow", "slowly"} for m in matched_keywords):
            is_wear_shipping = bool(re.search(
                r"\b(paint|chip|chips|chipping|peel|peeling|wear|fade|fading|shipping|delivery|charge|charging|drain)\b",
                text_clean, re.IGNORECASE
            ))
            has_software_context = bool(re.search(
                r"\b(phone|system|app|apps|ui|browser|device|loading|response|lag)\b",
                text_clean, re.IGNORECASE
            ))
            if is_wear_shipping and not has_software_context:
                return False, "Slow matched in physical/wear/shipping context", 0.85

        # Disambiguation: Fast matched only in charging, charger, or shipping context
        if all(m.lower() in {"fast"} for m in matched_keywords):
            is_charging_or_shipping = bool(re.search(
                r"\b(?:charg\w*|recharg\w*|shipping|delivery|dispatch)\b",
                text_clean, re.IGNORECASE
            ))
            has_software_context = bool(re.search(
                r"\b(phone|system|app|apps|ui|browser|device|loading|response|lag|game|gaming|scroll\w*|processor|cpu|ram|boot\w*|os|multitask\w*)\b",
                text_clean, re.IGNORECASE
            ))
            if is_charging_or_shipping and not has_software_context:
                return False, "Fast matched in charging/shipping context without software context", 0.90

    if matched_keywords:
        unique_matches = sorted(list({m.lower() for m in matched_keywords}))
        return True, f"Detected aspect keywords: {unique_matches}", 0.95

    tokens = text_clean.split()
    if len(tokens) < 3:
        return None, "Snippet too brief for confident absence determination", 0.40

    return False, "No aspect keywords or domain signals detected", 0.90


SENTENCE_SPLIT_PATTERN = re.compile(r'(?<=[.!?])\s+')
CLAUSE_BOUNDARY = re.compile(
    r'(?:[;:—]|--|\b(?:but|however|although|though|yet|while|except)\b|\band\s+(?=[a-z0-9\s]*(?:phone|battery|screen|camera|sound|audio|speaker|charge|charger|case|cover|app|apps|ui|system|processor|it|is|was|won\'t|wont)\b))',
    re.IGNORECASE
)


def get_aspect_scope_text(text: str, target_aspect: AspectName) -> str:
    """
    Extracts the clause(s) or window of text corresponding to target_aspect.
    Enforces sentence boundary isolation so that subsequent or preceding statements
    in merged text snippets never leak sentiment evidence into an unrelated aspect.
    """
    # Step 1: Split into individual sentences along terminal punctuation (. ! ?)
    raw_sentences = [s.strip() for s in SENTENCE_SPLIT_PATTERN.split(text) if s.strip()]
    if not raw_sentences:
        return text

    # Filter strictly to sentences that explicitly mention the target aspect
    relevant_sentences = []
    for s in raw_sentences:
        p, _, _ = detect_aspect(s, target_aspect)
        if p is True:
            relevant_sentences.append(s)

    # If no sentence individually passed detection, fallback to full text
    if not relevant_sentences:
        return text

    # Step 2: For each sentence mentioning target_aspect, isolate the relevant clause(s)
    scoped_clauses = []
    for s in relevant_sentences:
        present_in_sentence = []
        for asp in AspectName:
            p, _, _ = detect_aspect(s, asp)
            if p is True:
                present_in_sentence.append(asp)

        # If only target_aspect is discussed in this sentence, the entire sentence is its scope
        if len(present_in_sentence) <= 1:
            scoped_clauses.append(s)
            continue

        # Multiple aspects in this sentence: split into clauses
        clauses = []
        last_idx = 0
        for match in CLAUSE_BOUNDARY.finditer(s):
            clause_str = s[last_idx:match.start()].strip()
            if clause_str:
                clauses.append((clause_str, last_idx, match.start()))
            last_idx = match.end()
        tail = s[last_idx:].strip()
        if tail:
            clauses.append((tail, last_idx, len(s)))

        if not clauses:
            scoped_clauses.append(s)
            continue

        current_owner = None
        for clause_text, start, end in clauses:
            matched_in_clause = []
            for asp in present_in_sentence:
                p, _, _ = detect_aspect(clause_text, asp)
                if p is True:
                    matched_in_clause.append(asp)

            if len(matched_in_clause) == 1:
                current_owner = matched_in_clause[0]
                if current_owner == target_aspect:
                    scoped_clauses.append(clause_text)
            elif len(matched_in_clause) > 1:
                if target_aspect in matched_in_clause:
                    scoped_clauses.append(clause_text)
            else:
                # Orphaned clause within the same sentence (e.g. "and clear")
                # Attach to current owner only if it does not introduce a separate discourse subject
                is_separate_subject = bool(re.search(r"^\b(?:i|we|you|they|he|she|it\s+was|overall)\b", clause_text, re.IGNORECASE))
                if current_owner == target_aspect and not is_separate_subject:
                    scoped_clauses.append(clause_text)

    if scoped_clauses:
        return " ".join(scoped_clauses)
    return " ".join(relevant_sentences)


def detect_sentiment(text: str, aspect: AspectName) -> Tuple[SentimentLabel, str, float]:
    """
    Deterministically assigns aspect-specific sentiment given that the aspect is discussed.
    Uses sentence-isolated clause scoping to isolate aspect-specific signals and prevent cross-aspect leakage.
    Returns: (SentimentLabel, rationale: str, confidence: float)
    """
    scope_text = get_aspect_scope_text(text, aspect)
    scope_lower = scope_text.lower()
    words = re.findall(r"\b\w+(?:'\w+)?\b", scope_lower)

    pos_hits = []
    neg_hits = []

    # Aspect-specific domain patterns
    if aspect == AspectName.BATTERY_CHARGING:
        if re.search(r"\b(?:won't|wont|cannot|cant|can't|doesn't|doesnt|failed\s+to|stopped|stops|not)\s+(?:hold\s+(?:a\s+)?charge|charge|charging)\b", scope_lower):
            neg_hits.append("won't charge")
        if re.search(r"\bdrain\w*\b", scope_lower):
            neg_hits.append("drain")
        if re.search(r"\b(?:charges?|charging)\s+(?:fast|quickly)\b", scope_lower):
            pos_hits.append("charges fast")
        if re.search(r"\bfully\s+charged\b", scope_lower):
            pos_hits.append("fully charged")

    if aspect == AspectName.BUILD_DURABILITY:
        if re.search(r"\bsaved?\s+(?:my\s+)?phone\b", scope_lower):
            pos_hits.append("saved my phone")
        if re.search(r"\b(?:heavy[- ]duty|well[- ]made|well[- ]constructed|super\s+protective|drop\s+protection)\b", scope_lower):
            pos_hits.append("well made/protective")

    # Contextual check: when battery "drains fast", "fast" indicates rapid discharge (negative), not positive speed
    has_drain_fast = bool(re.search(r"\bdrain\w*\s+(?:fast|quickly)\b", scope_lower))

    for i, w in enumerate(words):
        if w == "fast" and has_drain_fast and aspect == AspectName.BATTERY_CHARGING:
            continue

        window_start = max(0, i - 3)
        preceding = words[window_start:i]
        is_negated = any(nw in NEGATION_WORDS for nw in preceding)

        if w in POSITIVE_WORDS:
            if is_negated:
                neg_hits.append(f"not_{w}")
            else:
                pos_hits.append(w)
        elif w in NEGATIVE_WORDS:
            if is_negated:
                pos_hits.append(f"not_{w}")
            else:
                neg_hits.append(w)

    has_contrast = bool(CONTRASTIVE_CONJUNCTIONS.search(scope_text))

    if pos_hits and neg_hits:
        return SentimentLabel.UNCERTAIN_UNCLASSIFIED, f"Mixed polarity detected for {aspect.value}: pos={pos_hits}, neg={neg_hits}", 0.80

    if has_contrast and (pos_hits or neg_hits):
        if len(pos_hits) == 1 and len(neg_hits) == 0:
            return SentimentLabel.UNCERTAIN_UNCLASSIFIED, f"Contrastive conjunction with single polarity ({pos_hits}) indicates potential mixed sentiment for {aspect.value}", 0.70

    if pos_hits and not neg_hits:
        return SentimentLabel.POSITIVE, f"Positive signals for {aspect.value}: {pos_hits}", 0.90

    if neg_hits and not pos_hits:
        return SentimentLabel.NEGATIVE, f"Negative signals for {aspect.value}: {neg_hits}", 0.90

    return SentimentLabel.NEUTRAL, f"Objective description for {aspect.value} without praise or criticism", 0.75


# ==============================================================================
# 4. STRUCTURED DATA MODELS & SERVICE API
# ==============================================================================

@dataclass
class AspectDetectionResult:
    aspect_name: AspectName
    detection_status: DetectionStatus
    confidence: float
    evidence: str


@dataclass
class AspectSentimentResult:
    aspect_name: AspectName
    sentiment_label: SentimentLabel
    confidence: float
    evidence: str


@dataclass
class SentenceAnalysis:
    sentence_index: int
    sentence_text: str
    char_start: int
    char_end: int
    aspect_detections: Dict[str, AspectDetectionResult]
    aspect_sentiments: Dict[str, AspectSentimentResult] = field(default_factory=dict)


@dataclass
class ReviewAnalysis:
    review_id: str
    raw_text: str
    sentences: List[SentenceAnalysis]
    present_aspects: List[str]


class RuleBasedBaselineNLPService:
    """
    Production-grade rule-based NLP baseline service.
    Exposes sentence-level and review-level aspect extraction and sentiment analysis.
    """

    def __init__(self):
        self.all_aspects = [a for a in AspectName]

    def analyze_sentence(
        self,
        sentence_text: str,
        sentence_index: int = 0,
        char_start: int = 0,
        char_end: int = 0
    ) -> SentenceAnalysis:
        """
        Analyzes a single sentence across all 6 aspects and generates aspect-conditional sentiment.
        """
        clean_text = sentence_text.strip()
        detections: Dict[str, AspectDetectionResult] = {}
        sentiments: Dict[str, AspectSentimentResult] = {}

        for asp in self.all_aspects:
            pres, rationale, conf = detect_aspect(clean_text, asp)
            if pres is True:
                det_status = DetectionStatus.PRESENT
                detections[asp.value] = AspectDetectionResult(
                    aspect_name=asp,
                    detection_status=det_status,
                    confidence=conf,
                    evidence=rationale
                )
                # Compute sentiment only when aspect is present
                s_label, s_rationale, s_conf = detect_sentiment(clean_text, asp)
                sentiments[asp.value] = AspectSentimentResult(
                    aspect_name=asp,
                    sentiment_label=s_label,
                    confidence=s_conf,
                    evidence=s_rationale
                )
            else:
                det_status = DetectionStatus.ABSENT
                detections[asp.value] = AspectDetectionResult(
                    aspect_name=asp,
                    detection_status=det_status,
                    confidence=conf,
                    evidence=rationale
                )

        return SentenceAnalysis(
            sentence_index=sentence_index,
            sentence_text=sentence_text,
            char_start=char_start,
            char_end=char_end,
            aspect_detections=detections,
            aspect_sentiments=sentiments
        )

    def analyze_review(self, raw_text: str, review_id: str = "") -> ReviewAnalysis:
        """
        Tokenizes a multi-sentence review using the project tokenizer and extracts
        all aspects and sentiments sentence by sentence.
        """
        spans: List[SentenceSpan] = segment_sentences(raw_text)
        sentences_analysis: List[SentenceAnalysis] = []
        present_set = set()

        for span in spans:
            sa = self.analyze_sentence(
                sentence_text=span.sentence_text,
                sentence_index=span.sentence_index,
                char_start=span.char_start,
                char_end=span.char_end
            )
            sentences_analysis.append(sa)
            for asp_str, det_res in sa.aspect_detections.items():
                if det_res.detection_status == DetectionStatus.PRESENT:
                    present_set.add(asp_str)

        return ReviewAnalysis(
            review_id=review_id,
            raw_text=raw_text,
            sentences=sentences_analysis,
            present_aspects=sorted(list(present_set))
        )
