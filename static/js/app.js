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
    theme: localStorage.getItem("sympsort_theme") || "light",
    summary: null,
    hasAnimatedNumbers: false,
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
    exportChartLink: document.getElementById("exportChartLink"),
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
    heroChart: document.getElementById("heroChart"),
    sampleBody: document.getElementById("sampleBody"),

    // Comparison
    comparisonSkeleton: document.getElementById("comparisonSkeleton"),
    comparisonError: document.getElementById("comparisonError"),
    comparisonRetry: document.getElementById("comparisonRetry"),
    comparisonContent: document.getElementById("comparisonContent"),
    statsBody: document.getElementById("statsBody"),
    comparisonChart: document.getElementById("comparisonChart"),

    // Explorer
    explorerSearch: document.getElementById("explorerSearch"),
    smokerFilter: document.getElementById("smokerFilter"),
    regionFilter: document.getElementById("regionFilter"),
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

    try {
      const res = await fetch("/api/health");
      if (!res.ok) throw new Error("Health check failed");
      const data = await res.json();
      if (dot) {
        dot.className = "status-dot status-dot--connected";
      }
      if (text) {
        text.textContent = `Connected (${NUMBER.format(data.rows)} rows)`;
      }
    } catch {
      if (dot) {
        dot.className = "status-dot status-dot--offline";
      }
      if (text) {
        text.textContent = "Offline";
      }
    }
  }

  // ── Theme Management ────────────────────────────────────────────────────
  function applyTheme(themeName) {
    state.theme = themeName;
    elements.html.setAttribute("data-theme", themeName);
    localStorage.setItem("sympsort_theme", themeName);

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
    if (elements.heroChart) {
      elements.heroChart.classList.remove("loaded");
      elements.heroChart.src = `/api/chart?theme=${t}`;
    }
    if (elements.comparisonChart) {
      elements.comparisonChart.classList.remove("loaded");
      elements.comparisonChart.src = `/api/chart?theme=${t}`;
    }
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

    // Lazy load explorer data
    if (viewName === "explorer" && state.explorer.totalFiltered === 0) {
      loadExplorerData();
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

      const res = await fetch("/api/summary");
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      state.summary = data;

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

      // Populate Methodology live output
      if (elements.groupbyOutput) {
        elements.groupbyOutput.textContent = data.groupby_text || "smoker\nno      8434.27\nyes    32050.23\nName: charges, dtype: float64";
      }

      // Populate Detailed Stats Table
      populateStatsTable(data);

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
    const rows = [
      { label: "Sample Count (n)", ns: NUMBER.format(data.non_smoker_count || 1064), sm: NUMBER.format(data.smoker_count || 274) },
      { label: "Mean Charge", ns: CURRENCY.format(data.non_smoker_mean), sm: CURRENCY.format(data.smoker_mean) },
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
    try {
      const res = await fetch("/api/data?page=1&page_size=5");
      if (!res.ok) return;
      const data = await res.json();
      if (!data.records || !data.records.length) return;

      elements.sampleBody.innerHTML = data.records
        .map((rec) => {
          return `<tr>
            <td class="num font-tabular">${rec.age ?? "—"}</td>
            <td>${rec.sex ?? "—"}</td>
            <td class="num font-tabular">${rec.bmi != null ? Number(rec.bmi).toFixed(2) : "—"}</td>
            <td class="num font-tabular">${rec.children ?? "—"}</td>
            <td>${rec.smoker === "yes" ? '<span class="tag tag--smoker">yes</span>' : '<span class="tag tag--nonsmoker">no</span>'}</td>
            <td>${rec.region ?? "—"}</td>
            <td class="num font-tabular">${rec.charges != null ? CURRENCY.format(rec.charges) : "—"}</td>
          </tr>`;
        })
        .join("");
    } catch {
      // Keep silent for sample rows
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

      renderExplorerRows(data.records || []);
      renderPagination();
      renderShowingText(data);
    } catch (err) {
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
          showToast("Reload failed");
        } finally {
          elements.reloadBtn.disabled = false;
          elements.reloadBtn.textContent = "Reload Data";
        }
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
  }

  // ── Chart Image Load Handlers ────────────────────────────────────────────
  function setupChartLoadHandlers() {
    [elements.heroChart, elements.comparisonChart].forEach((img) => {
      if (!img) return;
      img.addEventListener("load", () => {
        img.classList.add("loaded");
      });
      img.addEventListener("error", () => {
        img.classList.remove("loaded");
        loggerError("Chart image failed to load:", img.src);
      });
    });
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
