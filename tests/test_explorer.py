"""
Tests for Dataset Explorer Backend Improvements (Block 4).
==========================================================
Verifies:
1. Individual filters: search, smoker, region, sex, age_min/max, bmi_min/max, children
2. Combined multi-criteria filtering
3. Allowlisted sorting & invalid sort column rejection
4. Pagination clamping & stability
5. Selection summary computed over the entire filtered set (not just current page)
6. Filtered CSV export route
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── 1. Sex filter ──────────────────────────────────────────────────────────────

def test_filter_by_sex(client):
    """Filter records by sex (female vs male)."""
    res_female = client.get("/api/data?sex=female&page_size=100")
    assert res_female.status_code == 200
    data_female = res_female.get_json()
    assert data_female["total_filtered"] == 662
    for r in data_female["records"]:
        assert r["sex"] == "female"

    res_male = client.get("/api/data?sex=male&page_size=100")
    assert res_male.status_code == 200
    data_male = res_male.get_json()
    assert data_male["total_filtered"] == 676
    for r in data_male["records"]:
        assert r["sex"] == "male"

    # Total must equal 1,338
    assert data_female["total_filtered"] + data_male["total_filtered"] == 1338


# ── 2. Children filter ─────────────────────────────────────────────────────────

def test_filter_by_children(client):
    """Filter records by exact children count."""
    res_0 = client.get("/api/data?children=0")
    assert res_0.status_code == 200
    data_0 = res_0.get_json()
    assert data_0["total_filtered"] == 574
    for r in data_0["records"]:
        assert r["children"] == 0

    res_5 = client.get("/api/data?children=5")
    assert res_5.status_code == 200
    data_5 = res_5.get_json()
    assert data_5["total_filtered"] == 18
    for r in data_5["records"]:
        assert r["children"] == 5


# ── 3. Numeric Age Range filter ────────────────────────────────────────────────

def test_filter_by_numeric_age_range(client):
    """Filter records by age_min and age_max."""
    res = client.get("/api/data?age_min=30&age_max=35&page_size=100")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_filtered"] > 0
    for r in data["records"]:
        assert 30 <= r["age"] <= 35


# ── 4. Numeric BMI Range filter ────────────────────────────────────────────────

def test_filter_by_numeric_bmi_range(client):
    """Filter records by bmi_min and bmi_max."""
    res = client.get("/api/data?bmi_min=20.0&bmi_max=24.99&page_size=100")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_filtered"] > 0
    for r in data["records"]:
        assert 20.0 <= r["bmi"] <= 24.99


# ── 5. Text Search filter ──────────────────────────────────────────────────────

def test_filter_by_text_search(client):
    """Search matches against text or numeric attributes."""
    res = client.get("/api/data?search=southwest")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_filtered"] == 325
    for r in data["records"]:
        assert r["region"] == "southwest"


# ── 6. Combined multi-criteria filter ──────────────────────────────────────────

def test_combined_multi_criteria_filtering(client):
    """Intersect smoker, region, sex, children, and age range."""
    res = client.get("/api/data?smoker=yes&sex=female&region=southeast&children=0&age_min=25&age_max=50")
    assert res.status_code == 200
    data = res.get_json()
    for r in data["records"]:
        assert r["smoker"] == "yes"
        assert r["sex"] == "female"
        assert r["region"] == "southeast"
        assert r["children"] == 0
        assert 25 <= r["age"] <= 50


# ── 7. Allowlisted sorting & invalid column rejection ──────────────────────────

def test_allowlisted_sorting(client):
    """Sorting works for allowlisted columns and rejects invalid columns with 400."""
    # Ascending sort by charges
    res_asc = client.get("/api/data?sort=charges&order=asc&page_size=5")
    assert res_asc.status_code == 200
    records_asc = res_asc.get_json()["records"]
    assert records_asc[0]["charges"] <= records_asc[-1]["charges"]

    # Descending sort by charges
    res_desc = client.get("/api/data?sort=charges&order=desc&page_size=5")
    assert res_desc.status_code == 200
    records_desc = res_desc.get_json()["records"]
    assert records_desc[0]["charges"] >= records_desc[-1]["charges"]

    # Invalid column (SQL injection or unknown expression) is rejected with HTTP 400
    res_bad = client.get("/api/data?sort=id;DROP%20TABLE%20users--&order=asc")
    assert res_bad.status_code == 400
    data_bad = res_bad.get_json()
    assert data_bad["status"] == "error"
    assert "Invalid sort column" in data_bad["message"]

    # Invalid order is rejected with HTTP 400
    res_bad_order = client.get("/api/data?sort=charges&order=sideways")
    assert res_bad_order.status_code == 400
    assert "Invalid sort order" in res_bad_order.get_json()["message"]


# ── 8. Pagination validation & boundaries ──────────────────────────────────────

def test_pagination_boundaries(client):
    """Page and page_size values are validated and clamped."""
    # Non-integer page returns HTTP 400
    res_str = client.get("/api/data?page=abc")
    assert res_str.status_code == 400

    # Page < 1 returns HTTP 400
    res_neg = client.get("/api/data?page=-5&page_size=10")
    assert res_neg.status_code == 400

    # Oversized page number is clamped to total_pages
    res_over = client.get("/api/data?page=9999&page_size=50")
    assert res_over.status_code == 200
    data_over = res_over.get_json()
    assert data_over["page"] == data_over["pages"]

    # Page size > MAX_PAGE_SIZE (200) returns HTTP 400
    res_size = client.get("/api/data?page_size=500")
    assert res_size.status_code == 400
    assert "page_size must be between 1 and 200" in res_size.get_json()["message"]


# ── 9. Selection summary computed over entire filtered set ─────────────────────

def test_selection_summary_entire_dataset(client):
    """Selection summary must represent the entire filtered set, not just page 1."""
    # Filter only smokers (n = 274), but request page_size=10
    res = client.get("/api/data?smoker=yes&page=1&page_size=10")
    assert res.status_code == 200
    data = res.get_json()

    # The current page only has 10 records
    assert len(data["records"]) == 10

    # BUT the selection summary must represent all 274 smokers!
    summary = data["selection_summary"]
    assert summary["matched_records"] == 274
    assert summary["matched_count"] == 274
    # Mean of smokers across entire dataset is $32,050.23
    assert abs(summary["mean_charges"] - 32050.23) < 0.1
    assert abs(summary["average_charges"] - 32050.23) < 0.1
    # Median smoker charge is $34,456.35
    assert abs(summary["median_charges"] - 34456.35) < 0.1


# ── 10. Filtered CSV export endpoint ───────────────────────────────────────────

def test_download_filtered_csv(client):
    """Download filtered CSV route respects applied filters and sorting."""
    res = client.get("/api/download/filtered?smoker=yes&region=northeast&sort=charges&order=desc")
    assert res.status_code == 200
    assert "text/csv" in res.content_type
    content = res.data.decode("utf-8")
    lines = content.strip().split("\n")

    # Header line
    assert "age,sex,bmi,children,smoker,region,charges" in lines[0].lower()
    # Data rows: 67 smokers in northeast
    assert len(lines) == 67 + 1  # 67 rows + 1 header


# ── 11. Empty results & null statistics ────────────────────────────────────────

def test_empty_results_and_null_statistics(client):
    """When no records match, return total_filtered 0, empty records, and null (never 0.0) statistics."""
    # Search for an impossible combination: children=5, smoker=yes, region=northeast, age_min=60
    res = client.get("/api/data?children=5&smoker=yes&region=northeast&age_min=60")
    assert res.status_code == 200
    data = res.get_json()

    assert data["total_filtered"] == 0
    assert len(data["records"]) == 0
    assert data["page"] == 1
    assert data["pages"] == 1

    summary = data["selection_summary"]
    assert summary["matched_records"] == 0
    assert summary["matched_count"] == 0
    # Must be None / null in JSON, NOT 0.0
    assert summary["mean_charges"] is None
    assert summary["median_charges"] is None
    assert summary["mean_bmi"] is None
    assert summary["average_charges"] is None
    assert summary["average_bmi"] is None


# ── 12. Invalid category & numeric range validation (HTTP 400) ─────────────────

def test_invalid_filters_return_400(client):
    """Query parameters with invalid categories, inverted ranges, or invalid formats must return HTTP 400."""
    # Invalid smoker category
    res = client.get("/api/data?smoker=sometimes")
    assert res.status_code == 400
    assert "Invalid smoker" in res.get_json()["message"]

    # Invalid sex category
    res = client.get("/api/data?sex=other")
    assert res.status_code == 400
    assert "Invalid sex" in res.get_json()["message"]

    # Invalid region
    res = client.get("/api/data?region=antarctica")
    assert res.status_code == 400
    assert "Invalid region" in res.get_json()["message"]

    # Inverted age range (age_min > age_max)
    res = client.get("/api/data?age_min=50&age_max=20")
    assert res.status_code == 400
    assert "Invalid age range" in res.get_json()["message"]

    # Negative age_min
    res = client.get("/api/data?age_min=-5")
    assert res.status_code == 400
    assert "age_min cannot be negative" in res.get_json()["message"]

    # Non-numeric age_min
    res = client.get("/api/data?age_min=fifty")
    assert res.status_code == 400
    assert "Invalid age_min" in res.get_json()["message"]

    # Inverted BMI range (bmi_min > bmi_max)
    res = client.get("/api/data?bmi_min=35.0&bmi_max=25.0")
    assert res.status_code == 400
    assert "Invalid BMI range" in res.get_json()["message"]

    # Invalid children count
    res = client.get("/api/data?children=many")
    assert res.status_code == 400
    assert "Invalid children" in res.get_json()["message"]
