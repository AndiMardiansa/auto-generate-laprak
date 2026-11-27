const STORAGE_KEY = "laprakin_draft_v1";
const TUTORIAL_SEEN_KEY = "laprakin_tutorial_seen_v1";

const MODULES_CONFIG = {
  kdjk: {
    name: "Komunikasi Data & Jaringan Komputer",
    short: "KDJK",
    meetings: 14,
    needsPj: false,
    tools: "Cisco Packet Tracer & Winbox",
    topics: [
      "Sistem Perkabelan (Straight & Cross)",
      "Pengalamatan IP (Subnetting & Supernetting)",
      "Konfigurasi Point to Point Menggunakan Ubiquiti",
      "Fiber Optik",
      "LAN dan Aplikasi (Cisco Packet Tracer)",
      "Subnetting dan Superneting (CIDR)",
      "Routing (Static, RIP, EIGRP, OSPF)",
      "DHCP Server dan Domain Name Server (DNS)",
      "Virtual LAN (VLAN)",
      "Web Server dan Proxy Server",
      "Wireless LAN",
      "User Profile (Hotspot MikroTik)",
      "Manajemen Bandwidth",
      "Virtual Private Network (VPN)",
    ],
  },
  sdata: {
    name: "Struktur Data",
    short: "SData",
    meetings: 11,
    needsPj: true,
    tools: "C++",
    topics: [
      "Array Statis",
      "Array Dinamis",
      "Linked List",
      "Variasi Linked List (Circular & Doubly Linked List)",
      "Stack dengan Array",
      "Queue",
      "Circular Queue",
      "Priority Queue",
      "Tree (General Tree)",
      "Binary Search Tree (BST)",
      "BST Seimbang (AVL Tree)",
    ],
  },
  basdat: {
    name: "Basis Data",
    short: "BasisData",
    meetings: 12,
    needsPj: false,
    tools: "MySQL, ERD & MongoDB",
    topics: [
      "Identifikasi Entitas untuk Studi Proyek",
      "Konversi Model Data ke Tabel",
      "Normalisasi (1NF, 2NF, 3NF)",
      "Data Definition Language (DDL)",
      "Indeks",
      "DML dan Fungsi Agregasi",
      "Relasi Tabel dengan Join",
      "Trigger, Keamanan Data, dan Stored Procedure",
      "Pengenalan NoSQL (MongoDB Atlas & Compass)",
      "Operasi CRUD pada NoSQL",
      "NoSQL Index dan Agregasi",
      "NoSQL - Pemrograman dengan Python (PyMongo)",
    ],
  },
  statistika: {
    name: "Statistika Informatika",
    short: "Statistika",
    meetings: 14,
    needsPj: true,
    tools: "SPSS, MS Excel & Python",
    topics: [
      "Pembentukan Distribusi Frekuensi",
      "Pembentukan Distribusi Frekuensi Kumulatif",
      "Ukuran Pemusatan: Mean dan Median",
      "Ukuran Pemusatan: Modus dan Kuartil",
      "Ukuran Penyebaran Data: Deviasi Rata & Standar Deviasi",
      "Ukuran Penyebaran Data dengan Pemrograman Python",
      "Probabilistik Dasar dan Probabilistik Bersyarat",
      "Distribusi Teoritis (Binomial dan Normal)",
      "Distribusi Teoritis (Hipergeometrik dan Poisson)",
      "Uji Hipotesis (Parameter Mean - 1 Sampel)",
      "Uji Hipotesis dengan 2 Sampel Berpasangan",
      "Uji Reliabilitas dan Uji Validitas",
      "Inhal Praktikum",
      "Ujian Responsi Praktikum",
    ],
  },
};

const TECH_TERMS_REGEX = /\b(Cisco Packet Tracer|TCP\/IP|IP address|primary key|foreign key|linked list|standar deviasi|ping|router|switch|server|client|gateway|subnet|protocol|packet|database|query|table|array|stack|queue|pointer|struct|tree|graph|output|input|software|hardware|browser|localhost|syntax|error|debug|compile|execute|mean|median|modus|varians|regresi|korelasi|anova|hipotesis|dataset|flowchart|topology|interface|ethernet|wireless|DNS|DHCP|HTTP|HTTPS|SQL|ERD|MySQL|Minitab|SPSS)\b/gi;

let currentStep = 1;
let state = createDefaultState();

function createDefaultState() {
  return {
    moduleKey: "kdjk",
    nim: "",
    studentName: document.getElementById("studentName")?.value || "",
    meetingNumber: 1,
    className: "",
    topicTitle: "",
    dayName: "Senin",
    execDate: new Date().toISOString().slice(0, 10),
    execTime: "",
    pjAssistant: "",
    hasPretest: true,
    pretestImages: [],
    pretestQAs: [],
    resultImages: [],
    codeBlocks: [],
    toolsMaterials: [],
    workSteps: [],
    analysisText: "",
    reviewText: "",
    hasPosttest: true,
    posttestImages: [],
    posttestCodeBlocks: [],
    posttestQAs: [],
    posttestAnalysis: "",
    referencesText: "",
  };
}

function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

function saveDraft() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    const status = document.getElementById("autosaveStatus");
    if (status) {
      status.textContent = "Tersimpan otomatis (" + new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }) + ")";
    }
  } catch (e) {
    // Ignore quota errors on large images
  }
}

function loadDraft() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    state = { ...createDefaultState(), ...parsed };
  } catch (e) {
    state = createDefaultState();
  }
}

function resetDraft() {
  localStorage.removeItem(STORAGE_KEY);
  state = createDefaultState();
  syncInputsFromState();
  renderAll();
  goToStep(1);
  showToast("Draft berhasil direset.", "info");
}

function sanitizePart(val) {
  return String(val || "")
    .trim()
    .replace(/[\\/:*?"<>|]+/g, "")
    .replace(/\s+/g, " ") || "TanpaNama";
}

function getOfficialFilename() {
  const nim = sanitizePart(state.nim || "2500018000");
  const nim3 = nim.length >= 3 ? nim.slice(-3) : nim;
  const name = sanitizePart(state.studentName || "Nama");
  const meet = String(state.meetingNumber || 1).trim() || "1";
  const slotRaw = `${(state.dayName || "").trim()} ${(state.execTime || "").trim()}`.trim();
  const slot = slotRaw ? sanitizePart(slotRaw) : "Slot";
  const pj = (state.pjAssistant || "").trim() ? sanitizePart(state.pjAssistant) : "PJ";

  if (state.moduleKey === "sdata") return `Pert${meet}_${nim3}_${name}_SData_${slot}_${pj}.docx`;
  if (state.moduleKey === "kdjk") return `${nim}_${name}_${meet}_KDJK.docx`;
  if (state.moduleKey === "basdat") return `Pertemuan ${meet}_${nim}_${name}.docx`;
  if (state.moduleKey === "statistika") return `${nim}_${name}_${slot}_${pj}_STATISTIKA(${meet}).docx`;
  return `${nim}_${name}_${meet}_Laporan.docx`;
}

function syncInputsFromState() {
  document.querySelectorAll('input[name="moduleKey"]').forEach((r) => {
    r.checked = r.value === state.moduleKey;
    r.closest(".module-card").classList.toggle("selected", r.checked);
  });
  document.getElementById("nim").value = state.nim;
  document.getElementById("studentName").value = state.studentName;
  document.getElementById("meetingNumber").value = state.meetingNumber;
  document.getElementById("className").value = state.className;
  document.getElementById("topicTitle").value = state.topicTitle;
  document.getElementById("dayName").value = state.dayName;
  document.getElementById("execDate").value = state.execDate;
  document.getElementById("execTime").value = state.execTime;
  document.getElementById("pjAssistant").value = state.pjAssistant;
  document.getElementById("pjGroup").style.display = MODULES_CONFIG[state.moduleKey].needsPj ? "block" : "none";

  document.getElementById("hasPretest").checked = state.hasPretest;
  document.getElementById("pretestSection").style.display = state.hasPretest ? "block" : "none";

  document.getElementById("reviewText").value = state.reviewText;
  const toolsEl = document.getElementById("toolsMaterialsText");
  if (toolsEl) toolsEl.value = (state.toolsMaterials || []).join("\n");
  const stepsEl = document.getElementById("workStepsText");
  if (stepsEl) stepsEl.value = (state.workSteps || []).join("\n");
  const analysisEl = document.getElementById("analysisText");
  if (analysisEl) analysisEl.value = state.analysisText || "";
  const postAnalysisEl = document.getElementById("posttestAnalysisText");
  if (postAnalysisEl) postAnalysisEl.value = state.posttestAnalysis || "";
  const keyEl = document.getElementById("geminiApiKey");
  if (keyEl) keyEl.value = localStorage.getItem("laprakin_gemini_key") || "";

  document.getElementById("hasPosttest").checked = state.hasPosttest;
  document.getElementById("posttestSection").style.display = state.hasPosttest ? "block" : "none";
}

function bindInputs() {
  document.querySelectorAll('input[name="moduleKey"]').forEach((radio) => {
    radio.addEventListener("change", (e) => {
      const nextMod = e.target.value;
      if (nextMod !== state.moduleKey) {
        state.moduleKey = nextMod;
        const maxM = MODULES_CONFIG[nextMod].meetings || 14;
        if (state.meetingNumber > maxM) state.meetingNumber = 1;
        // Auto-fill topic preset for the selected module & meeting
        const topics = MODULES_CONFIG[nextMod].topics || [];
        state.topicTitle = topics[(state.meetingNumber || 1) - 1] || "";
        state.execDate = "";
        state.execTime = "";
        if (!MODULES_CONFIG[nextMod].needsPj) state.pjAssistant = "";
        syncInputsFromState();
        renderAll();
        saveDraft();
        showToast(`Modul diubah ke ${MODULES_CONFIG[nextMod].short}. Judul materi disesuaikan otomatis.`, "info");
      }
    });
  });

  const textFields = [
    ["nim", "nim"],
    ["studentName", "studentName"],
    ["meetingNumber", "meetingNumber"],
    ["className", "className"],
    ["topicTitle", "topicTitle"],
    ["dayName", "dayName"],
    ["execDate", "execDate"],
    ["execTime", "execTime"],
    ["pjAssistant", "pjAssistant"],
    ["analysisText", "analysisText"],
    ["reviewText", "reviewText"],
    ["posttestAnalysisText", "posttestAnalysis"],
  ];

  const toolsEl = document.getElementById("toolsMaterialsText");
  if (toolsEl) {
    toolsEl.addEventListener("input", () => {
      state.toolsMaterials = toolsEl.value.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
      saveDraft();
      renderLivePreview();
    });
  }
  const stepsEl = document.getElementById("workStepsText");
  if (stepsEl) {
    stepsEl.addEventListener("input", () => {
      state.workSteps = stepsEl.value.split(/\r?\n/).map((s) => s.trim()).filter(Boolean);
      saveDraft();
      renderLivePreview();
    });
  }
  const keyEl = document.getElementById("geminiApiKey");
  if (keyEl) {
    keyEl.addEventListener("input", () => {
      localStorage.setItem("laprakin_gemini_key", keyEl.value.trim());
    });
  }

  textFields.forEach(([elId, key]) => {
    const el = document.getElementById(elId);
    if (!el) return;
    el.addEventListener("input", () => {
      if (elId === "meetingNumber") {
        const mod = MODULES_CONFIG[state.moduleKey];
        const maxM = mod.meetings || 14;
        const prevMeeting = state.meetingNumber || 1;
        const nextMeeting = Math.min(maxM, Math.max(1, parseInt(el.value || "1", 10)));
        const prevPreset = (mod.topics || [])[prevMeeting - 1] || "";
        state.meetingNumber = nextMeeting;
        if (!state.topicTitle.trim() || state.topicTitle === prevPreset) {
          state.topicTitle = (mod.topics || [])[nextMeeting - 1] || state.topicTitle;
          const topicEl = document.getElementById("topicTitle");
          if (topicEl) topicEl.value = state.topicTitle;
        }
      } else {
        state[key] = el.value;
      }
      saveDraft();
      renderLivePreview();
      if (key === "reviewText") updateWordMeter();
      if (currentStep === 5) renderReviewChecklist();
    });
  });

  document.getElementById("hasPretest").addEventListener("change", (e) => {
    state.hasPretest = e.target.checked;
    document.getElementById("pretestSection").style.display = state.hasPretest ? "block" : "none";
    saveDraft();
    renderLivePreview();
  });

  document.getElementById("hasPosttest").addEventListener("change", (e) => {
    state.hasPosttest = e.target.checked;
    document.getElementById("posttestSection").style.display = state.hasPosttest ? "block" : "none";
    saveDraft();
    renderLivePreview();
  });

  setupUploadZone("pretestDropzone", "pretestFileInput", "pretestImages");
  setupUploadZone("resultDropzone", "resultFileInput", "resultImages");
  setupUploadZone("posttestDropzone", "posttestFileInput", "posttestImages");

  // Ctrl+V paste support based on active step
  document.addEventListener("paste", (e) => {
    const items = e.clipboardData?.items || [];
    for (const item of items) {
      if (item.type.startsWith("image/")) {
        const file = item.getAsFile();
        if (!file) continue;
        if (currentStep === 2 && state.hasPretest) readImageFile(file, "pretestImages");
        else if (currentStep === 3) readImageFile(file, "resultImages");
        else if (currentStep === 4 && state.hasPosttest) readImageFile(file, "posttestImages");
      }
    }
  });
}

function setupUploadZone(dropzoneId, inputId, targetArrayKey) {
  const dz = document.getElementById(dropzoneId);
  const inp = document.getElementById(inputId);
  if (!dz || !inp) return;

  dz.addEventListener("click", () => inp.click());
  dz.addEventListener("dragover", (e) => {
    e.preventDefault();
    dz.classList.add("dragover");
  });
  dz.addEventListener("dragleave", () => dz.classList.remove("dragover"));
  dz.addEventListener("drop", (e) => {
    e.preventDefault();
    dz.classList.remove("dragover");
    Array.from(e.dataTransfer.files).forEach((f) => readImageFile(f, targetArrayKey));
  });
  inp.addEventListener("change", (e) => {
    Array.from(e.target.files).forEach((f) => readImageFile(f, targetArrayKey));
    inp.value = "";
  });
}

function readImageFile(file, targetArrayKey) {
  if (!file.type.startsWith("image/")) return;
  const reader = new FileReader();
  reader.onload = () => {
    state[targetArrayKey].push({
      dataUrl: reader.result,
      title: "",
      description: "",
    });
    saveDraft();
    renderImageLists();
    renderLivePreview();
    showToast("Foto berhasil ditambahkan.", "success");
  };
  reader.readAsDataURL(file);
}

function renderImageLists() {
  renderImageCollection("pretestImagesList", "pretestImages", "Gambar 1", false);
  renderImageCollection("resultImagesList", "resultImages", "Gambar 2", true);
  renderImageCollection("posttestImagesList", "posttestImages", "Gambar 3", false);
  renderPretestQAs();
  renderCodeBlocks();
  renderPosttestCodeBlocks();
  renderPosttestQAs();
}

function renderImageCollection(containerId, key, prefix, descRequired) {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = "";
  state[key].forEach((img, idx) => {
    const item = document.createElement("div");
    item.className = "block-item";
    item.innerHTML = `
      <div class="block-item-header">
        <span class="block-badge">${prefix}.${idx + 1}</span>
        <button type="button" class="btn btn-outline btn-sm" onclick="removeImage('${key}', ${idx})">Hapus</button>
      </div>
      <img src="${img.dataUrl}" class="thumb-preview" alt="${prefix}.${idx + 1}" />
      <div class="form-group">
        <label class="form-label">Judul Foto</label>
        <input class="form-control" type="text" value="${escapeHtml(img.title)}" placeholder="Contoh: Hasil Ping ke Gateway" oninput="updateImageField('${key}', ${idx}, 'title', this.value)" />
      </div>
      <div class="form-group" style="margin-bottom: 0;">
        <label class="form-label">Keterangan Foto / Langkah Kerja ${descRequired ? '<span class="req">*</span>' : ''}</label>
        <textarea class="form-control" rows="2" placeholder="Jelaskan langkah kerja atau hasil pada gambar ini..." oninput="updateImageField('${key}', ${idx}, 'description', this.value)">${escapeHtml(img.description)}</textarea>
      </div>
    `;
    el.appendChild(item);
  });
}

function updateImageField(key, idx, field, value) {
  state[key][idx][field] = value;
  saveDraft();
  renderLivePreview();
}

function removeImage(key, idx) {
  state[key].splice(idx, 1);
  saveDraft();
  renderImageLists();
  renderLivePreview();
}

function addPretestQA() {
  state.pretestQAs.push({ question: "", answer: "" });
  saveDraft();
  renderPretestQAs();
  renderLivePreview();
}

function renderPretestQAs() {
  const el = document.getElementById("pretestQAList");
  if (!el) return;
  el.innerHTML = "";
  state.pretestQAs.forEach((qa, idx) => {
    const box = document.createElement("div");
    box.className = "block-item";
    box.innerHTML = `
      <div class="block-item-header">
        <span class="block-badge">Pertanyaan #${idx + 1}</span>
        <button type="button" class="btn btn-outline btn-sm" onclick="removePretestQA(${idx})">Hapus</button>
      </div>
      <div class="form-group">
        <label class="form-label">Soal (Opsional)</label>
        <input class="form-control" type="text" value="${escapeHtml(qa.question)}" placeholder="Tuliskan soal Pre-Test..." oninput="updateQA(${idx}, 'question', this.value)" />
      </div>
      <div class="form-group" style="margin-bottom: 0;">
        <label class="form-label">Jawaban (Opsional)</label>
        <textarea class="form-control" rows="2" placeholder="Tuliskan jawaban..." oninput="updateQA(${idx}, 'answer', this.value)">${escapeHtml(qa.answer)}</textarea>
      </div>
    `;
    el.appendChild(box);
  });
}

function updateQA(idx, field, val) {
  state.pretestQAs[idx][field] = val;
  saveDraft();
  renderLivePreview();
}

function removePretestQA(idx) {
  state.pretestQAs.splice(idx, 1);
  saveDraft();
  renderPretestQAs();
  renderLivePreview();
}

function addCodeBlock() {
  if (!Array.isArray(state.codeBlocks)) state.codeBlocks = [];
  state.codeBlocks.push({ title: "", code: "", description: "" });
  saveDraft();
  renderCodeBlocks();
  renderLivePreview();
}

function renderCodeBlocks() {
  const el = document.getElementById("codeBlocksList");
  if (!el) return;
  el.innerHTML = "";
  (state.codeBlocks || []).forEach((cb, idx) => {
    const box = document.createElement("div");
    box.className = "block-item";
    box.innerHTML = `
      <div class="block-item-header">
        <span class="block-badge">Kode Program 2.${idx + 1}</span>
        <button type="button" class="btn btn-outline btn-sm" onclick="removeCodeBlock(${idx})">Hapus</button>
      </div>
      <div class="form-group">
        <label class="form-label">Judul Kode Program (Capital Each Words)</label>
        <input class="form-control" type="text" value="${escapeHtml(cb.title)}" placeholder="Contoh: Implementasi Linked List C++" oninput="updateCodeBlock(${idx}, 'title', this.value)" />
      </div>
      <div class="form-group">
        <label class="form-label">Source Code (Otomatis bernomor baris & Courier New 10pt)</label>
        <textarea class="form-control" rows="5" style="font-family:'Courier New',monospace;font-size:12px;" placeholder="Tempel source code di sini..." oninput="updateCodeBlock(${idx}, 'code', this.value)">${escapeHtml(cb.code)}</textarea>
      </div>
      <div class="form-group" style="margin-bottom: 0;">
        <label class="form-label">Penjelasan Kode (Opsional)</label>
        <textarea class="form-control" rows="2" placeholder="Jelaskan alur logika atau fungsi kode..." oninput="updateCodeBlock(${idx}, 'description', this.value)">${escapeHtml(cb.description)}</textarea>
      </div>
    `;
    el.appendChild(box);
  });
}

function updateCodeBlock(idx, field, val) {
  state.codeBlocks[idx][field] = val;
  saveDraft();
  renderLivePreview();
}

function removeCodeBlock(idx) {
  state.codeBlocks.splice(idx, 1);
  saveDraft();
  renderCodeBlocks();
  renderLivePreview();
}

function addPosttestCodeBlock() {
  if (!Array.isArray(state.posttestCodeBlocks)) state.posttestCodeBlocks = [];
  state.posttestCodeBlocks.push({ title: "Post Test", code: "", description: "" });
  saveDraft();
  renderPosttestCodeBlocks();
  renderLivePreview();
}

function renderPosttestCodeBlocks() {
  const el = document.getElementById("posttestCodeBlocksList");
  if (!el) return;
  el.innerHTML = "";
  (state.posttestCodeBlocks || []).forEach((cb, idx) => {
    const box = document.createElement("div");
    box.className = "block-item";
    box.innerHTML = `
      <div class="block-item-header">
        <span class="block-badge">Kode Program 3.${idx + 1}</span>
        <button type="button" class="btn btn-outline btn-sm" onclick="removePosttestCodeBlock(${idx})">Hapus</button>
      </div>
      <div class="form-group">
        <label class="form-label">Judul Kode Program (Capital Each Words)</label>
        <input class="form-control" type="text" value="${escapeHtml(cb.title)}" placeholder="Contoh: Post Test" oninput="updatePosttestCodeBlock(${idx}, 'title', this.value)" />
      </div>
      <div class="form-group">
        <label class="form-label">Source Code (Otomatis bernomor baris & Courier New 10pt)</label>
        <textarea class="form-control" rows="5" style="font-family:'Courier New',monospace;font-size:12px;" placeholder="Tempel source code Post-Test di sini..." oninput="updatePosttestCodeBlock(${idx}, 'code', this.value)">${escapeHtml(cb.code)}</textarea>
      </div>
      <div class="form-group" style="margin-bottom: 0;">
        <label class="form-label">Penjelasan Kode (Opsional)</label>
        <textarea class="form-control" rows="2" placeholder="Jelaskan alur logika kode Post-Test..." oninput="updatePosttestCodeBlock(${idx}, 'description', this.value)">${escapeHtml(cb.description)}</textarea>
      </div>
    `;
    el.appendChild(box);
  });
}

function updatePosttestCodeBlock(idx, field, val) {
  state.posttestCodeBlocks[idx][field] = val;
  saveDraft();
  renderLivePreview();
}

function removePosttestCodeBlock(idx) {
  state.posttestCodeBlocks.splice(idx, 1);
  saveDraft();
  renderPosttestCodeBlocks();
  renderLivePreview();
}

function addPosttestQA() {
  if (!Array.isArray(state.posttestQAs)) state.posttestQAs = [];
  state.posttestQAs.push({ question: "", answer: "" });
  saveDraft();
  renderPosttestQAs();
  renderLivePreview();
}

function renderPosttestQAs() {
  const el = document.getElementById("posttestQAList");
  if (!el) return;
  el.innerHTML = "";
  (state.posttestQAs || []).forEach((qa, idx) => {
    const box = document.createElement("div");
    box.className = "block-item";
    box.innerHTML = `
      <div class="block-item-header">
        <span class="block-badge">Soal Post-Test #${idx + 1}</span>
        <button type="button" class="btn btn-outline btn-sm" onclick="removePosttestQA(${idx})">Hapus</button>
      </div>
      <div class="form-group">
        <label class="form-label">Pertanyaan (Opsional)</label>
        <input class="form-control" type="text" value="${escapeHtml(qa.question)}" placeholder="Tuliskan soal Post-Test..." oninput="updatePosttestQA(${idx}, 'question', this.value)" />
      </div>
      <div class="form-group" style="margin-bottom: 0;">
        <label class="form-label">Jawaban (Opsional)</label>
        <textarea class="form-control" rows="2" placeholder="Tuliskan jawaban..." oninput="updatePosttestQA(${idx}, 'answer', this.value)">${escapeHtml(qa.answer)}</textarea>
      </div>
    `;
    el.appendChild(box);
  });
}

function updatePosttestQA(idx, field, val) {
  state.posttestQAs[idx][field] = val;
  saveDraft();
  renderLivePreview();
}

function removePosttestQA(idx) {
  state.posttestQAs.splice(idx, 1);
  saveDraft();
  renderPosttestQAs();
  renderLivePreview();
}

function updateWordMeter() {
  const text = (state.reviewText || "").trim();
  const words = text ? text.split(/\s+/).length : 0;
  const pct = Math.min(100, Math.round((words / 80) * 100));
  document.getElementById("wordCountLabel").textContent = `${words} kata`;
  document.getElementById("completenessLabel").textContent = `Kelengkapan: ${pct}%`;
  document.getElementById("completenessFill").style.width = `${pct}%`;
}

function formatTechnicalHtml(str) {
  return escapeHtml(str).replace(TECH_TERMS_REGEX, (m) => `<em>${m}</em>`);
}

async function generateWithGeminiAI() {
  const btn = document.getElementById("aiGenerateBtn");
  const apiKey = (document.getElementById("geminiApiKey")?.value || "").trim() || localStorage.getItem("laprakin_gemini_key") || "";
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Menghasilkan dengan AI...";
  }
  try {
    const res = await fetch("/api/ai/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        apiKey,
        moduleKey: state.moduleKey,
        meetingNumber: state.meetingNumber,
        topicTitle: state.topicTitle,
        resultImages: state.resultImages,
        posttestImages: state.hasPosttest ? state.posttestImages : [],
        codeBlocks: state.codeBlocks,
        posttestCodeBlocks: state.hasPosttest ? state.posttestCodeBlocks : [],
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Gagal generate konten AI.");

    if (Array.isArray(data.toolsMaterials) && data.toolsMaterials.length) {
      state.toolsMaterials = data.toolsMaterials;
    }
    if (Array.isArray(data.workSteps) && data.workSteps.length) {
      state.workSteps = data.workSteps;
    }
    if (Array.isArray(data.resultImageDescriptions)) {
      state.resultImages.forEach((img, i) => {
        if (data.resultImageDescriptions[i]) img.description = data.resultImageDescriptions[i];
      });
    }
    if (Array.isArray(data.codeBlockDescriptions)) {
      (state.codeBlocks || []).forEach((cb, i) => {
        if (data.codeBlockDescriptions[i]) cb.description = data.codeBlockDescriptions[i];
      });
    }
    if (Array.isArray(data.posttestImageDescriptions)) {
      state.posttestImages.forEach((img, i) => {
        if (data.posttestImageDescriptions[i]) img.description = data.posttestImageDescriptions[i];
      });
    }
    if (Array.isArray(data.posttestCodeBlockDescriptions)) {
      (state.posttestCodeBlocks || []).forEach((cb, i) => {
        if (data.posttestCodeBlockDescriptions[i]) cb.description = data.posttestCodeBlockDescriptions[i];
      });
    }
    if (data.analysisText) state.analysisText = data.analysisText;
    if (data.posttestAnalysis) state.posttestAnalysis = data.posttestAnalysis;
    if (data.reviewText) state.reviewText = data.reviewText;

    syncInputsFromState();
    renderAll();
    saveDraft();
    showToast("Konten laporan berhasil dibuat dengan Gemini AI!", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Generate dengan AI (Gemini)";
    }
  }
}

async function generatePosttestWithGeminiAI() {
  const btn = document.getElementById("aiPosttestBtn");
  const apiKey = (document.getElementById("geminiApiKey")?.value || "").trim() || localStorage.getItem("laprakin_gemini_key") || "";
  if (btn) {
    btn.disabled = true;
    btn.textContent = "Menghasilkan Post-Test...";
  }
  try {
    const res = await fetch("/api/ai/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: "posttest",
        apiKey,
        moduleKey: state.moduleKey,
        meetingNumber: state.meetingNumber,
        topicTitle: state.topicTitle,
        posttestImages: state.hasPosttest ? state.posttestImages : [],
        posttestCodeBlocks: state.hasPosttest ? state.posttestCodeBlocks : [],
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Gagal generate Post-Test AI.");

    if (Array.isArray(data.posttestImageDescriptions)) {
      (state.posttestImages || []).forEach((img, i) => {
        if (data.posttestImageDescriptions[i]) img.description = data.posttestImageDescriptions[i];
      });
    }
    if (Array.isArray(data.posttestCodeBlockDescriptions)) {
      (state.posttestCodeBlocks || []).forEach((cb, i) => {
        if (data.posttestCodeBlockDescriptions[i]) cb.description = data.posttestCodeBlockDescriptions[i];
      });
    }
    if (data.posttestAnalysis) state.posttestAnalysis = data.posttestAnalysis;

    syncInputsFromState();
    renderAll();
    saveDraft();
    showToast("Keterangan & analisis Post-Test berhasil dibuat dengan AI!", "success");
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = "Generate Post-Test dengan AI (Gemini)";
    }
  }
}

function renderLivePreview() {
  const sheet = document.getElementById("a4PreviewSheet");
  if (!sheet) return;
  const mod = MODULES_CONFIG[state.moduleKey];
  const pjRow = mod.needsPj ? `<div><strong>PJ Asisten:</strong> ${escapeHtml(state.pjAssistant || "-")}</div>` : "";
  const codeCount = (state.codeBlocks || []).length;
  const postCodeCount = (state.posttestCodeBlocks || []).length;
  const postQaCount = (state.posttestQAs || []).length;
  const toolsList = (state.toolsMaterials || []).length ? state.toolsMaterials : ["Laptop / PC", mod.tools];
  const stepsList = (state.workSteps || []).length ? state.workSteps : [`Menyiapkan ${mod.tools}`, `Melaksanakan materi ${state.topicTitle || "..."}`];

  sheet.innerHTML = `
    <div style="text-align:center; border-bottom:1px solid #e5e7eb; padding-bottom:10px; margin-bottom:10px;">
      <div class="a4-cover-title" style="font-size:13px;">LAPORAN PRAKTIKUM</div>
      <div style="font-size:12px; font-weight:700;">${escapeHtml(mod.name)}</div>
      <div style="font-size:11px; font-weight:700; margin-top:2px;">Materi</div>
      <div style="font-size:11px; font-weight:700;">${escapeHtml((state.topicTitle || "Judul Materi").toUpperCase())}</div>
      <div style="font-size:10px; font-weight:700; margin-top:2px;">${escapeHtml(state.dayName)}, ${escapeHtml(state.execDate || "-")} ${escapeHtml(state.execTime || "")}</div>
      <div style="margin:10px auto;">
        <img src="/static/img/logo-uad.png" alt="Logo UAD" style="width:76px; height:auto;" />
      </div>
      <div style="font-size:10px; margin-top:6px;">
        <div><strong>Disusun Oleh:</strong></div>
        <div>${escapeHtml(state.studentName || "-")}</div>
        <div>${escapeHtml(state.nim || "-")}</div>
      </div>
      <div style="font-size:9px; font-weight:700; color:#4b5563; margin-top:8px;">PROGRAM STUDI S1 INFORMATIKA • FAKULTAS TEKNOLOGI INDUSTRI • UNIVERSITAS AHMAD DAHLAN • 2026</div>
    </div>
    <div class="a4-sec-title">I. Pre Test</div>
    <p>${state.hasPretest ? `${state.pretestImages.length} foto terlampir (Gambar 1.1..), ${state.pretestQAs.length} blok soal.` : "Tidak ada sesi Pre-Test pada pertemuan ini."}</p>
    <div class="a4-sec-title">II. Hasil Praktikum</div>
    <p style="margin-bottom:4px;"><strong>A. Alat dan Bahan:</strong> ${escapeHtml(toolsList.join(", "))}</p>
    <p style="margin-bottom:4px;"><strong>B. Langkah Kerja:</strong> ${stepsList.length} langkah tercatat</p>
    <p style="margin-bottom:4px;"><strong>C. Implementasi/Screenshot:</strong> ${state.resultImages.length} gambar (Gambar 2.1 - 2.${Math.max(1, state.resultImages.length)})${codeCount ? `, ${codeCount} Kode Program` : ""}.</p>
    <p style="margin-bottom:4px;"><strong>D. Analisis Hasil:</strong> ${state.analysisText ? formatTechnicalHtml(state.analysisText).replace(/\n/g, "<br/>") : "<em>Analisis hasil akan tampil di sini...</em>"}</p>
    <div class="a4-sec-title">III. Post Test</div>
    <p>${state.hasPosttest ? `${state.posttestImages.length} foto Post-Test (Gambar 3.1..)${postCodeCount ? `, ${postCodeCount} Kode Program` : ""}, ${postQaCount} blok soal.` : "Tidak ada Post-Test."}</p>
    ${state.posttestAnalysis ? `<p><strong>Analisis hasil :</strong> ${formatTechnicalHtml(state.posttestAnalysis).replace(/\n/g, "<br/>")}</p>` : ""}
    <div class="a4-sec-title" style="font-size:11px;">Ulasan Praktikum</div>
    <p>${state.reviewText ? formatTechnicalHtml(state.reviewText).replace(/\n/g, "<br/>") : "<em>Ulasan / refleksi praktikum akan tampil di sini...</em>"}</p>
    <p style="font-size:11px; color:#6b7280; margin-top:8px;">File resmi: <strong>${escapeHtml(getOfficialFilename())}</strong></p>
  `;
}

function validateStep(step) {
  if (step === 1) {
    if (!state.nim.trim() || !state.studentName.trim() || !state.className.trim() || !state.topicTitle.trim() || !state.execDate || !state.execTime.trim()) {
      showToast("Lengkapi semua field wajib pada Profil & Modul.", "error");
      return false;
    }
    if (MODULES_CONFIG[state.moduleKey].needsPj && !state.pjAssistant.trim()) {
      showToast("Nama PJ Asisten Praktikum wajib diisi untuk modul ini.", "error");
      return false;
    }
  }
  if (step === 2) {
    if (state.hasPretest && state.pretestImages.length === 0) {
      showToast("Pre-Test aktif: unggah minimal 1 foto Pre-Test sebelum lanjut.", "error");
      return false;
    }
  }
  if (step === 3) {
    if (state.resultImages.length === 0) {
      showToast("Unggah minimal 1 foto Hasil Praktikum.", "error");
      return false;
    }
    const missingDesc = state.resultImages.some((img) => !(img.description || "").trim());
    if (missingDesc) {
      showToast("Setiap foto Hasil Praktikum wajib memiliki Keterangan / Langkah Kerja.", "error");
      return false;
    }
    if (!state.reviewText.trim()) {
      showToast("Ulasan Praktikum wajib diisi.", "error");
      return false;
    }
  }
  return true;
}

function goToStep(target) {
  if (target > currentStep && !validateStep(currentStep)) return;
  currentStep = target;
  for (let i = 1; i <= 5; i++) {
    document.getElementById(`step${i}`).style.display = i === currentStep ? "block" : "none";
    const stepEl = document.querySelector(`.step-item[data-step="${i}"]`);
    stepEl.classList.toggle("active", i === currentStep);
    stepEl.classList.toggle("done", i < currentStep);
  }
  document.getElementById("prevBtn").style.visibility = currentStep === 1 ? "hidden" : "visible";
  document.getElementById("nextBtn").style.display = currentStep === 5 ? "none" : "inline-flex";
  document.getElementById("stepCounter").textContent = `Langkah ${currentStep} dari 5`;

  if (currentStep === 5) renderReviewChecklist();
}

function nextStep() {
  if (currentStep < 5) goToStep(currentStep + 1);
}

function prevStep() {
  if (currentStep > 1) goToStep(currentStep - 1);
}

function renderReviewChecklist() {
  const list = document.getElementById("reviewChecklist");
  const reviewWords = (state.reviewText || "").trim().split(/\s+/).filter(Boolean).length;
  const allResultsDescribed = state.resultImages.length > 0 && state.resultImages.every((img) => (img.description || "").trim().length > 0);
  const checks = [
    { ok: Boolean(state.nim && state.studentName && state.topicTitle), label: "1. Kelengkapan Profil, Cover UAD 2026 & Modul terkonfirmasi" },
    { ok: !state.hasPretest || state.pretestImages.length > 0, label: "2. Bagian Pre Test lengkap (Rubrik Skor 5)" },
    { ok: allResultsDescribed, label: "3. Hasil Praktikum runtut & setiap gambar memiliki keterangan" },
    { ok: reviewWords >= 40, label: `4. Ulasan / Refleksi spesifik (${reviewWords} kata — target >= 40 kata untuk Skor 5)` },
    { ok: !state.hasPosttest || state.posttestImages.length > 0 || (state.posttestQAs || []).length > 0, label: "5. Bagian Post Test siap" },
  ];
  list.innerHTML = checks
    .map((c) => `<li class="${c.ok ? "ok" : "warn"}">${c.ok ? "✓" : "!"} <span>${c.label}</span></li>`)
    .join("");
  document.getElementById("officialFilenamePreview").textContent = getOfficialFilename();
}

async function generateDocx() {
  for (let s = 1; s <= 3; s++) {
    if (!validateStep(s)) {
      goToStep(s);
      return;
    }
  }
  const modal = document.getElementById("progressModal");
  modal.classList.add("show");
  document.getElementById("successCard").style.display = "none";

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || "Gagal membuat laporan.");
    }
    document.getElementById("generatedFilenameText").textContent = data.filename;
    const dl = document.getElementById("downloadDocxLink");
    dl.href = data.downloadUrl;
    dl.setAttribute("download", data.filename);
    document.getElementById("successCard").style.display = "block";
    showToast("Laporan .DOCX berhasil digenerate!", "success");
    loadHistory();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    modal.classList.remove("show");
  }
}

let historyItems = [];
let historyCurrentPage = 1;
const HISTORY_PAGE_SIZE = 5;

async function loadHistory() {
  const tbody = document.getElementById("historyTableBody");
  if (!tbody) return;
  try {
    const res = await fetch("/api/reports");
    if (!res.ok) return;
    const data = await res.json();
    historyItems = data.reports || [];
    historyCurrentPage = 1;
    renderHistoryPage(1);
  } catch (e) {
    // ignore
  }
}

function renderHistoryPage(page) {
  const tbody = document.getElementById("historyTableBody");
  const pagEl = document.getElementById("historyPagination");
  if (!tbody) return;

  if (!historyItems.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:var(--text-muted);">Belum ada riwayat laporan.</td></tr>';
    if (pagEl) pagEl.innerHTML = "";
    return;
  }

  const totalItems = historyItems.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / HISTORY_PAGE_SIZE));
  historyCurrentPage = Math.min(Math.max(1, page), totalPages);

  const startIdx = (historyCurrentPage - 1) * HISTORY_PAGE_SIZE;
  const endIdx = Math.min(startIdx + HISTORY_PAGE_SIZE, totalItems);
  const pageSlice = historyItems.slice(startIdx, endIdx);

  tbody.innerHTML = pageSlice
    .map(
      (r) => `
      <tr>
        <td>${r.created_at}</td>
        <td><span class="history-mod-badge">${escapeHtml(r.module_name)}</span></td>
        <td>Pertemuan ${r.meeting_number}</td>
        <td>${escapeHtml(r.topic_title)}</td>
        <td><code>${escapeHtml(r.filename)}</code></td>
        <td><a class="btn btn-outline btn-sm" href="${r.downloadUrl}">Unduh Ulang</a></td>
      </tr>`
    )
    .join("");

  if (!pagEl) return;

  if (totalPages <= 1) {
    pagEl.innerHTML = `<div class="pagination-info">Menampilkan <strong>1–${totalItems}</strong> dari <strong>${totalItems}</strong> laporan</div>`;
    return;
  }

  const pages = [];
  for (let p = 1; p <= totalPages; p++) {
    if (p === 1 || p === totalPages || Math.abs(p - historyCurrentPage) <= 1) {
      pages.push(p);
    } else if (pages[pages.length - 1] !== "...") {
      pages.push("...");
    }
  }

  const pageButtons = pages
    .map((p) =>
      p === "..."
        ? `<span class="page-ellipsis">…</span>`
        : `<button type="button" class="page-btn ${p === historyCurrentPage ? "active" : ""}" onclick="renderHistoryPage(${p})">${p}</button>`
    )
    .join("");

  pagEl.innerHTML = `
    <div class="pagination-info">Menampilkan <strong>${startIdx + 1}–${endIdx}</strong> dari <strong>${totalItems}</strong> laporan</div>
    <div class="pagination-controls">
      <button type="button" class="page-btn" onclick="renderHistoryPage(${historyCurrentPage - 1})" ${historyCurrentPage === 1 ? "disabled" : ""}>← Prev</button>
      ${pageButtons}
      <button type="button" class="page-btn" onclick="renderHistoryPage(${historyCurrentPage + 1})" ${historyCurrentPage === totalPages ? "disabled" : ""}>Next →</button>
    </div>
  `;
}

function makeDemoImage(label, bgColor) {
  const canvas = document.createElement("canvas");
  canvas.width = 640;
  canvas.height = 360;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = bgColor;
  ctx.fillRect(0, 0, 640, 360);
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 4;
  ctx.strokeRect(20, 20, 600, 320);
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 24px sans-serif";
  ctx.fillText(label, 44, 175);
  ctx.font = "16px sans-serif";
  ctx.fillText("Simulasi Screenshot Praktikum LabTIF UAD", 44, 210);
  return canvas.toDataURL("image/png");
}

function fillExampleData() {
  state = {
    moduleKey: "kdjk",
    nim: "2400018042",
    studentName: document.getElementById("studentName").value || "Budi Santoso",
    meetingNumber: 3,
    className: "A",
    topicTitle: "Konfigurasi Routing Statis & Uji Ping Antar Router",
    dayName: "Rabu",
    execDate: new Date().toISOString().slice(0, 10),
    execTime: "08.00 - 10.00 WIB",
    pjAssistant: "",
    hasPretest: true,
    pretestImages: [
      {
        dataUrl: makeDemoImage("Pre-Test KDJK Pertemuan 3", "#1e3a8a"),
        title: "Skor Pre-Test Modul 3",
        description: "Hasil pengerjaan soal konsep IP address dan gateway sebelum praktikum.",
      },
    ],
    pretestQAs: [
      {
        question: "Apa fungsi default gateway pada konfigurasi jaringan?",
        answer: "Default gateway berfungsi sebagai jalur keluar menuju jaringan lain melalui router.",
      },
    ],
    resultImages: [
      {
        dataUrl: makeDemoImage("Topologi Cisco Packet Tracer", "#111827"),
        title: "Topologi Jaringan 2 Router & 2 Switch",
        description: "Merancang topologi pada Cisco Packet Tracer menggunakan 2 router, 2 switch, dan 4 PC client dengan subnet berbeda.",
      },
      {
        dataUrl: makeDemoImage("Hasil Uji Ping Sukses (Reply)", "#166534"),
        title: "Pengujian Koneksi Ping Antar Subnet",
        description: "Menjalankan perintah ping dari PC0 ke PC3 dan mendapatkan balasan reply tanpa packet loss.",
      },
    ],
    codeBlocks: [
      {
        title: "Konfigurasi Routing Statis Pada Router Cisco",
        code: "Router> enable\nRouter# configure terminal\nRouter(config)# ip route 192.168.2.0 255.255.255.0 10.0.0.2\nRouter(config)# end",
        description: "Perintah CLI untuk menambahkan rute statis menuju jaringan tujuan melalui alamat next-hop.",
      },
    ],
    toolsMaterials: ["Laptop / PC", "Cisco Packet Tracer"],
    workSteps: [
      "Merancang topologi jaringan dengan 2 router, 2 switch, dan 4 PC client pada Cisco Packet Tracer.",
      "Mengonfigurasi IP address dan subnet mask pada setiap interface router serta PC.",
      "Menambahkan entri static routing menggunakan perintah ip route pada kedua router.",
      "Melakukan pengujian konektivitas menggunakan perintah ping antar subnet.",
    ],
    analysisText:
      "Berdasarkan pengujian pada topologi 2 router, komunikasi antar subnet hanya dapat berjalan setelah tabel routing statis pada kedua router saling mengarah ke jaringan tujuan dan jaringan asal.",
    reviewText:
      "Pada praktikum kali ini dipelajari perancangan topologi jaringan menggunakan Cisco Packet Tracer dengan dua buah router dan dua switch. Setiap interface diberikan IP address sesuai alokasi subnet masing-masing.\n\nKendala yang sempat ditemui adalah status Request Timed Out saat pengujian awal karena tabel routing statis pada router kedua belum mengarah balik ke subnet asal. Solusinya adalah menambahkan rute balik menggunakan perintah ip route pada masing-masing router. Setelah diperbaiki, pengujian ping dari client menuju server berhasil dengan status reply 100%, membuktikan komunikasi protocol TCP/IP berjalan dengan baik.",
    hasPosttest: true,
    posttestImages: [
      {
        dataUrl: makeDemoImage("Post-Test KDJK Pertemuan 3", "#374151"),
        title: "Bukti Penyelesaian Post-Test",
        description: "Evaluasi akhir konfigurasi static routing dan verifikasi koneksi.",
      },
    ],
    posttestQAs: [
      {
        question: "Mengapa routing statis memerlukan konfigurasi dua arah (forward dan return route)?",
        answer: "Agar paket balasan (reply) dari jaringan tujuan mengetahui jalur kembali ke jaringan pengirim.",
      },
    ],
    posttestAnalysis:
      "Evaluasi Post-Test menunjukkan pemahaman terhadap konfigurasi ip route dua arah telah tercapai dengan hasil pengujian ping reply 100%.",
    referencesText: "LabTIF UAD. (2026). Modul Praktikum Komunikasi Data & Jaringan Komputer. Universitas Ahmad Dahlan.",
  };
  syncInputsFromState();
  renderAll();
  saveDraft();
  showToast("Data contoh berhasil diisikan ke seluruh 5 langkah!", "success");
}

function renderAll() {
  renderImageLists();
  updateWordMeter();
  renderLivePreview();
  if (currentStep === 5) renderReviewChecklist();
}

function escapeHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// 5-Step Tutorial Overlay
const TUTORIAL_STEPS = [
  { title: "1. Pilih Modul & Profil", desc: "Pilih salah satu dari 4 modul aktif, lalu isi NIM, Nama, Pertemuan, Kelas, dan jadwal praktikum." },
  { title: "2. Dokumentasi Pre-Test", desc: "Unggah foto Pre-Test lewat drag-drop atau Ctrl+V. Jika tidak ada Pre-Test, matikan toggle." },
  { title: "3. Hasil & Ulasan Praktikum", desc: "Tambahkan foto langkah kerja (Gambar 2.1, 2.2...) dan tulis ulasan dengan meter kelengkapan." },
  { title: "4. Post-Test & Daftar Pustaka", desc: "Lampirkan bukti Post-Test (Gambar 3.1...) dan daftar pustaka bila diperlukan." },
  { title: "5. Review & Unduh .DOCX", desc: "Periksa pratinjau nama file resmi lalu klik Generate untuk mengunduh file Word terformat baku." },
];
let tutIndex = 0;

function openTutorial() {
  tutIndex = 0;
  renderTutorial();
  document.getElementById("tutorialModal").classList.add("show");
}

function closeTutorial() {
  document.getElementById("tutorialModal").classList.remove("show");
  localStorage.setItem(TUTORIAL_SEEN_KEY, "1");
}

function renderTutorial() {
  const item = TUTORIAL_STEPS[tutIndex];
  document.getElementById("tutBadge").textContent = `Langkah ${tutIndex + 1} / 5`;
  document.getElementById("tutTitle").textContent = item.title;
  document.getElementById("tutDesc").textContent = item.desc;
  document.getElementById("tutPrevBtn").style.visibility = tutIndex === 0 ? "hidden" : "visible";
  document.getElementById("tutNextBtn").textContent = tutIndex === 4 ? "Selesai" : "Lanjut";
}

function nextTutorial() {
  if (tutIndex < 4) {
    tutIndex++;
    renderTutorial();
  } else {
    closeTutorial();
  }
}

function prevTutorial() {
  if (tutIndex > 0) {
    tutIndex--;
    renderTutorial();
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadDraft();
  syncInputsFromState();
  bindInputs();
  renderAll();
  loadHistory();
  if (!localStorage.getItem(TUTORIAL_SEEN_KEY)) {
    openTutorial();
  }
});
