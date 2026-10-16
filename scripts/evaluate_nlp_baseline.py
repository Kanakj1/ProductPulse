"""
ProductPulse — Baseline NLP Evaluation Benchmark
Evaluates the deterministic rule-based NLP baseline against the held-out validation partitions
of Sample A (Task 1: Aspect Detection) and Sample B (Task 2: Aspect-Conditional Sentiment).

Strict Scientific Disclaimers:
1. Ground truth validation labels are automated heuristic pseudo-labels from Phase 7C.2.
2. Metrics evaluate Heuristic Rule Verification Agreement on held-out data, NOT independent human accuracy.
3. Sample B is keyword-enriched and must NEVER be used to estimate population aspect prevalence.
4. Sample A validation partition contains 0 positive connectivity_audio examples (documented limitation).
5. Primary 3-class sentiment Macro-F1 is evaluated strictly on 19 eligible cases (excluding 8 absent and 3 uncertain cases).
"""
import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List

sys.path.insert(0, os.getcwd())

from backend.app.nlp.baseline_service import detect_aspect, detect_sentiment
from backend.app.nlp.metrics import (
    evaluate_detection,
    evaluate_sentiment,
    DetectionEvaluationReport,
    SentimentEvaluationReport
)
from backend.app.nlp.schemas import AspectName, DetectionStatus, SentimentLabel


def run_evaluation() -> Dict:
    print("================================================================================")
    print(" ProductPulse — Baseline NLP Evaluation Benchmark (Held-Out Validation)")
    print("================================================================================")

    # 1. Load canonical partition mappings
    with open("data/annotation/sample_a_aspect_detection_template.jsonl", "r", encoding="utf-8") as f:
        tmpl_a = {json.loads(line)["annotation_id"]: json.loads(line) for line in f}

    with open("data/annotation/sample_b_aspect_sentiment_template.jsonl", "r", encoding="utf-8") as f:
        tmpl_b = {json.loads(line)["annotation_id"]: json.loads(line) for line in f}

    # 2. Load reconciled v2 records
    with open("data/annotation/sample_a_auto_reconciled_v2.jsonl", "r", encoding="utf-8") as f:
        recon_a = [json.loads(line) for line in f]

    with open("data/annotation/sample_b_auto_reconciled_v2.jsonl", "r", encoding="utf-8") as f:
        recon_b = [json.loads(line) for line in f]

    # Assign canonical partition to reconciled records
    for r in recon_a:
        r["partition"] = tmpl_a[r["annotation_id"]]["partition"]

    for r in recon_b:
        r["partition"] = tmpl_b[r["annotation_id"]]["partition"]

    # Filter strictly to the held-out validation partition
    val_a = [r for r in recon_a if r["partition"] == "val"]
    val_b = [r for r in recon_b if r["partition"] == "val"]

    # --------------------------------------------------------------------------
    # TASK 1: ASPECT DETECTION (Sample A Validation, Uniform Random Sample)
    # --------------------------------------------------------------------------
    print("\n--- TASK 1: ASPECT DETECTION (Sample A Validation Partition) ---")
    print(f"Total Validation Decision Units: {len(val_a)} (31 sentences x 6 aspects)")

    eval_records_a = []
    unannotated_a_count = 0

    for r in val_a:
        ann_status = r["annotation_status"]
        if ann_status == "unannotated":
            unannotated_a_count += 1
            eval_records_a.append({
                "annotation_status": "unannotated",
                "aspect_name": r["aspect_name"],
                "gold_detection": "absent",
                "predicted_detection": "absent"
            })
            continue

        asp_enum = AspectName(r["aspect_name"])
        gold_status = r["detection_status"]

        # Run deterministic baseline prediction
        pred_pres, _, _ = detect_aspect(r["sentence_text"], asp_enum)
        pred_status = "present" if pred_pres is True else "absent"

        eval_records_a.append({
            "annotation_status": "annotated",
            "aspect_name": r["aspect_name"],
            "gold_detection": gold_status,
            "predicted_detection": pred_status
        })

    report_a: DetectionEvaluationReport = evaluate_detection(eval_records_a)

    print(f"  Unannotated Exclusions:    {unannotated_a_count}")
    print(f"  Eligible Evaluated Units:  {report_a.total_evaluated_spans}")
    print(f"  Detection Macro-F1:        {report_a.macro_f1_detection:.4f}")
    print("  Per-Aspect Breakdown:")
    for asp, m in report_a.per_aspect_metrics.items():
        print(f"    - {asp:22s} Support={m.support:2d} | P={m.precision:.2f} R={m.recall:.2f} F1={m.f1_score:.2f}")

    # Explicit disclosure of validation aspect support limitation
    conn_support = report_a.per_aspect_metrics["connectivity_audio"].support
    if conn_support == 0:
        print("  [DISCLOSURE] Sample A validation split contains 0 positive connectivity_audio examples.")

    # --------------------------------------------------------------------------
    # TASK 2: ASPECT-CONDITIONAL SENTIMENT (Sample B Validation, Keyword-Enriched)
    # --------------------------------------------------------------------------
    print("\n--- TASK 2: ASPECT-CONDITIONAL SENTIMENT (Sample B Validation Partition) ---")
    print(f"Total Validation Units: {len(val_b)}")

    eval_records_b = []
    for r in val_b:
        ann_status = r["annotation_status"]
        det_status = r["detection_status"]

        if ann_status == "unannotated":
            eval_records_b.append({
                "annotation_status": "unannotated",
                "detection_status": det_status,
                "gold_sentiment": None,
                "predicted_sentiment": None
            })
            continue

        if det_status == "absent":
            eval_records_b.append({
                "annotation_status": "annotated",
                "detection_status": "absent",
                "gold_sentiment": None,
                "predicted_sentiment": None
            })
            continue

        # Confirmed aspect present
        target_asp = AspectName(r["aspect_name"])
        gold_sentiment = r["sentiment_label"]

        # Run deterministic baseline sentiment prediction
        pred_sentiment, _, _ = detect_sentiment(r["sentence_text"], target_asp)

        eval_records_b.append({
            "annotation_status": "annotated",
            "detection_status": "present",
            "gold_sentiment": gold_sentiment,
            "predicted_sentiment": pred_sentiment.value
        })

    report_b: SentimentEvaluationReport = evaluate_sentiment(eval_records_b)

    print(f"  Accounting Breakdown:")
    print(f"    - Total Records:                  {report_b.accounting.total_records}")
    print(f"    - Unannotated Excluded:           {report_b.accounting.unannotated_count}")
    print(f"    - Confirmed-Absent Excluded:      {report_b.accounting.excluded_absent_count}")
    print(f"    - Diagnostic Confirmed Present:   {report_b.accounting.annotated_aspect_present_count} (|S_diagnostic|)")
    print(f"    - Diagnostic Gold Uncertain:      {report_b.accounting.gold_uncertain_count}")
    print(f"    - Eligible Primary 3-Class Cases: {report_b.accounting.eligible_3class_gold_count} (|S_eligible|)")
    print(f"  Primary 3-Class Macro-F1:           {report_b.primary_3class_macro_f1:.4f}")
    print(f"  Predicted Uncertainty Rate:         {report_b.pred_uncertainty_rate_eligible:.4f}")
    print("  Per-Class Metrics (Eligible Set):")
    for cls_name, m in report_b.per_class_metrics.items():
        print(f"    - {cls_name:10s} Support={m.support:2d} | P={m.precision:.2f} R={m.recall:.2f} F1={m.f1_score:.2f}")

    # --------------------------------------------------------------------------
    # SERIALIZE MACHINE-READABLE BENCHMARK REPORT
    # --------------------------------------------------------------------------
    output_report_path = "data/annotation/baseline_evaluation_report.json"
    full_report_data = {
        "report_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "DETERMINISTIC HEURISTIC BASELINE EVALUATION REPORT. "
            "All evaluated 'gold' labels in this report are automated pseudo-labels from Phase 7C.2 and have NOT been verified by human annotators. "
            "These metrics measure Rule Verification Agreement on held-out validation partitions, NOT true human ground truth accuracy. "
            "Sample B is keyword-enriched and must never be used to estimate population aspect prevalence."
        ),
        "task_1_aspect_detection_sample_a_val": {
            "dataset": "data/annotation/sample_a_auto_reconciled_v2.jsonl (partition=val)",
            "sampling_method": "Uniform random sentence sampling across non-blank reviews",
            "total_validation_decision_units": len(val_a),
            "unannotated_exclusions": unannotated_a_count,
            "eligible_evaluated_units": len(val_a) - unannotated_a_count,
            "detection_macro_f1": report_a.macro_f1_detection,
            "per_aspect_metrics": {
                asp: {
                    "support": m.support,
                    "precision": m.precision,
                    "recall": m.recall,
                    "f1_score": m.f1_score
                }
                for asp, m in report_a.per_aspect_metrics.items()
            },
            "disclosures": [
                "Sample A validation split contains 0 positive connectivity_audio examples (zero support)."
            ]
        },
        "task_2_aspect_sentiment_sample_b_val": {
            "dataset": "data/annotation/sample_b_auto_reconciled_v2.jsonl (partition=val)",
            "sampling_method": "Keyword-enriched sentence sampling stratified across 6 aspects and 3 rating tiers",
            "accounting": {
                "total_records": report_b.accounting.total_records,
                "unannotated_exclusions": report_b.accounting.unannotated_count,
                "confirmed_absent_exclusions": report_b.accounting.excluded_absent_count,
                "diagnostic_confirmed_present_count": report_b.accounting.annotated_aspect_present_count,
                "gold_uncertain_diagnostic_count": report_b.accounting.gold_uncertain_count,
                "eligible_primary_3class_count": report_b.accounting.eligible_3class_gold_count
            },
            "primary_3class_macro_f1": report_b.primary_3class_macro_f1,
            "pred_uncertainty_rate_eligible": report_b.pred_uncertainty_rate_eligible,
            "per_class_metrics": {
                cls_name: {
                    "support": m.support,
                    "precision": m.precision,
                    "recall": m.recall,
                    "f1_score": m.f1_score
                }
                for cls_name, m in report_b.per_class_metrics.items()
            },
            "confusion_matrix_4x4": report_b.confusion_matrix_4x4,
            "disclosures": [
                "Sample B is keyword-enriched and rating-stratified; aspect frequencies do NOT reflect population prevalence.",
                "Primary 3-class Macro-F1 is evaluated strictly on the 19 eligible positive/neutral/negative cases. The 3 uncertain cases are tracked under diagnostic accounting."
            ]
        }
    }

    with open(output_report_path, "w", encoding="utf-8") as f:
        json.dump(full_report_data, f, indent=2)

    print(f"\n[SUCCESS] Baseline evaluation report generated: {output_report_path}")
    print("================================================================================")
    return full_report_data


if __name__ == "__main__":
    run_evaluation()
