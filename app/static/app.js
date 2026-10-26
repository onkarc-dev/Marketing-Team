/**
 * Quanteinstein B2B Outbound Intelligence Engine UI Logic
 */

// Presets data for quick testing
const PRESETS = {
  slippage: {
    name: "Marcus Vance",
    company: "Apex Alpha Capital",
    title: "Managing Partner & Head Quant Trader",
    bio: "Ex-Citadel. Managing a quantitative equity market-neutral prop book. Building low-latency Python execution pipelines.",
    posts: "Our backtest showed a 2.4 Sharpe on statistical arbitrage intraday, but live execution slippage and spread friction completely destroyed the alpha on the first 100 fills. Backtest overfitting vs live exchange friction is the bane of every algorithmic desk.",
    jobs: "Senior Python Execution Developer (London / Remote) - Focus on order book feeds and latency optimization."
  },
  hiring: {
    name: "Elena Rostova",
    company: "Krypton Quant Labs",
    title: "CTO & Co-Founder",
    bio: "Founding a boutique systematic trading desk. Automating crypto derivatives and statistical arbitrage models.",
    posts: "Transitioning our manual volatility arbitrage strategies into 100% automated algorithmic order routing. Excited for Q4 launch.",
    jobs: "Hiring: Quant Execution Engineer / Algo Trader. Responsibilities: Build backtesting infrastructure, stress-test execution parameters, and interface with exchange websocket APIs."
  },
  tech: {
    name: "David Chen",
    company: "Self-Employed",
    title: "Systematic Retail Trader & Quant Researcher",
    bio: "Developing automated trading strategies in Python. Deep interest in vectorbt, pandas time-series, and CCXT order routing.",
    posts: "Just finished building a cross-exchange statistical arbitrage backtest using vectorbt and ccxt order book snapshots. Comparing Sharpe ratios across different rebalancing intervals.",
    jobs: "None (Independent Trader)"
  },
  inactive: {
    name: "Robert Langdon",
    company: "OldGuard Asset Management",
    title: "Senior Quantitative Portfolio Manager",
    bio: "20+ years managing systematic global macro books and fixed income multi-asset funds. Quantitative risk modeling.",
    posts: "Shared an article: 'Federal Reserve Rate Decisions and 10-Year Treasury Yield Movements'.",
    jobs: "No active quantitative developer job listings."
  },
  irrelevant: {
    name: "Sarah Jenkins",
    company: "BlueSky Realty Group",
    title: "Principal Residential Real Estate Broker",
    bio: "Top 1% luxury residential real estate agent in Miami. Helping families find their dream coastal homes.",
    posts: "Just listed this stunning 4-bedroom oceanfront villa in Coconut Grove! DM for private tour bookings.",
    jobs: "Hiring: Junior Real Estate Sales Associate."
  }
};

let currentResult = null;
let batchData = [];

document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initPresets();
  initForm();
  initBatch();
  loadSamplePreset("slippage");
});

// Tab Navigation
function initTabs() {
  const tabs = document.querySelectorAll(".tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(tc => tc.style.display = "none");
      
      tab.classList.add("active");
      const targetId = tab.getAttribute("data-tab");
      const targetContent = document.getElementById(targetId);
      if (targetContent) targetContent.style.display = "block";
    });
  });
}

// Quick Presets
function initPresets() {
  document.querySelectorAll(".btn-preset").forEach(btn => {
    btn.addEventListener("click", () => {
      const presetKey = btn.getAttribute("data-preset");
      loadSamplePreset(presetKey);
    });
  });

  document.getElementById("clearBtn").addEventListener("click", () => {
    document.getElementById("pName").value = "";
    document.getElementById("pCompany").value = "";
    document.getElementById("pTitle").value = "";
    document.getElementById("pBio").value = "";
    document.getElementById("pPosts").value = "";
    document.getElementById("pJobs").value = "";
    resetOutput();
  });
}

function loadSamplePreset(key) {
  const data = PRESETS[key];
  if (!data) return;

  document.getElementById("pName").value = data.name;
  document.getElementById("pCompany").value = data.company;
  document.getElementById("pTitle").value = data.title;
  document.getElementById("pBio").value = data.bio;
  document.getElementById("pPosts").value = data.posts;
  document.getElementById("pJobs").value = data.jobs;
}

// Single Form Analysis
function initForm() {
  const form = document.getElementById("prospectForm");
  const analyzeBtn = document.getElementById("analyzeBtn");
  const spinner = document.getElementById("btnSpinner");
  const copyBtn = document.getElementById("copyBtn");
  const toggleJsonBtn = document.getElementById("toggleRawJsonBtn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      name: document.getElementById("pName").value.trim() || "Prospect",
      company: document.getElementById("pCompany").value.trim() || "",
      title: document.getElementById("pTitle").value.trim() || "",
      scraped_profile_bio: document.getElementById("pBio").value.trim(),
      recent_posts_and_comments: document.getElementById("pPosts").value.trim(),
      recent_company_job_listings: document.getElementById("pJobs").value.trim()
    };

    if (!payload.scraped_profile_bio && !payload.recent_posts_and_comments) {
      alert("Please provide at least a profile bio or recent posts.");
      return;
    }

    // Set UI loading
    analyzeBtn.disabled = true;
    spinner.style.display = "inline-block";

    try {
      const resp = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);
      const data = await resp.json();
      currentResult = data;
      renderResult(data);
    } catch (err) {
      console.error("Analysis failed:", err);
      alert("Analysis failed: " + err.message);
    } finally {
      analyzeBtn.disabled = false;
      spinner.style.display = "none";
    }
  });

  copyBtn.addEventListener("click", () => {
    if (!currentResult || !currentResult.message) return;
    navigator.clipboard.writeText(currentResult.message).then(() => {
      showToast("Message copied to clipboard!");
    });
  });

  toggleJsonBtn.addEventListener("click", () => {
    const rawBlock = document.getElementById("rawJsonBlock");
    rawBlock.style.display = rawBlock.style.display === "none" ? "block" : "none";
  });
}

function resetOutput() {
  document.getElementById("emptyState").style.display = "block";
  document.getElementById("resultsView").style.display = "none";
  currentResult = null;
}

function renderResult(data) {
  document.getElementById("emptyState").style.display = "none";
  document.getElementById("resultsView").style.display = "block";

  // Score & Banner
  const scoreNum = document.getElementById("scoreNum");
  const scoreBanner = document.getElementById("scoreBanner");
  const intentPill = document.getElementById("intentTierPill");
  const reasoningText = document.getElementById("reasoningText");

  scoreNum.textContent = data.score;
  reasoningText.textContent = data.reasoning;

  scoreBanner.className = "score-banner";
  intentPill.className = "intent-pill";

  if (data.score >= 8) {
    scoreBanner.classList.add("score-tier-high");
    intentPill.classList.add("pill-high");
    intentPill.textContent = data.intent_tier;
  } else if (data.score >= 4) {
    scoreBanner.classList.add("score-tier-med");
    intentPill.classList.add("pill-med");
    intentPill.textContent = data.intent_tier;
  } else {
    scoreBanner.classList.add("score-tier-low");
    intentPill.classList.add("pill-low");
    intentPill.textContent = data.intent_tier;
  }

  // Triggers
  const triggersContainer = document.getElementById("triggersContainer");
  triggersContainer.innerHTML = "";
  if (data.triggers && data.triggers.length > 0) {
    data.triggers.forEach(t => {
      const badge = document.createElement("div");
      badge.className = "trigger-badge";
      badge.innerHTML = `
        <span class="trigger-category">[${t.category}]</span>
        <span class="trigger-text">${t.signal}</span>
      `;
      triggersContainer.appendChild(badge);
    });
  } else {
    triggersContainer.innerHTML = `<span class="text-secondary" style="font-size:0.8rem;">No explicit behavioral triggers detected.</span>`;
  }

  // Connection Request Message
  const msgSection = document.getElementById("messageSection");
  const msgContent = document.getElementById("messageContent");
  const wordBadge = document.getElementById("wordCounterBadge");
  const wordCountNum = document.getElementById("wordCountNum");
  const copyBtn = document.getElementById("copyBtn");

  if (data.score >= 8 && data.message) {
    msgContent.textContent = data.message;
    wordCountNum.textContent = data.word_count;
    wordBadge.className = data.word_count <= 45 ? "word-counter" : "word-counter over";
    copyBtn.style.display = "inline-flex";
  } else {
    msgContent.textContent = `No outreach message drafted (Score ${data.score} is below outreach threshold 8 -> PASS).`;
    wordCountNum.textContent = 0;
    copyBtn.style.display = "none";
  }

  // Strict JSON view
  const strictJson = {
    score: data.score,
    reasoning: data.reasoning,
    message: data.message
  };
  document.getElementById("rawJsonCode").textContent = JSON.stringify(strictJson, null, 2);
}

// Batch Processor
function initBatch() {
  const loadSampleBtn = document.getElementById("loadSampleBatchBtn");
  const csvInput = document.getElementById("csvFileInput");
  const exportBtn = document.getElementById("exportQualifiedBtn");
  const searchInput = document.getElementById("tableSearchInput");
  const filterPills = document.querySelectorAll(".filter-pill");

  loadSampleBtn.addEventListener("click", async () => {
    loadSampleBtn.disabled = true;
    loadSampleBtn.textContent = "Processing Sample Leads...";
    try {
      const sampleResp = await fetch("/static/sample_dataset.json");
      let sampleLeads = [];
      if (sampleResp.ok) {
        sampleLeads = await sampleResp.json();
      } else {
        // Fallback sample array
        sampleLeads = Object.values(PRESETS);
      }

      const batchResp = await fetch("/api/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prospects: sampleLeads })
      });
      const data = await batchResp.json();
      batchData = data.results;
      updateBatchMetrics(data);
      renderBatchTable(batchData);
    } catch (e) {
      console.error(e);
      alert("Failed loading batch: " + e.message);
    } finally {
      loadSampleBtn.disabled = false;
      loadSampleBtn.textContent = "Load Sample Scraped Dataset (8 Leads)";
    }
  });

  csvInput.addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const resp = await fetch("/api/upload-csv", {
        method: "POST",
        body: formData
      });
      if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);
      const data = await resp.json();
      batchData = data.results;
      updateBatchMetrics(data);
      renderBatchTable(batchData);
      showToast(`Analyzed ${data.total} leads from CSV!`);
    } catch (err) {
      alert("CSV upload failed: " + err.message);
    }
  });

  exportBtn.addEventListener("click", () => {
    window.location.href = "/api/export?min_score=8";
  });

  searchInput.addEventListener("input", () => {
    applyFilters();
  });

  filterPills.forEach(pill => {
    pill.addEventListener("click", () => {
      filterPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      applyFilters();
    });
  });
}

function updateBatchMetrics(data) {
  document.getElementById("metricTotal").textContent = data.total;
  document.getElementById("metricHighIntent").textContent = data.high_intent_count;
  document.getElementById("metricPassed").textContent = data.passed_count;
  document.getElementById("metricAvg").textContent = data.average_score;
}

function applyFilters() {
  const query = document.getElementById("tableSearchInput").value.toLowerCase();
  const activePill = document.querySelector(".filter-pill.active").getAttribute("data-filter");

  let filtered = batchData.filter(item => {
    const textMatch = (
      item.name.toLowerCase().includes(query) ||
      item.company.toLowerCase().includes(query) ||
      item.reasoning.toLowerCase().includes(query)
    );
    if (!textMatch) return false;

    if (activePill === "high") return item.score >= 8;
    if (activePill === "pass") return item.score < 8;
    return true;
  });

  renderBatchTable(filtered);
}

function renderBatchTable(leads) {
  const tbody = document.getElementById("batchTableBody");
  tbody.innerHTML = "";

  if (!leads || leads.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="text-center empty-table">No leads match criteria.</td></tr>`;
    return;
  }

  leads.forEach(r => {
    const tr = document.createElement("tr");
    const scoreClass = r.score >= 8 ? "high" : (r.score >= 4 ? "med" : "low");
    const messageCell = r.message ? 
      `<span style="color:#f0f6fc;">"${r.message}"</span> <span style="font-size:0.7rem; color:#3fb950; display:block;">(${r.word_count} words)</span>` : 
      `<span style="color:#586069; font-style:italic;">No outreach (Score < 8)</span>`;

    tr.innerHTML = `
      <td><span class="badge-score ${scoreClass}">${r.score}</span></td>
      <td><strong>${escapeHtml(r.name)}</strong><br><small style="color:#8b949e;">${escapeHtml(r.title || "N/A")}</small></td>
      <td>${escapeHtml(r.company || "N/A")}</td>
      <td style="max-width:280px; font-size:0.78rem;">${escapeHtml(r.reasoning)}</td>
      <td style="max-width:320px; font-size:0.8rem;">${messageCell}</td>
      <td>
        ${r.message ? `<button class="btn-copy" onclick="copyText('${escapeQuotes(r.message)}')">Copy</button>` : '-'}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function showToast(msg) {
  const toast = document.getElementById("toastNotification");
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
}

function copyText(txt) {
  navigator.clipboard.writeText(txt).then(() => {
    showToast("Message copied to clipboard!");
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function escapeQuotes(str) {
  if (!str) return "";
  return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
}
