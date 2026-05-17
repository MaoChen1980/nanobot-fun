"""Tests for goal scopes storage and filtering."""

import pytest

from nanobot.agent.db import NanobotDB


@pytest.fixture
def db(tmp_path):
    return NanobotDB(tmp_path / "test.db")


class TestGoalScopes:
    def test_scopes_stored_in_data_json(self, db):
        """Scopes should be stored inside the data JSON blob."""
        db.upsert_goal(
            id="g1",
            title="Test goal",
            data={"scopes": ["memory", "agent/loop"]},
        )
        goal = db.get_goal("g1")
        assert goal["data"]["scopes"] == ["memory", "agent/loop"]

    def test_scopes_empty_when_omitted(self, db):
        """Goals without scopes field should return empty array."""
        db.upsert_goal(
            id="g1",
            title="No scopes",
            data={},
        )
        goal = db.get_goal("g1")
        assert goal["data"].get("scopes", []) == []

    def test_list_goals_filter_by_single_scope(self, db):
        """list_goals with scope= should return only goals that have it."""
        db.upsert_goal(id="g1", title="Goal 1", data={"scopes": ["memory"]})
        db.upsert_goal(id="g2", title="Goal 2", data={"scopes": ["agent/loop"]})
        db.upsert_goal(id="g3", title="Goal 3", data={"scopes": ["memory", "agent/loop"]})
        db.upsert_goal(id="g4", title="No scopes", data={})

        results = db.list_goals(scope="memory")
        ids = {g["id"] for g in results}
        assert ids == {"g1", "g3"}

    def test_list_goals_filter_by_scope_no_match(self, db):
        """list_goals with non-existent scope should return empty."""
        db.upsert_goal(id="g1", title="Goal 1", data={"scopes": ["memory"]})
        results = db.list_goals(scope="nonexistent")
        assert results == []

    def test_list_goals_filter_by_scope_with_status(self, db):
        """scope filter should combine correctly with status filter."""
        db.upsert_goal(id="g1", title="Goal 1", status="completed", data={"scopes": ["memory"]})
        db.upsert_goal(id="g2", title="Goal 2", status="in_progress", data={"scopes": ["memory"]})
        db.upsert_goal(id="g3", title="Goal 3", status="completed", data={"scopes": ["agent/loop"]})

        results = db.list_goals(status="completed", scope="memory")
        ids = {g["id"] for g in results}
        assert ids == {"g1"}

    def test_list_goals_filter_by_scope_with_project(self, db):
        """scope filter should combine correctly with project filter."""
        db.upsert_goal(id="g1", title="Goal 1", project="nanobot", data={"scopes": ["memory"]})
        db.upsert_goal(id="g2", title="Goal 2", project="openclaw", data={"scopes": ["memory"]})

        results = db.list_goals(project="nanobot", scope="memory")
        ids = {g["id"] for g in results}
        assert ids == {"g1"}

    def test_scopes_are_list_of_strings(self, db):
        """Scopes field should support multiple string values."""
        db.upsert_goal(
            id="g1",
            title="Multi-scope",
            data={"scopes": ["memory", "agent/loop", "context"]},
        )
        goal = db.get_goal("g1")
        assert len(goal["data"]["scopes"]) == 3
        assert "memory" in goal["data"]["scopes"]

    def test_scopes_case_sensitive(self, db):
        """Scope matching should be case-sensitive."""
        db.upsert_goal(id="g1", title="Goal 1", data={"scopes": ["Memory"]})

        results = db.list_goals(scope="Memory")
        assert len(results) == 1

        results_lower = db.list_goals(scope="memory")
        assert len(results_lower) == 0