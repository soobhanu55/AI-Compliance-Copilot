import { render } from "./render.js";
import {
  sendChatMessage,
  uploadDocument,
  createGapReport,
  getDraftSections,
  downloadAnnexIvUrl,
} from "./api.js";

const state = {
  view: "dashboard",
  language: "en",
  userId: "demo-user",
  editingProfile: false,
  profile: {
    name: "RouteWise Logistics Software GmbH",
    sector: "Logistics software",
    employee_count: 45,
    uses_ai_systems: true,
    ai_system_descriptions: ["Machine-learning route optimization engine used by dispatch to assign delivery routes"],
    third_party_vendors: ["AWS (hosting)"],
    notes: "",
  },
  gapReport: null,
  gapReportLoading: false,
  gapReportFilter: "All",
  documents: [],
  chatMessages: [],
  chatLoading: false,
  draftedDoc: null,
  draftedDocLoading: false,
  annexIvDownloadUrl: "",
};

const root = document.getElementById("app");

function rerender() {
  root.innerHTML = render(state);
}

async function ensureGapReport() {
  state.gapReportLoading = true;
  rerender();
  try {
    const report = await createGapReport(state.userId, state.profile);
    state.gapReport = report;
  } catch (err) {
    console.error(err);
    alert(`Could not generate gap report: ${err.message}`);
  } finally {
    state.gapReportLoading = false;
    rerender();
  }
}

async function ensureDraftedDoc() {
  if (!state.gapReport) return;
  state.draftedDocLoading = true;
  rerender();
  try {
    const data = await getDraftSections(state.gapReport.id);
    state.draftedDoc = {
      title: data.title,
      sections: data.sections.map((s) => ({ ...s, reviewed: false })),
    };
    state.annexIvDownloadUrl = downloadAnnexIvUrl(state.gapReport.id);
  } catch (err) {
    console.error(err);
    alert(`Could not load drafted document: ${err.message}`);
  } finally {
    state.draftedDocLoading = false;
    rerender();
  }
}

function stageLabel(stage) {
  return ["Parsing", "Chunking", "Embedding", "Classifying"][stage];
}

async function handleFileUpload(file) {
  const doc = { name: file.name, status: "in_progress", stage: 0, progress: 0, error: null };
  state.documents.unshift(doc);
  rerender();

  // Cosmetic staged animation timed to the real upload — the actual work happens in one
  // fetch() call; this just gives the user something to watch instead of a blank spinner.
  const tick = setInterval(() => {
    if (doc.status !== "in_progress") return clearInterval(tick);
    doc.progress += 18;
    if (doc.progress >= 100 && doc.stage < 3) {
      doc.stage += 1;
      doc.progress = 0;
    } else if (doc.progress >= 100) {
      doc.progress = 95; // hold until the real response lands
    }
    rerender();
  }, 220);

  try {
    await uploadDocument(state.userId, "company_policy", file);
    clearInterval(tick);
    doc.status = "done";
    doc.stage = 3;
    doc.progress = 100;
  } catch (err) {
    clearInterval(tick);
    doc.status = "error";
    doc.error = err.message;
  }
  rerender();
}

async function handleSendChat(text) {
  state.chatMessages.push({ role: "user", text });
  state.chatLoading = true;
  rerender();
  try {
    const res = await sendChatMessage(state.userId, text, state.language);
    state.chatMessages.push({ role: "assistant", text: res.answer, citations: res.citations });
  } catch (err) {
    state.chatMessages.push({ role: "assistant", text: `Error: ${err.message}`, citations: [] });
  } finally {
    state.chatLoading = false;
    rerender();
  }
}

root.addEventListener("click", async (e) => {
  const el = e.target.closest("[data-action]");
  if (!el) return;
  const action = el.dataset.action;

  if (action === "nav") {
    state.view = el.dataset.view;
    rerender();
    if (state.view === "gap-report" && !state.gapReport && !state.gapReportLoading) {
      await ensureGapReport();
    }
    if (state.view === "drafted-docs" && state.gapReport && !state.draftedDoc && !state.draftedDocLoading) {
      await ensureDraftedDoc();
    }
    return;
  }

  if (action === "lang") {
    state.language = el.dataset.lang;
    rerender();
    return;
  }

  if (action === "edit-profile") {
    state.editingProfile = true;
    rerender();
    return;
  }

  if (action === "cancel-edit-profile") {
    state.editingProfile = false;
    rerender();
    return;
  }

  if (action === "generate-report") {
    await ensureGapReport();
    if (state.view === "drafted-docs") await ensureDraftedDoc();
    return;
  }

  if (action === "filter-gap") {
    state.gapReportFilter = el.dataset.filter;
    rerender();
    return;
  }

  if (action === "toggle-section") {
    const num = Number(el.dataset.section);
    const section = state.draftedDoc.sections.find((s) => s.number === num);
    section.reviewed = !section.reviewed;
    rerender();
    return;
  }

  if (action === "dropzone") {
    document.getElementById("file-input")?.click();
    return;
  }

  if (action === "send-chat") {
    const input = document.getElementById("chat-input");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    await handleSendChat(text);
    return;
  }
});

root.addEventListener("submit", async (e) => {
  if (e.target.dataset.form === "profile") {
    e.preventDefault();
    const formData = new FormData(e.target);
    state.profile = {
      ...state.profile,
      name: formData.get("name"),
      sector: formData.get("sector"),
      employee_count: Number(formData.get("employee_count")),
      uses_ai_systems: formData.get("uses_ai_systems") === "on",
      ai_system_descriptions: [formData.get("ai_system_descriptions")].filter(Boolean),
      notes: formData.get("notes"),
    };
    state.editingProfile = false;
    state.gapReport = null;
    state.draftedDoc = null;
    rerender();
    if (state.view === "dashboard" || state.view === "gap-report") {
      await ensureGapReport();
    }
  }
});

root.addEventListener("change", (e) => {
  if (e.target.id === "file-input" && e.target.files.length) {
    handleFileUpload(e.target.files[0]);
    e.target.value = "";
  }
});

root.addEventListener("keydown", (e) => {
  if (e.target.id === "chat-input" && e.key === "Enter") {
    root.querySelector('[data-action="send-chat"]')?.click();
  }
});

root.addEventListener("dragover", (e) => {
  const dz = e.target.closest("[data-action='dropzone']");
  if (dz) {
    e.preventDefault();
    dz.classList.add("dragover");
  }
});

root.addEventListener("dragleave", (e) => {
  const dz = e.target.closest("[data-action='dropzone']");
  if (dz) dz.classList.remove("dragover");
});

root.addEventListener("drop", (e) => {
  const dz = e.target.closest("[data-action='dropzone']");
  if (dz) {
    e.preventDefault();
    dz.classList.remove("dragover");
    if (e.dataTransfer.files.length) handleFileUpload(e.dataTransfer.files[0]);
  }
});

rerender();
