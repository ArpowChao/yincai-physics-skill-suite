const STORAGE_KEY = "tts-pronunciation-personal-rules-v1";
const SHARED_RULE_ISSUE_URL = "https://github.com/ArpowChao/yincai-physics-skill-suite/issues/new";
const FALLBACK_CONFIRMED_RULES = [
  {
    original: "主角",
    spoken: "主腳",
    pronunciation: "ㄓㄨˇ ㄐㄧㄠˇ",
    verified: true,
    note: "臺灣口語讀音；原稿仍保留「主角」。",
  },
  {
    original: "角色",
    spoken: "腳色",
    pronunciation: "ㄐㄧㄠˇ ㄙㄜˋ",
    verified: true,
    note: "「腳色」亦為教育部辭典收錄寫法，只用於配音稿。",
  },
];
const FALLBACK_FORMULA_CONFIG = {
  operators: {
    "+": "加上",
    "-": "減去",
    "−": "減去",
    "*": "乘以",
    "×": "乘以",
    "÷": "除以",
    "=": "等於",
    "≠": "不等於",
    ">=": "大於或等於",
    "≤": "小於或等於",
    "<=": "小於或等於",
    "≥": "大於或等於",
    ">": "大於",
    "<": "小於",
  },
  superscripts: {
    "²": "的平方",
    "³": "的三次方",
  },
};

const elements = {
  source: document.querySelector("#sourceText"),
  speech: document.querySelector("#speechText"),
  preview: document.querySelector("#sourcePreview"),
  reviewList: document.querySelector("#reviewList"),
  analyze: document.querySelector("#analyzeButton"),
  confirmedCount: document.querySelector("#confirmedCount"),
  referenceCount: document.querySelector("#referenceCount"),
  crossStraitCount: document.querySelector("#crossStraitCount"),
  changeCount: document.querySelector("#changeCount"),
  announcement: document.querySelector("#announcement"),
  fileInput: document.querySelector("#fileInput"),
  copy: document.querySelector("#copyButton"),
  download: document.querySelector("#downloadButton"),
  downloadChanges: document.querySelector("#downloadChangesButton"),
  ruleForm: document.querySelector("#ruleForm"),
  ruleOriginal: document.querySelector("#ruleOriginal"),
  ruleSpoken: document.querySelector("#ruleSpoken"),
  personalRuleSummary: document.querySelector("#personalRuleSummary"),
  ruleFileInput: document.querySelector("#ruleFileInput"),
  exportRules: document.querySelector("#exportRulesButton"),
  clearRules: document.querySelector("#clearRulesButton"),
  emptyTemplate: document.querySelector("#emptyReviewTemplate"),
  reviewFilters: document.querySelectorAll("[data-review-filter]"),
  keepAllPending: document.querySelector("#keepAllPendingButton"),
  reviewVisibleCount: document.querySelector("#reviewVisibleCount"),
  importChoice: document.querySelector("#importChoice"),
  pasteChoice: document.querySelector("#pasteChoice"),
  submitSharedRule: document.querySelector("#submitSharedRuleButton"),
  sharedRuleHint: document.querySelector("#sharedRuleHint"),
};

let confirmedRules = FALLBACK_CONFIRMED_RULES;
let formulaConfig = FALLBACK_FORMULA_CONFIG;
const referenceRules = (globalThis.MOE_HETERONYM_LEXICON?.rules || []).map(
  ([original, spoken, pronunciation]) => ({
    original,
    spoken,
    pronunciation,
    verified: false,
    source: "moe-reference",
    note: "教育部辭典讀音參考；同音字是配音草稿，套用前請人工確認。",
  }),
);
const crossStraitRules = (
  globalThis.CROSS_STRAIT_PRONUNCIATION_CANDIDATES?.rules || []
).map(([original, spoken, taiwanPronunciation, mainlandPronunciation, hasFullSuggestion]) => ({
  original,
  spoken,
  pronunciation: taiwanPronunciation,
  mainlandPronunciation,
  hasFullSuggestion,
  verified: false,
  source: "cross-strait-reference",
  note: "兩岸詞典讀音差異；同音字是依臺灣讀音產生的草稿，請用目標 TTS 試聽後再套用。",
}));
const pendingRules = [...crossStraitRules, ...referenceRules].sort((left, right) =>
  right.original.length - left.original.length
  || Number(right.source === "cross-strait-reference") - Number(left.source === "cross-strait-reference"),
);
const pendingRulesByFirst = new Map();
for (const rule of pendingRules) {
  const bucket = pendingRulesByFirst.get(rule.original[0]) || [];
  bucket.push(rule);
  pendingRulesByFirst.set(rule.original[0], bucket);
}
let submissionConfig = {
  apps_script_url: "https://script.google.com/macros/s/AKfycbzT2KEB4aqvUOLKOSqJvaTbFLZ7g-fAg275eifarNYOqNQBSuvtM3wbg7kmpwiypTRF/exec",
  github_issue_fallback: true,
};
let personalRules = loadPersonalRules();
let analysis = { source_text: elements.source.value, speech_text: elements.source.value, changes: [] };
let decisions = new Map();
let reviewFilter = "all";

function loadPersonalRules() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

function savePersonalRules() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(personalRules));
  renderPersonalRuleSummary();
}

function renderSubmissionProvider() {
  if (submissionConfig.apps_script_url) {
    elements.submitSharedRule.textContent = "送到 Google 共用候選表";
    elements.sharedRuleHint.textContent = "送出後會新增到團隊試算表，狀態預設為待確認。";
    return;
  }
  elements.submitSharedRule.textContent = "送交 GitHub 共用詞庫";
  elements.sharedRuleHint.textContent = "GitHub 會要求登入；送出後由團隊人工確認。";
}

function contextAround(text, phrase, limit = 240) {
  const index = text.indexOf(phrase);
  if (index < 0) return text.slice(0, limit);
  const padding = Math.floor((limit - phrase.length) / 2);
  return text.slice(Math.max(0, index - padding), index + phrase.length + padding);
}

function submitToAppsScript(endpoint, payload) {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = endpoint;
  form.target = "sharedRuleSubmissionFrame";
  form.className = "visually-hidden";
  for (const [name, value] of Object.entries(payload)) {
    const input = document.createElement("input");
    input.name = name;
    input.value = value;
    form.append(input);
  }
  const honeypot = document.createElement("input");
  honeypot.name = "website";
  honeypot.value = "";
  form.append(honeypot);
  document.body.append(form);
  form.submit();
  form.remove();
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function narrateFormula(formula) {
  let spoken = formula.replace(
    /([A-Za-zα-ωΑ-Ω][A-Za-z0-9₀-₉]*|\d+)\s*\/\s*([A-Za-zα-ωΑ-Ω][A-Za-z0-9₀-₉]*|\d+)/gu,
    (_, numerator, denominator) => `${denominator} 分之 ${numerator}`,
  );
  spoken = spoken.replace(/√\s*([A-Za-z0-9α-ωΑ-Ω₀-₉]+)/gu, "根號 $1");
  for (const [symbol, narration] of Object.entries(formulaConfig.superscripts || {})) {
    spoken = spoken.replaceAll(symbol, ` ${narration}`);
  }
  const operators = Object.entries(formulaConfig.operators || {}).sort(
    ([left], [right]) => right.length - left.length,
  );
  for (const [symbol, narration] of operators) {
    spoken = spoken.replace(
      new RegExp(`\\s*${escapeRegExp(symbol)}\\s*`, "gu"),
      `，${narration} `,
    );
  }
  return spoken
    .replace(/\s+/gu, " ")
    .replace(/\s*，\s*/gu, "，")
    .replace(/^[ ，]+|[ ，]+$/gu, "");
}

function findFormulaChanges(text) {
  const changes = [];
  const lines = text.match(/[^\n]*\n|[^\n]+$/gu) || [text];
  let offset = 0;
  for (const line of lines) {
    const content = line.replace(/\r?\n$/u, "");
    if (!content.includes("-->")) {
      const runs = content.matchAll(/[A-Za-z0-9α-ωΑ-Ω₀-₉⁰¹²³⁴⁵⁶⁷⁸⁹√∫∑∞+\-−*/×÷=≠≤≥<>^().{}[\],\s]+/gu);
      for (const match of runs) {
        const candidate = match[0];
        const core = candidate.trim();
        if (!core || !/[²³√∫∑∞+*/×÷=≠≤≥<>]|>=|<=/u.test(core)) continue;
        const spoken = narrateFormula(core);
        if (spoken === core) continue;
        const leading = candidate.length - candidate.trimStart().length;
        const trailing = candidate.length - candidate.trimEnd().length;
        const start = offset + match.index + leading;
        const end = offset + match.index + candidate.length - trailing;
        changes.push({
          id: `formula-${start}-${end}`,
          type: "formula",
          start,
          end,
          original: text.slice(start, end),
          spoken,
          pronunciation: "",
          verified: true,
          source: "confirmed",
          note: "依已確認的基礎公式朗讀規則展開；複雜公式請人工確認。",
        });
      }
    }
    offset += line.length;
  }
  return changes;
}

function analyzeLocally(text, overrides = []) {
  const merged = new Map();
  for (const rule of confirmedRules) {
    if (!rule.original || !rule.spoken) continue;
    merged.set(rule.original, { ...rule, source: "confirmed", verified: Boolean(rule.verified) });
  }
  for (const rule of overrides) {
    if (!rule.original || !rule.spoken) continue;
    merged.set(rule.original, { ...rule, source: "personal", verified: false });
  }
  const rules = [...merged.values()].sort((left, right) => right.original.length - left.original.length);
  const byFirst = new Map();
  for (const rule of rules) {
    const bucket = byFirst.get(rule.original[0]) || [];
    bucket.push(rule);
    byFirst.set(rule.original[0], bucket);
  }

  const phraseChanges = [];
  let index = 0;
  while (index < text.length) {
    const match = (byFirst.get(text[index]) || []).find((rule) => text.startsWith(rule.original, index));
    if (!match) {
      index += 1;
      continue;
    }
    const end = index + match.original.length;
    phraseChanges.push({
      id: `phrase-${index}-${end}`,
      type: "pronunciation",
      start: index,
      end,
      original: match.original,
      spoken: match.spoken,
      pronunciation: match.pronunciation || "",
      verified: match.verified,
      source: match.source,
      note: match.note || "",
    });
    index = end;
  }

  const pendingChanges = [];
  index = 0;
  while (index < text.length) {
    const match = (pendingRulesByFirst.get(text[index]) || []).find(
      (rule) => text.startsWith(rule.original, index),
    );
    if (!match) {
      index += 1;
      continue;
    }
    const end = index + match.original.length;
    const overlapsConfirmed = phraseChanges.some(
      (change) => index < change.end && change.start < end,
    );
    if (!overlapsConfirmed) {
      const type = match.source === "cross-strait-reference" ? "cross-strait" : "reference";
      pendingChanges.push({
        id: `${type}-${index}-${end}`,
        type,
        start: index,
        end,
        original: match.original,
        spoken: match.spoken,
        pronunciation: match.pronunciation || "",
        mainlandPronunciation: match.mainlandPronunciation || "",
        hasFullSuggestion: match.hasFullSuggestion !== false,
        verified: false,
        source: match.source,
        note: match.note,
      });
    }
    index = end;
  }

  const changes = [];
  for (const change of [...phraseChanges, ...pendingChanges, ...findFormulaChanges(text)].sort(
    (a, b) => a.start - b.start,
  )) {
    if (changes.length && change.start < changes.at(-1).end) continue;
    changes.push(change);
  }
  return { source_text: text, speech_text: text, changes };
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function downloadText(filename, text, type = "text/plain;charset=utf-8") {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([text], { type }));
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
}

function outputFilename(suffix) {
  const imported = elements.fileInput.files?.[0]?.name || "transcript.txt";
  const base = imported.replace(/\.[^.]+$/, "");
  return `${base}${suffix}`;
}

function renderPersonalRuleSummary() {
  elements.personalRuleSummary.textContent = personalRules.length
    ? `這台電腦目前有 ${personalRules.length} 條個人規則。`
    : "尚未加入個人規則。";
}

function decisionFor(change) {
  return decisions.get(change.id) || {
    status: isPendingChange(change) ? "pending" : "accepted",
    spoken: change.spoken,
  };
}

function isPendingChange(change) {
  return change.type === "reference" || change.type === "cross-strait";
}

function buildSpeechText() {
  const parts = [];
  let cursor = 0;
  for (const change of analysis.changes) {
    const decision = decisionFor(change);
    parts.push(analysis.source_text.slice(cursor, change.start));
    parts.push(decision.status === "accepted" ? decision.spoken : change.original);
    cursor = change.end;
  }
  parts.push(analysis.source_text.slice(cursor));
  return parts.join("");
}

function renderSpeechText() {
  elements.speech.value = buildSpeechText();
}

function renderPreview() {
  const parts = [];
  let cursor = 0;
  for (const change of analysis.changes) {
    const decision = decisionFor(change);
    parts.push(escapeHtml(analysis.source_text.slice(cursor, change.start)));
    parts.push(
      `<mark tabindex="0" data-change-id="${change.id}" data-type="${change.type}" ` +
        `data-status="${decision.status}" title="建議讀成：${escapeHtml(decision.spoken)}">` +
        `${escapeHtml(change.original)}</mark>`,
    );
    cursor = change.end;
  }
  parts.push(escapeHtml(analysis.source_text.slice(cursor)));
  elements.preview.innerHTML = parts.join("");
  elements.preview.querySelectorAll("mark").forEach((mark) => {
    const focusCard = () => {
      const card = document.getElementById(`review-${mark.dataset.changeId}`);
      if (!card) return;
      card.open = true;
      document.querySelectorAll(".review-card[open]").forEach((item) => {
        if (item !== card) item.open = false;
      });
      document.querySelectorAll(".review-card.is-focused").forEach((item) => item.classList.remove("is-focused"));
      card.classList.add("is-focused");
      card.scrollIntoView({ behavior: "smooth", block: "center" });
    };
    mark.addEventListener("click", focusCard);
    mark.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") focusCard();
    });
  });
}

function applyReviewFilter() {
  let visible = 0;
  elements.reviewList.querySelectorAll(".review-card").forEach((card) => {
    const matches = reviewFilter === "all"
      || (reviewFilter === "pending" && card.dataset.status === "pending")
      || (reviewFilter === "handled" && card.dataset.status !== "pending");
    card.hidden = !matches;
    if (matches) visible += 1;
  });
  elements.reviewFilters.forEach((button) => {
    const active = button.dataset.reviewFilter === reviewFilter;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  elements.reviewVisibleCount.textContent = `顯示 ${visible}／${analysis.changes.length} 筆`;
}

function renderReviewCards() {
  elements.reviewList.replaceChildren();
  if (!analysis.changes.length) {
    elements.reviewList.append(elements.emptyTemplate.content.cloneNode(true));
    return;
  }

  analysis.changes.forEach((change, index) => {
    const decision = decisionFor(change);
    const card = document.createElement("details");
    card.className = "review-card";
    card.id = `review-${change.id}`;
    card.dataset.type = change.type;
    card.dataset.status = decision.status;
    card.open = index === 0;
    const kind = change.type === "formula"
      ? "公式念法"
      : change.type === "cross-strait"
        ? "兩岸讀音差異"
      : change.type === "reference"
        ? "多音詞參考"
        : "讀音替換";
    const sourceBadge = change.type === "cross-strait"
      ? '<span class="review-card__cross-strait">兩岸詞典</span>'
      : change.type === "reference"
        ? '<span class="review-card__reference">教育部讀音</span>'
        : "";
    const pronunciationComparison = change.type === "cross-strait"
      ? `<div class="pronunciation-comparison" aria-label="臺灣與中國讀音比較">
          <div class="pronunciation-comparison__item pronunciation-comparison__item--taiwan">
            <span>臺灣建議讀音</span>
            <strong>${escapeHtml(change.pronunciation)}</strong>
          </div>
          <div class="pronunciation-comparison__item pronunciation-comparison__item--mainland">
            <span>中國資料讀音</span>
            <strong>${escapeHtml(change.mainlandPronunciation)}</strong>
          </div>
        </div>`
      : "";
    const pendingLabel = change.hasFullSuggestion
      ? "同音字草稿（確認後再套用）"
      : "尚無完整替代，請自行修改後套用";
    card.innerHTML = `
      <summary class="review-card__summary">
        <span class="review-card__number">${String(index + 1).padStart(2, "0")}</span>
        <span class="review-card__compact">
          <span class="review-card__compact-meta">
            <span class="review-card__kind">${kind}</span>
            <span class="review-card__status">${decision.status === "pending" ? "待確認" : decision.status === "accepted" ? "已套用" : "保留原稿"}</span>
          </span>
          <span class="review-card__compact-change">
            <strong>${escapeHtml(change.original)}</strong>
            <span aria-hidden="true">→</span>
            <span class="review-card__compact-spoken">${escapeHtml(decision.spoken)}</span>
          </span>
        </span>
        <span class="review-card__chevron" aria-hidden="true">⌄</span>
      </summary>
      <div class="review-card__body">
        <div class="review-card__meta">
          <span class="review-card__kind">${kind}</span>
          ${change.verified ? '<span class="review-card__verified">已確認</span>' : ""}
          ${sourceBadge}
        </div>
        ${pronunciationComparison}
        <p class="review-card__original"><span>原稿</span><strong>${escapeHtml(change.original)}</strong></p>
        <span class="review-card__arrow" aria-hidden="true">↓ 改成</span>
        <label class="field-label review-card__spoken-label" for="spoken-${change.id}">${isPendingChange(change) ? pendingLabel : "配音稿建議"}</label>
        <textarea class="review-card__input" id="spoken-${change.id}" rows="2">${escapeHtml(decision.spoken)}</textarea>
        ${change.note ? `<p class="review-card__note">${escapeHtml(change.note)}</p>` : ""}
        <div class="review-card__actions">
          <button class="review-card__accept" type="button">${isPendingChange(change) ? "確認並套用" : "套用建議"}</button>
          <button class="review-card__ignore" type="button">保留原稿</button>
        </div>
      </div>`;

    const input = card.querySelector("textarea");
    const compactSpoken = card.querySelector(".review-card__compact-spoken");
    const statusBadge = card.querySelector(".review-card__status");
    const updateCardState = (status) => {
      card.dataset.status = status;
      compactSpoken.textContent = input.value;
      statusBadge.textContent = status === "pending" ? "待確認" : status === "accepted" ? "已套用" : "保留原稿";
      applyReviewFilter();
    };
    card.addEventListener("toggle", () => {
      if (!card.open) return;
      elements.reviewList.querySelectorAll(".review-card[open]").forEach((item) => {
        if (item !== card) item.open = false;
      });
    });
    input.addEventListener("input", () => {
      decisions.set(change.id, { status: "accepted", spoken: input.value });
      updateCardState("accepted");
      renderSpeechText();
      renderPreview();
    });
    card.querySelector(".review-card__accept").addEventListener("click", () => {
      decisions.set(change.id, { status: "accepted", spoken: input.value });
      updateCardState("accepted");
      renderSpeechText();
      renderPreview();
    });
    card.querySelector(".review-card__ignore").addEventListener("click", () => {
      decisions.set(change.id, { status: "ignored", spoken: input.value });
      updateCardState("ignored");
      renderSpeechText();
      renderPreview();
    });
    elements.reviewList.append(card);
  });
  applyReviewFilter();
}

function renderAnalysis() {
  elements.changeCount.textContent = String(analysis.changes.length);
  renderReviewCards();
  renderPreview();
  renderSpeechText();
  elements.announcement.textContent = analysis.changes.length
    ? `找到 ${analysis.changes.length} 個可確認項目。`
    : "沒有找到已知項目；需要時可新增個人規則。";
}

async function analyzeText() {
  elements.analyze.disabled = true;
  elements.announcement.textContent = "正在檢查逐字稿…";
  try {
    analysis = analyzeLocally(elements.source.value, personalRules);
    decisions = new Map(
      analysis.changes.map((change) => [
        change.id,
        {
          status: isPendingChange(change) ? "pending" : "accepted",
          spoken: change.spoken,
        },
      ]),
    );
    renderAnalysis();
  } catch (error) {
    elements.announcement.textContent = `無法檢查：${error.message}`;
  } finally {
    elements.analyze.disabled = false;
  }
}

async function useFallbackConfig(modeLabel = "本機模式") {
  renderSubmissionProvider();
  elements.confirmedCount.textContent = String(confirmedRules.length);
  elements.referenceCount.textContent = String(referenceRules.length);
  elements.crossStraitCount.textContent = String(crossStraitRules.length);
  renderPersonalRuleSummary();
  await analyzeText();
  elements.announcement.textContent = analysis.changes.length
    ? `${modeLabel}：使用內建詞庫，找到 ${analysis.changes.length} 個可確認項目。`
    : `${modeLabel}：已載入內建詞庫，沒有找到已知項目。`;
}

async function loadConfig() {
  if (window.location.protocol === "file:") {
    await useFallbackConfig();
    return;
  }
  try {
    const [rulesResponse, formulasResponse, submissionResponse] = await Promise.all([
      fetch("data/verified.json"),
      fetch("data/formulas.json"),
      fetch("data/submission.json"),
    ]);
    if (!rulesResponse.ok || !formulasResponse.ok || !submissionResponse.ok) {
      throw new Error("找不到共用規則檔");
    }
    const rulesPayload = await rulesResponse.json();
    formulaConfig = await formulasResponse.json();
    submissionConfig = await submissionResponse.json();
    confirmedRules = rulesPayload.rules || [];
    renderSubmissionProvider();
    elements.confirmedCount.textContent = String(confirmedRules.length);
    elements.referenceCount.textContent = String(referenceRules.length);
    elements.crossStraitCount.textContent = String(crossStraitRules.length);
    renderPersonalRuleSummary();
    await analyzeText();
  } catch (error) {
    await useFallbackConfig("備援模式");
  }
}

elements.analyze.addEventListener("click", analyzeText);
elements.importChoice.addEventListener("click", () => elements.fileInput.click());
elements.pasteChoice.addEventListener("click", () => {
  elements.source.scrollIntoView({ behavior: "smooth", block: "center" });
  elements.source.focus();
  elements.source.select();
  elements.announcement.textContent = "已選取輸入框，可直接貼上文字。";
});
elements.source.addEventListener("input", () => {
  elements.announcement.textContent = "原稿已修改，請重新檢查。";
});

elements.fileInput.addEventListener("change", async () => {
  const [file] = elements.fileInput.files;
  if (!file) return;
  elements.source.value = await file.text();
  await analyzeText();
});

elements.copy.addEventListener("click", async () => {
  await navigator.clipboard.writeText(elements.speech.value);
  elements.announcement.textContent = "配音稿已複製。";
});

elements.download.addEventListener("click", () => {
  downloadText(outputFilename(".tts.txt"), elements.speech.value);
});

elements.downloadChanges.addEventListener("click", () => {
  const changes = analysis.changes.map((change) => ({
    ...change,
    decision: decisionFor(change),
  }));
  downloadText(
    outputFilename(".changes.json"),
    JSON.stringify({ schema_version: 1, changes }, null, 2),
    "application/json;charset=utf-8",
  );
});

elements.ruleForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const original = elements.ruleOriginal.value.trim();
  const spoken = elements.ruleSpoken.value.trim();
  if (!original || !spoken) return;
  personalRules = personalRules.filter((rule) => rule.original !== original);
  personalRules.push({ original, spoken, verified: false, source: "personal" });
  savePersonalRules();
  elements.ruleForm.reset();
  await analyzeText();
});

elements.submitSharedRule.addEventListener("click", () => {
  if (!elements.ruleForm.reportValidity()) return;
  const original = elements.ruleOriginal.value.trim();
  const spoken = elements.ruleSpoken.value.trim();
  if (submissionConfig.apps_script_url) {
    submitToAppsScript(submissionConfig.apps_script_url, {
      original,
      spoken,
      context: contextAround(elements.source.value, original),
      source_url: window.location.href,
    });
    elements.announcement.textContent = "已送到 Google 共用候選表，等待團隊確認。";
    return;
  }
  const query = new URLSearchParams({
    template: "tts-pronunciation.yml",
    title: `[讀音建議] ${original} → ${spoken}`,
    original,
    spoken,
  });
  window.open(`${SHARED_RULE_ISSUE_URL}?${query}`, "_blank", "noopener,noreferrer");
  elements.announcement.textContent = "已開啟 GitHub 讀音建議表；確認內容後送出即可。";
});

elements.ruleFileInput.addEventListener("change", async () => {
  const [file] = elements.ruleFileInput.files;
  if (!file) return;
  try {
    const payload = JSON.parse(await file.text());
    const rules = Array.isArray(payload) ? payload : payload.rules;
    if (!Array.isArray(rules)) throw new Error("找不到 rules 陣列");
    personalRules = rules.filter((rule) => rule.original && rule.spoken);
    savePersonalRules();
    await analyzeText();
  } catch (error) {
    elements.announcement.textContent = `個人詞庫格式錯誤：${error.message}`;
  }
});

elements.exportRules.addEventListener("click", () => {
  downloadText(
    "tts-pronunciation-personal-rules.json",
    JSON.stringify({ schema_version: 1, rules: personalRules }, null, 2),
    "application/json;charset=utf-8",
  );
});

elements.clearRules.addEventListener("click", async () => {
  personalRules = [];
  savePersonalRules();
  await analyzeText();
});

elements.reviewFilters.forEach((button) => {
  button.addEventListener("click", () => {
    reviewFilter = button.dataset.reviewFilter;
    applyReviewFilter();
  });
});

elements.keepAllPending.addEventListener("click", () => {
  let changed = 0;
  for (const change of analysis.changes) {
    const decision = decisionFor(change);
    if (decision.status !== "pending") continue;
    decisions.set(change.id, { status: "ignored", spoken: decision.spoken });
    changed += 1;
  }
  renderReviewCards();
  renderPreview();
  renderSpeechText();
  elements.announcement.textContent = changed
    ? `已將 ${changed} 筆待確認項目設為保留原稿。`
    : "目前沒有待確認項目。";
});

loadConfig();
