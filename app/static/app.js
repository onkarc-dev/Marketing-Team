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
  initProspector();
  checkSmtpStatus();
  updateSentSuppressionStats();
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

  const openLinkedInBtn = document.getElementById("openLinkedInBtn");
  if (openLinkedInBtn) {
    openLinkedInBtn.addEventListener("click", () => {
      if (!currentResult || !currentResult.message) return;
      navigator.clipboard.writeText(currentResult.message).then(() => {
        showToast("Note copied! Opening LinkedIn to connect...");
        const name = document.getElementById("pName").value.trim();
        const company = document.getElementById("pCompany").value.trim();
        const targetUrl = currentResult.linkedin_url || `https://www.linkedin.com/search/results/all/?keywords=${encodeURIComponent(name + ' ' + company)}`;
        window.open(targetUrl, "_blank");
      });
    });
  }

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
  const openLinkedInBtn = document.getElementById("openLinkedInBtn");

  if (data.score >= 8 && data.message) {
    msgContent.textContent = data.message;
    wordCountNum.textContent = data.word_count;
    wordBadge.className = data.word_count <= 45 ? "word-counter" : "word-counter over";
    copyBtn.style.display = "inline-flex";
    if (openLinkedInBtn) openLinkedInBtn.style.display = "inline-flex";
  } else {
    msgContent.textContent = `No outreach message drafted (Score ${data.score} is below outreach threshold 8 -> PASS).`;
    wordCountNum.textContent = 0;
    copyBtn.style.display = "none";
    if (openLinkedInBtn) openLinkedInBtn.style.display = "none";
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
        ${r.message ? `
          <div style="display:flex; gap:4px;">
            <button class="btn-copy" onclick="copyText('${escapeQuotes(r.message)}')">Copy</button>
            <button class="btn-small" style="background:#0a66c2; color:white; border:none; padding:4px 8px;" onclick="openLinkedInForLead('${escapeQuotes(r.name)}', '${escapeQuotes(r.company)}', '${escapeQuotes(r.message)}')">LinkedIn</button>
          </div>
        ` : '-'}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function openLinkedInForLead(name, company, message) {
  navigator.clipboard.writeText(message).then(() => {
    showToast("Connection note copied! Opening LinkedIn...");
    const targetUrl = `https://www.linkedin.com/search/results/all/?keywords=${encodeURIComponent(name + ' ' + company)}`;
    window.open(targetUrl, "_blank");
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

// =====================================================================
// Web Search, Scraper & Cold Email Outreach Logic
// =====================================================================

let currentCampaignData = null;

function initProspector() {
  const form = document.getElementById("prospectorForm");
  const runBtn = document.getElementById("runSearchBtn");
  const spinner = document.getElementById("searchSpinner");
  const exportBtn = document.getElementById("exportEmailsBtn");

  // Region quick selector buttons
  document.querySelectorAll("[data-region-preset]").forEach(btn => {
    btn.addEventListener("click", () => {
      const reg = btn.getAttribute("data-region-preset");
      document.getElementById("targetRegion").value = reg;
    });
  });

  const rangeSelect = document.getElementById("batchRangeSelect");
  const sizeSelect = document.getElementById("batchSizeSelect");
  const batchIndicator = document.getElementById("currentBatchIndicator");
  const prevBatchBtn = document.getElementById("prevBatchBtn");
  const nextBatchBtn = document.getElementById("nextBatchBtn");

  if (rangeSelect && batchIndicator) {
    rangeSelect.addEventListener("change", () => {
      batchIndicator.textContent = `Viewing: ${rangeSelect.options[rangeSelect.selectedIndex].text}`;
    });
  }

  if (nextBatchBtn && rangeSelect) {
    nextBatchBtn.addEventListener("click", () => {
      if (rangeSelect.selectedIndex < rangeSelect.options.length - 1) {
        rangeSelect.selectedIndex += 1;
        if (batchIndicator) {
          batchIndicator.textContent = `Viewing: ${rangeSelect.options[rangeSelect.selectedIndex].text}`;
        }
        form.requestSubmit();
      } else {
        alert("You have reached the maximum batch range (Firms 951 – 1,000) for this country.");
      }
    });
  }

  if (prevBatchBtn && rangeSelect) {
    prevBatchBtn.addEventListener("click", () => {
      if (rangeSelect.selectedIndex > 0) {
        rangeSelect.selectedIndex -= 1;
        if (batchIndicator) {
          batchIndicator.textContent = `Viewing: ${rangeSelect.options[rangeSelect.selectedIndex].text}`;
        }
        form.requestSubmit();
      } else {
        alert("You are already on the first batch (Firms 1 – 50).");
      }
    });
  }

  // Run full discovery campaign
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const rangeVal = rangeSelect ? rangeSelect.value : "1-50";
    const sizeVal = sizeSelect ? parseInt(sizeSelect.value, 10) : 50;
    const parts = rangeVal.split("-");
    const startNum = parseInt(parts[0], 10) || 1;

    const queryPayload = {
      niche: document.getElementById("targetNiche").value.trim(),
      region: document.getElementById("targetRegion").value.trim(),
      firm_type: document.getElementById("targetFirmType").value.trim(),
      num_results: sizeVal,
      offset: startNum - 1,
      batch_range: rangeVal,
      max_target_pool: 1000,
      sender_name: document.getElementById("senderName").value.trim() || "Onkar (Founder, Quanteinstein)"
    };

    if (!queryPayload.niche || !queryPayload.region) {
      alert("Please enter both target trading niche and region area.");
      return;
    }

    runBtn.disabled = true;
    spinner.style.display = "inline-block";

    try {
      const resp = await fetch("/api/discovery/run-campaign", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(queryPayload)
      });

      if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);
      const data = await resp.json();
      currentCampaignData = data;

      if (batchIndicator) {
        batchIndicator.textContent = `Viewing: Batch ${rangeSelect ? rangeSelect.selectedIndex + 1 : 1} (${data.batch_range}) • ${data.total_discovered} Desks Loaded`;
      }

      renderDiscoveredFirms(data.leads);
      renderGeneratedEmails(data.emails);
      showToast(`Analyzed web and crafted ${data.emails.length} personalized cold emails for batch ${rangeVal}!`);
    } catch (err) {
      console.error("Discovery failed:", err);
      alert("Web discovery failed: " + err.message);
    } finally {
      runBtn.disabled = false;
      spinner.style.display = "none";
    }
  });

  exportBtn.addEventListener("click", () => {
    window.location.href = "/api/discovery/export-emails";
  });

  const viewSentBtn = document.getElementById("viewSentBtn");
  if (viewSentBtn) {
    viewSentBtn.addEventListener("click", async () => {
      try {
        const resp = await fetch("/api/discovery/sent-emails");
        const data = await resp.json();
        if (!data.sent_count) {
          alert("No outreach emails sent yet.\n\nOnce you send an email to a firm, they are automatically recorded to your suppression list and excluded from all future searches so you never send duplicates!");
          return;
        }
        let summary = `Contacted Suppression List (${data.sent_count} total):\n\n`;
        (data.records || []).slice(0, 15).forEach((r, idx) => {
          summary += `${idx+1}. ${r.firm_name || 'N/A'} - ${r.recipient_email} (${r.sent_at.split('T')[0]})\n`;
        });
        if (data.sent_count > 15) {
          summary += `...and ${data.sent_count - 15} more.\n`;
        }
        summary += `\nAll these firms are excluded from future searches to ensure you only discover fresh leads!`;
        alert(summary);
      } catch (err) {
        console.error(err);
      }
    });
  }
}


function renderDiscoveredFirms(leads) {
  const countBadge = document.getElementById("discoveredCount");
  const container = document.getElementById("firmListContainer");

  countBadge.textContent = `${leads.length} firms found`;
  container.innerHTML = "";

  if (!leads || leads.length === 0) {
    container.innerHTML = `<p class="text-secondary" style="font-size:0.8rem; padding: 1rem 0;">No matching firms found for this region.</p>`;
    return;
  }

  leads.forEach(lead => {
    const card = document.createElement("div");
    card.className = "firm-card";
    const tags = (lead.strategies_detected || []).map(s => `<span class="tag-strategy">${escapeHtml(s)}</span>`).join("");
    const findingsHtml = lead.website_findings ? `
      <div class="firm-website-findings">
        <span class="finding-badge">🔍 Studied Mandate:</span>
        <span class="finding-text">${escapeHtml(lead.website_findings)}</span>
      </div>
    ` : "";

    const isSweetSpot = (lead.firm_segment && lead.firm_segment.includes("Proprietary")) || !lead.firm_segment;
    const segmentBadgeClass = isSweetSpot ? "badge-sweet-spot" : "badge-stepping-stone";
    const segmentLabel = isSweetSpot ? "🎯 Sweet Spot: Prop Desk" : "📈 Stepping Stone: Emerging Fund";

    card.innerHTML = `
      <div class="firm-card-header">
        <span class="firm-title">${escapeHtml(lead.firm_name)}</span>
        <div style="display:flex; gap:6px; align-items:center;">
          <span class="firm-segment-badge ${segmentBadgeClass}">${segmentLabel}</span>
          <span class="firm-region-badge">${escapeHtml(lead.region)}</span>
        </div>
      </div>
      <div class="firm-meta-line" style="margin-bottom:0.4rem;">
        <span>🌐 <a href="${escapeHtml(lead.website)}" target="_blank" style="color:#58a6ff; text-decoration:none;">${escapeHtml(lead.website.replace("https://", ""))}</a></span>
        <span>✉️ <span class="firm-email-highlight">${escapeHtml(lead.email)}</span></span>
      </div>
      <div class="firm-metrics-pills">
        <span class="metric-pill">👥 ${escapeHtml(lead.headcount || '2–15 employees')}</span>
        <span class="metric-pill">💰 ${escapeHtml(lead.aum || '$10M–$50M AUM')}</span>
        <span class="metric-pill metric-buyer">👔 Buyer: ${escapeHtml(lead.target_decision_maker || lead.contact_title || 'Founder & Lead PM')}</span>
      </div>
      <p class="firm-summary-text">${escapeHtml(lead.summary)}</p>
      ${findingsHtml}
      <div class="firm-tags-flex">${tags}</div>
    `;
    container.appendChild(card);
  });
}

function renderGeneratedEmails(emails) {
  const emptyState = document.getElementById("emailEmptyState");
  const resultsView = document.getElementById("emailResultsView");
  const container = document.getElementById("emailCardsContainer");

  emptyState.style.display = "none";
  resultsView.style.display = "block";
  container.innerHTML = "";

  if (!emails || emails.length === 0) {
    emptyState.style.display = "block";
    resultsView.style.display = "none";
    return;
  }

  emails.forEach((em, idx) => {
    const card = document.createElement("div");
    card.className = "email-card";
    card.id = `emailCard_${idx}`;

    const mailtoLink = `mailto:${encodeURIComponent(em.recipient_email)}?subject=${encodeURIComponent(em.subject)}&body=${encodeURIComponent(em.body)}`;
    const analysisHtml = em.website_findings ? `
      <div class="email-analysis-badge">
        <span class="analysis-pill">🔍 Analyzed Web Mandate:</span>
        <span class="analysis-text">${escapeHtml(em.website_findings)}</span>
      </div>
    ` : "";

    const askHtml = em.the_ask ? `
      <div class="the-ask-box">
        <span class="the-ask-badge">🎯 The Ask (Zero Meeting Pressure):</span>
        <span class="the-ask-text">${escapeHtml(em.the_ask)}</span>
      </div>
    ` : "";

    // Build Follow-up Sequence navigation tabs and panels
    const followUps = em.follow_ups || [];
    let sequenceNavHtml = "";
    let sequencePanelsHtml = "";

    if (followUps.length > 0) {
      sequenceNavHtml = `
        <div class="sequence-section">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
            <span style="font-size:0.75rem; font-weight:600; color:#58a6ff; font-family:var(--font-mono);">
              📬 OUTREACH SEQUENCE (Initial + ${followUps.length} Follow-Ups)
            </span>
            <span style="font-size:0.68rem; color:#8b949e;">Non-confrontational cadence</span>
          </div>
          <div class="sequence-nav">
            <button class="seq-tab-btn active" id="tabBtn_${idx}_0" onclick="switchSeqTab(${idx}, 0)">
              ✉️ Step 1: Initial (Day 0)
            </button>
            ${followUps.map((fu, fIdx) => `
              <button class="seq-tab-btn" id="tabBtn_${idx}_${fIdx + 1}" onclick="switchSeqTab(${idx}, ${fIdx + 1})">
                ${escapeHtml(fu.step)}
              </button>
            `).join("")}
          </div>
        </div>
      `;

      // Panel 0: Initial Outreach
      sequencePanelsHtml += `
        <div class="seq-panel active" id="seqPanel_${idx}_0">
          <div class="email-body-box">${escapeHtml(em.body)}</div>
          ${askHtml}
          <div class="email-card-footer">
            <div class="constraints-checklist">
              <span>✓ 3-Sentence Rule</span>
              <span>✓ Isolated Low-Friction Ask</span>
              <span>✓ ${em.word_count} words</span>
            </div>
            <div class="email-footer-actions">
              <button class="btn btn-small" onclick="copyText('${escapeQuotes(em.subject)}')">Copy Subject</button>
              <button class="btn btn-copy" onclick="copyText('${escapeQuotes(em.body)}')">Copy Full Email</button>
              <a href="${mailtoLink}" class="btn btn-small" style="text-decoration:none; display:inline-flex; align-items:center;">Open in Mail Client</a>
              <button class="btn btn-small" style="background:#238636; color:white; border:none;" onclick="sendEmailViaSmtp(${idx}, this)">Send via SMTP (1-Click)</button>
            </div>
          </div>
        </div>
      `;

      // Panels for Follow-Ups
      followUps.forEach((fu, fIdx) => {
        const fuMailto = `mailto:${encodeURIComponent(em.recipient_email)}?subject=${encodeURIComponent(fu.subject)}&body=${encodeURIComponent(fu.body)}`;
        sequencePanelsHtml += `
          <div class="seq-panel" id="seqPanel_${idx}_${fIdx + 1}">
            <div class="follow-up-box">
              <div class="follow-up-meta">
                <span style="color:#58a6ff; font-weight:600;">${escapeHtml(fu.step)}</span>
                <span class="delay-pill">+${fu.delay_days} Days After Previous</span>
              </div>
              <div class="follow-up-subject"><strong>Subject:</strong> ${escapeHtml(fu.subject)}</div>
              <div class="follow-up-body">${escapeHtml(fu.body)}</div>
              <div class="follow-up-actions">
                <button class="btn btn-small" onclick="copyText('${escapeQuotes(fu.subject)}')">Copy Subject</button>
                <button class="btn btn-small" onclick="copyText('${escapeQuotes(fu.body)}')">Copy Body</button>
                <a href="${fuMailto}" class="btn btn-small" style="text-decoration:none; display:inline-flex; align-items:center;">Open in Mail Client</a>
                <button class="btn btn-small" style="background:#238636; color:white; border:none;" onclick="sendCustomFollowUpViaSmtp(${idx}, ${fIdx}, this)">Send Step via SMTP</button>
              </div>
            </div>
          </div>
        `;
      });
    } else {
      sequencePanelsHtml = `
        <div class="email-body-box">${escapeHtml(em.body)}</div>
        ${askHtml}
        <div class="email-card-footer">
          <div class="constraints-checklist">
            <span>✓ 3-Sentence Rule</span>
            <span>✓ ${em.word_count} words</span>
          </div>
          <div class="email-footer-actions">
            <button class="btn btn-small" onclick="copyText('${escapeQuotes(em.subject)}')">Copy Subject</button>
            <button class="btn btn-copy" onclick="copyText('${escapeQuotes(em.body)}')">Copy Full Email</button>
            <a href="${mailtoLink}" class="btn btn-small" style="text-decoration:none; display:inline-flex; align-items:center;">Open in Mail Client</a>
            <button class="btn btn-small" style="background:#238636; color:white; border:none;" onclick="sendEmailViaSmtp(${idx}, this)">Send via SMTP (1-Click)</button>
          </div>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="email-card-header">
        <div class="email-row">
          <span class="email-row-label">FIRM:</span>
          <span class="email-row-val">${escapeHtml(em.firm_name)} (${escapeHtml(em.region)})</span>
        </div>
        <div class="email-row">
          <span class="email-row-label">TO:</span>
          <span class="email-row-val" style="color:#3fb950;">${escapeHtml(em.recipient_email)}</span>
          <span style="color:#8b949e; margin-left: 0.5rem;">[${escapeHtml(em.recipient_name)}]</span>
        </div>
        <div class="email-row">
          <span class="email-row-label">SUBJECT:</span>
          <span class="email-subject-val">${escapeHtml(em.subject)}</span>
        </div>
      </div>

      ${analysisHtml}

      ${sequenceNavHtml}
      ${sequencePanelsHtml}
    `;
    container.appendChild(card);
  });
}

function switchSeqTab(cardIdx, stepIdx) {
  const card = document.getElementById(`emailCard_${cardIdx}`);
  if (!card) return;
  card.querySelectorAll(".seq-tab-btn").forEach(btn => btn.classList.remove("active"));
  card.querySelectorAll(".seq-panel").forEach(p => p.classList.remove("active"));

  const targetBtn = document.getElementById(`tabBtn_${cardIdx}_${stepIdx}`);
  const targetPanel = document.getElementById(`seqPanel_${cardIdx}_${stepIdx}`);
  if (targetBtn) targetBtn.classList.add("active");
  if (targetPanel) targetPanel.classList.add("active");
}

async function sendCustomFollowUpViaSmtp(cardIdx, followUpIdx, btn) {
  if (!currentCampaignData || !currentCampaignData.emails || !currentCampaignData.emails[cardIdx]) return;
  const em = currentCampaignData.emails[cardIdx];
  const fu = em.follow_ups && em.follow_ups[followUpIdx];
  if (!fu) return;

  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Sending...";

  try {
    const resp = await fetch("/api/discovery/send-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipient_email: em.recipient_email,
        recipient_name: em.recipient_name,
        firm_name: em.firm_name,
        subject: fu.subject,
        body: fu.body
      })
    });

    const res = await resp.json();
    if (!resp.ok) {
      throw new Error(res.detail || "Failed to send follow-up email");
    }
    btn.textContent = "✓ Sent";
    btn.style.background = "#238636";
    showToast(`Follow-up sent to ${em.recipient_email}!`);
  } catch (err) {
    console.error("SMTP follow-up dispatch error:", err);
    alert("Follow-up dispatch failed: " + err.message);
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

async function sendEmailViaSmtp(idx, btn) {
  if (!currentCampaignData || !currentCampaignData.emails || !currentCampaignData.emails[idx]) return;
  const em = currentCampaignData.emails[idx];
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Sending...";

  try {
    const resp = await fetch("/api/discovery/send-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipient_email: em.recipient_email,
        recipient_name: em.recipient_name,
        firm_name: em.firm_name,
        subject: em.subject,
        body: em.body
      })
    });

    const res = await resp.json();
    if (!resp.ok) {
      throw new Error(res.detail || "Failed to send email");
    }
    btn.textContent = "✓ Sent (Suppressed from next search)";
    btn.style.background = "#238636";
    showToast(`Email dispatched to ${em.recipient_email}! Added to suppression list.`);
    updateSentSuppressionStats();
  } catch (err) {
    console.error("SMTP dispatch error:", err);
    alert("Email dispatch failed: " + err.message + "\n\nMake sure SMTP_USER and SMTP_PASSWORD are set in your .env file.");
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

async function updateSentSuppressionStats() {
  try {
    const resp = await fetch("/api/discovery/sent-emails");
    if (!resp.ok) return;
    const data = await resp.json();
    const counter = document.getElementById("sentCounter");
    const badge = document.getElementById("contactedCountBadge");
    if (counter) counter.textContent = data.sent_count || 0;
    if (badge) {
      if (data.sent_count > 0) {
        badge.style.display = "inline-block";
        badge.textContent = `${data.sent_count} contacted (suppressed)`;
      } else {
        badge.style.display = "none";
      }
    }
  } catch (e) {
    console.error("Failed fetching sent stats:", e);
  }
}


async function checkSmtpStatus() {
  try {
    const resp = await fetch("/api/health");
    if (!resp.ok) return;
    const data = await resp.json();
    const pill = document.getElementById("smtpStatusPill");
    if (!pill) return;
    if (data.smtp_configured) {
      pill.innerHTML = `<span class="pulse" style="background:#3fb950;"></span> Email: ${escapeHtml(data.smtp_user)}`;
      pill.classList.add("active");
    } else {
      pill.innerHTML = `<span class="dot"></span> Email: Not Configured`;
      pill.classList.remove("active");
    }
  } catch (e) {
    console.error("Health check error:", e);
  }
}


