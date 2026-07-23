from pathlib import Path

import pytest

from taiga.curriculum_seed import canonical_hash, load_json, stable_uuid

CURRICULUM_DIR = Path(__file__).parents[3] / "design/taiga-42-v4.0-implementation-pack/curriculum"
pytestmark = pytest.mark.skipif(
    not CURRICULUM_DIR.exists(),
    reason="Project Taiga implementation pack is mounted locally, not in CI checkout",
)


def test_canonical_curriculum_counts() -> None:
    assert len(load_json(CURRICULUM_DIR, "weeks")) == 28
    assert len(load_json(CURRICULUM_DIR, "task_templates")) == 196
    assert len(load_json(CURRICULUM_DIR, "task_assignments")) == 196
    assert len(load_json(CURRICULUM_DIR, "exams")) == 28
    assert len(load_json(CURRICULUM_DIR, "exam_variants")) == 56
    assert len(load_json(CURRICULUM_DIR, "exam_hidden_tests")) == 56


def test_stable_uuid_is_deterministic() -> None:
    assert stable_uuid("week", "WEEK-001") == stable_uuid("week", "WEEK-001")
    assert stable_uuid("week", "WEEK-001") != stable_uuid("week", "WEEK-002")


def test_canonical_hash_is_sha256() -> None:
    assert len(canonical_hash(CURRICULUM_DIR)) == 64
