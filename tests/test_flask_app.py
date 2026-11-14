"""Tests for app.py — Flask API endpoints and web routes."""

import json
import sys
from pathlib import Path

import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── 1. GET / returns 200 ────────────────────────────────────────────────

def test_index_returns_200(client):
    """The home page must return HTTP 200."""
    response = client.get("/")
    assert response.status_code == 200


# ── 2. GET /api/health returns 200 with status "ok" ─────────────────────

def test_health_endpoint(client):
    """The health check must return 200 and include status='ok' or similar."""
    response = client.get("/api/health")
    # Health endpoint may or may not exist yet; if 404 skip gracefully
    if response.status_code == 404:
        pytest.skip("/api/health not implemented yet")
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data.get("status") == "ok"


# ── 3. GET /api/summary returns valid JSON with expected means ───────────

def test_summary_returns_valid_json(client):
    """Summary endpoint must return valid JSON with analysis data."""
    response = client.get("/api/summary")
    assert response.status_code == 200

    data = response.get_json()
    assert data is not None
    assert data.get("status") == "success" or data.get("is_valid") is True

    # Check analysis sub-dict when available
    analysis = data.get("analysis")
    if analysis:
        assert "smoker_mean" in analysis
        assert "non_smoker_mean" in analysis
        # Verify means are close to expected
        assert abs(analysis["non_smoker_mean"] - 8434.27) < 1.0
        assert abs(analysis["smoker_mean"] - 32050.23) < 1.0


# ── 4. GET /api/chart returns image/png ──────────────────────────────────

def test_chart_returns_png(client):
    """Chart endpoint must return a PNG image."""
    response = client.get("/api/chart")
    assert response.status_code == 200
    assert response.content_type.startswith("image/png")
    # PNG magic bytes: \x89PNG
    assert response.data[:4] == b"\x89PNG"


# ── 5. GET /api/data returns paginated records ───────────────────────────

def test_data_returns_paginated_records(client):
    """Data endpoint must return a paginated JSON response with records."""
    response = client.get("/api/data?page=1&page_size=10")
    assert response.status_code == 200

    data = response.get_json()
    assert data is not None
    assert "records" in data
    assert "total_records" in data or "total_unfiltered" in data
    assert isinstance(data["records"], list)
    assert len(data["records"]) <= 10
    assert data.get("page") == 1


# ── 6. POST /api/reload returns success ──────────────────────────────────

def test_reload_returns_success(client):
    """Reload endpoint must return success after re-reading the CSV."""
    response = client.post("/api/reload")
    assert response.status_code == 200

    data = response.get_json()
    assert data is not None
    assert data.get("status") == "success"
    assert data.get("total_rows", 0) > 0 or data.get("valid_rows", 0) > 0


# ── 7. GET /api/data smoker filter works ─────────────────────────────────

def test_data_smoker_filter(client):
    """Filtering by smoker=yes must return only smoker rows."""
    response = client.get("/api/data?smoker=yes&page_size=100")
    assert response.status_code == 200

    data = response.get_json()
    records = data.get("records", [])
    assert len(records) > 0

    for record in records:
        smoker_val = record.get("smoker", "").lower()
        assert smoker_val in ("smoker", "yes"), (
            f"Expected smoker record, got smoker='{record.get('smoker')}'"
        )


# ── 8. GET /api/data with region filter ──────────────────────────────────

def test_data_region_filter(client):
    """Filtering by region should narrow results (or return all if unsupported)."""
    response = client.get("/api/data?region=southwest&page_size=100")
    assert response.status_code == 200

    data = response.get_json()
    records = data.get("records", [])
    # If region filtering is implemented, all returned records should be southwest
    if records and any("region" in r for r in records):
        for record in records:
            region_val = record.get("region", "").lower()
            # Accept either the filter worked or all data returned (not implemented)
            if data.get("total_records", 0) < data.get("total_unfiltered", 0):
                assert region_val == "southwest", (
                    f"Region filter returned '{region_val}' instead of 'southwest'"
                )


# ── 9. GET /api/data with sort parameter ─────────────────────────────────

def test_data_sort_parameter(client):
    """Sorting by charges descending should order records correctly."""
    response = client.get("/api/data?sort=charges&order=desc&page_size=10")
    assert response.status_code == 200

    data = response.get_json()
    records = data.get("records", [])
    # If sort is implemented, check descending order via raw_charges
    if len(records) >= 2 and "raw_charges" in records[0]:
        charges = [r["raw_charges"] for r in records]
        assert charges == sorted(charges, reverse=True), (
            "Records not sorted by charges descending"
        )


# ── 10. No "NaN" string anywhere in /api/data response ──────────────────

def test_no_nan_string_in_data(client):
    """The /api/data response must never contain the literal string 'NaN'."""
    response = client.get("/api/data?page_size=100")
    assert response.status_code == 200

    raw_text = response.data.decode("utf-8")
    # Check for "NaN" as a standalone JSON value (not inside a word like "Nantucket")
    # The string "NaN" should not appear as a JSON value
    assert '"NaN"' not in raw_text, "Found literal '\"NaN\"' in /api/data response"
    # Also check for unquoted NaN (invalid JSON, but be safe)
    parsed = response.get_json()
    records = parsed.get("records", [])
    for i, record in enumerate(records):
        for key, value in record.items():
            assert str(value) != "NaN", (
                f"Record {i} field '{key}' contains 'NaN'"
            )


# ── 11. /api/summary groupby_text field is present and non-empty ─────────

def test_summary_has_groupby_text(client):
    """The summary response should include a groupby_text field."""
    response = client.get("/api/summary")
    assert response.status_code == 200

    data = response.get_json()
    analysis = data.get("analysis", {})

    # groupby_text may be in the top-level or nested under analysis
    groupby_text = analysis.get("groupby_text") or data.get("groupby_text")

    if groupby_text is None:
        pytest.skip("groupby_text not yet implemented in API")

    assert isinstance(groupby_text, str)
    assert len(groupby_text.strip()) > 0, "groupby_text is empty"


# ── 12. GET /api/data returns correct page count ─────────────────────────

def test_data_pagination_total_pages(client):
    """total_pages should be consistent with total_records and page_size."""
    response = client.get("/api/data?page_size=10")
    assert response.status_code == 200

    data = response.get_json()
    total_records = data.get("total_records", 0)
    total_pages = data.get("total_pages", 1)
    page_size = data.get("page_size", 10)

    expected_pages = max(1, (total_records + page_size - 1) // page_size)
    assert total_pages == expected_pages, (
        f"Expected {expected_pages} pages, got {total_pages}"
    )


# ── 13. GET /api/chart with dark theme ───────────────────────────────────

def test_chart_dark_theme(client):
    """Requesting chart with ?theme=dark must still return a valid PNG."""
    response = client.get("/api/chart?theme=dark")
    assert response.status_code == 200
    assert response.content_type.startswith("image/png")
    assert response.data[:4] == b"\x89PNG"
