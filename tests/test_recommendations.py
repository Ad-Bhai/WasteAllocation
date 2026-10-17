"""Tests for recommendation engine logic, urgency tiers, and mathematical reasoning."""
import pytest
from datetime import datetime
from wastewise.recommendations.engine import RecommendationEngine
from wastewise.etl.pipeline import WasteWisePipeline
from wastewise.ingestion.samples import generate_sample_datasets


@pytest.fixture
def sample_analytics():
    raw = generate_sample_datasets()
    pipe = WasteWisePipeline(preferred_engine="pandas")
    res = pipe.run(raw["products"], raw["inventory"], raw["expiry"], raw["sales"], save_parquet=False)
    return res.analytics_df


def test_recommendation_generation(sample_analytics):
    recs = RecommendationEngine.generate_recommendations(sample_analytics)
    assert len(recs) > 0

    # Ensure urgent actions exist
    urgencies = [r.urgency for r in recs]
    assert "CRITICAL" in urgencies or "HIGH" in urgencies

    # Check each recommendation item has valid fields
    for r in recs:
        assert r.rec_id.startswith("REC-")
        assert len(r.headline) > 0
        assert len(r.action_plan) > 0
        assert r.potential_loss_at_risk >= 0
        assert "Current Stock" in r.supporting_data
        assert len(r.calculation_breakdown) > 0


def test_empty_analytics_recommendations():
    import pandas as pd
    recs = RecommendationEngine.generate_recommendations(pd.DataFrame())
    assert recs == []
