#!/usr/bin/env python3
"""
ProductPulse — Explainable Automated Draft Annotation Generator (Phase 7C)
Generates deterministic, explainable pseudo-labels for Sample A and Sample B
using regex lexicons, disambiguation rules, negation detection, and sentiment analysis.

DISCLAIMER & PROVENANCE NOTICE:
These annotations are machine-generated draft labels produced by a deterministic
rule-based heuristic. They are NOT human gold labels and have NOT been verified by a human.
They are provided solely to allow pipeline demonstration and workflow testing today
without overwriting canonical templates.
"""
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.nlp.schemas import AspectName, SentimentLabel
from scripts.reconcile_annotations import reconcile_sample_a, reconcile_sample_b


# ==============================================================================
# 1. DOMAIN ASPECT LEXICONS & DISAMBIGUATION RULES
# ==============================================================================

ASPECT_PATTERNS: Dict[AspectName, List[str]] = {
    AspectName.BUILD_DURABILITY: [
        r"\bbuild\b", r"\bdurab\w*", r"\bsturd\w*", r"\bflims\w*", r"\bfragil\w*",
        r"\bscratch\w*", r"\bdrop\w*", r"\bmaterial\w*", r"\bplastic\b", r"\bmetal\w*",
        r"\baluminum\b", r"\brubber\w*", r"\bsilicone\b", r"\bhinge\w*", r"\bcrack\w*",
        r"\bcase\b", r"\bcases\b", r"\bcover\b", r"\bcovers\b", r"\bsleeve\w*", r"\bbumper\w*",
        r"\brugged\b", r"\bheavy[- ]duty\b", r"\bfit\b", r"\bsnug\b", r"\bfinish\b"
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
        # Bounded pairing
        r"\b(?:bluetooth\s+)?pair(?:s|ed|ing)?\s+(?:with|to|via|up)\b|\bpairing\b",
        # Bounded connection
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

# Negative disambiguation patterns (words that look like aspect keywords but are NOT)
IDIOM_EXCLUSIONS = {
    # Durability idiom: "in my case", "in this case", "just in case", "in any case", "in either case", "case of"
    AspectName.BUILD_DURABILITY: re.compile(
        r"\bin\s+(?:my|this|that|any|each|every|either|some|most|all|no|such|which)?\s*cases?\b|"
        r"\bjust\s+in\s+case\b|\bcase\s+in\s+point\b|\bcase\s+of\b|\bas\s+(?:is\s+)?the\s+case\s+may\s+be\b",
        re.IGNORECASE
    ),
    # Audio idioms: "tough call", "close call", "safe and sound"
    AspectName.CONNECTIVITY_AUDIO: re.compile(
        r"\b(tough|close|good|bad)\s+call\b|\bsafe\s+and\s+sound\b",
        re.IGNORECASE
    ),
    # Camera metadata & listing photo idioms: [[VIDEOID:...]], "picture included", "in the picture", "shown in the picture"
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
# 3. ASPECT & SENTIMENT INFERENCE FUNCTIONS
# ==============================================================================

def detect_aspect(text: str, aspect: AspectName) -> Tuple[Optional[bool], str, float]:
    """
    Deterministically detects whether an aspect is mentioned in text.
    Returns: (presence: True | False | None, rationale: str, confidence: float)
      - True (present): explicit aspect keywords matched and passed disambiguation.
      - False (absent): sentence has adequate text and zero aspect indicators.
      - None (unresolved): ambiguous or insufficient evidence.
    """
    text_clean = text.strip()
    if not text_clean:
        return None, "Empty text snippet", 0.0

    # Check for idiomatic exclusion if applicable
    sanitized_text = text_clean
    if aspect in IDIOM_EXCLUSIONS:
        sanitized_text = IDIOM_EXCLUSIONS[aspect].sub("", text_clean)

    matched_keywords = []
    for pattern in ASPECT_PATTERNS[aspect]:
        matches = re.findall(pattern, sanitized_text, re.IGNORECASE)
        if matches:
            matched_keywords.extend(matches)

    # Disambiguation: "cord" / "cable" with audio context
    if aspect == AspectName.BATTERY_CHARGING and matched_keywords:
        if all(m.lower() in {"cord", "cords", "cable", "cables", "wire", "wires"} for m in matched_keywords):
            if re.search(r"\b(headphone|audio|earphone|sound|aux|mic)\b", text_clean, re.IGNORECASE):
                # Attribute to connectivity_audio instead
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

    if matched_keywords:
        unique_matches = sorted(list({m.lower() for m in matched_keywords}))
        return True, f"Detected aspect keywords: {unique_matches}", 0.95

    # If sentence is extremely short (< 3 words) without keywords, mark unresolved
    tokens = text_clean.split()
    if len(tokens) < 3:
        return None, "Snippet too brief for confident absence determination", 0.40

    return False, "No aspect keywords or domain signals detected", 0.90


def detect_sentiment(text: str, aspect: AspectName) -> Tuple[SentimentLabel, str, float]:
    """
    Deterministically assigns aspect-specific sentiment given that the aspect is present.
    Returns: (SentimentLabel, rationale: str, confidence: float)
    """
    text_lower = text.lower()
    words = re.findall(r"\b\w+(?:'\w+)?\b", text_lower)

    pos_hits = []
    neg_hits = []

    for i, w in enumerate(words):
        # Lookback up to 3 tokens for negation
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

    has_contrast = bool(CONTRASTIVE_CONJUNCTIONS.search(text))

    # Check for mixed polarity or contrastive ambiguity
    if pos_hits and neg_hits:
        return SentimentLabel.UNCERTAIN_UNCLASSIFIED, f"Mixed polarity detected: pos={pos_hits}, neg={neg_hits}", 0.80

    if has_contrast and (pos_hits or neg_hits):
        # Contrastive word with sentiment often signals qualification (e.g. "nice case but...")
        if len(pos_hits) == 1 and len(neg_hits) == 0:
            # Check if negative clause follows but lacks explicit keyword
            return SentimentLabel.UNCERTAIN_UNCLASSIFIED, f"Contrastive conjunction with single polarity ({pos_hits}) indicates potential mixed sentiment", 0.70

    if pos_hits and not neg_hits:
        return SentimentLabel.POSITIVE, f"Positive signals: {pos_hits}", 0.90

    if neg_hits and not pos_hits:
        return SentimentLabel.NEGATIVE, f"Negative signals: {neg_hits}", 0.90

    # Factual / specification sentences without sentiment words
    # e.g., "outputs 15 watts", "plastic case with cutout", "glass screen protector"
    return SentimentLabel.NEUTRAL, "Objective description without praise or criticism", 0.75


# ==============================================================================
# 4. AUTO-DRAFT GENERATION WORKFLOW
# ==============================================================================

def generate_auto_drafts(version: str = "v2", output_dir: str = "data/annotation") -> Dict:
    """
    Generates Sample A and Sample B auto-draft CSVs, companion report, and reconciles them.
    Never modifies canonical templates or raw data.
    """
    # Paths
    sample_a_tmpl_csv = "data/annotation/sample_a_aspect_detection_template.csv"
    sample_a_tmpl_jsonl = "data/annotation/sample_a_aspect_detection_template.jsonl"
    sample_b_tmpl_csv = "data/annotation/sample_b_aspect_sentiment_template.csv"
    sample_b_tmpl_jsonl = "data/annotation/sample_b_aspect_sentiment_template.jsonl"

    suffix = f"_{version}" if version else ""
    sample_a_draft_csv = f"{output_dir}/sample_a_aspect_detection_auto_draft{suffix}.csv"
    sample_b_draft_csv = f"{output_dir}/sample_b_aspect_sentiment_auto_draft{suffix}.csv"
    sample_a_reconciled_jsonl = f"{output_dir}/sample_a_auto_reconciled{suffix}.jsonl"
    sample_b_reconciled_jsonl = f"{output_dir}/sample_b_auto_reconciled{suffix}.jsonl"
    report_path = f"{output_dir}/auto_draft_generation_report{suffix}.json"

    # --- PROCESS SAMPLE A ---
    sample_a_rows: List[Dict] = []
    with open(sample_a_tmpl_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sample_a_rows = list(reader)

    sample_a_stats = {
        "total_sentences": len(sample_a_rows),
        "total_aspect_decisions": len(sample_a_rows) * 6,
        "present_count": 0,
        "absent_count": 0,
        "unresolved_count": 0,
        "per_aspect_present": {a.value: 0 for a in AspectName}
    }

    sample_a_draft_rows: List[Dict] = []
    aspect_list = [
        "build_durability", "battery_charging", "screen_display",
        "camera_optics", "connectivity_audio", "performance_software"
    ]

    for row in sample_a_rows:
        text = row["sentence_text"]
        new_row = dict(row)
        detected_notes = []

        for asp_str in aspect_list:
            asp_enum = AspectName(asp_str)
            presence, rationale, conf = detect_aspect(text, asp_enum)
            if presence is True:
                new_row[asp_str] = "1"
                sample_a_stats["present_count"] += 1
                sample_a_stats["per_aspect_present"][asp_str] += 1
                detected_notes.append(f"{asp_str}:present")
            elif presence is False:
                new_row[asp_str] = "0"
                sample_a_stats["absent_count"] += 1
            else:
                new_row[asp_str] = ""  # Unresolved -> left blank
                sample_a_stats["unresolved_count"] += 1
                detected_notes.append(f"{asp_str}:unresolved")

        note_str = "auto_draft: " + (", ".join(detected_notes) if detected_notes else "all_absent")
        new_row["annotator_notes"] = note_str
        sample_a_draft_rows.append(new_row)

    # Write Sample A Draft CSV
    with open(sample_a_draft_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(sample_a_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_a_draft_rows)

    # --- PROCESS SAMPLE B ---
    sample_b_rows: List[Dict] = []
    with open(sample_b_tmpl_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sample_b_rows = list(reader)

    sample_b_stats = {
        "total_units": len(sample_b_rows),
        "confirmed_present": 0,
        "confirmed_absent": 0,
        "unresolved": 0,
        "sentiment_distribution": {
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "uncertain/unclassified": 0
        }
    }

    sample_b_draft_rows: List[Dict] = []

    for row in sample_b_rows:
        text = row["sentence_text"]
        target_asp = AspectName(row["target_aspect"])
        new_row = dict(row)

        presence, p_rationale, p_conf = detect_aspect(text, target_asp)

        if presence is True:
            new_row["aspect_confirmed"] = "1"
            sample_b_stats["confirmed_present"] += 1

            sentiment, s_rationale, s_conf = detect_sentiment(text, target_asp)
            new_row["human_sentiment"] = sentiment.value
            sample_b_stats["sentiment_distribution"][sentiment.value] += 1
            new_row["annotator_notes"] = f"auto_draft: present ({p_rationale}); {sentiment.value} ({s_rationale})"

        elif presence is False:
            new_row["aspect_confirmed"] = "0"
            new_row["human_sentiment"] = ""  # Must be null for absent
            sample_b_stats["confirmed_absent"] += 1
            new_row["annotator_notes"] = f"auto_draft: absent ({p_rationale})"

        else:
            # Unresolved aspect presence -> leave blank
            new_row["aspect_confirmed"] = ""
            new_row["human_sentiment"] = ""
            sample_b_stats["unresolved"] += 1
            new_row["annotator_notes"] = f"auto_draft: unresolved ({p_rationale})"

        sample_b_draft_rows.append(new_row)

    # Write Sample B Draft CSV
    with open(sample_b_draft_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(sample_b_rows[0].keys()))
        writer.writeheader()
        writer.writerows(sample_b_draft_rows)

    # --- GENERATE COMPANION REPORT ---
    report = {
        "report_version": "2.0" if version == "v2" else "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "AUTOMATICALLY GENERATED DRAFT LABELS. "
            "These annotations were generated deterministically using rule-based keyword lexicons, "
            "negation tracking, and heuristics. They are NOT human gold annotations and have NOT been verified by a human. "
            "Do not report baseline model accuracy or benchmark performance against these labels as if they were human truth."
        ),
        "methodology": {
            "aspect_detection": (
                "Domain-locked regex lexicon with targeted heuristic disambiguations: "
                "1. Micro/micro-USB excluded from mic/microphone audio detection. "
                "2. Listing photos ('picture included', 'in the picture') and [[VIDEOID:...]] excluded from camera detection. "
                "3. Discourse 'focus on' excluded from camera detection without optical context. "
                "4. Idioms ('in my case', 'in this case', 'just in case') excluded from build/durability. "
                "5. Physical texture ('smooth texture', 'smooth feel', 'paint chips') excluded from software performance. "
                "6. Bounded audio/connectivity ('headset', 'pairing', 'connection') with context gating."
            ),
            "sentiment_classification": "Lexicon matching with 3-token lookback negation flipping and contrastive conjunction mixed-sentiment detection",
            "uncertainty_policy": "Unresolved presence left blank (unannotated); ambiguous/mixed sentiment classified as 'uncertain/unclassified'"
        },
        "sample_a_detection_draft": {
            "source_csv": sample_a_draft_csv,
            "canonical_template": sample_a_tmpl_jsonl,
            "statistics": sample_a_stats
        },
        "sample_b_sentiment_draft": {
            "source_csv": sample_b_draft_csv,
            "canonical_template": sample_b_tmpl_jsonl,
            "statistics": sample_b_stats
        }
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # --- RECONCILE WITH SQLITE VERIFICATION ---
    recon_a = reconcile_sample_a(
        csv_path=sample_a_draft_csv,
        canonical_jsonl_path=sample_a_tmpl_jsonl,
        output_jsonl_path=sample_a_reconciled_jsonl,
        db_path="backend/db/productpulse.db",
        overwrite=True
    )

    recon_b = reconcile_sample_b(
        csv_path=sample_b_draft_csv,
        canonical_jsonl_path=sample_b_tmpl_jsonl,
        output_jsonl_path=sample_b_reconciled_jsonl,
        db_path="backend/db/productpulse.db",
        overwrite=True
    )

    return {
        "sample_a_draft_csv": sample_a_draft_csv,
        "sample_b_draft_csv": sample_b_draft_csv,
        "sample_a_reconciled_jsonl": sample_a_reconciled_jsonl,
        "sample_b_reconciled_jsonl": sample_b_reconciled_jsonl,
        "report_path": report_path,
        "reconciliation_a": recon_a,
        "reconciliation_b": recon_b,
        "sample_a_stats": sample_a_stats,
        "sample_b_stats": sample_b_stats
    }


def main():
    print("[INFO] Generating deterministic automated draft annotations...")
    results = generate_auto_drafts()
    print("[SUCCESS] Draft annotations generated and reconciled successfully!")
    print(f"  Sample A Reconciled: {results['sample_a_reconciled_jsonl']}")
    print(f"  Sample B Reconciled: {results['sample_b_reconciled_jsonl']}")
    print(f"  Companion Report:    {results['report_path']}")
    print("\nSummary Statistics:")
    print("  Sample A Decisions:", results["sample_a_stats"])
    print("  Sample B Units:    ", results["sample_b_stats"])


if __name__ == "__main__":
    main()
