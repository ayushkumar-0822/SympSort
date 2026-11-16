"""
SympSort — Flask Web Application
=================================
Application factory and routes for the SympSort desktop web application.
Serves static assets, HTML templates, and REST JSON APIs for data,
statistical summaries, charts, and file downloads.
"""

from __future__ import annotations

import csv
import io
import logging
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Optional

# Ensure Matplotlib config directory is writable across all OS & serverless environments
mpl_dir = os.path.join(tempfile.gettempdir(), ".matplotlib")
os.environ.setdefault("MPLCONFIGDIR", mpl_dir)

import pandas as pd
from flask import (
    Flask,
    Response,
    jsonify,
    render_template,
    request,
    send_file,
)

import config
from analysis import SmokerAnalysisResult, calculate_smoker_charges
from data_loader import ValidationReport, load_dataset
from visualization import clear_chart_cache, generate_chart_bytes, save_default_chart

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure the Flask application."""
    base_dir = Path(__file__).resolve().parent
    app = Flask(
        __name__,
        template_folder=str(base_dir / "templates"),
        static_folder=str(base_dir / "static"),
    )
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    def get_asset_version() -> str:
        """Return timestamp of newest static asset to guarantee cache-busting."""
        try:
            static_dir = Path(__file__).parent / "static"
            css_mtime = (static_dir / "css" / "desktop.css").stat().st_mtime
            js_mtime = (static_dir / "js" / "app.js").stat().st_mtime
            return str(int(max(css_mtime, js_mtime)))
        except Exception:
            return "2.1"

    @app.context_processor
    def inject_asset_version():
        return {"asset_version": get_asset_version()}

    @app.after_request
    def add_no_cache_headers(response):
        if "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    # ── Application-level cache ───────────────────────────────────────────
    _cache: dict[str, Any] = {
        "df_valid": None,
        "df_raw": None,
        "report": None,
        "analysis": None,
    }

    def get_data(
        force_reload: bool = False,
    ) -> tuple[pd.DataFrame, SmokerAnalysisResult, ValidationReport]:
        """Return cached (df, analysis, report), loading on first call."""
        if not force_reload and _cache["df_valid"] is not None:
            return _cache["df_valid"], _cache["analysis"], _cache["report"]

        logger.info("Loading dataset (force_reload=%s)", force_reload)
        df_valid, df_raw, report = load_dataset()

        if report.is_valid and df_valid is not None and not df_valid.empty:
            analysis = calculate_smoker_charges(df_valid)
            if not os.environ.get("VERCEL"):
                try:
                    save_default_chart(df_valid)
                except Exception as exc:
                    logger.warning("Could not pre-save default chart: %s", exc)
        else:
            analysis = SmokerAnalysisResult()
            df_valid = pd.DataFrame()
            df_raw = pd.DataFrame()

        _cache["df_valid"] = df_valid
        _cache["df_raw"] = df_raw
        _cache["report"] = report
        _cache["analysis"] = analysis

        return df_valid, analysis, report

    # ── Page routes ───────────────────────────────────────────────────────

    @app.route("/")
    @app.route("/api/index")
    def index():
        """Serve the single-page application shell."""
        df, analysis, report = get_data()
        return render_template(
            "index.html",
            project_name=config.PROJECT_NAME,
            project_title=config.PROJECT_TITLE,
            course_name=config.COURSE_NAME,
            course_code=config.COURSE_CODE,
            academic_year=getattr(config, "ACADEMIC_YEAR", "2026–27"),
            assigned_problem_statement=getattr(
                config, "ASSIGNED_PROBLEM_STATEMENT", config.PROBLEM_STATEMENT
            ),
            problem_statement=config.PROBLEM_STATEMENT,
            dataset_source_url=config.DATASET_SOURCE_URL,
            dataset_source_name=getattr(config, "DATASET_SOURCE_NAME", "Medical Cost Personal Datasets (Kaggle)"),
            analysis=analysis.to_dict(),
            report={
                "is_valid": report.is_valid,
                "total_raw_rows": report.total_raw_rows,
                "valid_rows": report.valid_rows,
                "excluded_rows": report.excluded_rows,
                "used_sample": report.used_sample,
            },
        )

    # ── API routes ────────────────────────────────────────────────────────

    @app.route("/api")
    def api_root():
        """API discovery endpoint."""
        return jsonify({
            "status": "ok",
            "message": "SympSort API is active",
            "endpoints": [
                "/api/health",
                "/api/summary",
                "/api/chart",
                "/api/data",
                "/api/sample-data",
                "/api/profile-match",
                "/api/data-quality",
            ],
        })

    @app.route("/api/health")
    def api_health():
        """Simple health check endpoint."""
        df, _analysis, _report = get_data()
        return jsonify({"status": "ok", "rows": len(df)})

    @app.route("/api/summary")
    def api_summary():
        """Full analysis summary as JSON."""
        df, analysis, report = get_data()
        payload = analysis.to_dict()
        payload["status"] = "success"
        payload["is_valid"] = report.is_valid
        payload["analysis"] = analysis.to_dict()
        payload["validation"] = {
            "is_valid": report.is_valid,
            "file_path": report.file_path,
            "total_raw_rows": report.total_raw_rows,
            "valid_rows": report.valid_rows,
            "excluded_rows": report.excluded_rows,
            "null_charges_count": report.null_charges_count,
            "invalid_smoker_count": report.invalid_smoker_count,
            "used_sample": report.used_sample,
            "warnings": report.warnings,
        }
        return jsonify(payload)

    @app.route("/api/chart")
    def api_chart():
        """Return chart PNG. ``?theme=dark`` for dark-mode variant. ``?kind=bar|dist|box|scatter|region|sex|age``."""
        df, analysis, _report = get_data()
        chart_data = df if (df is not None and not df.empty) else analysis.df_grouped
        if chart_data is None:
            return jsonify({"error": "No data available"}), 500

        theme = request.args.get("theme", "light").strip().lower()
        kind = request.args.get("kind", "bar").strip().lower()
        dark_mode = theme == "dark"
        png_bytes = generate_chart_bytes(
            chart_data, kind=kind, dark_mode=dark_mode, high_res=False
        )
        return send_file(
            io.BytesIO(png_bytes),
            mimetype="image/png",
            download_name=f"chart_{kind}.png",
        )

    @app.route("/api/data")
    def api_data():
        """Paginated, filterable, sortable dataset rows."""
        df, _analysis, _report = get_data()
        filtered = _apply_filters(df, request.args)

        # Sorting
        sort_col = request.args.get("sort", "").strip().lower()
        order = request.args.get("order", "asc").strip().lower()
        if sort_col and sort_col in filtered.columns:
            ascending = order != "desc"
            filtered = filtered.sort_values(by=sort_col, ascending=ascending)

        # Pagination
        try:
            page = max(1, int(request.args.get("page", 1)))
        except (ValueError, TypeError):
            page = 1
        try:
            page_size = min(
                config.MAX_PAGE_SIZE,
                max(1, int(request.args.get("page_size", config.DEFAULT_PAGE_SIZE))),
            )
        except (ValueError, TypeError):
            page_size = config.DEFAULT_PAGE_SIZE

        total_filtered = len(filtered)
        total_pages = max(1, math.ceil(total_filtered / page_size))
        page = min(page, total_pages)

        start = (page - 1) * page_size
        end = start + page_size
        page_df = filtered.iloc[start:end]

        # Convert to list[dict], replacing NaN with None for JSON
        records = _df_to_records(page_df)

        selection_summary = {
            "matched_count": total_filtered,
            "mean_charges": round(float(filtered[config.COLUMN_CHARGES].mean()), 2) if total_filtered > 0 else 0.0,
            "median_charges": round(float(filtered[config.COLUMN_CHARGES].median()), 2) if total_filtered > 0 else 0.0,
            "mean_bmi": round(float(filtered[config.COLUMN_BMI].mean()), 2) if (total_filtered > 0 and config.COLUMN_BMI in filtered.columns) else 0.0,
        }

        return jsonify({
            "records": records,
            "total_records": len(df),
            "total_unfiltered": len(df),
            "total_filtered": total_filtered,
            "selection_summary": selection_summary,
            "page": page,
            "pages": total_pages,
            "total_pages": total_pages,
            "page_size": page_size,
        })

    @app.route("/api/sample-data")
    def api_sample_data():
        """Return sample records for initial preview tables."""
        df, _analysis, _report = get_data()
        try:
            limit = min(50, max(1, int(request.args.get("limit", 5))))
        except (ValueError, TypeError):
            limit = 5
        sample_df = df.head(limit)
        return jsonify({
            "status": "success",
            "count": len(sample_df),
            "total_records": len(df),
            "records": _df_to_records(sample_df),
        })

    @app.route("/api/reload", methods=["POST"])
    def api_reload():
        """Force-reload the dataset from disk."""
        clear_chart_cache()
        df, _analysis, report = get_data(force_reload=True)
        return jsonify({
            "status": "success",
            "message": f"Reloaded {len(df)} rows",
            "total_rows": len(df),
            "rows": len(df),
            "valid_rows": report.valid_rows,
            "is_valid": report.is_valid,
        })

    @app.route("/api/download/chart")
    def api_download_chart():
        """Download high-resolution (300 DPI) chart."""
        df, analysis, _report = get_data()
        chart_data = df if (df is not None and not df.empty) else analysis.df_grouped
        if chart_data is None:
            return jsonify({"error": "No data available"}), 500

        kind = request.args.get("kind", "bar").strip().lower()
        png_bytes = generate_chart_bytes(
            chart_data, kind=kind, dark_mode=False, high_res=True
        )
        return send_file(
            io.BytesIO(png_bytes),
            mimetype="image/png",
            as_attachment=True,
            download_name=f"sympsort_{kind}_chart.png",
        )

    @app.route("/api/profile-match")
    def api_profile_match():
        """Empirical profile matcher: filter records by profile criteria."""
        df, _analysis, _report = get_data()
        if df is None or df.empty:
            return jsonify({"status": "error", "message": "No data available"}), 500

        matched = df.copy()

        # Age band filter
        age_band = request.args.get("age_band", "all").strip().lower()
        if age_band == "18-29":
            matched = matched[(matched[config.COLUMN_AGE] >= 18) & (matched[config.COLUMN_AGE] <= 29)]
        elif age_band == "30-44":
            matched = matched[(matched[config.COLUMN_AGE] >= 30) & (matched[config.COLUMN_AGE] <= 44)]
        elif age_band == "45-64":
            matched = matched[(matched[config.COLUMN_AGE] >= 45) & (matched[config.COLUMN_AGE] <= 64)]

        # BMI band filter
        bmi_band = request.args.get("bmi_band", "all").strip().lower()
        if bmi_band in ("<25", "normal"):
            matched = matched[matched[config.COLUMN_BMI] < 25.0]
        elif bmi_band in ("25-29.9", "overweight"):
            matched = matched[(matched[config.COLUMN_BMI] >= 25.0) & (matched[config.COLUMN_BMI] < 30.0)]
        elif bmi_band in (">=30", "obese"):
            matched = matched[matched[config.COLUMN_BMI] >= 30.0]

        # Sex filter
        sex = request.args.get("sex", "all").strip().lower()
        if sex in ("male", "female"):
            matched = matched[matched[config.COLUMN_SEX] == sex]

        # Region filter
        region = request.args.get("region", "all").strip().lower()
        if region in config.VALID_REGIONS:
            matched = matched[matched[config.COLUMN_REGION] == region]

        # Smoker filter
        smoker = request.args.get("smoker", "all").strip().lower()
        if smoker in config.VALID_SMOKER_VALUES:
            matched = matched[matched[config.COLUMN_SMOKER] == smoker]

        count = len(matched)
        if count == 0:
            return jsonify({
                "status": "success",
                "count": 0,
                "mean": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "warning": "No matching records found in dataset for this profile.",
            })

        mean_val = round(float(matched[config.COLUMN_CHARGES].mean()), 2)
        med_val = round(float(matched[config.COLUMN_CHARGES].median()), 2)
        min_val = round(float(matched[config.COLUMN_CHARGES].min()), 2)
        max_val = round(float(matched[config.COLUMN_CHARGES].max()), 2)

        warning = (
            f"Small sample size (n = {count} < 20). Empirical estimates have higher statistical variance."
            if count < 20
            else None
        )

        return jsonify({
            "status": "success",
            "count": count,
            "mean": mean_val,
            "median": med_val,
            "min": min_val,
            "max": max_val,
            "warning": warning,
        })

    @app.route("/api/data-quality")
    def api_data_quality():
        """Data quality report and inspection data for methodology view."""
        df, _analysis, report = get_data()
        num_cols = [c for c in [config.COLUMN_AGE, config.COLUMN_BMI, config.COLUMN_CHILDREN, config.COLUMN_CHARGES] if c in df.columns]
        desc_dict = df[num_cols].describe().round(2).to_dict() if not df.empty else {}

        info_list = []
        for col in df.columns:
            info_list.append({
                "column": col,
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].notna().sum()),
                "null_count": int(df[col].isna().sum()),
            })

        return jsonify({
            "status": "success",
            "validation": {
                "is_valid": report.is_valid,
                "file_path": report.file_path,
                "total_raw_rows": report.total_raw_rows,
                "valid_rows": report.valid_rows,
                "excluded_rows": report.excluded_rows,
                "null_charges_count": report.null_charges_count,
                "invalid_smoker_count": report.invalid_smoker_count,
                "used_sample": report.used_sample,
                "warnings": report.warnings,
            },
            "columns": info_list,
            "describe": desc_dict,
            "head": _df_to_records(df.head(5)),
        })

    @app.route("/api/download/filtered")
    def api_download_filtered():
        """Download currently filtered and sorted rows as CSV."""
        df, _analysis, _report = get_data()
        filtered = _apply_filters(df, request.args)

        sort_col = request.args.get("sort", "").strip().lower()
        order = request.args.get("order", "asc").strip().lower()
        if sort_col and sort_col in filtered.columns:
            ascending = order != "desc"
            filtered = filtered.sort_values(by=sort_col, ascending=ascending)

        buf = io.StringIO()
        filtered.to_csv(buf, index=False)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=sympsort_filtered_records.csv"
            },
        )

    @app.route("/export-csv")
    @app.route("/api/download/summary")
    def api_download_summary():
        """Download analysis summary as CSV."""
        _df, analysis, _report = get_data()
        summary = analysis.to_dict()

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["metric", "value"])
        for k, v in summary.items():
            if k not in ("academic_disclaimer", "groupby_text"):
                writer.writerow([k, v])

        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=smoker_charges_summary.csv"
            },
        )

    # ── Global Exception Handler (Surfaces full traceback for Vercel debugging) ──
    @app.errorhandler(Exception)
    def handle_all_exceptions(exc: Exception):
        import html
        import traceback

        tb = traceback.format_exc()
        logger.critical("Unhandled Exception: %s", tb)
        print(f"CRITICAL APP ERROR:\n{tb}", file=sys.stderr, flush=True)

        code = getattr(exc, "code", 500)
        return (
            f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>SympSort Server Error ({code})</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, monospace; background: #141416; color: #f4f4f5; padding: 2.5rem; }}
    h1 {{ color: #f87171; font-size: 1.3rem; margin-top: 0; }}
    pre {{ background: #1f1f23; border: 1px solid #333; padding: 1.25rem; border-radius: 6px; overflow-x: auto; font-size: 0.88rem; line-height: 1.5; color: #e4e4e7; }}
  </style>
</head>
<body>
  <h1>Server Error ({code}): {html.escape(str(exc))}</h1>
  <pre>{html.escape(tb)}</pre>
</body>
</html>""",
            code,
            {"Content-Type": "text/html; charset=utf-8"},
        )

    return app


# ── Internal helpers ──────────────────────────────────────────────────────────

def _apply_filters(df: pd.DataFrame, params: dict[str, Any]) -> pd.DataFrame:
    """Filter DataFrame by search query, smoker status, and region."""
    filtered = df.copy()

    # Smoker filter
    smoker = params.get("smoker", "").strip().lower()
    if smoker in config.VALID_SMOKER_VALUES:
        filtered = filtered[filtered[config.COLUMN_SMOKER] == smoker]

    # Region filter
    region = params.get("region", "").strip().lower()
    if region and region in config.VALID_REGIONS:
        filtered = filtered[filtered[config.COLUMN_REGION] == region]

    # Search filter (across text & numeric columns)
    search = params.get("search", "").strip().lower()
    if search:
        masks = []
        for col in filtered.columns:
            masks.append(
                filtered[col].astype(str).str.lower().str.contains(search, regex=False)
            )
        combined_mask = pd.concat(masks, axis=1).any(axis=1)
        filtered = filtered[combined_mask]

    return filtered


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame rows to JSON-safe dictionaries (NaN -> None)."""
    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        record: dict[str, Any] = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                record[col] = None
            elif isinstance(val, (int, float)):
                # Ensure Python native types
                record[col] = int(val) if isinstance(val, int) or val == int(val) else float(val)
            else:
                record[col] = str(val)
        records.append(record)
    return records


# ── WSGI Application Instance for Vercel / Gunicorn Deployment ───────────────
app = create_app()

