from unittest.mock import patch

from src.modules.doba_pipeline.application.orchestrator import run_doba_pipeline


def test_run_doba_pipeline_dry_run_returns_candidate_summary():
    with patch(
        "src.modules.doba_pipeline.application.orchestrator.build_doba_publish_candidate_pool",
        return_value={"summary": {"qualified_count": 3, "skipped_by_reason": {"active_product_exists": 1}}},
    ):
        result = run_doba_pipeline({"mode": "dry-run"})

    assert result["ok"] is True
    assert result["mode"] == "dry-run"
    assert result["candidate_pool_summary"]["qualified_count"] == 3


def test_run_doba_pipeline_archive_and_publish_runs_all_stages():
    with patch(
        "src.modules.doba_pipeline.application.orchestrator.run_doba_online_archive",
        return_value={"completed": True, "progress": {"archived_sku": 4}},
    ):
        with patch(
            "src.modules.doba_pipeline.application.orchestrator.build_doba_publish_candidate_pool",
            return_value={"summary": {"qualified_count": 2}},
        ):
            with patch(
                "src.modules.doba_pipeline.application.orchestrator.publish_doba_products_live",
                return_value={"completed": True, "summary": {"published_count": 2}},
            ):
                result = run_doba_pipeline({"mode": "archive-and-publish"})

    assert result["ok"] is True
    assert result["archive_result"]["progress"]["archived_sku"] == 4
    assert result["candidate_pool_result"]["summary"]["qualified_count"] == 2
    assert result["publish_result"]["summary"]["published_count"] == 2


def test_run_doba_pipeline_stream_publish_passes_archive_hook_and_marks_mode():
    captured_kwargs = {}

    def _fake_archive(**kwargs):
        captured_kwargs.update(kwargs)
        hook = kwargs.get("post_archive_hook")
        assert hook is not None
        hook([], {"spu_no": "SPU-1", "title": "Product 1"})
        return {"completed": True, "progress": {"archived_sku": 1}}

    with patch(
        "src.modules.doba_pipeline.application.orchestrator.run_doba_online_archive",
        side_effect=_fake_archive,
    ):
        with patch(
            "src.modules.doba_pipeline.application.orchestrator.build_doba_publish_candidate_pool",
            return_value={"summary": {"qualified_count": 1}},
        ) as build_mock:
            with patch(
                "src.modules.doba_pipeline.application.orchestrator.publish_doba_products_live",
                return_value={"completed": True, "summary": {"published_count": 1}},
            ) as publish_mock:
                result = run_doba_pipeline({"mode": "archive-and-publish", "stream_publish": True})

    assert result["ok"] is True
    assert result["mode"] == "archive-stream-publish"
    assert "post_archive_hook" in captured_kwargs
    assert build_mock.call_count == 1
    assert publish_mock.call_count == 1
    first_stream_build_kwargs = build_mock.call_args_list[0].kwargs
    first_stream_publish_kwargs = publish_mock.call_args_list[0].kwargs
    assert first_stream_build_kwargs["incremental_spu_nos"] == ["SPU-1"]
    assert first_stream_publish_kwargs["candidate_spu_nos"] == ["SPU-1"]
    assert result["candidate_pool_result"]["source"] == "stream_publish_hook"
    assert result["publish_result"]["source"] == "stream_publish_hook"
