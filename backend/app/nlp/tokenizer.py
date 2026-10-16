"""
ProductPulse — NLP Robust Sentence Segmenter
Deterministic, offset-preserving sentence segmenter implemented using pure Python standard library regex.
Tracks exact [char_start, char_end] character indices in the original raw review text.
"""
import re
from typing import List, Optional
from backend.app.nlp.schemas import SentenceSpan

# Common abbreviations in English and e-commerce reviews that shouldn't trigger sentence splits
COMMON_ABBREVIATIONS = {
    "e.g.", "i.e.", "vs.", "approx.", "oz.", "ft.", "in.", "yd.", "lb.", "lbs.",
    "no.", "nos.", "vol.", "v1.0", "v2.0", "v3.0", "etc.", "mr.", "mrs.", "ms.",
    "dr.", "prof.", "gen.", "rep.", "sen.", "st.", "co.", "corp.", "inc.", "ltd."
}

# Regex matching potential sentence termination followed by whitespace and next sentence start or end of text
_TERMINAL_PUNCT_PATTERN = re.compile(r'([.!?]+|\n+)(?=(\s+|$))')


def segment_sentences(
    raw_text: Optional[str],
    raw_title: Optional[str] = None
) -> List[SentenceSpan]:
    """
    Deterministically segment review text into sentence spans with exact character offsets.
    
    If raw_text is None or whitespace-only, attempts fallback to raw_title.
    If both are blank/empty, returns an empty list.
    
    Args:
        raw_text: Customer review text.
        raw_title: Optional customer review headline.
        
    Returns:
        List of SentenceSpan objects containing exact character slice boundaries.
    """
    if raw_text is None or not raw_text.strip():
        if raw_title is not None and raw_title.strip():
            # Fallback to title as single sentence index 0
            title_clean = raw_title.strip()
            # Find offsets in original raw_title
            start = raw_title.find(title_clean)
            end = start + len(title_clean)
            return [
                SentenceSpan(
                    sentence_index=0,
                    sentence_text=title_clean,
                    char_start=start,
                    char_end=end,
                    is_title=True
                )
            ]
        return []

    text_len = len(raw_text)
    spans: List[SentenceSpan] = []
    
    current_start = 0
    # Advance past any leading whitespace
    while current_start < text_len and raw_text[current_start].isspace():
        current_start += 1
        
    if current_start >= text_len:
        return []

    idx = current_start
    while idx < text_len:
        # Check for paragraph breaks (one or more newlines)
        if raw_text[idx] == '\n':
            seg_text = raw_text[current_start:idx].strip()
            if seg_text:
                actual_start = raw_text.find(seg_text, current_start)
                actual_end = actual_start + len(seg_text)
                spans.append(
                    SentenceSpan(
                        sentence_index=len(spans),
                        sentence_text=seg_text,
                        char_start=actual_start,
                        char_end=actual_end,
                        is_title=False
                    )
                )
            # Advance past newlines and leading whitespace
            while idx < text_len and raw_text[idx].isspace():
                idx += 1
            current_start = idx
            continue

        # Check for sentence terminal punctuation: . ! ?
        if raw_text[idx] in {'.', '!', '?'}:
            # Find end of consecutive punctuation (e.g. "...", "!?")
            punct_end = idx
            while punct_end < text_len and raw_text[punct_end] in {'.', '!', '?'}:
                punct_end += 1

            # Check if this period is part of a number (e.g. "3.5", ".99")
            if raw_text[idx] == '.':
                is_prev_digit = (idx > 0 and raw_text[idx - 1].isdigit())
                is_next_digit = (punct_end < text_len and raw_text[punct_end].isdigit())
                if is_prev_digit and is_next_digit:
                    idx = punct_end
                    continue

                # Check if it's an abbreviation
                # Look back up to 10 characters to see the preceding word token
                token_start = idx - 1
                while token_start >= 0 and (raw_text[token_start].isalnum() or raw_text[token_start] in {'.', '_'}):
                    token_start -= 1
                token_start += 1
                preceding_token = raw_text[token_start:punct_end].lower()
                if preceding_token in COMMON_ABBREVIATIONS:
                    idx = punct_end
                    continue

            # Check if followed by whitespace or end of string
            if punct_end >= text_len or raw_text[punct_end].isspace():
                candidate_text = raw_text[current_start:punct_end].strip()
                if candidate_text:
                    actual_start = raw_text.find(candidate_text, current_start)
                    actual_end = actual_start + len(candidate_text)
                    spans.append(
                        SentenceSpan(
                            sentence_index=len(spans),
                            sentence_text=candidate_text,
                            char_start=actual_start,
                            char_end=actual_end,
                            is_title=False
                        )
                    )
                # Advance past whitespace
                idx = punct_end
                while idx < text_len and raw_text[idx].isspace():
                    idx += 1
                current_start = idx
                continue
            else:
                idx = punct_end
                continue

        idx += 1

    # Remaining trailing text
    if current_start < text_len:
        trailing_text = raw_text[current_start:].strip()
        if trailing_text:
            actual_start = raw_text.find(trailing_text, current_start)
            actual_end = actual_start + len(trailing_text)
            spans.append(
                SentenceSpan(
                    sentence_index=len(spans),
                    sentence_text=trailing_text,
                    char_start=actual_start,
                    char_end=actual_end,
                    is_title=False
                )
            )

    return spans
