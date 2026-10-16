"""
ProductPulse — NLP Evaluation Metrics Engine
Pure Python standard library mathematical evaluation engine.
Implements:
1. Auditable Accounting Breakdown separating unannotated, absent, uncertain, and eligible sets.
2. Primary Three-Class Sentiment Macro-F1 restricted to eligible unambiguous gold units.
3. Four-Class Diagnostic Confusion Matrix (positive, neutral, negative, uncertain/unclassified).
4. Operational Uncertainty Metrics with explicit, mathematically defined denominators.
5. Aspect Detection Metrics (Precision, Recall, F1 per aspect & Macro-F1).
6. Strict validation: missing, null, or invalid predictions raise explicit errors and are never silently discarded.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from backend.app.nlp.schemas import (
    AnnotationStatus,
    AnnotationUnit,
    AspectName,
    DetectionStatus,
    SentimentLabel
)


class EvaluationValidationError(ValueError):
    """Raised when an evaluation record is malformed, missing required predictions, or invalid."""
    pass


@dataclass
class AccountingBreakdown:
    """Auditable tallies for all records submitted to the evaluation engine."""
    total_records: int
    unannotated_count: int
    excluded_absent_count: int
    annotated_aspect_present_count: int  # |S_diagnostic|
    gold_uncertain_count: int
    eligible_3class_gold_count: int      # |S_eligible|
    pred_uncertain_count: int
    missing_prediction_count: int


@dataclass
class ClassMetrics:
    """Per-class evaluation metrics."""
    true_positives: int
    false_positives: int
    false_negatives: int
    support: int
    precision: float
    recall: float
    f1_score: float


@dataclass
class SentimentEvaluationReport:
    """Structured report for aspect sentiment classification benchmarking."""
    accounting: AccountingBreakdown
    primary_3class_macro_f1: float
    per_class_metrics: Dict[str, ClassMetrics]
    confusion_matrix_4x4: Dict[str, Dict[str, int]]
    pred_uncertainty_rate_eligible: float
    pred_uncertainty_rate_overall: float
    gold_uncertainty_prevalence: float


@dataclass
class DetectionEvaluationReport:
    """Structured report for aspect detection benchmarking (Sample A)."""
    macro_f1_detection: float
    per_aspect_metrics: Dict[str, ClassMetrics]
    total_evaluated_spans: int


def _safe_divide(numerator: float, denominator: float) -> float:
    """Safely divide two numbers, returning 0.0 if denominator is 0."""
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def evaluate_sentiment(
    records: List[Dict]
) -> SentimentEvaluationReport:
    """
    Evaluates aspect sentiment classification against gold annotations.
    
    Each record must be a dict containing:
    - 'annotation_status': 'annotated' | 'unannotated'
    - 'detection_status': 'present' | 'absent'
    - 'gold_sentiment': Optional['positive' | 'neutral' | 'negative' | 'uncertain/unclassified']
    - 'predicted_sentiment': Optional['positive' | 'neutral' | 'negative' | 'uncertain/unclassified']
    
    Raises EvaluationValidationError on missing predictions for annotated aspect-present units.
    """
    total_records = len(records)
    unannotated_count = 0
    excluded_absent_count = 0
    annotated_aspect_present: List[Dict] = []
    gold_uncertain_count = 0
    pred_uncertain_count = 0
    missing_pred_count = 0

    valid_labels = {"positive", "neutral", "negative", "uncertain/unclassified"}

    # Step 1: Accounting breakdown
    for idx, r in enumerate(records):
        ann_status = r.get("annotation_status")
        det_status = r.get("detection_status")

        if ann_status == "unannotated" or ann_status == AnnotationStatus.UNANNOTATED:
            unannotated_count += 1
            continue

        if det_status == "absent" or det_status == DetectionStatus.ABSENT:
            excluded_absent_count += 1
            continue

        if ann_status == "annotated" or ann_status == AnnotationStatus.ANNOTATED:
            if det_status == "present" or det_status == DetectionStatus.PRESENT:
                # Must have valid gold sentiment
                gold_sent = r.get("gold_sentiment")
                if isinstance(gold_sent, SentimentLabel):
                    gold_sent = gold_sent.value
                if gold_sent not in valid_labels:
                    raise EvaluationValidationError(
                        f"Record {idx} ({r.get('annotation_id', 'unknown')}): annotated aspect-present record has invalid gold_sentiment: {gold_sent}"
                    )

                # Prediction validation: must not be missing or None
                pred_sent = r.get("predicted_sentiment")
                if isinstance(pred_sent, SentimentLabel):
                    pred_sent = pred_sent.value
                if pred_sent is None or pred_sent not in valid_labels:
                    missing_pred_count += 1
                    raise EvaluationValidationError(
                        f"Record {idx} ({r.get('annotation_id', 'unknown')}): missing or invalid predicted_sentiment: '{pred_sent}'. "
                        "Missing predictions cannot be silently discarded."
                    )

                if gold_sent == "uncertain/unclassified":
                    gold_uncertain_count += 1
                if pred_sent == "uncertain/unclassified":
                    pred_uncertain_count += 1

                annotated_aspect_present.append({
                    "annotation_id": r.get("annotation_id", f"rec_{idx}"),
                    "gold": gold_sent,
                    "pred": pred_sent
                })

    n_diagnostic = len(annotated_aspect_present)
    if total_records > 0 and unannotated_count == total_records:
        raise EvaluationValidationError(
            "Cannot evaluate performance: 100% of submitted records are unannotated templates. "
            "Evaluation requires human-annotated gold data."
        )

    # Step 2: Separate eligible 3-class gold set (S_eligible)
    s_eligible = [r for r in annotated_aspect_present if r["gold"] in {"positive", "neutral", "negative"}]
    eligible_3class_count = len(s_eligible)

    accounting = AccountingBreakdown(
        total_records=total_records,
        unannotated_count=unannotated_count,
        excluded_absent_count=excluded_absent_count,
        annotated_aspect_present_count=n_diagnostic,
        gold_uncertain_count=gold_uncertain_count,
        eligible_3class_gold_count=eligible_3class_count,
        pred_uncertain_count=pred_uncertain_count,
        missing_prediction_count=missing_pred_count
    )

    # Step 3: Compute Primary Three-Class Metrics on S_eligible
    classes_3 = ["positive", "neutral", "negative"]
    tp = {c: 0 for c in classes_3}
    fp = {c: 0 for c in classes_3}
    fn = {c: 0 for c in classes_3}
    support = {c: 0 for c in classes_3}
    pred_uncertain_on_eligible = 0

    for r in s_eligible:
        g = r["gold"]
        p = r["pred"]
        support[g] += 1

        if p == g:
            tp[g] += 1
        elif p in classes_3:
            fn[g] += 1
            fp[p] += 1
        elif p == "uncertain/unclassified":
            # Model abstained/uncertain on eligible gold class -> counts as a miss (FN) for gold class
            fn[g] += 1
            pred_uncertain_on_eligible += 1

    per_class_metrics: Dict[str, ClassMetrics] = {}
    f1_sum = 0.0

    for c in classes_3:
        prec = _safe_divide(float(tp[c]), float(tp[c] + fp[c]))
        rec = _safe_divide(float(tp[c]), float(tp[c] + fn[c]))
        f1 = _safe_divide(2.0 * prec * rec, prec + rec)
        f1_sum += f1

        per_class_metrics[c] = ClassMetrics(
            true_positives=tp[c],
            false_positives=fp[c],
            false_negatives=fn[c],
            support=support[c],
            precision=round(prec, 4),
            recall=round(rec, 4),
            f1_score=round(f1, 4)
        )

    primary_macro_f1 = round(f1_sum / 3.0, 4)

    # Step 4: Construct 4x4 Diagnostic Confusion Matrix over S_diagnostic
    classes_4 = ["positive", "neutral", "negative", "uncertain/unclassified"]
    matrix_4x4: Dict[str, Dict[str, int]] = {g: {p: 0 for p in classes_4} for g in classes_4}

    for r in annotated_aspect_present:
        matrix_4x4[r["gold"]][r["pred"]] += 1

    # Step 5: Compute Operational Uncertainty Metrics with exact denominators
    # Denominator 1: Pred Uncertainty Rate on eligible 3-class gold units (|S_eligible|)
    pred_rate_eligible = _safe_divide(float(pred_uncertain_on_eligible), float(eligible_3class_count))

    # Denominator 2: Overall Pred Uncertainty Rate on all annotated aspect-present units (|S_diagnostic|)
    pred_rate_overall = _safe_divide(float(pred_uncertain_count), float(n_diagnostic))

    # Denominator 3: Gold Uncertainty Prevalence on all annotated aspect-present units (|S_diagnostic|)
    gold_prevalence = _safe_divide(float(gold_uncertain_count), float(n_diagnostic))

    return SentimentEvaluationReport(
        accounting=accounting,
        primary_3class_macro_f1=primary_macro_f1,
        per_class_metrics=per_class_metrics,
        confusion_matrix_4x4=matrix_4x4,
        pred_uncertainty_rate_eligible=round(pred_rate_eligible, 4),
        pred_uncertainty_rate_overall=round(pred_rate_overall, 4),
        gold_uncertainty_prevalence=round(gold_prevalence, 4)
    )


def evaluate_detection(
    records: List[Dict]
) -> DetectionEvaluationReport:
    """
    Evaluates aspect detection benchmarking on Sample A spans.
    
    Each record must be a dict containing:
    - 'aspect_name': AspectName or str
    - 'gold_detection': 'present' | 'absent'
    - 'predicted_detection': 'present' | 'absent'
    """
    all_aspects = [a.value if isinstance(a, AspectName) else a for a in AspectName]
    tp = {a: 0 for a in all_aspects}
    fp = {a: 0 for a in all_aspects}
    fn = {a: 0 for a in all_aspects}
    support = {a: 0 for a in all_aspects}
    unannotated_count = 0
    total_records = len(records)

    for idx, r in enumerate(records):
        ann_status = r.get("annotation_status")
        if ann_status == "unannotated" or ann_status == AnnotationStatus.UNANNOTATED:
            unannotated_count += 1
            continue

        asp = r.get("aspect_name")
        if isinstance(asp, AspectName):
            asp = asp.value
        if asp not in all_aspects:
            raise EvaluationValidationError(f"Record {idx}: unknown aspect_name '{asp}'")

        gold = r.get("gold_detection")
        if gold is None:
            gold = r.get("detection_status")
        if isinstance(gold, DetectionStatus):
            gold = gold.value
        pred = r.get("predicted_detection")
        if isinstance(pred, DetectionStatus):
            pred = pred.value

        if gold not in {"present", "absent"}:
            raise EvaluationValidationError(f"Record {idx}: invalid gold_detection '{gold}'")
        if pred not in {"present", "absent"}:
            raise EvaluationValidationError(f"Record {idx}: invalid predicted_detection '{pred}'")

        if gold == "present":
            support[asp] += 1
            if pred == "present":
                tp[asp] += 1
            else:
                fn[asp] += 1
        else:
            if pred == "present":
                fp[asp] += 1

    if total_records > 0 and unannotated_count == total_records:
        raise EvaluationValidationError(
            "Cannot evaluate detection performance: 100% of submitted records are unannotated templates. "
            "Evaluation requires human-annotated gold data."
        )

    per_aspect_metrics: Dict[str, ClassMetrics] = {}
    f1_sum = 0.0

    for a in all_aspects:
        prec = _safe_divide(float(tp[a]), float(tp[a] + fp[a]))
        rec = _safe_divide(float(tp[a]), float(tp[a] + fn[a]))
        f1 = _safe_divide(2.0 * prec * rec, prec + rec)
        f1_sum += f1

        per_aspect_metrics[a] = ClassMetrics(
            true_positives=tp[a],
            false_positives=fp[a],
            false_negatives=fn[a],
            support=support[a],
            precision=round(prec, 4),
            recall=round(rec, 4),
            f1_score=round(f1, 4)
        )

    macro_f1 = round(f1_sum / float(len(all_aspects)), 4)

    return DetectionEvaluationReport(
        macro_f1_detection=macro_f1,
        per_aspect_metrics=per_aspect_metrics,
        total_evaluated_spans=len(records)
    )
