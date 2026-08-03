function esc(s) {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
}

function shortArticle(article) {
  return (article || "").replace(/^Article\s+/i, "Art. ");
}

const NAV_ITEMS = [
  ["dashboard", "Dashboard"],
  ["gap-report", "Gap Report"],
  ["documents", "Documents"],
  ["assistant", "Assistant"],
  ["drafted-docs", "Drafted Docs"],
];

export function renderShell(state, innerHtml) {
  const profile = state.profile;
  return `
    <aside class="sidebar">
      <div class="brand">
        <h1>Statuta</h1>
        <div class="subtitle">Compliance Copilot</div>
      </div>

      <div>
        <div class="sidebar-section-label">Company profile</div>
        <button class="company-card" data-action="edit-profile" style="all:unset;display:block;cursor:pointer;width:100%;">
          <div class="company-card" style="border:none;padding:0;background:none;">
            <div class="company-name">${esc(profile.name)}</div>
            <div class="company-meta">${esc(profile.sector)} &middot; ${esc(profile.employee_count)} employees</div>
          </div>
        </button>
      </div>

      <nav class="nav">
        ${NAV_ITEMS.map(
          ([id, label]) =>
            `<button class="nav-item ${state.view === id ? "active" : ""}" data-action="nav" data-view="${id}">${label}</button>`
        ).join("")}
      </nav>

      <div class="sidebar-spacer"></div>

      <div>
        <div class="sidebar-section-label">Language</div>
        <div class="lang-toggle">
          <button class="lang-btn ${state.language === "en" ? "active" : ""}" data-action="lang" data-lang="en">EN</button>
          <button class="lang-btn ${state.language === "de" ? "active" : ""}" data-action="lang" data-lang="de">DE</button>
        </div>
      </div>

      <div class="disclaimer-box">
        <span class="dot"></span>
        <span>Proof-of-concept classifier. Not a substitute for legal advice.</span>
      </div>
    </aside>
    <main class="main">${innerHtml}</main>
  `;
}

function pageHeader(title, subtitle, companyName) {
  return `
    <div class="page-header">
      <div>
        <h2>${esc(title)}</h2>
        <div class="page-subtitle">${esc(subtitle)}</div>
      </div>
      <div class="company-tag">${esc(companyName)}</div>
    </div>
  `;
}

function profileEditForm(state) {
  if (!state.editingProfile) return "";
  const p = state.profile;
  return `
    <div class="card" style="margin-bottom:20px;">
      <div class="section-title" style="margin-top:0;">Edit company profile</div>
      <form data-form="profile" style="display:flex;flex-direction:column;gap:10px;max-width:520px;">
        <label>Name<input name="name" value="${esc(p.name)}" style="width:100%;padding:8px;margin-top:4px;border:1px solid var(--color-card-border);border-radius:6px;"/></label>
        <label>Sector<input name="sector" value="${esc(p.sector)}" style="width:100%;padding:8px;margin-top:4px;border:1px solid var(--color-card-border);border-radius:6px;"/></label>
        <label>Employees<input name="employee_count" type="number" value="${esc(p.employee_count)}" style="width:100%;padding:8px;margin-top:4px;border:1px solid var(--color-card-border);border-radius:6px;"/></label>
        <label><input name="uses_ai_systems" type="checkbox" ${p.uses_ai_systems ? "checked" : ""}/> Uses AI systems</label>
        <label>AI system description<input name="ai_system_descriptions" value="${esc(p.ai_system_descriptions[0] || "")}" style="width:100%;padding:8px;margin-top:4px;border:1px solid var(--color-card-border);border-radius:6px;"/></label>
        <label>Notes<textarea name="notes" rows="2" style="width:100%;padding:8px;margin-top:4px;border:1px solid var(--color-card-border);border-radius:6px;">${esc(p.notes)}</textarea></label>
        <div style="display:flex;gap:10px;margin-top:6px;">
          <button type="submit" class="btn-primary">Save &amp; regenerate report</button>
          <button type="button" data-action="cancel-edit-profile" style="background:none;border:1px solid var(--color-card-border);border-radius:6px;padding:10px 16px;cursor:pointer;">Cancel</button>
        </div>
      </form>
    </div>
  `;
}

function computeRegStats(assessments, regulation) {
  const rows = assessments.filter((a) => a.regulation === regulation);
  const applicable = rows.filter((a) => a.verdict === "applicable");
  const met = applicable.filter((a) => a.evidence_status === "evidence_found").length;
  const gap = applicable.filter((a) => a.evidence_status === "gap").length;
  const review = applicable.filter((a) => a.evidence_status === "partial_match").length;
  return { total: applicable.length, met, gap, review };
}

function regCard(regulation, stats) {
  const total = stats.total || 1;
  return `
    <div class="card reg-card">
      <h3>${esc(regulation)}</h3>
      <div class="reg-bar">
        <span style="width:${(stats.met / total) * 100}%;background:var(--color-green);"></span>
        <span style="width:${(stats.gap / total) * 100}%;background:var(--color-accent);"></span>
        <span style="width:${(stats.review / total) * 100}%;background:var(--color-amber);"></span>
      </div>
      <div class="reg-stat-row" style="font-weight:600;">
        <span>Applicable</span><span>${stats.total}</span>
      </div>
      <div class="reg-stat-row">
        <span class="dot-label"><span class="stat-dot" style="background:var(--color-green);"></span>Met</span><span>${stats.met}</span>
      </div>
      <div class="reg-stat-row">
        <span class="dot-label"><span class="stat-dot" style="background:var(--color-accent);"></span>Gap</span><span>${stats.gap}</span>
      </div>
      <div class="reg-stat-row">
        <span class="dot-label"><span class="stat-dot" style="background:var(--color-amber);"></span>Needs review</span><span>${stats.review}</span>
      </div>
    </div>
  `;
}

export function renderDashboard(state) {
  const p = state.profile;
  const report = state.gapReport;

  let regGrid = "";
  let actionList = "";

  if (report) {
    const regs = [...new Set(report.assessments.map((a) => a.regulation))];
    regGrid = `<div class="reg-grid">${regs.map((r) => regCard(r, computeRegStats(report.assessments, r))).join("")}</div>`;

    const actionable = report.assessments.filter(
      (a) => a.verdict === "applicable" && a.evidence_status !== "evidence_found"
    );
    actionList = actionable.length
      ? `<div class="action-list">${actionable
          .map((a) => {
            const badge =
              a.evidence_status === "gap"
                ? `<span class="badge badge-needs-review">Gap</span>`
                : `<span class="badge badge-needs-review">Needs human review</span>`;
            return `
              <div class="action-item">
                <span class="action-text">${
                  a.evidence_status === "gap" ? "Provide evidence for" : "Review evidence for"
                } ${esc(shortArticle(a.article))}</span>
                <span class="action-right">
                  <span class="action-reg">${esc(a.regulation)}</span>
                  ${badge}
                </span>
              </div>`;
          })
          .join("")}</div>`
      : `<div class="loading-row">No outstanding actions — every applicable clause has supporting evidence.</div>`;
  } else {
    regGrid = `<div class="card"><p style="margin:0;">No gap report yet.</p><button class="btn-primary" style="margin-top:14px;" data-action="generate-report">Generate gap report</button></div>`;
  }

  return renderShell(
    state,
    `
    ${pageHeader("Dashboard", "Compliance posture across AI Act, NIS2 and CSRD", p.name)}
    ${profileEditForm(state)}
    <div class="card profile-card">
      <div class="profile-title">${esc(p.name)}</div>
      <div class="profile-meta">${esc(p.sector)} &middot; ${esc(p.employee_count)} employees</div>
      <hr/>
      <p>${esc(p.notes || (p.ai_system_descriptions[0] || "No AI systems currently in use."))}</p>
    </div>

    <div class="section-title">Compliance status by regulation</div>
    ${regGrid}

    <div class="section-title">Prioritized action list</div>
    ${actionList}
  `
  );
}

export function renderGapReport(state) {
  const p = state.profile;
  const report = state.gapReport;
  const filter = state.gapReportFilter;

  let body;
  if (state.gapReportLoading) {
    body = `<div class="loading-row">Retrieving regulation text &rarr; classifying relevance &rarr; matching evidence&hellip;</div>`;
  } else if (!report) {
    body = `<div class="card"><p style="margin:0 0 14px 0;">No gap report yet for this profile.</p><button class="btn-primary" data-action="generate-report">Generate gap report</button></div>`;
  } else {
    const regs = ["All", ...new Set(report.assessments.map((a) => a.regulation))];
    const filterBar = `<div class="filter-bar">${regs
      .map(
        (r) =>
          `<button class="filter-btn ${filter === r ? "active" : ""}" data-action="filter-gap" data-filter="${esc(r)}">${esc(r)}</button>`
      )
      .join("")}</div>`;

    const rows = report.assessments.filter((a) => filter === "All" || a.regulation === filter);

    const rowsHtml = rows
      .map((a) => {
        const verdictBadge =
          a.verdict === "applicable"
            ? `<span class="badge badge-applicable">Applicable</span>`
            : a.verdict === "not_applicable"
            ? `<span class="badge badge-not-applicable">Not applicable</span>`
            : `<span class="badge badge-needs-review">Needs human review</span>`;

        let right;
        if (a.verdict === "applicable") {
          const statusMap = {
            evidence_found: ["found", "Evidence found"],
            partial_match: ["partial", "Partial match"],
            gap: ["gap", "No evidence — gap"],
          };
          const [cls, label] = statusMap[a.evidence_status] || ["gap", "Not yet checked"];
          const quote =
            a.evidence_excerpt && a.evidence_source
              ? `<div class="evidence-quote">&ldquo;${esc(a.evidence_source)}&rdquo; — "${esc(a.evidence_excerpt)}&hellip;"</div>`
              : "";
          const note =
            a.evidence_status === "gap"
              ? "No matching evidence found in your uploaded documents."
              : a.evidence_status === "partial_match"
              ? "Partial match — verify this covers the requirement in full."
              : "Matched evidence covers this clause.";
          right = `
            <div class="evidence-status ${cls}">${label}</div>
            ${quote}
            <div class="evidence-note">${note}</div>
          `;
        } else {
          right = `<div class="evidence-note">${esc(a.rationale)}</div>`;
        }

        return `
          <div class="gap-row">
            <div class="gap-left">
              <div class="gap-left-top">
                <span class="chip">§ ${esc(shortArticle(a.article))}</span>
                <span class="gap-reg-label">${esc(a.regulation)}</span>
              </div>
              <h4>${esc(a.article_title || a.article)}</h4>
              ${verdictBadge}
            </div>
            <div class="gap-right">${right}</div>
          </div>
        `;
      })
      .join("");

    body = `
      <div class="context-note">Detailed example shown for ${esc(p.name)}</div>
      ${filterBar}
      ${rowsHtml || `<div class="loading-row">No clauses match this filter.</div>`}
    `;
  }

  return renderShell(
    state,
    `
    ${pageHeader("Gap Report", "Regulation clauses matched against your policy library", p.name)}
    ${body}
  `
  );
}

export function renderDocuments(state) {
  const p = state.profile;
  const docsHtml = state.documents
    .map((d) => {
      const stageWidth = (stage) => (d.stage > stage ? 100 : d.stage === stage ? d.progress : 0);
      const stages = ["Parsing", "Chunking", "Embedding", "Classifying"];
      const bars = stages
        .map((label, i) => {
          const active = d.stage === i && d.status === "in_progress";
          return `
            <div class="pipeline-step">
              <div class="pipeline-bar ${active ? "active" : ""}"><span style="width:${stageWidth(i)}%;"></span></div>
              <label>${label}</label>
            </div>
          `;
        })
        .join("");
      const statusLabel =
        d.status === "error"
          ? `<span class="doc-status status-parsing" style="color:var(--color-accent);">Failed</span>`
          : d.status === "done"
          ? `<span class="doc-status status-done">Classified</span>`
          : `<span class="doc-status status-${stages[d.stage].toLowerCase()}">${stages[d.stage]}&hellip;</span>`;
      return `
        <div class="doc-card">
          <div class="doc-header">
            <span class="doc-name">${esc(d.name)}</span>
            ${statusLabel}
          </div>
          <div class="pipeline">${bars}</div>
          ${d.status === "error" ? `<div class="error-row" style="margin-top:10px;">${esc(d.error)}</div>` : ""}
        </div>
      `;
    })
    .join("");

  return renderShell(
    state,
    `
    ${pageHeader("Document Ingestion", "Upload policies to update your evidence base", p.name)}
    <div class="dropzone" data-action="dropzone">
      <div class="dz-title">Drop company policy documents here</div>
      <div class="dz-sub">PDF, DOCX, or plain text — or click to choose a file</div>
      <input type="file" id="file-input" style="display:none;" accept=".pdf,.docx,.txt"/>
    </div>
    ${docsHtml}
  `
  );
}

export function renderAssistant(state) {
  const p = state.profile;
  const log = state.chatMessages
    .map((m) => {
      if (m.role === "user") {
        return `
          <div class="chat-turn-user">
            <div class="who">You</div>
            <div class="chat-bubble-user">${esc(m.text)}</div>
          </div>
        `;
      }
      const chips = (m.citations || [])
        .map((c) => `<span class="chip">§ ${esc(shortArticle(c.article))}</span>`)
        .join(" ");
      return `
        <div class="chat-turn-assistant">
          <div class="who">Statuta</div>
          <div class="chat-bubble-assistant">${esc(m.text)}<div style="margin-top:8px;">${chips}</div></div>
        </div>
      `;
    })
    .join("");

  return renderShell(
    state,
    `
    ${pageHeader("Assistant", "Ask whether an obligation applies — every answer is cited", p.name)}
    <div class="assistant-warning">AI-generated answers are a proof of concept — not legal advice. Always confirm with counsel before acting.</div>
    <div class="chat-log">${log || `<div class="loading-row">Ask a question to get started.</div>`}</div>
    <div class="chat-input-row">
      <input type="text" id="chat-input" placeholder="Ask a compliance question&hellip;" ${state.chatLoading ? "disabled" : ""}/>
      <button class="btn-primary" data-action="send-chat" ${state.chatLoading ? "disabled" : ""}>${state.chatLoading ? "Thinking…" : "Send"}</button>
    </div>
  `
  );
}

export function renderDraftedDocs(state) {
  const p = state.profile;
  const report = state.gapReport;
  const draft = state.draftedDoc;

  let body;
  if (!report) {
    body = `<div class="card"><p style="margin:0 0 14px 0;">Generate a gap report first — drafted documentation is built from its findings.</p><button class="btn-primary" data-action="generate-report">Generate gap report</button></div>`;
  } else if (state.draftedDocLoading || !draft) {
    body = `<div class="loading-row">Drafting Annex IV skeleton from gap-report findings&hellip;</div>`;
  } else {
    const reviewedCount = draft.sections.filter((s) => s.reviewed).length;
    body = `
      <div class="draft-status-bar">
        <span>&#9632; Auto-drafted — needs human review before submission</span>
        <span class="count">${reviewedCount} of ${draft.sections.length} sections reviewed</span>
      </div>
      <div class="draft-doc-title">${esc(draft.title)}</div>
      ${draft.sections
        .map(
          (s) => `
        <div class="draft-section">
          <div class="draft-section-head">
            <h4>${s.number}. ${esc(s.title)}</h4>
            <div class="draft-section-right">
              <span class="chip">§ ${esc(shortArticle(s.citation))}</span>
              <button type="button" class="badge ${s.reviewed ? "badge-reviewed" : "badge-unreviewed"}" style="border:none;" data-action="toggle-section" data-section="${s.number}">${s.reviewed ? "Reviewed ✓" : "Mark reviewed"}</button>
            </div>
          </div>
          <p>${esc(s.body)}</p>
        </div>
      `
        )
        .join("")}
      <a class="btn-primary" style="display:inline-block;text-decoration:none;margin-top:6px;" href="${state.annexIvDownloadUrl}" target="_blank" rel="noopener">Download .docx</a>
    `;
  }

  return renderShell(
    state,
    `
    ${pageHeader("Drafted Documentation", "Auto-generated skeleton, pending human review", p.name)}
    ${body}
  `
  );
}

export function render(state) {
  switch (state.view) {
    case "gap-report":
      return renderGapReport(state);
    case "documents":
      return renderDocuments(state);
    case "assistant":
      return renderAssistant(state);
    case "drafted-docs":
      return renderDraftedDocs(state);
    default:
      return renderDashboard(state);
  }
}
