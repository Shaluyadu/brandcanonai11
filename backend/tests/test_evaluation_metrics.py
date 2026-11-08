from evaluation.metrics.precision_recall import (
    compute_all,
    compute_f1,
    compute_pairwise_metrics,
)


def test_compute_all_flat():
    cm = {"VERIFIED": 10, "CONTRADICTED": 5}
    p, r, f1 = compute_all(cm)
    assert p == 1.0
    assert r == 1.0
    assert f1 == 1.0


def test_compute_pairwise_metrics():
    # 8 true VERIFIED, 2 VERIFIED predicted as CONTRADICTED
    # 7 true CONTRADICTED, 3 CONTRADICTED predicted as VERIFIED
    cm = {
        ("VERIFIED", "VERIFIED"): 8,
        ("VERIFIED", "CONTRADICTED"): 2,
        ("CONTRADICTED", "CONTRADICTED"): 7,
        ("CONTRADICTED", "VERIFIED"): 3,
    }
    metrics = compute_pairwise_metrics(cm)
    assert "macro_precision" in metrics
    assert "macro_recall" in metrics
    assert "macro_f1" in metrics
    assert metrics["macro_precision"] > 0.5
    assert metrics["macro_recall"] > 0.5
    assert metrics["macro_f1"] > 0.5
    assert "VERIFIED" in metrics["per_class"]
    assert "CONTRADICTED" in metrics["per_class"]

