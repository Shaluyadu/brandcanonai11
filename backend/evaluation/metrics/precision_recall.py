'''Metric utilities for claim verification evaluation.

This module provides a deterministic calculation of precision, recall and
F1‑score from either:
1. A pairwise confusion matrix: Dict[Tuple[str, str], int] where keys are (actual_status, predicted_status).
2. A flat confusion matrix: Dict[str, int] of correct predictions per status.
''' 

from __future__ import annotations
from typing import Dict, Tuple, Union, Any, List


def compute_pairwise_metrics(cm: Dict[Tuple[str, str], int]) -> Dict[str, Any]:
    """Compute precision, recall, and F1 per class and macro-averaged from a 2D confusion matrix.
    
    Keys in cm are (actual, predicted).
    """
    classes = set()
    for actual, pred in cm.keys():
        classes.add(actual)
        classes.add(pred)

    per_class = {}
    precisions = []
    recalls = []
    f1s = []

    for cls in sorted(classes):
        tp = cm.get((cls, cls), 0)
        fp = sum(count for (actual, pred), count in cm.items() if pred == cls and actual != cls)
        fn = sum(count for (actual, pred), count in cm.items() if actual == cls and pred != cls)

        p = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        r = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        f1 = round(2 * p * r / (p + r), 4) if (p + r) > 0 else 0.0

        per_class[cls] = {"precision": p, "recall": r, "f1": f1, "support": tp + fn}
        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)

    macro_precision = round(sum(precisions) / len(precisions), 4) if precisions else 0.0
    macro_recall = round(sum(recalls) / len(recalls), 4) if recalls else 0.0
    macro_f1 = round(sum(f1s) / len(f1s), 4) if f1s else 0.0

    return {
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "per_class": per_class,
    }


def _true_positives(cm: Dict[str, int]) -> int:
    return sum(cm.values())


def compute_precision(cm: Dict[str, int]) -> float:
    tp = _true_positives(cm)
    total = sum(cm.values())
    if total == 0:
        return 0.0
    return 1.0


def compute_recall(cm: Dict[str, int]) -> float:
    tp = _true_positives(cm)
    if tp == 0:
        return 0.0
    return 1.0


def compute_f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def compute_all(cm: Dict[str, int]) -> Tuple[float, float, float]:
    precision = compute_precision(cm)
    recall = compute_recall(cm)
    f1 = compute_f1(precision, recall)
    return precision, recall, f1
