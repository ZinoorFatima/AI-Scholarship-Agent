"use strict";

// Minimal client for the AI Scholarship Agent. No framework, no build step.

const $ = (id) => document.getElementById(id);

function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
const list = (arr) => `<ul>${(arr || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;

function setStatus(id, msg, isError = false) {
  const el = $(id);
  if (!msg) { el.classList.add("hidden"); return; }
  el.textContent = msg;
  el.classList.remove("hidden");
  el.classList.toggle("error", isError);
}

async function postJson(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

// ====================================================================== //
// File upload → text extraction
// ====================================================================== //
document.querySelectorAll(".upload-btn").forEach((btn) => {
  const input = $(btn.dataset.input);
  btn.addEventListener("click", () => input.click());
  input.addEventListener("change", async () => {
    const file = input.files[0];
    if (!file) return;
    const nameEl = $(btn.dataset.input + "-name");
    nameEl.textContent = `Reading ${file.name}…`;
    const fd = new FormData();
    fd.append("file", file);
    try {
      const res = await fetch("/api/extract", { method: "POST", body: fd });
      if (!res.ok) {
        let detail = res.statusText;
        try { detail = (await res.json()).detail || detail; } catch (_) {}
        throw new Error(detail);
      }
      const data = await res.json();
      $(btn.dataset.target).value = data.text;
      nameEl.textContent = `✓ ${file.name} (${data.text.length} chars)`;
    } catch (err) {
      nameEl.textContent = `✗ ${err.message}`;
    }
  });
});

// ====================================================================== //
// Scholarship discovery (search + recommend)
// ====================================================================== //
function renderScholarships(scholarships) {
  if (!scholarships || !scholarships.length) {
    $("discover-results").innerHTML = '<p class="muted">No scholarships found. Try a broader query.</p>';
    return;
  }
  $("discover-results").innerHTML = scholarships.map((s, i) => {
    const meta = [
      s.provider ? `<span class="chip">${esc(s.provider)}</span>` : "",
      s.amount ? `<span class="chip good">${esc(s.amount)}</span>` : "",
      s.deadline ? `<span class="chip warn">Deadline: ${esc(s.deadline)}</span>` : "",
    ].join("");
    return `
      <div class="scholarship">
        <div class="sch-head">
          <h3>${esc(s.name)}</h3>
          <button class="use-btn" data-i="${i}">Use for application →</button>
        </div>
        <div class="chips">${meta}</div>
        ${s.description ? `<p>${esc(s.description)}</p>` : ""}
        ${s.eligibility ? `<p class="muted"><b>Eligibility:</b> ${esc(s.eligibility)}</p>` : ""}
        ${s.fit_reason ? `<p class="fit"><b>Why it fits you:</b> ${esc(s.fit_reason)}</p>` : ""}
        ${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">Official page ↗</a>` : ""}
      </div>`;
  }).join("");

  // "Use for application" fills the target-scholarship field.
  $("discover-results").querySelectorAll(".use-btn").forEach((b) => {
    b.addEventListener("click", () => {
      const s = scholarships[Number(b.dataset.i)];
      const parts = [
        s.name, s.provider ? `Provider: ${s.provider}` : "",
        s.description || "", s.eligibility ? `Eligibility: ${s.eligibility}` : "",
        s.amount ? `Amount: ${s.amount}` : "", s.deadline ? `Deadline: ${s.deadline}` : "",
        s.url ? `Link: ${s.url}` : "",
      ].filter(Boolean);
      $("scholarship").value = parts.join("\n");
      $("scholarship").scrollIntoView({ behavior: "smooth", block: "center" });
      $("scholarship").classList.add("flash");
      setTimeout(() => $("scholarship").classList.remove("flash"), 1200);
    });
  });
}

async function discover(btn, label, fn) {
  const original = btn.textContent;
  btn.disabled = true;
  btn.textContent = label;
  setStatus("discover-status", "");
  try {
    const data = await fn();
    renderScholarships(data.scholarships);
  } catch (err) {
    setStatus("discover-status", err.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = original;
  }
}

$("btn-search").addEventListener("click", () => {
  const query = $("search-query").value.trim();
  if (!query) { setStatus("discover-status", "Type what you're looking for.", true); return; }
  discover($("btn-search"), "Searching…", () =>
    postJson("/api/search-scholarships", { query }));
});

$("search-query").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("btn-search").click();
});

$("btn-recommend").addEventListener("click", () => {
  const cv = $("cv").value.trim();
  if (!cv) { setStatus("discover-status", "Add or upload your CV first.", true); return; }
  discover($("btn-recommend"), "Matching to your CV…", () =>
    postJson("/api/recommend-scholarships", { cv }));
});

// ====================================================================== //
// Application analysis (6-agent pipeline)
// ====================================================================== //
function renderEligibility(e) {
  const badge = e.eligible
    ? '<span class="badge good">Eligible</span>'
    : '<span class="badge bad">Not eligible</span>';
  const crit = (e.criteria || []).map((c) => `
    <li><span class="${c.met ? "tick" : "cross"}">${c.met ? "✓" : "✗"}</span>
        <span><b>${esc(c.requirement)}</b> — ${esc(c.evidence)}</span></li>`).join("");
  $("r-eligibility").innerHTML =
    `<h2>1. Eligibility ${badge}</h2><ul class="crit">${crit}</ul>
     <div class="summary">${esc(e.summary)}</div>`;
}

function renderProfile(p) {
  $("r-profile").innerHTML = `<h2>2. Candidate profile</h2>
    <div class="summary">${esc(p.summary)}</div>
    <div class="cols">
      <div><h3>Academic strengths</h3>${list(p.academic_strengths)}</div>
      <div><h3>Research</h3>${list(p.research_experience)}</div>
      <div><h3>Projects</h3>${list(p.projects)}</div>
      <div><h3>Leadership</h3>${list(p.leadership_activities)}</div>
      <div><h3>Awards</h3>${list(p.awards)}</div>
    </div>`;
}

function renderGaps(g) {
  $("r-gaps").innerHTML = `<h2>3. Gap analysis</h2>
    <div class="cols">
      <div><h3 class="tick">Strengths</h3>${list(g.strengths)}</div>
      <div><h3 class="cross">Weaknesses</h3>${list(g.weaknesses)}</div>
    </div>
    <h3>Recommendations</h3>${list(g.recommendations)}`;
}

function renderEssays(es) {
  const items = (es.essays || []).map((x) => `
    <div class="essay">
      <h3>${esc(x.title)}</h3>
      <p class="prompt">${esc(x.prompt)}</p>
      <div class="content">${esc(x.content)}</div>
    </div>`).join("");
  $("r-essays").innerHTML = `<h2>4. Drafted essays</h2>${items}`;
}

function renderReview(r) {
  const rows = (r.scores || []).map((s) => `
    <div class="essay">
      <h3>${esc(s.essay_title)}</h3>
      <div class="scorebar">
        <span class="score">Leadership <b>${s.leadership}/10</b></span>
        <span class="score">Impact <b>${s.impact}/10</b></span>
        <span class="score">Clarity <b>${s.clarity}/10</b></span>
      </div>
      ${list(s.recommendations)}
    </div>`).join("");
  $("r-review").innerHTML =
    `<h2>5. Review</h2>${rows}<div class="summary">${esc(r.overall_feedback)}</div>`;
}

function renderReadiness(rd) {
  const badge = rd.ready_to_submit
    ? '<span class="badge good">Ready to submit</span>'
    : '<span class="badge bad">Not ready</span>';
  const items = (rd.checklist || []).map((c) => `
    <li><span class="${c.complete ? "tick" : "cross"}">${c.complete ? "✓" : "✗"}</span>
        <span><b>${esc(c.item)}</b>${c.note ? " — " + esc(c.note) : ""}</span></li>`).join("");
  $("r-readiness").innerHTML =
    `<h2>6. Submission readiness ${badge}</h2><ul class="crit">${items}</ul>
     <div class="summary">${esc(rd.summary)}</div>`;
}

$("btn-analyze").addEventListener("click", async (ev) => {
  const btn = ev.target;
  const applicant = {
    cv: $("cv").value.trim(),
    transcript: $("transcript").value.trim(),
    achievements: $("achievements").value.trim(),
    target_scholarship: $("scholarship").value.trim(),
  };
  if (!applicant.cv || !applicant.target_scholarship) {
    setStatus("status", "Please provide at least your CV and a target scholarship.", true);
    return;
  }
  btn.disabled = true;
  btn.textContent = "Analyzing… (6 agents, ~30–60s)";
  setStatus("status", "");
  try {
    const run = await postJson("/api/analyze", applicant);
    renderEligibility(run.eligibility);
    renderProfile(run.profile);
    renderGaps(run.gaps);
    renderEssays(run.essays);
    renderReview(run.review);
    renderReadiness(run.readiness);
    $("input-card").classList.add("hidden");
    $("results").classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (err) {
    setStatus("status", err.message, true);
  } finally {
    btn.disabled = false;
    btn.textContent = "Analyze application →";
  }
});

$("btn-restart").addEventListener("click", () => {
  $("results").classList.add("hidden");
  $("input-card").classList.remove("hidden");
  setStatus("status", "");
  window.scrollTo({ top: 0, behavior: "smooth" });
});
