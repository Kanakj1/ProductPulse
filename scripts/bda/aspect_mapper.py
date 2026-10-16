#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ProductPulse — Hadoop Streaming Mapper for Aspect Aggregation
Processes 25k Amazon Cell Phones & Accessories reviews from standard input.
Compatible with Python 2.7 and Python 3.x.
Emits aspect-level and product-level key-value pairs for MapReduce aggregation.

Aspect detection uses domain-locked heuristics aligned with the Phase 7 baseline:
- build_durability
- battery_charging
- screen_display
- camera_optics
- connectivity_audio
- performance_software

Output format (tab-separated):
  parent_asin \t aspect \t 1 \t rating \t helpful_votes \t is_low \t is_med \t is_high
"""
import sys
import json
import re


def to_unicode(val):
    if val is None:
        return u""
    if sys.version_info[0] < 3:
        if isinstance(val, unicode):
            return val
        try:
            return str(val).decode("utf-8", "replace")
        except Exception:
            return unicode(str(val))
    else:
        if isinstance(val, bytes):
            return val.decode("utf-8", errors="replace")
        return str(val)


def to_utf8(val):
    if val is None:
        return ""
    if sys.version_info[0] < 3:
        if isinstance(val, unicode):
            return val.encode("utf-8")
        return str(val)
    else:
        if isinstance(val, bytes):
            return val.decode("utf-8", errors="replace")
        return str(val)


# Aspect regex patterns matching domain-locked lexicons
ASPECT_PATTERNS = {
    "build_durability": [
        r"\bbuild\b", r"\bdurab\w*", r"\bsturd\w*", r"\bflims\w*", r"\bfragil\w*",
        r"\bscratch\w*", r"\bdrop\w*", r"\bmaterial\w*", r"\bplastic\b", r"\bmetal\w*",
        r"\baluminum\b", r"\brubber\w*", r"\bsilicone\b", r"\bhinge\w*", r"\bcrack\w*",
        r"\bcase\b", r"\bcases\b", r"\bcover\b", r"\bcovers\b", r"\bsleeve\w*", r"\bbumper\w*",
        r"\brugged\b", r"\bheavy[- ]duty\b", r"\bfinish\b",
        r"\bsaved?\s+(?:my\s+)?phone\b", r"\bprotect\w*\s+(?:the\s+|my\s+)?phone\b",
        r"\bdrop\s+protection\b", r"\bshock\s*proof\b", r"\bshatter\s*proof\b",
        r"\b(?:case|cover|bumper|sleeve)\s+fits?\b|\bfits?\s+(?:the\s+)?(?:case|cover|bumper|sleeve)\b",
        r"\b(?:tight|snug)\s+(?:case|cover)\b|\b(?:case|cover)\s+(?:is\s+)?(?:tight|snug)\b"
    ],
    "battery_charging": [
        r"\bbatter\w*", r"\bcharg\w*", r"\bdrain\w*", r"\bmah\b", r"\brun[- ]?time\b",
        r"\bpower\s*bank\b", r"\brecharg\w*", r"\bcable\w*", r"\bcord\w*", r"\bwire\w*",
        r"\bplug\w*", r"\badapter\w*", r"\bwireless\s+charg\w*", r"\bfast\s+charg\w*",
        r"\bquick\s+charg\w*", r"\boverheat\w*", r"\bbattery\s+life\b", r"\bwatt\w*"
    ],
    "screen_display": [
        r"\bscreen\w*", r"\bdisplay\w*", r"\boled\b", r"\bamoled\b", r"\blcd\b",
        r"\bretina\b", r"\bbright\w*", r"\bresolution\b", r"\btouch\w*", r"\btouchscreen\w*",
        r"\brefresh\s+rate\b", r"\b\d+hz\b", r"\bpixel\w*", r"\bglare\b", r"\bviewing\s+angle\w*",
        r"\bdim\b", r"\bdimness\b", r"\bwashed\s+out\b", r"\bglass\b", r"\bgorilla\s+glass\b",
        r"\bscreen\s+protector\w*", r"\bbezel\w*", r"\bnotch\b"
    ],
    "camera_optics": [
        r"\bcamera\w*", r"\bphoto\w*", r"\bphotograph\w*", r"\bpicture\w*", r"\bpic\w*",
        r"\blens\w*", r"\bvideo\w*", r"\brecording\b", r"\bsensor\w*", r"\bmegapixel\w*",
        r"\b\d+mp\b", r"\bzoom\w*", r"\bfocus\w*", r"\bportrait\w*", r"\bselfie\w*",
        r"\bnight\s+mode\b", r"\bflash\b", r"\bsharpness\b", r"\bblur\w*", r"\bbokeh\b",
        r"\bmacro\b", r"\bwide[- ]angle\b", r"\btelephoto\b"
    ],
    "connectivity_audio": [
        r"\bbluetooth\b", r"\bwi[- ]?fi\b", r"\bsignal\w*", r"\breception\b", r"\b5g\b",
        r"\b4g\b", r"\blte\b", r"\bcellular\b", r"\bantenna\w*",
        r"\bdisconnect\w*", r"\bspeaker\w*", r"\baudio\b", r"\bsound\w*", r"\bvolume\b",
        r"\bloud\b", r"\bquiet\b", r"\b(?:mic|mics|microphone\w*)\b", r"\bcall\w*", r"\bcalling\b",
        r"\bvoice\b", r"\bstatic\b", r"\b(?:headphone|earphone|earbud|headset)\w*\b",
        r"\baux\b", r"\bjack\b",
        r"\b(?:bluetooth\s+)?pair(?:s|ed|ing)?\s+(?:with|to|via|up)\b|\bpairing\b",
        r"\b(?:bluetooth|wifi|wi-fi|wireless|cellular|network|audio|call|phone|stable|unstable|lost|drop(?:ped)?)\s+connection\w*\b|\bconnection\s+(?:is\s+like\s+having\s+a\s+headset|to\s+(?:bluetooth|wifi|the\s+network|my\s+car|the\s+phone|audio))\b|\b(?:internet|network|signal|bluetooth)\s+connection\b"
    ],
    "performance_software": [
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

COMPILED_PATTERNS = {
    aspect: [re.compile(pat, re.IGNORECASE | re.UNICODE) for pat in pats]
    for aspect, pats in ASPECT_PATTERNS.items()
}

IDIOM_EXCLUSIONS = {
    "build_durability": re.compile(
        r"\bin\s+(?:my|this|that|any|each|every|either|some|most|all|no|such|which)?\s*cases?\b|"
        r"\bjust\s+in\s+case\b|\bcase\s+in\s+point\b|\bcase\s+of\b|\bas\s+(?:is\s+)?the\s+case\s+may\s+be\b",
        re.IGNORECASE | re.UNICODE
    ),
    "connectivity_audio": re.compile(
        r"\b(tough|close|good|bad)\s+call\b|\bsafe\s+and\s+sound\b",
        re.IGNORECASE | re.UNICODE
    ),
    "camera_optics": re.compile(
        r"\[\[VIDEOID:[^\]]+\]\]|\bVIDEOID:[a-zA-Z0-9]+\b|\bVIDEOID\b|"
        r"\b(picture|photo)\s+(?:included|shows|above|below)\b|"
        r"\b(?:included|see|shown\s+in|in)\s+(?:the\s+)?(picture|photo|pic)\b|"
        r"\bpicture\s+of\s+the\s+(?:case|phone\s+case|box|packaging)\b",
        re.IGNORECASE | re.UNICODE
    )
}

AUDIO_CONTEXT_PATTERNS = [
    re.compile(p, re.IGNORECASE | re.UNICODE) for p in [
        r"\b(headphone|earphone|earbud|headset|audio|sound|aux|jack|mic|speaker|listen|music)\w*\b"
    ]
]


def detect_aspects(text):
    """Returns set of detected aspect names in the given text."""
    detected = set()
    text_clean = to_unicode(text).strip()
    if not text_clean:
        return detected

    for aspect, compiled_list in COMPILED_PATTERNS.items():
        sanitized = text_clean
        if aspect in IDIOM_EXCLUSIONS:
            sanitized = IDIOM_EXCLUSIONS[aspect].sub(u"", text_clean)

        matches = []
        for pat in compiled_list:
            m = pat.findall(sanitized)
            if m:
                matches.extend(m)

        # Disambiguate audio cables vs charging cables
        if aspect == "battery_charging" and matches:
            cable_only = all(
                to_unicode(term).lower() in {u"cord", u"cords", u"cable", u"cables", u"wire", u"wires"}
                for term in matches
            )
            if cable_only:
                has_audio = any(p.search(sanitized) for p in AUDIO_CONTEXT_PATTERNS)
                if has_audio:
                    continue

        if matches:
            detected.add(aspect)

    return detected


def _write_record(parent_asin, aspect, rating, helpful, is_low, is_med, is_high):
    line = u"{0}\t{1}\t1\t{2:.1f}\t{3}\t{4}\t{5}\t{6}\n".format(
        parent_asin, aspect, rating, helpful, is_low, is_med, is_high
    )
    if sys.version_info[0] < 3:
        sys.stdout.write(line.encode("utf-8"))
    else:
        sys.stdout.write(line)


def main():
    for line in sys.stdin:
        line_str = line.strip()
        if not line_str:
            continue

        try:
            record = json.loads(line_str)
        except Exception:
            # Report malformed record transparently
            if sys.version_info[0] < 3:
                sys.stdout.write("__MALFORMED__\t__RECORD__\t1\t0.0\t0\t0\t0\t0\n")
            else:
                sys.stdout.write("__MALFORMED__\t__RECORD__\t1\t0.0\t0\t0\t0\t0\n")
            continue

        raw_parent = record.get("parent_asin") or record.get("asin") or "UNKNOWN"
        parent_asin = to_unicode(raw_parent)
        try:
            rating = float(record.get("rating", 0.0))
        except (ValueError, TypeError):
            rating = 0.0

        try:
            helpful = int(record.get("helpful_vote", 0))
        except (ValueError, TypeError):
            helpful = 0

        # Rating bands: explicitly based on Amazon 1-5 star ratings, NOT sentiment
        # low: 1.0 - 2.0 stars; med: 3.0 stars; high: 4.0 - 5.0 stars
        is_low = 1 if rating <= 2.0 else 0
        is_med = 1 if rating == 3.0 else 0
        is_high = 1 if rating >= 4.0 else 0

        title = to_unicode(record.get("title"))
        text = to_unicode(record.get("text"))
        combined = (title + u" " + text).strip()

        # Emit product total review record
        _write_record(parent_asin, u"__ALL_REVIEWS__", rating, helpful, is_low, is_med, is_high)

        # Note: detect_aspects returns a set(), ensuring at most one emission per aspect per review.
        # Downstream MapReduce aggregation therefore yields distinct reviews mentioning the aspect.
        detected = detect_aspects(combined)
        if detected:
            for aspect in sorted(detected):
                _write_record(parent_asin, aspect, rating, helpful, is_low, is_med, is_high)
        else:
            _write_record(parent_asin, u"__NO_ASPECT__", rating, helpful, is_low, is_med, is_high)


if __name__ == "__main__":
    main()
