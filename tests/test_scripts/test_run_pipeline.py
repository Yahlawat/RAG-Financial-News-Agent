"""Tests for the full data pipeline (cleanup → scrape → chunk → embed)."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from finnews.scripts.pipeline import run_pipeline


@pytest.fixture
def steps():
    """Patch every pipeline step and record the order they run in."""
    calls = []
    with (
        patch("finnews.scripts.cleanup_old_articles.cleanup_and_rebuild") as cleanup,
        patch("finnews.rag.chunker.main") as chunk,
        patch("finnews.rag.embedder.main") as embed,
        patch("finnews.scripts.pipeline.set_pipeline_stage") as set_stage,
        patch("finnews.scripts.pipeline.set_pipeline_error") as set_error,
        patch("finnews.scripts.pipeline.complete_pipeline") as complete,
    ):
        cleanup.side_effect = lambda **kwargs: calls.append("cleanup")
        chunk.side_effect = lambda: calls.append("chunk")
        embed.side_effect = lambda: calls.append("embed")
        yield SimpleNamespace(
            calls=calls,
            scrape=lambda tickers: calls.append(("scrape", tickers)),
            embed=embed,
            set_stage=set_stage,
            set_error=set_error,
            complete=complete,
        )


def test_run_pipeline_runs_steps_in_order(steps):
    run_pipeline(["AAPL"], scrape=steps.scrape)

    assert steps.calls == ["cleanup", ("scrape", ["AAPL"]), "chunk", "embed"]
    assert [c.args[0] for c in steps.set_stage.call_args_list] == ["chunking", "embedding"]
    steps.complete.assert_called_once_with(status="completed")


def test_run_pipeline_without_cleanup(steps):
    run_pipeline(["AAPL"], scrape=steps.scrape, cleanup=False)

    assert steps.calls == [("scrape", ["AAPL"]), "chunk", "embed"]


def test_run_pipeline_step_failure(steps):
    steps.embed.side_effect = RuntimeError("Chroma down")

    with pytest.raises(RuntimeError, match="Chroma down"):
        run_pipeline(["AAPL"], scrape=steps.scrape)

    steps.set_error.assert_called_once_with("embedding", "Chroma down")
    steps.complete.assert_not_called()
