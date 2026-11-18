/**
 * SympSort — Medical Cost & Lifestyle Factors
 * ===========================================
 * Client application controller.
 * Handles client-side hash routing, theme toggling, data fetching,
 * animated number tickers, accessible sortable table rendering,
 * and live methodology output.
 */

(function () {
  "use strict";

  // ── Currency and Number Formatters ───────────────────────────────────────
  const CURRENCY = new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

  const NUMBER = new Intl.NumberFormat("en-US");

  function escapeHtml(str) {
    if (str == null) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // ── Column Definitions (Single source of truth for Table) ────────────────
  const COLUMNS = [
    { key: "age", label: "Age", align: "right", sortable: true },
    { key: "sex", label: "Sex", align: "left", sortable: true },
    {
      key: "bmi",
      label: "BMI",
      align: "right",
      sortable: true,
      format: (v) => (v != null && !isNaN(v) ? Number(v).toFixed(2) : "—"),
    },
    { key: "children", label: "Children", align: "right", sortable: true },
    {
      key: "smoker",
      label: "Smoker",
      align: "left",
      sortable: true,
      format: (v) =>
        v === "yes"
          ? '<span class="tag tag--smoker">yes</span>'
          : '<span class="tag tag--nonsmoker">no</span>',
    },
    { key: "region", label: "Region", align: "left", sortable: true },
    {
      key: "charges",
      label: "Charges",
      align: "right",
      sortable: true,
      format: (v) => (v != null && !isNaN(v) ? CURRENCY.format(v) : "—"),
    },
  ];

  // ── Application State ───────────────────────────────────────────────────
  const state = {
    currentView: "overview",
    theme: localStorage.getItem("sympsort_editorial_theme") || "light",
    chartMode: "seaborn", // "seaborn" or "canvas"
    comparisonChartKind: "bar",
    summary: null,
    hasAnimatedNumbers: false,
    dataQualityLoaded: false,
    scenarioLoaded: false,
    explorer: {
      page: 1,
      pageSize: 15,
      search: "",
      smoker: "",
      region: "",
      sex: "",
      children: "",
      bmi: "",
      age: "",
      sort: "",
      order: "asc",
      totalFiltered: 0,
      totalPages: 1,
      isLoading: false,
    },
  };

  // ── DOM Element Cache ───────────────────────────────────────────────────
  const elements = {
    html: document.documentElement,
    navItems: document.querySelectorAll(".nav-item"),
    views: document.querySelectorAll(".view"),
    headerTitle: document.getElementById("headerTitle"),
    themeToggle: document.getElementById("themeToggle"),
    reloadBtn: document.getElementById("reloadBtn"),
    exportChartBtn: document.getElementById("exportChartBtn"),
    downloadSummaryLink: document.getElementById("downloadSummaryLink"),
    downloadFilteredLink: document.getElementById("downloadFilteredLink"),
    statusPill: document.getElementById("statusPill"),
    toastContainer: document.getElementById("toastContainer"),
    mobileMenuBtn: document.getElementById("mobileMenuBtn"),
    sidebar: document.querySelector(".sidebar"),

    // Overview
    overviewSkeleton: document.getElementById("overviewSkeleton"),
    overviewError: document.getElementById("overviewError"),
    overviewRetry: document.getElementById("overviewRetry"),
    overviewContent: document.getElementById("overviewContent"),
    findingLine: document.getElementById("findingLine"),
    kpiNonSmoker: document.getElementById("kpiNonSmoker"),
    kpiSmoker: document.getElementById("kpiSmoker"),
    diffAbs: document.getElementById("diffAbs"),
    diffBadge: document.getElementById("diffBadge"),
    kpiMultiplier: document.getElementById("kpiMultiplier"),
    kpiNonSmokerCount: document.getElementById("kpiNonSmokerCount"),
    kpiSmokerCount: document.getElementById("kpiSmokerCount"),
    kpiValidCount: document.getElementById("kpiValidCount"),
    heroChart: document.getElementById("heroChart"),
    sampleBody: document.getElementById("sampleBody"),

    // Overview Chart Controls & Views
    overviewChartContainer: document.getElementById("overviewChartContainer"),
    tabSeaborn: document.getElementById("tabSeaborn"),
    tabCanvas: document.getElementById("tabCanvas"),
    chartLoadingOverlay: document.getElementById("chartLoadingOverlay"),
    chartErrorOverlay: document.getElementById("chartErrorOverlay"),
    chartRetryBtn: document.getElementById("chartRetryBtn"),
    seabornFigure: document.getElementById("seabornFigure"),
    canvasWrapper: document.getElementById("canvasWrapper"),
    overviewCanvas: document.getElementById("overviewCanvas"),

    // Comparison
    comparisonSkeleton: document.getElementById("comparisonSkeleton"),
    comparisonError: document.getElementById("comparisonError"),
    comparisonRetry: document.getElementById("comparisonRetry"),
    comparisonContent: document.getElementById("comparisonContent"),
    statsBody: document.getElementById("statsBody"),
    comparisonChart: document.getElementById("comparisonChart"),
    comparisonChartSelector: document.getElementById("comparisonChartSelector"),
    comparisonActiveKindBadge: document.getElementById("comparisonActiveKindBadge"),
    comparisonChartCaption: document.getElementById("comparisonChartCaption"),
    comparisonTakeawayText: document.getElementById("comparisonTakeawayText"),
    statSignificancePill: document.getElementById("statSignificancePill"),
    statTVal: document.getElementById("statTVal"),
    statTSub: document.getElementById("statTSub"),
    statMWVal: document.getElementById("statMWVal"),
    statCohenVal: document.getElementById("statCohenVal"),
    statCautionNote: document.getElementById("statCautionNote"),
    profileAge: document.getElementById("profileAge"),
    profileBmi: document.getElementById("profileBmi"),
    profileSex: document.getElementById("profileSex"),
    profileRegion: document.getElementById("profileRegion"),
    profileSmoker: document.getElementById("profileSmoker"),
    profileMatchCount: document.getElementById("profileMatchCount"),
    profileMatchMean: document.getElementById("profileMatchMean"),
    profileMatchMedian: document.getElementById("profileMatchMedian"),
    profileMatchRange: document.getElementById("profileMatchRange"),
    profileWarning: document.getElementById("profileWarning"),

    // Scenario Comparison Elements
    scenMeanA: document.getElementById("scenMeanA"),
    scenCountA: document.getElementById("scenCountA"),
    scenMedianA: document.getElementById("scenMedianA"),
    scenCiA: document.getElementById("scenCiA"),
    scenMeanB: document.getElementById("scenMeanB"),
    scenCountB: document.getElementById("scenCountB"),
    scenMedianB: document.getElementById("scenMedianB"),
    scenCiB: document.getElementById("scenCiB"),
    scenDiffMean: document.getElementById("scenDiffMean"),
    scenPctBadge: document.getElementById("scenPctBadge"),
    scenMultiplier: document.getElementById("scenMultiplier"),
    scenTStat: document.getElementById("scenTStat"),
    scenStatement: document.getElementById("scenStatement"),
    scenWarning: document.getElementById("scenWarning"),

    // Scenario Comparison (View 6)
    scenA_smoker: document.getElementById("scenA_smoker"),
    scenA_sex: document.getElementById("scenA_sex"),
    scenA_region: document.getElementById("scenA_region"),
    scenA_age_min: document.getElementById("scenA_age_min"),
    scenA_age_max: document.getElementById("scenA_age_max"),
    scenA_bmi_min: document.getElementById("scenA_bmi_min"),
    scenA_bmi_max: document.getElementById("scenA_bmi_max"),
    scenA_children: document.getElementById("scenA_children"),

    scenB_smoker: document.getElementById("scenB_smoker"),
    scenB_sex: document.getElementById("scenB_sex"),
    scenB_region: document.getElementById("scenB_region"),
    scenB_age_min: document.getElementById("scenB_age_min"),
    scenB_age_max: document.getElementById("scenB_age_max"),
    scenB_bmi_min: document.getElementById("scenB_bmi_min"),
    scenB_bmi_max: document.getElementById("scenB_bmi_max"),
    scenB_children: document.getElementById("scenB_children"),

    scenCompareRunBtn: document.getElementById("scenCompareRunBtn"),
    scenCompareResetBtn: document.getElementById("scenCompareResetBtn"),
    downloadScenarioPdfBtn: document.getElementById("downloadScenarioPdfBtn"),
    downloadScenarioPdfBtn2: document.getElementById("downloadScenarioPdfBtn2"),
    scenStatusIndicator: document.getElementById("scenStatusIndicator"),
    scenDiffCard: document.getElementById("scenDiffCard"),
    scenDiffAmount: document.getElementById("scenDiffAmount"),
    scenDiffPctBadge: document.getElementById("scenDiffPctBadge"),
    scenHigherBadge: document.getElementById("scenHigherBadge"),
    scenWarningBox: document.getElementById("scenWarningBox"),
    scenWarningText: document.getElementById("scenWarningText"),
    scenDiffTStat: document.getElementById("scenDiffTStat"),
    scenRefNote: document.getElementById("scenRefNote"),
    scenStatsACount: document.getElementById("scenStatsACount"),
    scenStatsAMean: document.getElementById("scenStatsAMean"),
    scenStatsAMedian: document.getElementById("scenStatsAMedian"),
    scenStatsARange: document.getElementById("scenStatsARange"),
    scenStatsAStd: document.getElementById("scenStatsAStd"),
    scenStatsACI: document.getElementById("scenStatsACI"),
    scenStatsBCount: document.getElementById("scenStatsBCount"),
    scenStatsBMean: document.getElementById("scenStatsBMean"),
    scenStatsBMedian: document.getElementById("scenStatsBMedian"),
    scenStatsBRange: document.getElementById("scenStatsBRange"),
    scenStatsBStd: document.getElementById("scenStatsBStd"),
    scenStatsBCI: document.getElementById("scenStatsBCI"),
    scenDisclaimerText: document.getElementById("scenDisclaimerText"),

    // Explorer
    explorerSearch: document.getElementById("explorerSearch"),
    smokerFilter: document.getElementById("smokerFilter"),
    smokerPills: document.getElementById("smokerPills"),
    regionFilter: document.getElementById("regionFilter"),
    sexFilter: document.getElementById("sexFilter"),
    childrenFilter: document.getElementById("childrenFilter"),
    bmiFilter: document.getElementById("bmiFilter"),
    ageFilter: document.getElementById("ageFilter"),
    resetFiltersBtn: document.getElementById("resetFiltersBtn"),
    selectionSummaryStrip: document.getElementById("selectionSummaryStrip"),
    selCount: document.getElementById("selCount"),
    selMean: document.getElementById("selMean"),
    selMedian: document.getElementById("selMedian"),
    selBmi: document.getElementById("selBmi"),
    explorerTable: document.getElementById("explorerTable"),
    explorerHead: document.getElementById("explorerHead"),
    explorerBody: document.getElementById("explorerBody"),
    explorerEmpty: document.getElementById("explorerEmpty"),
    pageSize: document.getElementById("pageSize"),
    showingText: document.getElementById("showingText"),
    pagination: document.getElementById("pagination"),

    // Methodology
    methodologyCode: document.getElementById("methodologyCode"),
    copyCodeBtn: document.getElementById("copyCodeBtn"),
    groupbyOutput: document.getElementById("groupbyOutput"),
    auditRawRows: document.getElementById("auditRawRows"),
    auditValidRows: document.getElementById("auditValidRows"),
    auditExcludedRows: document.getElementById("auditExcludedRows"),
    auditNulls: document.getElementById("auditNulls"),
    auditDescribeOutput: document.getElementById("auditDescribeOutput"),
    auditHeadOutput: document.getElementById("auditHeadOutput"),
    auditInfoOutput: document.getElementById("auditInfoOutput"),
    qualityTabs: document.querySelectorAll(".quality-tab"),
  };

  // ── Toast Notification System ───────────────────────────────────────────
  function showToast(message, duration = 3000) {
    if (!elements.toastContainer) return;
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.textContent = message;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.classList.add("toast--exit");
      setTimeout(() => toast.remove(), 250);
    }, duration);
  }

  // ── Health Check & Status Pill ──────────────────────────────────────────
  async function checkHealth() {
    if (!elements.statusPill) return;
    const dot = elements.statusPill.querySelector(".status-dot");
    const text = elements.statusPill.querySelector(".status-text");

    let isConnected = false;
    let rows = null;

    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        if (data && typeof data.rows === "number") {
          isConnected = true;
          rows = data.rows;
        }
      }
    } catch {}

    if (!isConnected) {
      const embeddedEl = document.getElementById("serverSummaryData");
      if (embeddedEl && embeddedEl.textContent.trim()) {
        try {
          const s = JSON.parse(embeddedEl.textContent);
          if (s && typeof s.total_valid_records === "number") {
            rows = s.total_valid_records;
            isConnected = true;
          }
        } catch {}
      }
    }

    if (isConnected) {
      if (dot) dot.className = "status-dot status-dot--connected";
      if (text) text.textContent = rows != null ? `Connected (${NUMBER.format(rows)} rows)` : "Connected";
    } else {
      if (dot) dot.className = "status-dot status-dot--offline";
      if (text) text.textContent = "Offline";
    }
  }

  // ── Theme Management ────────────────────────────────────────────────────
  function applyTheme(themeName) {
    state.theme = themeName;
    elements.html.setAttribute("data-theme", themeName);
    localStorage.setItem("sympsort_editorial_theme", themeName);

    if (elements.themeToggle) {
      elements.themeToggle.textContent = themeName === "dark" ? "🌙" : "☀";
      elements.themeToggle.setAttribute(
        "title",
        themeName === "dark" ? "Switch to light theme" : "Switch to dark theme"
      );
    }

    // Refresh charts with theme param
    refreshCharts();
  }

  function toggleTheme() {
    const next = state.theme === "dark" ? "light" : "dark";
    applyTheme(next);
  }

  function refreshCharts() {
    const t = `${state.theme}&_t=${Date.now()}`;
    if (elements.chartLoadingOverlay) {
      elements.chartLoadingOverlay.classList.remove("hidden");
    }
    if (elements.chartErrorOverlay) {
      elements.chartErrorOverlay.classList.add("hidden");
    }

    if (elements.heroChart) {
      elements.heroChart.classList.remove("loaded");
      elements.heroChart.src = `/api/chart?kind=bar&theme=${t}`;
    }
    if (elements.comparisonChart) {
      elements.comparisonChart.classList.remove("loaded");
      elements.comparisonChart.src = `/api/chart?kind=${state.comparisonChartKind || "bar"}&theme=${t}`;
    }

    if (state.summary && elements.overviewCanvas) {
      renderOverviewCanvas(state.summary);
    }
  }

  // ── Chart Render Mode Switching ─────────────────────────────────────────
  function setChartMode(mode) {
    state.chartMode = mode;
    if (elements.tabSeaborn && elements.tabCanvas) {
      elements.tabSeaborn.classList.toggle("active", mode === "seaborn");
      elements.tabCanvas.classList.toggle("active", mode === "canvas");
    }
    if (elements.seabornFigure && elements.canvasWrapper) {
      if (mode === "seaborn") {
        elements.seabornFigure.classList.remove("hidden");
        elements.canvasWrapper.classList.add("hidden");
      } else {
        elements.seabornFigure.classList.add("hidden");
        elements.canvasWrapper.classList.remove("hidden");
        if (state.summary) {
          renderOverviewCanvas(state.summary);
        }
      }
    }
  }

  // ── High-DPI Interactive Canvas Chart Renderer ──────────────────────────
  function renderOverviewCanvas(data) {
    if (!elements.overviewCanvas) return;
    const canvas = elements.overviewCanvas;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Scale with devicePixelRatio for crisp typography
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const cssWidth = rect.width > 50 ? rect.width : 800;
    const cssHeight = rect.height > 50 ? rect.height : 420;

    canvas.width = Math.round(cssWidth * dpr);
    canvas.height = Math.round(cssHeight * dpr);
    ctx.resetTransform?.();
    ctx.scale(dpr, dpr);

    const isDark = state.theme === "dark";
    const bg = isDark ? "#1E1F22" : "#FAF8F4";
    const textColor = isDark ? "#E8E6E1" : "#1C1B19";
    const textSec = isDark ? "#9C998F" : "#6B6760";
    const gridColor = isDark ? "rgba(255, 255, 255, 0.08)" : "rgba(0, 0, 0, 0.08)";
    const colorNonSmoker = "#1F6F63";
    const colorSmoker = "#B5442E";

    // Clear background
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, cssWidth, cssHeight);

    // Validate that required summary means are present
    const hasData =
      data &&
      typeof data.non_smoker_mean === "number" &&
      typeof data.smoker_mean === "number" &&
      !isNaN(data.non_smoker_mean) &&
      !isNaN(data.smoker_mean);

    if (!hasData) {
      ctx.fillStyle = textSec;
      ctx.font = "14px system-ui, -apple-system, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Statistical summary data unavailable.", cssWidth / 2, cssHeight / 2);
      return;
    }

    const nsMean = data.non_smoker_mean;
    const smMean = data.smoker_mean;
    const nsCount = typeof data.non_smoker_count === "number" ? data.non_smoker_count : null;
    const smCount = typeof data.smoker_count === "number" ? data.smoker_count : null;

    // Use genuine calculated confidence interval margins from backend (derived from Student's t critical values)
    const nsCI = typeof data.non_smoker_ci_margin === "number" && !isNaN(data.non_smoker_ci_margin) ? data.non_smoker_ci_margin : null;
    const smCI = typeof data.smoker_ci_margin === "number" && !isNaN(data.smoker_ci_margin) ? data.smoker_ci_margin : null;

    // Plot geometry
    const margin = { top: 55, right: 35, bottom: 65, left: 80 };
    const plotWidth = Math.max(100, cssWidth - margin.left - margin.right);
    const plotHeight = Math.max(100, cssHeight - margin.top - margin.bottom);

    const maxVal = Math.max(40000, (smMean + (smCI || 0)) * 1.15);
    const scaleY = (val) => margin.top + plotHeight - (val / maxVal) * plotHeight;

    // Chart Title
    ctx.fillStyle = textColor;
    ctx.font = "bold 15px system-ui, -apple-system, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("Average Medical Charges: Smoker vs Non-Smoker", cssWidth / 2, 28);

    // Y-Axis Ticks & Gridlines
    const yTicks = [0, 10000, 20000, 30000, 40000];
    ctx.lineWidth = 1;
    yTicks.forEach((tick) => {
      const y = scaleY(tick);
      ctx.strokeStyle = gridColor;
      ctx.beginPath();
      ctx.moveTo(margin.left, y);
      ctx.lineTo(margin.left + plotWidth, y);
      ctx.stroke();

      ctx.fillStyle = textSec;
      ctx.font = "11px system-ui, sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(CURRENCY.format(tick).replace(".00", ""), margin.left - 10, y + 4);
    });

    // Bar placements
    const barWidth = Math.min(130, plotWidth * 0.28);
    const col1X = margin.left + plotWidth * 0.3 - barWidth / 2;
    const col2X = margin.left + plotWidth * 0.7 - barWidth / 2;

    const bars = [
      {
        x: col1X,
        mean: nsMean,
        ci: nsCI,
        color: colorNonSmoker,
        label: "Non-Smoker",
        count: nsCount,
      },
      {
        x: col2X,
        mean: smMean,
        ci: smCI,
        color: colorSmoker,
        label: "Smoker",
        count: smCount,
      },
    ];

    bars.forEach((bar) => {
      const barTop = scaleY(bar.mean);
      const barHeight = scaleY(0) - barTop;

      // Draw Bar
      ctx.fillStyle = bar.color;
      if (typeof ctx.roundRect === "function") {
        ctx.beginPath();
        ctx.roundRect(bar.x, barTop, barWidth, barHeight, [4, 4, 0, 0]);
        ctx.fill();
      } else {
        ctx.fillRect(bar.x, barTop, barWidth, barHeight);
      }

      // Draw 95% CI Error Whisker if genuinely calculated
      let labelY = barTop - 10;
      if (bar.ci != null && bar.ci > 0) {
        const ciTop = scaleY(bar.mean + bar.ci);
        const ciBottom = scaleY(bar.mean - bar.ci);
        const centerX = bar.x + barWidth / 2;
        const capWidth = 18;

        ctx.strokeStyle = textColor;
        ctx.lineWidth = 1.8;

        // Vertical line
        ctx.beginPath();
        ctx.moveTo(centerX, ciTop);
        ctx.lineTo(centerX, ciBottom);
        ctx.stroke();

        // Top cap
        ctx.beginPath();
        ctx.moveTo(centerX - capWidth / 2, ciTop);
        ctx.lineTo(centerX + capWidth / 2, ciTop);
        ctx.stroke();

        // Bottom cap
        ctx.beginPath();
        ctx.moveTo(centerX - capWidth / 2, ciBottom);
        ctx.lineTo(centerX + capWidth / 2, ciBottom);
        ctx.stroke();

        labelY = Math.min(barTop, ciTop) - 10;
      }

      // Dollar label above bar
      ctx.fillStyle = textColor;
      ctx.font = "bold 13px system-ui, sans-serif";
      ctx.textAlign = "center";
      const centerX = bar.x + barWidth / 2;
      ctx.fillText(CURRENCY.format(bar.mean), centerX, labelY);

      // X-Axis Category Label
      ctx.font = "600 13px system-ui, sans-serif";
      ctx.fillText(bar.label, centerX, margin.top + plotHeight + 24);

      // Group count subtext
      if (bar.count != null) {
        ctx.font = "11px system-ui, sans-serif";
        ctx.fillStyle = textSec;
        ctx.fillText(`(n = ${NUMBER.format(bar.count)})`, centerX, margin.top + plotHeight + 42);
      } else {
        ctx.font = "11px system-ui, sans-serif";
        ctx.fillStyle = textSec;
        ctx.fillText("(n = —)", centerX, margin.top + plotHeight + 42);
      }
    });

    // X-Axis baseline
    ctx.strokeStyle = textSec;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(margin.left, margin.top + plotHeight);
    ctx.lineTo(margin.left + plotWidth, margin.top + plotHeight);
    ctx.stroke();
  }

  // ── Router & Navigation ─────────────────────────────────────────────────
  const VIEW_TITLES = {
    overview: "Overview",
    comparison: "Cost Comparison",
    explorer: "Dataset Explorer",
    methodology: "Methodology",
    about: "About",
    scenario: "Scenario Comparison",
  };

  function switchView(viewName, updateHash = true) {
    if (!VIEW_TITLES[viewName]) viewName = "overview";
    state.currentView = viewName;

    if (updateHash && window.location.hash !== `#${viewName}`) {
      window.location.hash = `#${viewName}`;
    }

    // Update Header title
    if (elements.headerTitle) {
      elements.headerTitle.textContent = VIEW_TITLES[viewName];
    }
    document.title = `SympSort — ${VIEW_TITLES[viewName]}`;

    // Update Nav buttons
    elements.navItems.forEach((btn) => {
      const match = btn.getAttribute("data-view") === viewName;
      btn.classList.toggle("active", match);
      if (match) {
        btn.setAttribute("aria-current", "page");
      } else {
        btn.removeAttribute("aria-current");
      }
    });

    // Update View sections
    elements.views.forEach((view) => {
      const match = view.id === `view-${viewName}`;
      view.classList.toggle("active", match);
      if (match) {
        view.classList.remove("view-enter");
        void view.offsetWidth; // Force reflow
        view.classList.add("view-enter");
      }
    });

    // Update contextual header actions per P1 requirements
    if (elements.exportChartBtn) {
      elements.exportChartBtn.classList.toggle(
        "hidden",
        !(viewName === "overview" || viewName === "comparison")
      );
    }
    if (elements.downloadSummaryLink) {
      elements.downloadSummaryLink.classList.toggle(
        "hidden",
        viewName !== "comparison"
      );
    }
    if (elements.downloadFilteredLink) {
      elements.downloadFilteredLink.classList.toggle(
        "hidden",
        viewName !== "explorer"
      );
    }

    // Lazy load explorer data
    if (viewName === "explorer" && state.explorer.totalFiltered === 0) {
      loadExplorerData();
    }
    if (viewName === "comparison") {
      updateProfileMatch();
    }
    if (viewName === "methodology" && !state.dataQualityLoaded) {
      loadDataQualityAudit();
    }
    if (viewName === "scenario" && !state.scenarioLoaded) {
      runScenarioComparison();
    }
  }

  function handleHashChange() {
    const hash = window.location.hash.replace("#", "").trim();
    if (hash && VIEW_TITLES[hash]) {
      switchView(hash, false);
    } else {
      switchView("overview", true);
    }
  }

  // ── Count-up Animation for Headline Numbers ──────────────────────────────
  function animateValue(elem, start, end, duration = 800, isCurrency = true) {
    if (!elem) return;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion) {
      elem.textContent = isCurrency ? CURRENCY.format(end) : end;
      return;
    }

    const startTime = performance.now();
    function tick(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutQuart
      const ease = 1 - Math.pow(1 - progress, 4);
      const current = start + (end - start) * ease;
      elem.textContent = isCurrency ? CURRENCY.format(current) : current.toFixed(1);
      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        elem.textContent = isCurrency ? CURRENCY.format(end) : end;
      }
    }
    requestAnimationFrame(tick);
  }

  // ── Overview Data Rendering ─────────────────────────────────────────────
  async function loadSummaryData() {
    try {
      if (elements.overviewSkeleton) elements.overviewSkeleton.classList.remove("hidden");
      if (elements.overviewContent) elements.overviewContent.classList.add("hidden");
      if (elements.overviewError) elements.overviewError.classList.add("hidden");

      let data;
      try {
        const res = await fetch("/api/summary");
        if (res.ok) {
          const json = await res.json();
          if (json && typeof json.smoker_mean === "number") {
            data = json;
          }
        }
      } catch (e) {}

      if (!data) {
        const embeddedEl = document.getElementById("serverSummaryData");
        if (embeddedEl && embeddedEl.textContent.trim()) {
          try {
            data = JSON.parse(embeddedEl.textContent);
          } catch (e) {}
        }
      }

      if (!data || typeof data.smoker_mean !== "number") {
        throw new Error("Could not load summary data from API or server cache");
      }

      state.summary = data;
      loggerInfo("Summary loaded successfully:", {
        smoker_mean: data.smoker_mean,
        non_smoker_mean: data.non_smoker_mean,
        multiplier: data.multiplier,
      });

      // Populate Overview
      if (elements.findingLine) {
        if (data.multiplier != null && data.smoker_mean != null && data.non_smoker_mean != null) {
          const mult = `${data.multiplier.toFixed(1)}×`;
          elements.findingLine.innerHTML = `Smokers are charged about <strong>${mult} more</strong> on average: <strong>${CURRENCY.format(data.smoker_mean)}</strong> vs <strong>${CURRENCY.format(data.non_smoker_mean)}</strong>.`;
        } else if (data.smoker_mean != null && data.non_smoker_mean != null) {
          elements.findingLine.innerHTML = `Smoker average: <strong>${CURRENCY.format(data.smoker_mean)}</strong> vs Non-Smoker average: <strong>${CURRENCY.format(data.non_smoker_mean)}</strong>.`;
        } else {
          elements.findingLine.textContent = "Smoker vs non-smoker empirical insurance charge comparison.";
        }
      }

      if (!state.hasAnimatedNumbers) {
        if (typeof data.non_smoker_mean === "number") animateValue(elements.kpiNonSmoker, 0, data.non_smoker_mean);
        else if (elements.kpiNonSmoker) elements.kpiNonSmoker.textContent = "—";

        if (typeof data.smoker_mean === "number") animateValue(elements.kpiSmoker, 0, data.smoker_mean);
        else if (elements.kpiSmoker) elements.kpiSmoker.textContent = "—";

        state.hasAnimatedNumbers = true;
      } else {
        if (elements.kpiNonSmoker) {
          elements.kpiNonSmoker.textContent = typeof data.non_smoker_mean === "number" ? CURRENCY.format(data.non_smoker_mean) : "—";
        }
        if (elements.kpiSmoker) {
          elements.kpiSmoker.textContent = typeof data.smoker_mean === "number" ? CURRENCY.format(data.smoker_mean) : "—";
        }
      }

      if (elements.diffAbs) {
        elements.diffAbs.textContent = typeof data.absolute_difference === "number" ? `+${CURRENCY.format(data.absolute_difference)}` : "—";
      }
      if (elements.diffBadge) {
        elements.diffBadge.textContent = typeof data.percentage_difference === "number" ? `+${data.percentage_difference.toFixed(1)}%` : "—";
      }

      // Populate P1 Secondary KPI Strip
      if (elements.kpiMultiplier) {
        elements.kpiMultiplier.textContent = typeof data.multiplier === "number" ? `${data.multiplier.toFixed(2)}×` : "—";
      }
      if (elements.kpiNonSmokerCount) {
        elements.kpiNonSmokerCount.textContent = typeof data.non_smoker_count === "number" ? `n = ${NUMBER.format(data.non_smoker_count)}` : "n = —";
      }
      if (elements.kpiSmokerCount) {
        if (typeof data.smoker_count === "number") {
          const total = typeof data.total_valid_records === "number"
            ? data.total_valid_records
            : (typeof data.non_smoker_count === "number" ? data.smoker_count + data.non_smoker_count : null);
          const pct = total && total > 0 ? ` (${((data.smoker_count / total) * 100).toFixed(1)}% of records)` : "";
          elements.kpiSmokerCount.textContent = `n = ${NUMBER.format(data.smoker_count)}${pct}`;
        } else {
          elements.kpiSmokerCount.textContent = "n = —";
        }
      }
      if (elements.kpiValidCount) {
        elements.kpiValidCount.textContent = typeof data.total_valid_records === "number" ? NUMBER.format(data.total_valid_records) : "—";
      }

      // Populate Methodology live output
      if (elements.groupbyOutput) {
        elements.groupbyOutput.textContent = data.groupby_text || "No groupby output available.";
      }

      // Populate Detailed Stats Table
      populateStatsTable(data);

      // Populate P2 Statistical Significance Card
      if (elements.statSignificancePill) {
        elements.statSignificancePill.textContent = data.t_p_value ? `p ${data.t_p_value}` : "—";
      }
      if (elements.statTVal) {
        elements.statTVal.textContent = typeof data.t_statistic === "number" ? `t = ${data.t_statistic.toFixed(2)}` : "t = —";
      }
      if (elements.statTSub) {
        const dfStr = typeof data.welch_df === "number" ? `df ≈ ${data.welch_df.toFixed(2)}, ` : "";
        const pStr = data.t_p_value ? `p ${data.t_p_value}` : "p = —";
        elements.statTSub.textContent = `${dfStr}${pStr}`;
      }
      if (elements.statMWVal) {
        elements.statMWVal.textContent = data.mann_whitney_p_value ? String(data.mann_whitney_p_value) : "—";
      }
      if (elements.statCohenVal) {
        elements.statCohenVal.textContent = typeof data.cohen_d === "number" ? `d = ${data.cohen_d.toFixed(2)}` : "d = —";
      }
      if (elements.statCautionNote && data.stat_takeaway) {
        elements.statCautionNote.innerHTML = `<strong>Statistical Verification:</strong> ${data.stat_takeaway}`;
      }

      // Populate Comparison dynamic takeaway
      if (elements.comparisonTakeawayText && data.chart_takeaways) {
        elements.comparisonTakeawayText.textContent = data.chart_takeaways[state.comparisonChartKind || "bar"] || data.chart_takeaways["bar"];
      }

      // Render interactive canvas if active
      if (elements.overviewCanvas) {
        renderOverviewCanvas(data);
      }

      // Load 5 sample rows
      loadSampleRows();

      // Show content
      if (elements.overviewSkeleton) elements.overviewSkeleton.classList.add("hidden");
      if (elements.overviewContent) elements.overviewContent.classList.remove("hidden");
      if (elements.comparisonSkeleton) elements.comparisonSkeleton.classList.add("hidden");
      if (elements.comparisonContent) elements.comparisonContent.classList.remove("hidden");
    } catch (err) {
      loggerError("Failed to load summary", err);
      if (elements.overviewSkeleton) elements.overviewSkeleton.classList.add("hidden");
      if (elements.overviewError) {
        elements.overviewError.classList.remove("hidden");
        const msg = elements.overviewError.querySelector(".error-message");
        if (msg) msg.textContent = "Could not connect to the backend server. Please verify Flask is running.";
      }
    }
  }

  function populateStatsTable(data) {
    if (!elements.statsBody) return;

    const formatOrDash = (val, isCurrency = true) => {
      if (val == null || (typeof val === "number" && isNaN(val))) return "—";
      return isCurrency ? CURRENCY.format(val) : NUMBER.format(val);
    };

    const buildCiCell = (mean, margin, low, high) => {
      if (mean == null || margin == null) return "—";
      const meanStr = CURRENCY.format(mean);
      const marginStr = CURRENCY.format(margin);
      const lowStr = low != null ? CURRENCY.format(low) : "—";
      const highStr = high != null ? CURRENCY.format(high) : "—";
      const titleAttr = data.ci_method || "95% Confidence Interval";
      return `<span title="${titleAttr}">${meanStr} ± ${marginStr}<br><small class="text-tertiary">[${lowStr} – ${highStr}]</small></span>`;
    };

    const rows = [
      {
        label: "Sample Count (n)",
        ns: data.non_smoker_count != null ? NUMBER.format(data.non_smoker_count) : "—",
        sm: data.smoker_count != null ? NUMBER.format(data.smoker_count) : "—",
      },
      {
        label: "Mean Charge",
        ns: formatOrDash(data.non_smoker_mean),
        sm: formatOrDash(data.smoker_mean),
      },
      {
        label: "95% Confidence Interval",
        ns: buildCiCell(data.non_smoker_mean, data.non_smoker_ci_margin, data.non_smoker_ci_low, data.non_smoker_ci_high),
        sm: buildCiCell(data.smoker_mean, data.smoker_ci_margin, data.smoker_ci_low, data.smoker_ci_high),
      },
      {
        label: "Median Charge",
        ns: formatOrDash(data.non_smoker_median),
        sm: formatOrDash(data.smoker_median),
      },
      {
        label: "Std Deviation",
        ns: formatOrDash(data.non_smoker_std),
        sm: formatOrDash(data.smoker_std),
      },
      {
        label: "Minimum Charge",
        ns: formatOrDash(data.non_smoker_min),
        sm: formatOrDash(data.smoker_min),
      },
      {
        label: "Maximum Charge",
        ns: formatOrDash(data.non_smoker_max),
        sm: formatOrDash(data.smoker_max),
      },
    ];

    elements.statsBody.innerHTML = rows
      .map(
        (r) => `
        <tr>
          <td><strong>${r.label}</strong></td>
          <td class="num font-tabular">${r.ns}</td>
          <td class="num font-tabular">${r.sm}</td>
        </tr>
      `
      )
      .join("");
  }

  async function loadSampleRows() {
    if (!elements.sampleBody) return;

    // Show subtle skeleton loader while fetching
    elements.sampleBody.innerHTML = `
      <tr class="skeleton-tr"><td colspan="7"><div class="skeleton-row-line"></div></td></tr>
      <tr class="skeleton-tr"><td colspan="7"><div class="skeleton-row-line"></div></td></tr>
      <tr class="skeleton-tr"><td colspan="7"><div class="skeleton-row-line"></div></td></tr>
    `;

    let records = [];
    try {
      // Connect to sample data endpoint (falls back to data endpoint)
      let res = await fetch("/api/sample-data?limit=5");
      if (!res.ok) {
        res = await fetch("/api/data?page=1&page_size=5");
      }
      if (res.ok) {
        const data = await res.json();
        records = data.records || [];
      }
    } catch (e) {}

    if (!records.length) {
      const sampleEl = document.getElementById("serverSampleData");
      if (sampleEl && sampleEl.textContent.trim()) {
        try {
          const allSample = JSON.parse(sampleEl.textContent);
          records = allSample.slice(0, 5);
        } catch (e) {}
      }
    }

    try {
      if (!records.length) {
        elements.sampleBody.innerHTML = '<tr><td colspan="7" class="empty-state">No records available</td></tr>';
        return;
      }

      elements.sampleBody.innerHTML = records
        .map((rec) => {
          const sex = rec.sex ? rec.sex.charAt(0).toUpperCase() + rec.sex.slice(1).toLowerCase() : "—";
          const region = rec.region ? rec.region.charAt(0).toUpperCase() + rec.region.slice(1).toLowerCase() : "—";
          const smokerTag = rec.smoker === "yes"
            ? '<span class="tag tag--smoker">Yes</span>'
            : '<span class="tag tag--nonsmoker">No</span>';

          return `<tr>
            <td class="num font-tabular">${rec.age ?? "—"}</td>
            <td>${sex}</td>
            <td class="num font-tabular">${rec.bmi != null && !isNaN(rec.bmi) ? Number(rec.bmi).toFixed(2) : "—"}</td>
            <td class="num font-tabular">${rec.children ?? "—"}</td>
            <td>${smokerTag}</td>
            <td>${region}</td>
            <td class="num font-tabular">${rec.charges != null && !isNaN(rec.charges) ? CURRENCY.format(rec.charges) : "—"}</td>
          </tr>`;
        })
        .join("");
    } catch (err) {
      loggerError("Failed to populate sample data table:", err);
      elements.sampleBody.innerHTML = '<tr><td colspan="7" class="table-error">Failed to load sample data.</td></tr>';
    }
  }

  // ── Dataset Explorer Table (Built from COLUMNS) ──────────────────────────
  function initTableHeaders() {
    if (!elements.explorerHead) return;
    elements.explorerHead.innerHTML = COLUMNS.map((col) => {
      const sortableClass = col.sortable ? "sortable" : "";
      const alignClass = col.align === "right" ? "num" : "";
      return `
        <th class="${alignClass} ${sortableClass}" data-key="${col.key}" scope="col" aria-sort="none">
          <button type="button" class="th-button" data-key="${col.key}">
            <span>${col.label}</span>
            ${col.sortable ? '<span class="sort-indicator" aria-hidden="true">↕</span>' : ""}
          </button>
        </th>
      `;
    }).join("");

    // Attach sort event
    elements.explorerHead.querySelectorAll(".th-button").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.getAttribute("data-key");
        handleSort(key);
      });
    });
  }

  function handleSort(key) {
    if (state.explorer.sort === key) {
      state.explorer.order = state.explorer.order === "asc" ? "desc" : "asc";
    } else {
      state.explorer.sort = key;
      state.explorer.order = "asc";
    }

    // Update aria-sort
    elements.explorerHead.querySelectorAll("th").forEach((th) => {
      const thKey = th.getAttribute("data-key");
      const indicator = th.querySelector(".sort-indicator");
      if (thKey === state.explorer.sort) {
        const ariaVal = state.explorer.order === "asc" ? "ascending" : "descending";
        th.setAttribute("aria-sort", ariaVal);
        if (indicator) indicator.textContent = state.explorer.order === "asc" ? "↑" : "↓";
      } else {
        th.setAttribute("aria-sort", "none");
        if (indicator) indicator.textContent = "↕";
      }
    });

    state.explorer.page = 1;
    loadExplorerData();
  }

  let explorerRequestSeq = 0;

  async function loadExplorerData() {
    if (!elements.explorerBody) return;
    state.explorer.isLoading = true;
    const thisRequestSeq = ++explorerRequestSeq;

    const params = new URLSearchParams({
      page: state.explorer.page,
      page_size: state.explorer.pageSize,
    });

    if (state.explorer.search) params.set("search", state.explorer.search);
    if (state.explorer.smoker) params.set("smoker", state.explorer.smoker);
    if (state.explorer.region) params.set("region", state.explorer.region);
    if (state.explorer.sex) params.set("sex", state.explorer.sex);
    if (state.explorer.children) params.set("children", state.explorer.children);
    if (state.explorer.bmi) params.set("bmi_band", state.explorer.bmi);
    if (state.explorer.age) params.set("age_band", state.explorer.age);
    if (state.explorer.sort) params.set("sort", state.explorer.sort);
    if (state.explorer.order) params.set("order", state.explorer.order);

    try {
      const res = await fetch(`/api/data?${params.toString()}`);
      if (!res.ok) {
        let errMsg = `Server returned status ${res.status}`;
        try {
          const errData = await res.json();
          if (errData && errData.message) errMsg = errData.message;
        } catch (_) {}
        throw new Error(errMsg);
      }
      const data = await res.json();

      // Discard stale response if a newer query has already been dispatched
      if (thisRequestSeq !== explorerRequestSeq) {
        return;
      }

      state.explorer.totalFiltered = data.total_filtered || 0;
      state.explorer.totalPages = data.pages || 1;
      state.explorer.page = data.page || 1;

      // Update contextual Download filtered CSV link with active filter query
      if (elements.downloadFilteredLink) {
        const downloadParams = new URLSearchParams();
        if (state.explorer.search) downloadParams.set("search", state.explorer.search);
        if (state.explorer.smoker) downloadParams.set("smoker", state.explorer.smoker);
        if (state.explorer.region) downloadParams.set("region", state.explorer.region);
        if (state.explorer.sex) downloadParams.set("sex", state.explorer.sex);
        if (state.explorer.children) downloadParams.set("children", state.explorer.children);
        if (state.explorer.bmi) downloadParams.set("bmi_band", state.explorer.bmi);
        if (state.explorer.age) downloadParams.set("age_band", state.explorer.age);
        if (state.explorer.sort) downloadParams.set("sort", state.explorer.sort);
        if (state.explorer.order) downloadParams.set("order", state.explorer.order);
        elements.downloadFilteredLink.href = `/api/download/filtered?${downloadParams.toString()}`;
      }

      // Update live selection summary strip
      if (data.selection_summary) {
        const sel = data.selection_summary;
        if (elements.selCount) {
          elements.selCount.textContent = sel.matched_count != null ? `${NUMBER.format(sel.matched_count)} rows` : "0 rows";
        }
        if (elements.selMean) {
          elements.selMean.textContent = sel.mean_charges != null ? CURRENCY.format(sel.mean_charges) : "—";
        }
        if (elements.selMedian) {
          elements.selMedian.textContent = sel.median_charges != null ? CURRENCY.format(sel.median_charges) : "—";
        }
        if (elements.selBmi) {
          elements.selBmi.textContent = sel.mean_bmi != null && !isNaN(sel.mean_bmi) ? Number(sel.mean_bmi).toFixed(2) : "—";
        }
      }

      renderExplorerRows(data.records || []);
      renderPagination();
      renderShowingText(data);
    } catch (err) {
      if (thisRequestSeq !== explorerRequestSeq) {
        return;
      }
      loggerError("Failed to load explorer data", err);
      if (elements.explorerEmpty) elements.explorerEmpty.classList.add("hidden");
      const safeErrMsg = escapeHtml(err.message || "Connection error.");
      elements.explorerBody.innerHTML = `<tr><td colspan="${COLUMNS.length}" class="table-error"><div style="display:flex;align-items:center;justify-content:center;gap:0.75rem;padding:1rem 0;"><span>Failed to load data: ${safeErrMsg}</span><button type="button" class="btn-text" id="explorerRetryBtn" style="text-decoration:underline;cursor:pointer;">Retry</button></div></td></tr>`;
      const retryBtn = document.getElementById("explorerRetryBtn");
      if (retryBtn) {
        retryBtn.addEventListener("click", () => loadExplorerData());
      }
      if (elements.showingText) elements.showingText.textContent = "Error loading records";
      if (elements.pagination) elements.pagination.innerHTML = "";
      if (elements.selCount) elements.selCount.textContent = "—";
      if (elements.selMean) elements.selMean.textContent = "—";
      if (elements.selMedian) elements.selMedian.textContent = "—";
      if (elements.selBmi) elements.selBmi.textContent = "—";
    } finally {
      if (thisRequestSeq === explorerRequestSeq) {
        state.explorer.isLoading = false;
      }
    }
  }

  function renderExplorerRows(records) {
    if (!elements.explorerBody) return;

    if (!records.length) {
      elements.explorerBody.innerHTML = "";
      if (elements.explorerEmpty) elements.explorerEmpty.classList.remove("hidden");
      return;
    }

    if (elements.explorerEmpty) elements.explorerEmpty.classList.add("hidden");

    // Render cells strictly according to COLUMNS definition
    elements.explorerBody.innerHTML = records
      .map((row) => {
        const cells = COLUMNS.map((col) => {
          const rawVal = row[col.key];
          const formatted = col.format ? col.format(rawVal) : escapeHtml(rawVal ?? "—");
          const alignClass = col.align === "right" ? "num font-tabular" : "";
          return `<td class="${alignClass}">${formatted}</td>`;
        }).join("");
        return `<tr>${cells}</tr>`;
      })
      .join("");
  }

  function renderShowingText(data) {
    if (!elements.showingText) return;
    const total = data.total_filtered || 0;
    if (total === 0) {
      elements.showingText.textContent = "Showing 0 of 0";
      return;
    }
    const start = (data.page - 1) * state.explorer.pageSize + 1;
    const end = Math.min(start + state.explorer.pageSize - 1, total);
    elements.showingText.textContent = `Showing ${NUMBER.format(start)}–${NUMBER.format(end)} of ${NUMBER.format(total)}`;
  }

  function renderPagination() {
    if (!elements.pagination) return;
    const { page, totalPages } = state.explorer;
    if (totalPages <= 1) {
      elements.pagination.innerHTML = "";
      return;
    }

    let html = `
      <button type="button" class="btn-page" ${page <= 1 ? "disabled" : ""} data-page="${page - 1}" aria-label="Previous page">‹</button>
    `;

    const range = getPaginationRange(page, totalPages);
    range.forEach((p) => {
      if (p === "...") {
        html += `<span class="page-ellipsis">…</span>`;
      } else {
        const isCurrent = p === page;
        html += `
          <button type="button" class="btn-page ${isCurrent ? "btn-page--active" : ""}" data-page="${p}" ${isCurrent ? 'aria-current="page"' : ""}>${p}</button>
        `;
      }
    });

    html += `
      <button type="button" class="btn-page" ${page >= totalPages ? "disabled" : ""} data-page="${page + 1}" aria-label="Next page">›</button>
    `;

    elements.pagination.innerHTML = html;

    // Attach click events
    elements.pagination.querySelectorAll(".btn-page").forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetPage = parseInt(btn.getAttribute("data-page"), 10);
        if (!isNaN(targetPage) && targetPage >= 1 && targetPage <= totalPages && targetPage !== page) {
          state.explorer.page = targetPage;
          loadExplorerData();
        }
      });
    });
  }

  function getPaginationRange(current, total) {
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
    if (current <= 4) return [1, 2, 3, 4, 5, "...", total];
    if (current >= total - 3) return [1, "...", total - 4, total - 3, total - 2, total - 1, total];
    return [1, "...", current - 1, current, current + 1, "...", total];
  }

  // ── Debounce Utility ────────────────────────────────────────────────────
  function debounce(func, wait) {
    let timeout;
    return function (...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), wait);
    };
  }

  function loggerError(...args) {
    if (typeof console !== "undefined" && console.error) {
      console.error("[SympSort]", ...args);
    }
  }

  function loggerInfo(...args) {
    if (typeof console !== "undefined" && console.info) {
      console.info("[SympSort]", ...args);
    }
  }

  // ── Multi-Chart Explorer (Beyond the Average) ───────────────────────────
  const CHART_INFO = {
    bar: {
      badge: "Barplot (Default)",
      caption: "Average medical insurance charges by smoking status (95% CI error whiskers)",
    },
    dist: {
      badge: "Distribution (KDE)",
      caption: "Kernel Density Estimation (KDE) comparing cost distributions between cohorts",
    },
    box: {
      badge: "Boxplot",
      caption: "Boxplot of charges by smoking status showing median, IQR, spread, and outliers",
    },
    scatter: {
      badge: "BMI vs Charges",
      caption: "Scatter plot of BMI vs medical charges highlighting the BMI ≥ 30 obesity interaction",
    },
    region: {
      badge: "Region × Smoker",
      caption: "Mean medical charges across 4 geographic regions split by smoking status",
    },
    sex: {
      badge: "Sex × Smoker",
      caption: "Mean medical charges by sex cohort split by smoking status",
    },
    age: {
      badge: "Age Bands × Smoker",
      caption: "Mean medical charges across age cohorts (18–29, 30–44, 45–64) split by smoking status",
    },
  };

  function updateComparisonChart(kind) {
    if (!CHART_INFO[kind]) kind = "bar";
    state.comparisonChartKind = kind;

    if (elements.comparisonChartSelector) {
      elements.comparisonChartSelector.querySelectorAll(".segmented-btn").forEach((btn) => {
        const isMatch = btn.getAttribute("data-kind") === kind;
        btn.classList.toggle("active", isMatch);
        btn.setAttribute("aria-selected", isMatch ? "true" : "false");
      });
    }

    if (elements.comparisonActiveKindBadge) {
      elements.comparisonActiveKindBadge.textContent = CHART_INFO[kind].badge;
    }
    if (elements.comparisonChartCaption) {
      elements.comparisonChartCaption.textContent = CHART_INFO[kind].caption;
    }

    if (elements.comparisonChart) {
      elements.comparisonChart.classList.remove("loaded");
      elements.comparisonChart.src = `/api/chart?kind=${kind}&theme=${state.theme}&_t=${Date.now()}`;
    }

    if (elements.comparisonTakeawayText && state.summary && state.summary.chart_takeaways) {
      elements.comparisonTakeawayText.textContent =
        state.summary.chart_takeaways[kind] || state.summary.chart_takeaways["bar"];
    }
  }

  // ── Scenario Comparison Engine Controller ───────────────────────────────
  async function updateScenarioComparison() {
    const aParams = {
      age_band: elements.profileAge ? elements.profileAge.value : "all",
      bmi_band: elements.profileBmi ? elements.profileBmi.value : "all",
      sex: elements.profileSex ? elements.profileSex.value : "all",
      region: elements.profileRegion ? elements.profileRegion.value : "all",
      smoker: elements.profileSmoker ? elements.profileSmoker.value : "no",
    };

    const bAgeEl = document.getElementById("scenarioB_age");
    const bBmiEl = document.getElementById("scenarioB_bmi");
    const bSexEl = document.getElementById("scenarioB_sex");
    const bRegionEl = document.getElementById("scenarioB_region");
    const bSmokerEl = document.getElementById("scenarioB_smoker");

    const bParams = {
      age_band: bAgeEl ? bAgeEl.value : "all",
      bmi_band: bBmiEl ? bBmiEl.value : "all",
      sex: bSexEl ? bSexEl.value : "all",
      region: bRegionEl ? bRegionEl.value : "all",
      smoker: bSmokerEl ? bSmokerEl.value : "yes",
    };

    try {
      const q = new URLSearchParams({
        a_age_band: aParams.age_band,
        a_bmi_band: aParams.bmi_band,
        a_sex: aParams.sex,
        a_region: aParams.region,
        a_smoker: aParams.smoker,
        b_age_band: bParams.age_band,
        b_bmi_band: bParams.bmi_band,
        b_sex: bParams.sex,
        b_region: bParams.region,
        b_smoker: bParams.smoker,
      });

      const res = await fetch(`/api/scenario-compare?${q.toString()}`);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();

      // Update Cohort A
      const cA = data.cohort_a || {};
      if (elements.scenMeanA) elements.scenMeanA.textContent = cA.count > 0 ? CURRENCY.format(cA.mean) : "—";
      if (elements.scenCountA) elements.scenCountA.textContent = `n = ${NUMBER.format(cA.count)} records`;
      if (elements.scenMedianA) elements.scenMedianA.textContent = cA.count > 0 ? CURRENCY.format(cA.median) : "—";
      if (elements.scenCiA) elements.scenCiA.textContent = cA.ci_margin > 0 ? `±${CURRENCY.format(cA.ci_margin)}` : "—";

      // Update Cohort B
      const cB = data.cohort_b || {};
      if (elements.scenMeanB) elements.scenMeanB.textContent = cB.count > 0 ? CURRENCY.format(cB.mean) : "—";
      if (elements.scenCountB) elements.scenCountB.textContent = `n = ${NUMBER.format(cB.count)} records`;
      if (elements.scenMedianB) elements.scenMedianB.textContent = cB.count > 0 ? CURRENCY.format(cB.median) : "—";
      if (elements.scenCiB) elements.scenCiB.textContent = cB.ci_margin > 0 ? `±${CURRENCY.format(cB.ci_margin)}` : "—";

      // Update Delta Box
      if (elements.scenDiffMean) {
        const sign = data.diff_mean >= 0 ? "+" : "";
        elements.scenDiffMean.textContent = `${sign}${CURRENCY.format(data.diff_mean)}`;
      }
      if (elements.scenPctBadge) {
        const sign = data.pct_diff >= 0 ? "+" : "";
        elements.scenPctBadge.textContent = `${sign}${data.pct_diff.toFixed(1)}%`;
      }
      if (elements.scenMultiplier) {
        elements.scenMultiplier.textContent = `${data.multiplier ? data.multiplier.toFixed(2) : "1.00"}×`;
      }
      if (elements.scenTStat) {
        if (data.t_statistic !== null) {
          elements.scenTStat.textContent = `t = ${data.t_statistic.toFixed(2)}, ${data.p_value}`;
        } else {
          elements.scenTStat.textContent = "t = N/A";
        }
      }
      if (elements.scenStatement && data.statement) {
        elements.scenStatement.textContent = data.statement;
      }

      if (elements.scenWarning) {
        if (data.warnings && data.warnings.length > 0) {
          elements.scenWarning.textContent = data.warnings.join(" ");
          elements.scenWarning.classList.remove("hidden");
        } else {
          elements.scenWarning.classList.add("hidden");
        }
      }
    } catch (err) {
      loggerError("Scenario comparison calculation failed:", err);
    }
  }

  const updateProfileMatch = updateScenarioComparison;

  // ── Scenario Comparison (View 6) Controller ─────────────────────────────
  function serializeScenarioCohort(prefix) {
    const smokerEl = elements[`${prefix}_smoker`];
    const sexEl = elements[`${prefix}_sex`];
    const regionEl = elements[`${prefix}_region`];
    const ageMinEl = elements[`${prefix}_age_min`];
    const ageMaxEl = elements[`${prefix}_age_max`];
    const bmiMinEl = elements[`${prefix}_bmi_min`];
    const bmiMaxEl = elements[`${prefix}_bmi_max`];
    const childrenEl = elements[`${prefix}_children`];

    const parseNum = (el, isFloat = false) => {
      if (!el || !el.value || el.value.trim() === "") return null;
      const parsed = isFloat ? parseFloat(el.value.trim()) : parseInt(el.value.trim(), 10);
      return isNaN(parsed) ? null : parsed;
    };

    const parseChildren = (el) => {
      if (!el || !el.value || el.value === "all") return "all";
      const parsed = parseInt(el.value, 10);
      return isNaN(parsed) ? "all" : parsed;
    };

    return {
      smoker: smokerEl ? smokerEl.value : "all",
      sex: sexEl ? sexEl.value : "all",
      region: regionEl ? regionEl.value : "all",
      age_min: parseNum(ageMinEl, false),
      age_max: parseNum(ageMaxEl, false),
      bmi_min: parseNum(bmiMinEl, true),
      bmi_max: parseNum(bmiMaxEl, true),
      children: parseChildren(childrenEl),
    };
  }

  async function runScenarioComparison() {
    if (!elements.scenCompareRunBtn) return;

    const payloadA = serializeScenarioCohort("scenA");
    const payloadB = serializeScenarioCohort("scenB");

    elements.scenCompareRunBtn.disabled = true;
    if (elements.scenStatusIndicator) {
      elements.scenStatusIndicator.textContent = "Calculating comparison…";
    }

    try {
      const res = await fetch("/api/scenario-compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_a: payloadA,
          scenario_b: payloadB,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        const msg = data.message || `Calculation error (${res.status})`;
        if (elements.scenWarningBox && elements.scenWarningText) {
          elements.scenWarningText.textContent = msg;
          elements.scenWarningBox.classList.remove("hidden");
        }
        showToast(msg);
        return;
      }

      state.scenarioLoaded = true;

      // Render Scenario A metrics
      const a = data.scenario_a || {};
      if (elements.scenStatsACount) elements.scenStatsACount.textContent = a.count !== undefined ? NUMBER.format(a.count) : "0";
      if (elements.scenStatsAMean) elements.scenStatsAMean.textContent = a.mean !== null && a.mean !== undefined ? CURRENCY.format(a.mean) : "—";
      if (elements.scenStatsAMedian) elements.scenStatsAMedian.textContent = a.median !== null && a.median !== undefined ? CURRENCY.format(a.median) : "—";
      if (elements.scenStatsARange) {
        elements.scenStatsARange.textContent = (a.min !== null && a.max !== null && a.min !== undefined && a.max !== undefined)
          ? `${CURRENCY.format(a.min)} – ${CURRENCY.format(a.max)}`
          : "—";
      }
      if (elements.scenStatsAStd) elements.scenStatsAStd.textContent = a.std !== null && a.std !== undefined ? CURRENCY.format(a.std) : "—";
      if (elements.scenStatsACI) elements.scenStatsACI.textContent = a.ci_margin !== null && a.ci_margin !== undefined ? `±${CURRENCY.format(a.ci_margin)}` : "—";

      // Render Scenario B metrics
      const b = data.scenario_b || {};
      if (elements.scenStatsBCount) elements.scenStatsBCount.textContent = b.count !== undefined ? NUMBER.format(b.count) : "0";
      if (elements.scenStatsBMean) elements.scenStatsBMean.textContent = b.mean !== null && b.mean !== undefined ? CURRENCY.format(b.mean) : "—";
      if (elements.scenStatsBMedian) elements.scenStatsBMedian.textContent = b.median !== null && b.median !== undefined ? CURRENCY.format(b.median) : "—";
      if (elements.scenStatsBRange) {
        elements.scenStatsBRange.textContent = (b.min !== null && b.max !== null && b.min !== undefined && b.max !== undefined)
          ? `${CURRENCY.format(b.min)} – ${CURRENCY.format(b.max)}`
          : "—";
      }
      if (elements.scenStatsBStd) elements.scenStatsBStd.textContent = b.std !== null && b.std !== undefined ? CURRENCY.format(b.std) : "—";
      if (elements.scenStatsBCI) elements.scenStatsBCI.textContent = b.ci_margin !== null && b.ci_margin !== undefined ? `±${CURRENCY.format(b.ci_margin)}` : "—";

      // Render Comparative Difference
      const comp = data.comparison || {};
      if (elements.scenDiffAmount) {
        if (comp.difference_mean !== null && comp.difference_mean !== undefined) {
          const sign = comp.difference_mean > 0 ? "+" : "";
          elements.scenDiffAmount.textContent = `${sign}${CURRENCY.format(comp.difference_mean)}`;
        } else {
          elements.scenDiffAmount.textContent = "—";
        }
      }

      if (elements.scenDiffPctBadge) {
        if (comp.percentage_difference !== null && comp.percentage_difference !== undefined) {
          const sign = comp.percentage_difference > 0 ? "+" : "";
          elements.scenDiffPctBadge.textContent = `${sign}${comp.percentage_difference.toFixed(1)}%`;
        } else {
          elements.scenDiffPctBadge.textContent = "—";
        }
      }

      if (elements.scenHigherBadge) {
        if (comp.higher_scenario === "scenario_b") {
          elements.scenHigherBadge.textContent = "Scenario B is higher";
          elements.scenHigherBadge.className = "higher-badge";
        } else if (comp.higher_scenario === "scenario_a") {
          elements.scenHigherBadge.textContent = "Scenario A is higher";
          elements.scenHigherBadge.className = "higher-badge higher-badge--a";
        } else {
          elements.scenHigherBadge.textContent = "Means are identical or undefined";
          elements.scenHigherBadge.className = "higher-badge higher-badge--equal";
        }
      }

      if (elements.scenRefNote) {
        elements.scenRefNote.textContent = "Reference baseline: Scenario A";
      }

      if (elements.scenDiffTStat) {
        if (typeof comp.t_statistic === "number") {
          const dfText = typeof comp.degrees_of_freedom === "number" ? `df ≈ ${comp.degrees_of_freedom.toFixed(2)}, ` : "";
          const pText = typeof comp.p_value === "number" ? (comp.p_value < 0.001 ? "p < 0.001" : `p = ${comp.p_value.toFixed(3)}`) : "p = —";
          elements.scenDiffTStat.textContent = `t = ${comp.t_statistic.toFixed(2)} (${dfText}${pText})`;
        } else {
          elements.scenDiffTStat.textContent = "t = — (insufficient sample size)";
        }
      }

      // Warnings
      if (elements.scenWarningBox && elements.scenWarningText) {
        if (data.warnings && data.warnings.length > 0) {
          elements.scenWarningText.textContent = data.warnings.join(" ");
          elements.scenWarningBox.classList.remove("hidden");
        } else {
          elements.scenWarningBox.classList.add("hidden");
        }
      }

      // Disclaimer
      if (elements.scenDisclaimerText && data.disclaimer) {
        elements.scenDisclaimerText.textContent = data.disclaimer;
      }
    } catch (err) {
      loggerError("Scenario comparison failed:", err);
      if (elements.scenWarningBox && elements.scenWarningText) {
        elements.scenWarningText.textContent = "Network or server failure during scenario comparison calculation.";
        elements.scenWarningBox.classList.remove("hidden");
      }
      showToast("Unable to calculate scenario comparison.");
    } finally {
      elements.scenCompareRunBtn.disabled = false;
      if (elements.scenStatusIndicator) {
        elements.scenStatusIndicator.textContent = "";
      }
    }
  }

  function resetScenarioInputs() {
    // Reset Scenario A
    if (elements.scenA_smoker) elements.scenA_smoker.value = "no";
    if (elements.scenA_sex) elements.scenA_sex.value = "all";
    if (elements.scenA_region) elements.scenA_region.value = "all";
    if (elements.scenA_age_min) elements.scenA_age_min.value = "";
    if (elements.scenA_age_max) elements.scenA_age_max.value = "";
    if (elements.scenA_bmi_min) elements.scenA_bmi_min.value = "";
    if (elements.scenA_bmi_max) elements.scenA_bmi_max.value = "";
    if (elements.scenA_children) elements.scenA_children.value = "all";

    // Reset Scenario B
    if (elements.scenB_smoker) elements.scenB_smoker.value = "yes";
    if (elements.scenB_sex) elements.scenB_sex.value = "all";
    if (elements.scenB_region) elements.scenB_region.value = "all";
    if (elements.scenB_age_min) elements.scenB_age_min.value = "";
    if (elements.scenB_age_max) elements.scenB_age_max.value = "";
    if (elements.scenB_bmi_min) elements.scenB_bmi_min.value = "";
    if (elements.scenB_bmi_max) elements.scenB_bmi_max.value = "";
    if (elements.scenB_children) elements.scenB_children.value = "all";

    runScenarioComparison();
  }

  async function downloadScenarioPdfReport(cohortMode = false) {
    let payloadA, payloadB;
    if (cohortMode) {
      payloadA = {
        age_band: elements.profileAge ? elements.profileAge.value : "all",
        bmi_band: elements.profileBmi ? elements.profileBmi.value : "all",
        sex: elements.profileSex ? elements.profileSex.value : "all",
        region: elements.profileRegion ? elements.profileRegion.value : "all",
        smoker: elements.profileSmoker ? elements.profileSmoker.value : "no",
      };
      const bAgeEl = document.getElementById("scenarioB_age");
      const bBmiEl = document.getElementById("scenarioB_bmi");
      const bSexEl = document.getElementById("scenarioB_sex");
      const bRegionEl = document.getElementById("scenarioB_region");
      const bSmokerEl = document.getElementById("scenarioB_smoker");
      payloadB = {
        age_band: bAgeEl ? bAgeEl.value : "all",
        bmi_band: bBmiEl ? bBmiEl.value : "all",
        sex: bSexEl ? bSexEl.value : "all",
        region: bRegionEl ? bRegionEl.value : "all",
        smoker: bSmokerEl ? bSmokerEl.value : "yes",
      };
    } else {
      payloadA = serializeScenarioCohort("scenA");
      payloadB = serializeScenarioCohort("scenB");
    }

    showToast("Generating scenario comparison PDF report…");

    try {
      const res = await fetch("/api/report/pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_a: payloadA,
          scenario_b: payloadB,
        }),
      });

      if (!res.ok) {
        let errMsg = `Failed to generate PDF (${res.status})`;
        try {
          const errData = await res.json();
          if (errData && errData.message) errMsg = errData.message;
        } catch (_) {}
        throw new Error(errMsg);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "sympsort_scenario_comparison_report.pdf";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      showToast("Comparison report downloaded successfully.");
    } catch (err) {
      loggerError("Scenario PDF download error:", err);
      showToast(`PDF download failed: ${err.message || "Unknown error"}`);
    }
  }

  // ── Methodology Data Quality & Ingestion Audit ─────────────────────────
  async function loadDataQualityAudit() {
    try {
      const res = await fetch("/api/data-quality");
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      state.dataQualityLoaded = true;

      const val = data.validation || {};
      if (elements.auditRawRows) elements.auditRawRows.textContent = val.total_raw_rows != null ? NUMBER.format(val.total_raw_rows) : "—";
      if (elements.auditValidRows) elements.auditValidRows.textContent = val.valid_rows != null ? NUMBER.format(val.valid_rows) : "—";
      if (elements.auditExcludedRows) elements.auditExcludedRows.textContent = val.excluded_rows != null ? NUMBER.format(val.excluded_rows) : "—";
      if (elements.auditNulls) {
        const nullCount = (val.null_charges_count || 0) + (val.invalid_smoker_count || 0);
        elements.auditNulls.textContent = NUMBER.format(nullCount);
      }

      // Describe output format
      if (elements.auditDescribeOutput && data.describe) {
        const desc = data.describe;
        const metrics = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"];
        let out = "Metric        Age         BMI         Children    Charges\n";
        out += "--------------------------------------------------------------------\n";
        metrics.forEach((m) => {
          const mPad = m.padEnd(12);
          const ageVal = desc.age && desc.age[m] != null ? Number(desc.age[m]).toFixed(2).padStart(10) : "".padStart(10);
          const bmiVal = desc.bmi && desc.bmi[m] != null ? Number(desc.bmi[m]).toFixed(2).padStart(10) : "".padStart(10);
          const chVal = desc.children && desc.children[m] != null ? Number(desc.children[m]).toFixed(2).padStart(10) : "".padStart(10);
          const cgVal = desc.charges && desc.charges[m] != null ? Number(desc.charges[m]).toFixed(2).padStart(12) : "".padStart(12);
          out += `${mPad}${ageVal}  ${bmiVal}  ${chVal}  ${cgVal}\n`;
        });
        elements.auditDescribeOutput.textContent = out;
      }

      // Head output format
      if (elements.auditHeadOutput && data.head) {
        let out = "   age  sex     bmi      children  smoker  region     charges\n";
        out += "--------------------------------------------------------------------\n";
        data.head.forEach((row, idx) => {
          const idxStr = idx.toString().padStart(2);
          const ageStr = (row.age ?? "").toString().padStart(3);
          const sexStr = (row.sex ?? "").padEnd(7);
          const bmiStr = (row.bmi != null ? Number(row.bmi).toFixed(2) : "").padStart(7);
          const chStr = (row.children ?? "").toString().padStart(8);
          const smStr = (row.smoker ?? "").padEnd(6);
          const regStr = (row.region ?? "").padEnd(10);
          const cgStr = (row.charges != null ? Number(row.charges).toFixed(2) : "").padStart(10);
          out += `${idxStr}  ${ageStr}  ${sexStr}  ${bmiStr}  ${chStr}  ${smStr}  ${regStr} ${cgStr}\n`;
        });
        elements.auditHeadOutput.textContent = out;
      }

      // Info output format
      if (elements.auditInfoOutput && data.columns) {
        const totalRows = val.total_raw_rows != null ? val.total_raw_rows : (data.columns[0]?.non_null_count || 0);
        const maxIdx = totalRows > 0 ? totalRows - 1 : 0;
        let out = `<class 'pandas.core.frame.DataFrame'>\nRangeIndex: ${totalRows} entries, 0 to ${maxIdx}\n`;
        out += `Data columns (total ${data.columns.length} columns):\n`;
        out += " #   Column        Non-Null Count  Dtype\n";
        out += "---  ------        --------------  -----\n";
        data.columns.forEach((col, idx) => {
          const iStr = idx.toString().padStart(2);
          const cStr = col.column.padEnd(13);
          const nnStr = `${col.non_null_count} non-null`.padEnd(15);
          const dtStr = col.dtype;
          out += ` ${iStr}  ${cStr} ${nnStr} ${dtStr}\n`;
        });
        elements.auditInfoOutput.textContent = out;
      }
    } catch (err) {
      loggerError("Data quality audit load failed:", err);
    }
  }

  // ── Event Handlers & Initialization ─────────────────────────────────────
  function setupEventListeners() {
    // Nav Items click
    elements.navItems.forEach((item) => {
      item.addEventListener("click", () => {
        const view = item.getAttribute("data-view");
        if (view) switchView(view);
      });
    });

    // Hash navigation
    window.addEventListener("hashchange", handleHashChange);

    // Keyboard shortcuts (1–6)
    window.addEventListener("keydown", (e) => {
      if (e.target && ["INPUT", "SELECT", "TEXTAREA"].includes(e.target.tagName)) return;
      const keyMap = {
        "1": "overview",
        "2": "comparison",
        "3": "explorer",
        "4": "methodology",
        "5": "about",
        "6": "scenario",
      };
      if (keyMap[e.key]) {
        e.preventDefault();
        switchView(keyMap[e.key]);
      }
    });

    // Theme Toggle
    if (elements.themeToggle) {
      elements.themeToggle.addEventListener("click", toggleTheme);
    }

    // Chart Mode Tabs (Seaborn vs Interactive Canvas)
    if (elements.tabSeaborn) {
      elements.tabSeaborn.addEventListener("click", () => setChartMode("seaborn"));
    }
    if (elements.tabCanvas) {
      elements.tabCanvas.addEventListener("click", () => setChartMode("canvas"));
    }
    if (elements.chartRetryBtn) {
      elements.chartRetryBtn.addEventListener("click", () => {
        refreshCharts();
        loadSummaryData();
      });
    }

    // Window resize redrawing for responsive Canvas
    window.addEventListener(
      "resize",
      debounce(() => {
        if (state.chartMode === "canvas" && state.summary) {
          renderOverviewCanvas(state.summary);
        }
      }, 150)
    );

    // Reload Data button
    if (elements.reloadBtn) {
      elements.reloadBtn.addEventListener("click", async () => {
        try {
          elements.reloadBtn.disabled = true;
          elements.reloadBtn.textContent = "Reloading…";
          const res = await fetch("/api/reload", { method: "POST" });
          const data = await res.json();
          const countMsg = typeof data.rows === "number" ? `Reloaded ${NUMBER.format(data.rows)} rows` : "Reloaded dataset";
          showToast(data.message || countMsg);
          await loadSummaryData();
          if (state.currentView === "explorer") {
            loadExplorerData();
          }
          checkHealth();
          refreshCharts();
        } catch (err) {
          loggerError("Reload failed:", err);
          showToast("Reload failed");
        } finally {
          elements.reloadBtn.disabled = false;
          elements.reloadBtn.textContent = "Reload Data";
        }
      });
    }

    // Export Chart button (Client-side Canvas or 300 DPI Seaborn PNG)
    if (elements.exportChartBtn) {
      elements.exportChartBtn.addEventListener("click", () => {
        try {
          if (state.chartMode === "canvas" && elements.overviewCanvas) {
            const dataUrl = elements.overviewCanvas.toDataURL("image/png");
            const a = document.createElement("a");
            a.href = dataUrl;
            a.download = "sympsort_smoker_charges_canvas.png";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            showToast("Exported Canvas chart as PNG");
          } else {
            // Trigger 300 DPI high-res server download
            const kind = state.currentView === "comparison" ? (state.comparisonChartKind || "bar") : "bar";
            const a = document.createElement("a");
            a.href = `/api/download/chart?kind=${kind}`;
            a.download = `sympsort_${kind}_chart.png`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            showToast(`Exporting 300 DPI Seaborn chart (${kind})`);
          }
        } catch (err) {
          loggerError("Export chart error:", err);
          showToast("Failed to export chart");
        }
      });
    }

    // Download Links with Feedback Toast
    if (elements.downloadSummaryLink) {
      elements.downloadSummaryLink.addEventListener("click", () => {
        showToast("Downloading summary metrics CSV…");
      });
    }
    if (elements.downloadFilteredLink) {
      elements.downloadFilteredLink.addEventListener("click", () => {
        showToast("Downloading filtered records CSV…");
      });
    }

    // Retries
    if (elements.overviewRetry) {
      elements.overviewRetry.addEventListener("click", loadSummaryData);
    }
    if (elements.comparisonRetry) {
      elements.comparisonRetry.addEventListener("click", loadSummaryData);
    }

    // Explorer search (debounced)
    if (elements.explorerSearch) {
      elements.explorerSearch.addEventListener(
        "input",
        debounce((e) => {
          state.explorer.search = e.target.value.trim();
          state.explorer.page = 1;
          loadExplorerData();
        }, 300)
      );
    }

    // Explorer smoker filter
    if (elements.smokerFilter) {
      elements.smokerFilter.addEventListener("change", (e) => {
        state.explorer.smoker = e.target.value;
        state.explorer.page = 1;
        loadExplorerData();
      });
    }

    // Explorer region filter
    if (elements.regionFilter) {
      elements.regionFilter.addEventListener("change", (e) => {
        state.explorer.region = e.target.value;
        state.explorer.page = 1;
        loadExplorerData();
      });
    }

    // Explorer sex filter
    if (elements.sexFilter) {
      elements.sexFilter.addEventListener("change", (e) => {
        state.explorer.sex = e.target.value;
        state.explorer.page = 1;
        loadExplorerData();
      });
    }

    // Explorer children filter
    if (elements.childrenFilter) {
      elements.childrenFilter.addEventListener("change", (e) => {
        state.explorer.children = e.target.value;
        state.explorer.page = 1;
        loadExplorerData();
      });
    }

    // Explorer BMI filter
    if (elements.bmiFilter) {
      elements.bmiFilter.addEventListener("change", (e) => {
        state.explorer.bmi = e.target.value;
        state.explorer.page = 1;
        loadExplorerData();
      });
    }

    // Explorer Age filter
    if (elements.ageFilter) {
      elements.ageFilter.addEventListener("change", (e) => {
        state.explorer.age = e.target.value;
        state.explorer.page = 1;
        loadExplorerData();
      });
    }

    // Explorer page size
    if (elements.pageSize) {
      elements.pageSize.addEventListener("change", (e) => {
        state.explorer.pageSize = parseInt(e.target.value, 10) || 15;
        state.explorer.page = 1;
        loadExplorerData();
      });
    }

    // Copy Code button in Methodology
    if (elements.copyCodeBtn && elements.methodologyCode) {
      elements.copyCodeBtn.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(elements.methodologyCode.textContent);
          elements.copyCodeBtn.textContent = "Copied!";
          setTimeout(() => {
            elements.copyCodeBtn.textContent = "Copy";
          }, 2000);
        } catch {
          elements.copyCodeBtn.textContent = "Error";
        }
      });
    }

    // Mobile menu toggle
    if (elements.mobileMenuBtn && elements.sidebar) {
      elements.mobileMenuBtn.addEventListener("click", () => {
        elements.sidebar.classList.toggle("sidebar--open");
      });
    }

    // Comparison Beyond the Average segmented buttons
    if (elements.comparisonChartSelector) {
      elements.comparisonChartSelector.querySelectorAll(".segmented-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const kind = btn.getAttribute("data-kind") || "bar";
          updateComparisonChart(kind);
        });
      });
    }

    // Scenario Comparison inputs
    document.querySelectorAll(".scenario-input").forEach((sel) => {
      sel.addEventListener("change", updateScenarioComparison);
    });

    // Scenario Comparison (View 6) actions
    if (elements.scenCompareRunBtn) {
      elements.scenCompareRunBtn.addEventListener("click", runScenarioComparison);
    }
    if (elements.scenCompareResetBtn) {
      elements.scenCompareResetBtn.addEventListener("click", resetScenarioInputs);
    }
    if (elements.downloadScenarioPdfBtn) {
      elements.downloadScenarioPdfBtn.addEventListener("click", () => downloadScenarioPdfReport(false));
    }
    if (elements.downloadScenarioPdfBtn2) {
      elements.downloadScenarioPdfBtn2.addEventListener("click", () => downloadScenarioPdfReport(true));
    }

    // Explorer smoker pills
    if (elements.smokerPills) {
      elements.smokerPills.querySelectorAll(".smoker-pill").forEach((pill) => {
        pill.addEventListener("click", () => {
          elements.smokerPills.querySelectorAll(".smoker-pill").forEach((p) => {
            p.classList.remove("active");
            p.setAttribute("aria-checked", "false");
          });
          pill.classList.add("active");
          pill.setAttribute("aria-checked", "true");
          state.explorer.smoker = pill.getAttribute("data-smoker") || "";
          if (elements.smokerFilter) elements.smokerFilter.value = state.explorer.smoker;
          state.explorer.page = 1;
          loadExplorerData();
        });
      });
    }

    // Explorer reset filters button
    if (elements.resetFiltersBtn) {
      elements.resetFiltersBtn.addEventListener("click", () => {
        if (elements.explorerSearch) elements.explorerSearch.value = "";
        if (elements.regionFilter) elements.regionFilter.value = "";
        if (elements.sexFilter) elements.sexFilter.value = "";
        if (elements.childrenFilter) elements.childrenFilter.value = "";
        if (elements.bmiFilter) elements.bmiFilter.value = "";
        if (elements.ageFilter) elements.ageFilter.value = "";
        if (elements.smokerFilter) elements.smokerFilter.value = "";
        state.explorer.sex = "";
        state.explorer.children = "";
        state.explorer.bmi = "";
        state.explorer.age = "";
        if (elements.smokerPills) {
          elements.smokerPills.querySelectorAll(".smoker-pill").forEach((p, idx) => {
            const isFirst = idx === 0;
            p.classList.toggle("active", isFirst);
            p.setAttribute("aria-checked", isFirst ? "true" : "false");
          });
        }
        state.explorer.search = "";
        state.explorer.smoker = "";
        state.explorer.region = "";
        state.explorer.sort = "";
        state.explorer.order = "asc";
        state.explorer.page = 1;

        if (elements.explorerHead) {
          elements.explorerHead.querySelectorAll("th").forEach((th) => {
            th.setAttribute("aria-sort", "none");
            const ind = th.querySelector(".sort-indicator");
            if (ind) ind.textContent = "↕";
          });
        }

        loadExplorerData();
        showToast("Explorer filters reset");
      });
    }

    // Methodology quality audit tabs
    if (elements.qualityTabs) {
      elements.qualityTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
          const qtab = tab.getAttribute("data-qtab");
          elements.qualityTabs.forEach((t) => {
            const active = t === tab;
            t.classList.toggle("active", active);
            t.setAttribute("aria-selected", active ? "true" : "false");
          });
          const describePane = document.getElementById("qualityDescribePane");
          const headPane = document.getElementById("qualityHeadPane");
          const infoPane = document.getElementById("qualityInfoPane");
          if (describePane) describePane.classList.toggle("hidden", qtab !== "describe");
          if (headPane) headPane.classList.toggle("hidden", qtab !== "head");
          if (infoPane) infoPane.classList.toggle("hidden", qtab !== "info");
        });
      });
    }
  }

  // ── Chart Image Load Handlers ────────────────────────────────────────────
  function setupChartLoadHandlers() {
    if (elements.heroChart) {
      elements.heroChart.addEventListener("load", () => {
        elements.heroChart.classList.add("loaded");
        if (elements.chartLoadingOverlay) {
          elements.chartLoadingOverlay.classList.add("hidden");
        }
        if (elements.chartErrorOverlay) {
          elements.chartErrorOverlay.classList.add("hidden");
        }
      });
      elements.heroChart.addEventListener("error", () => {
        elements.heroChart.classList.remove("loaded");
        if (elements.chartLoadingOverlay) {
          elements.chartLoadingOverlay.classList.add("hidden");
        }
        // Graceful automatic switch to high-DPI Canvas renderer if backend PNG fails
        setChartMode("canvas");
        loggerError("Hero chart image failed to load from /api/chart; switched to Canvas renderer");
      });
    }

    if (elements.comparisonChart) {
      elements.comparisonChart.addEventListener("load", () => {
        elements.comparisonChart.classList.add("loaded");
      });
      elements.comparisonChart.addEventListener("error", () => {
        elements.comparisonChart.classList.remove("loaded");
        loggerError("Comparison chart failed to load from /api/chart");
      });
    }
  }

  // ── Application Bootstrapping ───────────────────────────────────────────
  function init() {
    applyTheme(state.theme);
    initTableHeaders();
    setupChartLoadHandlers();
    setupEventListeners();
    handleHashChange();
    loadSummaryData();
    checkHealth();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
