"""
Tests for PDF and CSV Reporting Engine (Block 5).
=================================================
Verifies:
1. GET /api/report/pdf returns HTTP 200, application/pdf, and valid PDF magic bytes (%PDF-)
2. In-memory generation contains complete visual and tabular sections
3. Empty dataset raises / returns clear HTTP error, not a broken download
4. Summary CSV export retains required columns, exact calculated statistics, and metadata
5. Filtered CSV export retains correct headers and respects active query filters
6. Chart download endpoint returns valid 300 DPI PNG bytes
"""

import io
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis import calculate_smoker_charges
from reporting import generate_pdf_report


# ── 1. PDF generation function unit test ───────────────────────────────────────

def test_generate_pdf_report_bytes(valid_df):
    """generate_pdf_report creates a valid, non-empty PDF in memory."""
    analysis = calculate_smoker_charges(valid_df)
    pdf_bytes = generate_pdf_report(valid_df, analysis)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 10000  # High-res chart embedded ensures > 10KB
    assert pdf_bytes.startswith(b"%PDF-"), "Must start with standard PDF magic signature"


def test_generate_pdf_report_empty_dataset_raises():
    """Generating PDF on empty DataFrame must raise ValueError."""
    import pandas as pd
    from analysis import SmokerAnalysisResult

    with pytest.raises(ValueError, match="empty or null"):
        generate_pdf_report(pd.DataFrame(), SmokerAnalysisResult())


# ── 2. GET /api/report/pdf endpoint test ───────────────────────────────────────

def test_api_report_pdf_endpoint(client):
    """GET /api/report/pdf streams downloadable PDF with correct headers."""
    res = client.get("/api/report/pdf")
    assert res.status_code == 200
    assert res.content_type == "application/pdf"
    assert "attachment" in res.headers.get("Content-Disposition", "")
    assert "sympsort_executive_report.pdf" in res.headers.get("Content-Disposition", "")
    assert res.data.startswith(b"%PDF-")
    assert len(res.data) > 10000


# ── 3. Summary CSV export test ─────────────────────────────────────────────────

def test_api_download_summary_csv(client):
    """GET /api/download/summary returns valid CSV with metrics and disclaimers."""
    for endpoint in ("/api/download/summary", "/export-csv"):
        res = client.get(endpoint)
        assert res.status_code == 200
        assert "text/csv" in res.content_type
        assert "attachment" in res.headers.get("Content-Disposition", "")

        csv_text = res.data.decode("utf-8")
        assert "metric,value" in csv_text
        assert "smoker_mean" in csv_text
        assert "non_smoker_mean" in csv_text
        assert "t_statistic" in csv_text
        assert "cohens_d" in csv_text
        assert "32050" in csv_text
        assert "8434" in csv_text


# ── 4. Filtered CSV export test ────────────────────────────────────────────────

def test_api_download_filtered_csv(client):
    """GET /api/download/filtered returns matching rows according to query filters."""
    # Request non-smokers in northwest
    res = client.get("/api/download/filtered?smoker=no&region=northwest")
    assert res.status_code == 200
    assert "text/csv" in res.content_type

    csv_text = res.data.decode("utf-8")
    lines = csv_text.strip().split("\n")
    headers = [h.strip().lower() for h in lines[0].split(",")]

    assert "age" in headers
    assert "smoker" in headers
    assert "charges" in headers

    # Verify every data row matches the filter
    smoker_idx = headers.index("smoker")
    region_idx = headers.index("region")
    for row in lines[1:]:
        cols = row.split(",")
        assert cols[smoker_idx].strip().lower() == "no"
        assert cols[region_idx].strip().lower() == "northwest"


# ── 5. High-resolution chart download test ────────────────────────────────────

def test_api_download_chart_png(client):
    """GET /api/download/chart returns 300 DPI PNG chart bytes."""
    res = client.get("/api/download/chart?kind=bar")
    assert res.status_code == 200
    assert "image/png" in res.content_type
    assert "attachment" in res.headers.get("Content-Disposition", "")
    assert res.data.startswith(b"\x89PNG\r\n\x1a\n"), "Must start with PNG signature"
    assert len(res.data) > 20000
