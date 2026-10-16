"""
ProductPulse — Baseline NLP Pipeline Demonstration
Demonstrates end-to-end sentence tokenization, aspect detection, and aspect-conditional
sentiment classification using real, traceable reviews queried read-only from SQLite.

Explicit Academic Framing:
All displayed aspects and sentiments are RULE-BASED MODEL PREDICTIONS generated
dynamically by the baseline heuristic engine. They are NOT human ground truth.
"""
import os
import sqlite3
import sys

sys.path.insert(0, os.getcwd())

from backend.app.nlp.baseline_service import (
    RuleBasedBaselineNLPService,
    ReviewAnalysis,
    SentenceAnalysis
)
from backend.app.nlp.schemas import DetectionStatus

# Three real, traceable review IDs verified from backend/db/productpulse.db
DEMO_REVIEW_IDS = [
    "ce3691f979ab4e2a56407049312fe718661f9363ff76a2dfb477d300573c9ec3",
    "b1e95f6b04986e2f1eff6f58b55d76bae805e98428cc344b0acedba3a6239e4b",
    "6b07278b9a3ddd5cee0dbda914454236776f02d5faf4fe55aa1e606f54fe93a1"
]


def run_demo(db_path: str = "backend/db/productpulse.db"):
    print("================================================================================")
    print(" ProductPulse — Baseline NLP Pipeline Demonstration")
    print(" Dynamic Inference on Real Reviews from SQLite (Read-Only)")
    print(" Disclaimer: Predictions are rule-based model outputs, NOT ground truth.")
    print("================================================================================")

    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found at: {db_path}")
        sys.exit(1)

    # Open SQLite in read-only mode to prevent any modification
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    c = conn.cursor()

    service = RuleBasedBaselineNLPService()

    for idx, review_id in enumerate(DEMO_REVIEW_IDS, 1):
        c.execute(
            """
            SELECT review_id, parent_asin, rating, verified_purchase, raw_title, raw_text
            FROM reviews
            WHERE review_id = ?
            """,
            (review_id,)
        )
        row = c.fetchone()
        if not row:
            print(f"[WARNING] Review ID {review_id} not found in database.")
            continue

        rid, pasin, rating, verified, title, raw_text = row

        print(f"\n--------------------------------------------------------------------------------")
        print(f"EXAMPLE {idx}: Review ID: {rid}")
        print(f"Parent ASIN: {pasin} | Source Rating: {rating}* | Verified: {bool(verified)}")
        print(f"Title: \"{title}\"")
        print(f"Raw Text: \"{raw_text}\"")
        print(f"--------------------------------------------------------------------------------")

        # Run dynamic baseline NLP pipeline
        analysis: ReviewAnalysis = service.analyze_review(raw_text, review_id=rid)

        print(f"Segmented Sentences ({len(analysis.sentences)}):")
        for s_idx, sa in enumerate(analysis.sentences):
            print(f"\n  [Sentence {sa.sentence_index}] (Offsets: {sa.char_start}:{sa.char_end})")
            print(f"  Text: \"{sa.sentence_text}\"")

            # Collect aspects predicted present
            present_aspects = [
                (asp, det) for asp, det in sa.aspect_detections.items()
                if det.detection_status == DetectionStatus.PRESENT
            ]

            if present_aspects:
                print("  Aspect-Based Extractions (Rule-Based Predictions):")
                for asp_str, det_res in present_aspects:
                    sent_res = sa.aspect_sentiments.get(asp_str)
                    sent_label = sent_res.sentiment_label.value if sent_res else "N/A"
                    sent_evidence = sent_res.evidence if sent_res else "N/A"

                    print(f"    - Aspect:    {asp_str}")
                    print(f"      Detection: PRESENT (Confidence: {det_res.confidence:.2f})")
                    print(f"      Evidence:  {det_res.evidence}")
                    print(f"      Sentiment: {sent_label.upper()} (Confidence: {sent_res.confidence:.2f})")
                    print(f"      Evidence:  {sent_evidence}")
            else:
                print("  Aspect-Based Extractions: (No aspects predicted present in this sentence)")

    conn.close()
    print("\n================================================================================")
    print(" End of Live Demonstration — All outputs generated dynamically from rules.")
    print("================================================================================")


if __name__ == "__main__":
    run_demo()
