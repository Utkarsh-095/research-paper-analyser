/**
 * Research Paper RAG – Frontend Application
 */

const API_BASE = "http://localhost:8000/api";

// ─────────────────────── state ───────────────────────
let currentPaperId = null;
let papers = [];

// ─────────────────────── DOM refs ────────────────────
const fileUpload       = document.getElementById("file-upload");
const uploadProgress   = document.getElementById("upload-progress");
const progressFill     = document.querySelector(".progress-fill");
const progressText     = document.querySelector(".progress-text");
const papersContainer  = document.getElementById("papers-container");
const emptyState       = document.getElementById("empty-state");
const paperView        = document.getElementById("paper-view");
const paperTitle       = document.getElementById("paper-title");
const paperMeta        = document.getElementById("paper-meta");
const summaryContent   = document.getElementById("summary-content");
const findingsContent  = document.getElementById("findings-content");
const chatContainer    = document.getElementById("chat-container");
const questionInput    = document.getElementById("question-input");
const askBtn           = document.getElementById("ask-btn");

// ─────────────────────── init ────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadPapers();
    setupEventListeners();
});

function setupEventListeners() {
    fileUpload.addEventListener("change", handleFileUpload);
    askBtn.addEventListener("click", handleAskQuestion);
    questionInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleAskQuestion(); }
    });

    document.querySelectorAll(".tab").forEach((tab) => {
        tab.addEventListener("click", () => switchTab(tab.dataset.tab));
    });
}

// ─────────────────────── papers ──────────────────────

async function loadPapers() {
    try {
        const res = await fetch(`${API_BASE}/papers/`);
        papers = await res.json();
        renderPapersList();
    } catch (err) {
        console.error("Failed to load papers:", err);
    }
}

function renderPapersList() {
    if (!papers.length) {
        papersContainer.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No papers uploaded yet</p>';
        return;
    }
    papersContainer.innerHTML = papers.map((p) => `
        <div class="paper-item ${p.id === currentPaperId ? 'active' : ''}"
             onclick="selectPaper(${p.id})">
            <i class="fas fa-file-pdf paper-item-icon"></i>
            <div class="paper-item-info">
                <div class="paper-item-title" title="${escapeHtml(p.title)}">${escapeHtml(p.title)}</div>
                <div class="paper-item-meta">${p.num_pages} pages · ${formatBytes(p.file_size)}</div>
            </div>
            <button class="paper-item-delete" onclick="event.stopPropagation(); deletePaper(${p.id})"
                    title="Delete paper">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `).join("");
}

// ─────────────────────── upload ──────────────────────

async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    uploadProgress.classList.remove("hidden");
    progressFill.style.width = "10%";
    progressText.textContent = "Uploading…";

    const formData = new FormData();
    formData.append("file", file);

    try {
        progressFill.style.width = "30%";
        progressText.textContent = "Processing PDF…";

        const res = await fetch(`${API_BASE}/papers/upload`, { method: "POST", body: formData });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Upload failed");
        }

        progressFill.style.width = "90%";
        progressText.textContent = "Finalizing…";

        const paper = await res.json();

        progressFill.style.width = "100%";
        progressText.textContent = "Done!";

        setTimeout(() => {
            uploadProgress.classList.add("hidden");
            progressFill.style.width = "0%";
        }, 1500);

        await loadPapers();
        selectPaper(paper.id);
    } catch (err) {
        progressText.textContent = `Error: ${err.message}`;
        progressFill.style.background = "var(--danger)";
        setTimeout(() => {
            uploadProgress.classList.add("hidden");
            progressFill.style.width = "0%";
            progressFill.style.background = "";
        }, 3000);
    }

    fileUpload.value = "";
}

// ─────────────────────── select / delete ─────────────

async function selectPaper(id) {
    currentPaperId = id;
    const paper = papers.find((p) => p.id === id);
    if (!paper) return;

    emptyState.classList.add("hidden");
    paperView.classList.remove("hidden");

    paperTitle.textContent = paper.title;
    paperMeta.innerHTML = `
        <span><i class="fas fa-file"></i> ${paper.num_pages} pages</span>
        <span><i class="fas fa-puzzle-piece"></i> ${paper.num_chunks} chunks</span>
        <span><i class="fas fa-hdd"></i> ${formatBytes(paper.file_size)}</span>
        <span><i class="fas fa-calendar"></i> ${new Date(paper.upload_date).toLocaleDateString()}</span>
    `;

    renderSummary(paper);
    renderFindings(paper);
    loadChatHistory(id);
    renderPapersList();
    switchTab("summary");
}

async function deletePaper(id) {
    if (!confirm("Delete this paper and all its data?")) return;
    try {
        await fetch(`${API_BASE}/papers/${id}`, { method: "DELETE" });
        if (currentPaperId === id) {
            currentPaperId = null;
            paperView.classList.add("hidden");
            emptyState.classList.remove("hidden");
        }
        await loadPapers();
    } catch (err) {
        console.error("Delete failed:", err);
    }
}

// ─────────────────────── summary ─────────────────────

function renderSummary(paper) {
    if (!paper.summary) {
        summaryContent.innerHTML = '<p style="color:var(--text-muted)">No summary available.</p>';
        return;
    }
    const paragraphs = paper.summary.split("\n").filter(Boolean);
    summaryContent.innerHTML = `
        <h3>📄 Paper Summary</h3>
        ${paragraphs.map((p) => `<p>${escapeHtml(p)}</p>`).join("")}
    `;
}

function renderFindings(paper) {
    if (!paper.key_findings) {
        findingsContent.innerHTML = '<p style="color:var(--text-muted)">No key findings extracted.</p>';
        return;
    }
    const items = paper.key_findings.split("\n").filter((l) => l.trim().startsWith("-"));
    if (!items.length) {
        findingsContent.innerHTML = `<p>${escapeHtml(paper.key_findings)}</p>`;
        return;
    }
    findingsContent.innerHTML = items.map((item) => `
        <div class="finding-item">
            <div class="finding-bullet"></div>
            <div class="finding-text">${escapeHtml(item.replace(/^-\s*/, ""))}</div>
        </div>
    `).join("");
}

// ─────────────────────── Q&A ─────────────────────────

async function handleAskQuestion() {
    const question = questionInput.value.trim();
    if (!question || !currentPaperId) return;

    addChatMessage("user", question);
    questionInput.value = "";
    askBtn.disabled = true;

    const loadingId = addLoadingMessage();

    try {
        const res = await fetch(`${API_BASE}/qa/ask`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ paper_id: currentPaperId, question, include_sources: true }),
        });

        removeLoadingMessage(loadingId);

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Failed to get answer");
        }

        const data = await res.json();
        addChatMessage("assistant", data.answer, data.sources, data.confidence);
    } catch (err) {
        removeLoadingMessage(loadingId);
        addChatMessage("assistant", `Sorry, an error occurred: ${err.message}`);
    }

    askBtn.disabled = false;
    questionInput.focus();
}

async function loadChatHistory(paperId) {
    chatContainer.innerHTML = "";
    try {
        const res = await fetch(`${API_BASE}/qa/history/${paperId}`);
        const history = await res.json();
        history.reverse().forEach((item) => {
            addChatMessage("user", item.question);
            let sources = [];
            try { sources = JSON.parse(item.sources); } catch {}
            addChatMessage("assistant", item.answer, sources, item.confidence);
        });
    } catch {}
}

// ─────────────────────── chat helpers ────────────────

function addChatMessage(role, text, sources = [], confidence = 0) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `chat-message ${role}`;

    const icon = role === "user" ? "fa-user" : "fa-robot";
    let sourcesHtml = "";

    if (sources.length && role === "assistant") {
        sourcesHtml = `
            <div class="chat-sources">
                <div class="chat-sources-title">Sources</div>
                ${sources.map((s, i) => `
                    <div class="source-item">
                        <span class="source-badge">Chunk ${s.chunk_index} · ${(s.similarity * 100).toFixed(1)}%</span>
                        <p>${escapeHtml(s.text)}</p>
                    </div>
                `).join("")}
                <div class="confidence-bar">
                    Confidence:
                    <div class="confidence-fill" style="background:${confidenceColor(confidence)};width:${confidence * 100}%"></div>
                    ${(confidence * 100).toFixed(1)}%
                </div>
            </div>
        `;
    }

    msgDiv.innerHTML = `
        <div class="chat-avatar"><i class="fas ${icon}"></i></div>
        <div class="chat-bubble">
            ${formatMessageText(text)}
            ${sourcesHtml}
        </div>
    `;

    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addLoadingMessage() {
    const id = "loading-" + Date.now();
    const div = document.createElement("div");
    div.className = "chat-message assistant";
    div.id = id;
    div.innerHTML = `
        <div class="chat-avatar"><i class="fas fa-robot"></i></div>
        <div class="chat-bubble">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    chatContainer.appendChild(div);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return id;
}

function removeLoadingMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ─────────────────────── tabs ────────────────────────

function switchTab(name) {
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${name}`));
}

// ─────────────────────── utilities ───────────────────

function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
}

function formatBytes(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
}

function confidenceColor(c) {
    if (c >= 0.7) return "var(--success)";
    if (c >= 0.4) return "var(--warning)";
    return "var(--danger)";
}

function formatMessageText(text) {
    // very light markdown → HTML
    return text
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\*(.*?)\*/g, "<em>$1</em>")
        .replace(/`(.*?)`/g, "<code>$1</code>")
        .replace(/\n/g, "<br>");
}

// expose to inline onclick handlers
window.selectPaper = selectPaper;
window.deletePaper = deletePaper;