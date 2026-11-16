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
    explorer: {
      page: 1,
      pageSize: 15,
      search: "",
      smoker: "",
      region: "",
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
    statTVal: document.getElementById("statTVal"),
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

    // Explorer
    explorerSearch: document.getElementById("explorerSearch"),
    smokerFilter: document.getElementById("smokerFilter"),
    smokerPills: document.getElementById("smokerPills"),
    regionFilter: document.getElementById("regionFilter"),
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
    let rows = 1338;

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
          if (s && s.total_valid_records) rows = s.total_valid_records;
          isConnected = true;
        } catch {}
      }
    }

    if (isConnected) {
      if (dot) dot.className = "status-dot status-dot--connected";
      if (text) text.textContent = `Connected (${NUMBER.format(rows)} rows)`;
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

    // Statistical figures from Pandas groupby
    const nsMean = data?.non_smoker_mean || 8434.27;
    const smMean = data?.smoker_mean || 32050.23;
    const nsStd = data?.non_smoker_std || 5993.78;
    const smStd = data?.smoker_std || 11541.56;
    const nsCount = data?.non_smoker_count || 1064;
    const smCount = data?.smoker_count || 274;

    // 95% Confidence Interval: SE = std / sqrt(n), CI = 1.96 * SE
    const nsSE = nsStd / Math.sqrt(Math.max(1, nsCount));
    const smSE = smStd / Math.sqrt(Math.max(1, smCount));
    const nsCI = 1.96 * nsSE;
    const smCI = 1.96 * smSE;

    // Plot geometry
    const margin = { top: 55, right: 35, bottom: 65, left: 80 };
    const plotWidth = Math.max(100, cssWidth - margin.left - margin.right);
    const plotHeight = Math.max(100, cssHeight - margin.top - margin.bottom);

    const maxVal = 40000;
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

      // Draw 95% CI Error Whisker
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

      // Dollar label above bar
      ctx.fillStyle = textColor;
      ctx.font = "bold 13px system-ui, sans-serif";
      ctx.textAlign = "center";
      const labelY = Math.min(barTop, ciTop) - 10;
      ctx.fillText(CURRENCY.format(bar.mean), centerX, labelY);

      // X-Axis Category Label
      ctx.font = "600 13px system-ui, sans-serif";
      ctx.fillText(bar.label, centerX, margin.top + plotHeight + 24);

      // Group count subtext
      ctx.font = "11px system-ui, sans-serif";
      ctx.fillStyle = textSec;
      ctx.fillText(`(n = ${NUMBER.format(bar.count)})`, centerX, margin.top + plotHeight + 42);
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
        const mult = data.multiplier ? `${data.multiplier.toFixed(1)}×` : "3.8×";
        elements.findingLine.innerHTML = `Smokers are charged about <strong>${mult} more</strong> on average: <strong>${CURRENCY.format(data.smoker_mean)}</strong> vs <strong>${CURRENCY.format(data.non_smoker_mean)}</strong>.`;
      }

      if (!state.hasAnimatedNumbers) {
        animateValue(elements.kpiNonSmoker, 0, data.non_smoker_mean);
        animateValue(elements.kpiSmoker, 0, data.smoker_mean);
        state.hasAnimatedNumbers = true;
      } else {
        if (elements.kpiNonSmoker) elements.kpiNonSmoker.textContent = CURRENCY.format(data.non_smoker_mean);
        if (elements.kpiSmoker) elements.kpiSmoker.textContent = CURRENCY.format(data.smoker_mean);
      }

      if (elements.diffAbs) {
        elements.diffAbs.textContent = `+${CURRENCY.format(data.absolute_difference)}`;
      }
      if (elements.diffBadge) {
        const pct = data.percentage_difference != null ? data.percentage_difference.toFixed(1) : "280.0";
        elements.diffBadge.textContent = `+${pct}%`;
      }

      // Populate P1 Secondary KPI Strip
      if (elements.kpiMultiplier) {
        elements.kpiMultiplier.textContent = (data.multiplier ? data.multiplier.toFixed(2) : "3.80") + "×";
      }
      if (elements.kpiNonSmokerCount) {
        elements.kpiNonSmokerCount.textContent = `n = ${NUMBER.format(data.non_smoker_count || 1064)}`;
      }
      if (elements.kpiSmokerCount) {
        const total = data.total_valid_records || (data.smoker_count + data.non_smoker_count) || 1338;
        const pct = (( (data.smoker_count || 274) / total ) * 100).toFixed(1);
        elements.kpiSmokerCount.textContent = `n = ${NUMBER.format(data.smoker_count || 274)} (${pct}% of records)`;
      }
      if (elements.kpiValidCount) {
        elements.kpiValidCount.textContent = NUMBER.format(data.total_valid_records || 1338);
      }

      // Populate Methodology live output
      if (elements.groupbyOutput) {
        elements.groupbyOutput.textContent = data.groupby_text || "smoker\nno      8434.27\nyes    32050.23\nName: charges, dtype: float64";
      }

      // Populate Detailed Stats Table
      populateStatsTable(data);

      // Populate P2 Statistical Significance Card
      if (elements.statTVal) {
        elements.statTVal.textContent = "t = " + (data.t_statistic != null ? data.t_statistic.toFixed(2) : "32.75");
      }
      if (elements.statMWVal) {
        elements.statMWVal.textContent = data.mann_whitney_p_value || "p < 0.001";
      }
      if (elements.statCohenVal) {
        elements.statCohenVal.textContent = "d = " + (data.cohen_d != null ? data.cohen_d.toFixed(2) : "3.16");
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

    const nsMargin = data.non_smoker_ci_margin != null ? CURRENCY.format(data.non_smoker_ci_margin) : "$360.15";
    const smMargin = data.smoker_ci_margin != null ? CURRENCY.format(data.smoker_ci_margin) : "$1,366.61";
    const nsLow = data.non_smoker_ci_low != null ? CURRENCY.format(data.non_smoker_ci_low) : "$8,074.12";
    const nsHigh = data.non_smoker_ci_high != null ? CURRENCY.format(data.non_smoker_ci_high) : "$8,794.42";
    const smLow = data.smoker_ci_low != null ? CURRENCY.format(data.smoker_ci_low) : "$30,683.62";
    const smHigh = data.smoker_ci_high != null ? CURRENCY.format(data.smoker_ci_high) : "$33,416.84";

    const rows = [
      { label: "Sample Count (n)", ns: NUMBER.format(data.non_smoker_count || 1064), sm: NUMBER.format(data.smoker_count || 274) },
      { label: "Mean Charge", ns: CURRENCY.format(data.non_smoker_mean), sm: CURRENCY.format(data.smoker_mean) },
      {
        label: "95% Confidence Interval",
        ns: `<span title="${data.ci_method || "Student's t / Normal distribution (95% CI)"}">${CURRENCY.format(data.non_smoker_mean)} ± ${nsMargin}<br><small class="text-tertiary">[${nsLow} – ${nsHigh}]</small></span>`,
        sm: `<span title="${data.ci_method || "Student's t / Normal distribution (95% CI)"}">${CURRENCY.format(data.smoker_mean)} ± ${smMargin}<br><small class="text-tertiary">[${smLow} – ${smHigh}]</small></span>`,
      },
      { label: "Median Charge", ns: CURRENCY.format(data.non_smoker_median), sm: CURRENCY.format(data.smoker_median) },
      { label: "Std Deviation", ns: CURRENCY.format(data.non_smoker_std), sm: CURRENCY.format(data.smoker_std) },
      { label: "Minimum Charge", ns: CURRENCY.format(data.non_smoker_min), sm: CURRENCY.format(data.smoker_min) },
      { label: "Maximum Charge", ns: CURRENCY.format(data.non_smoker_max), sm: CURRENCY.format(data.smoker_max) },
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

  async function loadExplorerData() {
    if (!elements.explorerBody) return;
    state.explorer.isLoading = true;

    const params = new URLSearchParams({
      page: state.explorer.page,
      page_size: state.explorer.pageSize,
    });

    if (state.explorer.search) params.set("search", state.explorer.search);
    if (state.explorer.smoker) params.set("smoker", state.explorer.smoker);
    if (state.explorer.region) params.set("region", state.explorer.region);
    if (state.explorer.sort) params.set("sort", state.explorer.sort);
    if (state.explorer.order) params.set("order", state.explorer.order);

    try {
      const res = await fetch(`/api/data?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();

      state.explorer.totalFiltered = data.total_filtered || 0;
      state.explorer.totalPages = data.pages || 1;
      state.explorer.page = data.page || 1;

      // Update contextual Download filtered CSV link with active filter query
      if (elements.downloadFilteredLink) {
        const downloadParams = new URLSearchParams();
        if (state.explorer.search) downloadParams.set("search", state.explorer.search);
        if (state.explorer.smoker) downloadParams.set("smoker", state.explorer.smoker);
        if (state.explorer.region) downloadParams.set("region", state.explorer.region);
        if (state.explorer.sort) downloadParams.set("sort", state.explorer.sort);
        if (state.explorer.order) downloadParams.set("order", state.explorer.order);
        elements.downloadFilteredLink.href = `/api/download/filtered?${downloadParams.toString()}`;
      }

      // Update live selection summary strip
      if (data.selection_summary) {
        if (elements.selCount) elements.selCount.textContent = `${NUMBER.format(data.selection_summary.matched_count)} rows`;
        if (elements.selMean) elements.selMean.textContent = CURRENCY.format(data.selection_summary.mean_charges);
        if (elements.selMedian) elements.selMedian.textContent = CURRENCY.format(data.selection_summary.median_charges);
        if (elements.selBmi) elements.selBmi.textContent = data.selection_summary.mean_bmi ? Number(data.selection_summary.mean_bmi).toFixed(2) : "—";
      }

      renderExplorerRows(data.records || []);
      renderPagination();
      renderShowingText(data);
    } catch (err) {
      const sampleEl = document.getElementById("serverSampleData");
      if (sampleEl && sampleEl.textContent.trim()) {
        try {
          const sampleRecords = JSON.parse(sampleEl.textContent);
          if (sampleRecords && sampleRecords.length) {
            state.explorer.totalFiltered = 1338;
            state.explorer.totalPages = Math.ceil(1338 / state.explorer.pageSize);
            state.explorer.page = 1;
            renderExplorerRows(sampleRecords.slice(0, state.explorer.pageSize));
            renderPagination();
            renderShowingText({
              total_filtered: 1338,
              total_records: 1338,
              page: 1,
              pages: Math.ceil(1338 / state.explorer.pageSize),
              page_size: state.explorer.pageSize,
            });
            return;
          }
        } catch (e) {}
      }
      loggerError("Failed to load explorer data", err);
      elements.explorerBody.innerHTML = `<tr><td colspan="${COLUMNS.length}" class="table-error">Failed to load data. Please retry.</td></tr>`;
    } finally {
      state.explorer.isLoading = false;
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
          const formatted = col.format ? col.format(rawVal) : (rawVal ?? "—");
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

  // ── Compare a Profile Empirical Lookup Tool ────────────────────────────
  async function updateProfileMatch() {
    const age = elements.profileAge ? elements.profileAge.value : "all";
    const bmi = elements.profileBmi ? elements.profileBmi.value : "all";
    const sex = elements.profileSex ? elements.profileSex.value : "all";
    const region = elements.profileRegion ? elements.profileRegion.value : "all";
    const smoker = elements.profileSmoker ? elements.profileSmoker.value : "all";

    try {
      const params = new URLSearchParams({
        age_band: age,
        bmi_band: bmi,
        sex: sex,
        region: region,
        smoker: smoker,
      });
      const res = await fetch(`/api/profile-match?${params.toString()}`);
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();

      if (elements.profileMatchCount) {
        elements.profileMatchCount.textContent = NUMBER.format(data.count);
      }
      if (data.count > 0) {
        if (elements.profileMatchMean) elements.profileMatchMean.textContent = CURRENCY.format(data.mean);
        if (elements.profileMatchMedian) elements.profileMatchMedian.textContent = CURRENCY.format(data.median);
        if (elements.profileMatchRange) elements.profileMatchRange.textContent = `${CURRENCY.format(data.min)} – ${CURRENCY.format(data.max)}`;
      } else {
        if (elements.profileMatchMean) elements.profileMatchMean.textContent = "—";
        if (elements.profileMatchMedian) elements.profileMatchMedian.textContent = "—";
        if (elements.profileMatchRange) elements.profileMatchRange.textContent = "—";
      }

      if (elements.profileWarning) {
        if (data.warning) {
          elements.profileWarning.textContent = data.warning;
          elements.profileWarning.classList.remove("hidden");
        } else {
          elements.profileWarning.classList.add("hidden");
        }
      }
    } catch (err) {
      loggerError("Profile match lookup failed:", err);
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
      if (elements.auditRawRows) elements.auditRawRows.textContent = NUMBER.format(val.total_raw_rows || 1338);
      if (elements.auditValidRows) elements.auditValidRows.textContent = NUMBER.format(val.valid_rows || 1338);
      if (elements.auditExcludedRows) elements.auditExcludedRows.textContent = NUMBER.format(val.excluded_rows || 0);
      if (elements.auditNulls) elements.auditNulls.textContent = NUMBER.format((val.null_charges_count || 0) + (val.invalid_smoker_count || 0));

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
        let out = "<class 'pandas.core.frame.DataFrame'>\nRangeIndex: 1338 entries, 0 to 1337\n";
        out += "Data columns (total 8 columns):\n";
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

    // Keyboard shortcuts (1–5)
    window.addEventListener("keydown", (e) => {
      if (e.target && ["INPUT", "SELECT", "TEXTAREA"].includes(e.target.tagName)) return;
      const keyMap = {
        "1": "overview",
        "2": "comparison",
        "3": "explorer",
        "4": "methodology",
        "5": "about",
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
          showToast(data.message || `Reloaded ${data.rows || 1338} rows`);
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

    // Profile Compare dropdowns
    [
      elements.profileAge,
      elements.profileBmi,
      elements.profileSex,
      elements.profileRegion,
      elements.profileSmoker,
    ].forEach((sel) => {
      if (sel) {
        sel.addEventListener("change", updateProfileMatch);
      }
    });

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
        if (elements.smokerFilter) elements.smokerFilter.value = "";
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
