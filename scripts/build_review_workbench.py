from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


NINE_STEP_LABELS = {
    "S1": "主題目標",
    "S2": "大概念",
    "S3": "原理",
    "S4": "專家語言",
    "S5": "學生觀察語言",
    "S6": "體驗活動",
    "S7": "證據事實",
    "S8": "探究",
    "S9": "有感應用",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_workbench_data(package_dir: Path) -> dict[str, Any]:
    manifest = read_json(package_dir / "manifest.json")
    review = read_json(package_dir / "review-result.json")
    alignments: dict[int, list[dict[str, Any]]] = {}
    for item in review.get("media_alignment", []):
        alignments.setdefault(int(item["slide"]), []).append(item)
    findings: dict[int, list[dict[str, Any]]] = {}
    for item in review.get("slide_findings", []):
        findings.setdefault(int(item["slide"]), []).append(item)

    slides: list[dict[str, Any]] = []
    for slide in manifest["slides"]:
        number = int(slide["slide"])
        slide_media = alignments.get(number, [])
        slides.append(
            {
                "number": number,
                "image": f"slides/slide-{number:02d}.png",
                "text": slide.get("text", ""),
                "notes": slide.get("notes", ""),
                "has_notes": bool(slide.get("notes", "").strip()),
                "media": [
                    {
                        **item,
                        "path": f"media/{item['media']}",
                    }
                    for item in slide_media
                ],
                "findings": findings.get(number, []),
            }
        )

    step_status: dict[str, str] = {}
    summary = review.get("nine_step_summary", {})
    for status, codes in summary.items():
        for code in codes:
            step_status[code] = status
    nine_steps = [
        {
            "code": code,
            "label": label,
            "status": step_status.get(code, "unknown"),
        }
        for code, label in NINE_STEP_LABELS.items()
    ]

    return {
        "schema_version": "1.0",
        "unit_code": review.get("unit_code", ""),
        "unit_title": review.get("unit_title", ""),
        "decision": review.get("decision", "HOLD"),
        "decision_reason": review.get("decision_reason", ""),
        "source_filename": manifest.get("source_filename", ""),
        "source_sha256": manifest.get("source_sha256", ""),
        "inventory": review.get("inventory", {}),
        "nine_steps": nine_steps,
        "priority_actions": review.get("priority_actions", []),
        "slides": slides,
        "links": {
            "report": "review-report.md",
            "playback": "playback.mp4",
            "manifest": "manifest.json",
            "machine_result": "review-result.json",
        },
    }


HTML_TEMPLATE = r"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>__TITLE__｜教材審查工作台</title>
  <style>
    :root {
      --ink: #172125;
      --muted: #66747a;
      --paper: #f3f7f6;
      --panel: #ffffff;
      --line: #d8e1df;
      --teal: #0c6f69;
      --teal-soft: #d9eeeb;
      --amber: #a65c00;
      --amber-soft: #fff0cf;
      --red: #b63d36;
      --red-soft: #fae5e2;
      --green: #39724c;
      --green-soft: #e4f0e6;
      --shadow: 0 18px 45px rgba(32, 62, 60, .11);
      --radius: 14px;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      overflow: hidden;
      color: var(--ink);
      background:
        linear-gradient(rgba(12,111,105,.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(12,111,105,.045) 1px, transparent 1px),
        var(--paper);
      background-size: 26px 26px;
      font-family: "Noto Sans TC", "Microsoft JhengHei UI", "PingFang TC", sans-serif;
    }
    button, input, textarea { font: inherit; }
    button, a { -webkit-tap-highlight-color: transparent; }
    button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible {
      outline: 3px solid rgba(12,111,105,.3);
      outline-offset: 2px;
    }
    .app { height: 100%; display: grid; grid-template-rows: 76px minmax(0,1fr); }
    .topbar {
      display: grid;
      grid-template-columns: minmax(300px,1fr) auto;
      gap: 24px;
      align-items: center;
      padding: 12px 20px;
      color: white;
      background: #15383a;
      border-bottom: 4px solid #e6a729;
      box-shadow: 0 6px 20px rgba(18,42,43,.16);
      z-index: 10;
    }
    .identity { min-width: 0; display: flex; align-items: center; gap: 14px; }
    .unit-mark {
      display: grid;
      place-items: center;
      width: 44px;
      height: 44px;
      flex: 0 0 auto;
      border: 1px solid rgba(255,255,255,.3);
      border-radius: 50%;
      font: 700 13px/1 "Cascadia Mono", Consolas, monospace;
      color: #ffd976;
    }
    .title-wrap { min-width: 0; }
    .eyebrow {
      margin-bottom: 4px;
      font: 600 11px/1.2 "Cascadia Mono", Consolas, monospace;
      letter-spacing: .12em;
      color: #9fd0cb;
      text-transform: uppercase;
    }
    h1 { margin: 0; overflow: hidden; font-size: 20px; text-overflow: ellipsis; white-space: nowrap; }
    .top-actions { display: flex; align-items: center; gap: 10px; }
    .decision {
      padding: 8px 12px;
      border: 1px solid rgba(255,217,118,.45);
      border-radius: 999px;
      font: 800 12px/1 "Cascadia Mono", Consolas, monospace;
      color: #ffda79;
      background: rgba(0,0,0,.12);
    }
    .top-button, .ghost-button {
      border: 0;
      border-radius: 9px;
      cursor: pointer;
      font-weight: 700;
      transition: transform .16s ease, background .16s ease;
    }
    .top-button { padding: 10px 14px; color: #15383a; background: #ffdf8b; }
    .top-button:hover, .ghost-button:hover { transform: translateY(-1px); }
    .shell {
      min-height: 0;
      display: grid;
      grid-template-columns: 268px minmax(480px,1fr) 390px;
      gap: 12px;
      padding: 12px;
    }
    .panel {
      min-height: 0;
      overflow: hidden;
      background: rgba(255,255,255,.94);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }
    .sidebar { display: grid; grid-template-rows: auto auto minmax(0,1fr); }
    .sidebar-head { padding: 14px; border-bottom: 1px solid var(--line); }
    .search {
      width: 100%;
      padding: 10px 12px;
      color: var(--ink);
      background: #f7faf9;
      border: 1px solid var(--line);
      border-radius: 9px;
    }
    .filters { display: flex; gap: 6px; padding: 10px 12px; overflow-x: auto; border-bottom: 1px solid var(--line); }
    .filter {
      flex: 0 0 auto;
      padding: 7px 9px;
      border: 1px solid var(--line);
      border-radius: 999px;
      color: var(--muted);
      background: white;
      cursor: pointer;
      font-size: 12px;
      font-weight: 700;
    }
    .filter.active { color: white; border-color: var(--teal); background: var(--teal); }
    .slide-list { overflow-y: auto; padding: 8px; }
    .slide-card {
      width: 100%;
      display: grid;
      grid-template-columns: 64px 1fr;
      gap: 10px;
      align-items: center;
      margin: 0 0 7px;
      padding: 7px;
      text-align: left;
      color: inherit;
      background: transparent;
      border: 1px solid transparent;
      border-radius: 10px;
      cursor: pointer;
    }
    .slide-card:hover { background: #f2f8f6; }
    .slide-card.active { background: var(--teal-soft); border-color: #91c8c1; }
    .thumb { width: 64px; aspect-ratio: 16/9; object-fit: cover; background: #dfe8e6; border-radius: 6px; }
    .slide-meta { min-width: 0; }
    .slide-line { display: flex; align-items: center; justify-content: space-between; gap: 6px; }
    .slide-no { font: 700 12px/1 "Cascadia Mono", Consolas, monospace; color: var(--teal); }
    .slide-summary {
      margin-top: 5px;
      overflow: hidden;
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .dots { display: flex; gap: 4px; }
    .dot { width: 7px; height: 7px; border-radius: 50%; background: #c6d1cf; }
    .dot.major { background: var(--red); }
    .dot.minor { background: var(--amber); }
    .dot.video { box-shadow: inset 0 0 0 2px var(--teal); background: white; }
    .viewer { display: grid; grid-template-rows: auto minmax(0,1fr) auto; }
    .viewer-head {
      min-height: 58px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 11px 14px;
      border-bottom: 1px solid var(--line);
    }
    .viewer-title { display: flex; align-items: center; gap: 10px; }
    .viewer-title strong { font-size: 16px; }
    .badges { display: flex; flex-wrap: wrap; gap: 6px; }
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 5px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 800;
    }
    .badge.major, .badge.weak { color: var(--red); background: var(--red-soft); }
    .badge.minor, .badge.partial, .badge.hold { color: var(--amber); background: var(--amber-soft); }
    .badge.strong, .badge.complete { color: var(--green); background: var(--green-soft); }
    .badge.unknown, .badge.insufficient { color: #73545a; background: #eee4e6; }
    .badge.no-notes { color: #5e5b83; background: #eceafa; }
    .view-tabs { display: flex; padding: 4px; background: #edf3f2; border-radius: 9px; }
    .view-tab { padding: 7px 10px; color: var(--muted); background: transparent; border: 0; border-radius: 7px; cursor: pointer; font-size: 12px; font-weight: 800; }
    .view-tab.active { color: var(--teal); background: white; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
    .stage {
      min-height: 0;
      overflow: auto;
      display: grid;
      place-items: center;
      padding: 20px;
      background:
        radial-gradient(circle at 50% 40%, rgba(12,111,105,.08), transparent 52%),
        #e8efed;
    }
    .stage img, .stage video {
      display: block;
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
      background: #071313;
      border-radius: 9px;
      box-shadow: 0 18px 38px rgba(20,45,45,.22);
    }
    .viewer-foot {
      display: grid;
      grid-template-columns: auto minmax(0,1fr) auto;
      gap: 12px;
      align-items: center;
      padding: 10px 14px;
      border-top: 1px solid var(--line);
    }
    .nav-btn { width: 38px; height: 38px; color: var(--teal); background: white; border: 1px solid var(--line); border-radius: 50%; cursor: pointer; font-weight: 900; }
    .nav-btn:disabled { opacity: .35; cursor: default; }
    .evidence-rail {
      min-width: 0;
      display: grid;
      grid-template-columns: 1fr 22px 1fr 22px 1fr;
      align-items: center;
      gap: 5px;
      font-size: 11px;
    }
    .rail-box { min-width: 0; padding: 7px 8px; overflow: hidden; border: 1px solid var(--line); border-radius: 7px; background: #f8fbfa; text-overflow: ellipsis; white-space: nowrap; }
    .rail-label { margin-right: 5px; color: var(--muted); font: 700 9px/1 "Cascadia Mono", Consolas, monospace; }
    .rail-arrow { color: #89a09c; text-align: center; }
    .inspector { display: grid; grid-template-rows: auto minmax(0,1fr); }
    .inspector-tabs { display: grid; grid-template-columns: repeat(3,1fr); padding: 7px; border-bottom: 1px solid var(--line); }
    .inspector-tab { padding: 9px 6px; color: var(--muted); background: transparent; border: 0; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 800; }
    .inspector-tab.active { color: var(--teal); background: var(--teal-soft); }
    .inspector-body { overflow-y: auto; padding: 15px; }
    .section-label { margin: 0 0 9px; color: var(--muted); font: 700 10px/1 "Cascadia Mono", Consolas, monospace; letter-spacing: .12em; text-transform: uppercase; }
    .finding {
      margin-bottom: 10px;
      padding: 12px;
      border: 1px solid var(--line);
      border-left: 4px solid var(--amber);
      border-radius: 9px;
      background: #fff;
    }
    .finding.major { border-left-color: var(--red); }
    .finding h3 { margin: 0 0 6px; font-size: 14px; line-height: 1.35; }
    .finding p { margin: 0; color: var(--muted); font-size: 12px; line-height: 1.55; }
    .finding .action { margin-top: 8px; padding-top: 8px; color: var(--ink); border-top: 1px dashed var(--line); }
    .empty { padding: 20px; color: var(--muted); text-align: center; border: 1px dashed var(--line); border-radius: 9px; }
    .note-card, .media-card, .priority-card {
      margin-bottom: 10px;
      padding: 11px;
      background: #f7faf9;
      border: 1px solid var(--line);
      border-radius: 9px;
      font-size: 12px;
      line-height: 1.55;
    }
    .media-card strong { display: block; margin-bottom: 5px; }
    .step-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
    .step {
      padding: 10px;
      background: #f7faf9;
      border: 1px solid var(--line);
      border-radius: 9px;
    }
    .step-code { font: 800 11px/1 "Cascadia Mono", Consolas, monospace; color: var(--teal); }
    .step-name { margin: 5px 0 7px; font-size: 12px; font-weight: 800; }
    .review-choice { display: grid; grid-template-columns: repeat(3,1fr); gap: 7px; margin-bottom: 12px; }
    .choice {
      padding: 10px 5px;
      color: var(--muted);
      background: white;
      border: 1px solid var(--line);
      border-radius: 8px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 800;
    }
    .choice.active[data-value="pass"] { color: var(--green); border-color: var(--green); background: var(--green-soft); }
    .choice.active[data-value="revise"] { color: var(--amber); border-color: var(--amber); background: var(--amber-soft); }
    .choice.active[data-value="hold"] { color: var(--red); border-color: var(--red); background: var(--red-soft); }
    textarea {
      width: 100%;
      min-height: 150px;
      padding: 11px;
      resize: vertical;
      color: var(--ink);
      background: #fbfdfc;
      border: 1px solid var(--line);
      border-radius: 9px;
      line-height: 1.55;
    }
    .autosave { margin-top: 6px; color: var(--muted); font-size: 11px; }
    dialog { width: min(900px, 92vw); padding: 0; border: 0; border-radius: 14px; box-shadow: 0 28px 80px rgba(0,0,0,.34); }
    dialog::backdrop { background: rgba(4,19,19,.72); }
    .modal-head { display: flex; justify-content: space-between; align-items: center; padding: 13px 16px; color: white; background: #15383a; }
    .modal-head h2 { margin: 0; font-size: 16px; }
    .modal-head button { color: white; background: transparent; border: 0; cursor: pointer; font-size: 23px; }
    dialog video { display: block; width: 100%; background: #000; }
    .toast {
      position: fixed;
      left: 50%;
      bottom: 24px;
      z-index: 100;
      padding: 10px 15px;
      color: white;
      background: #15383a;
      border-radius: 999px;
      opacity: 0;
      transform: translate(-50%, 12px);
      transition: .2s ease;
      pointer-events: none;
    }
    .toast.show { opacity: 1; transform: translate(-50%, 0); }
    @media (max-width: 1120px) {
      body { overflow: auto; }
      .app { height: auto; min-height: 100%; }
      .shell { grid-template-columns: 230px minmax(0,1fr); }
      .inspector { grid-column: 1 / -1; min-height: 520px; }
    }
    @media (max-width: 760px) {
      .app { display: block; }
      .topbar { grid-template-columns: 1fr; }
      .top-actions { flex-wrap: wrap; }
      .shell { display: block; padding: 8px; }
      .panel { margin-bottom: 10px; }
      .sidebar { height: 340px; }
      .viewer { height: 72vh; }
      .viewer-foot { grid-template-columns: auto 1fr auto; }
      .evidence-rail { display: none; }
      .inspector { min-height: 620px; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { scroll-behavior: auto !important; transition: none !important; }
    }
  </style>
</head>
<body>
  <main class="app">
    <header class="topbar">
      <div class="identity">
        <div class="unit-mark" id="unit-mark">PBa</div>
        <div class="title-wrap">
          <div class="eyebrow">EVIDENCE-LED REVIEW WORKBENCH</div>
          <h1 id="unit-title"></h1>
        </div>
      </div>
      <div class="top-actions">
        <span class="decision" id="decision"></span>
        <button class="top-button" id="play-all">播放完整簡報</button>
        <button class="top-button" id="export-review">匯出審查紀錄</button>
      </div>
    </header>
    <section class="shell">
      <aside class="panel sidebar">
        <div class="sidebar-head">
          <input class="search" id="search" type="search" placeholder="搜尋頁面文字或缺失" aria-label="搜尋頁面">
        </div>
        <div class="filters" id="filters"></div>
        <div class="slide-list" id="slide-list" aria-label="投影片清單"></div>
      </aside>

      <section class="panel viewer">
        <div class="viewer-head">
          <div class="viewer-title">
            <strong id="slide-title">第 1 頁</strong>
            <div class="badges" id="slide-badges"></div>
          </div>
          <div class="view-tabs" id="view-tabs">
            <button class="view-tab active" data-mode="slide">投影片</button>
            <button class="view-tab" data-mode="video">本頁影片</button>
          </div>
        </div>
        <div class="stage" id="stage"></div>
        <div class="viewer-foot">
          <button class="nav-btn" id="previous" aria-label="上一頁">←</button>
          <div class="evidence-rail" id="evidence-rail"></div>
          <button class="nav-btn" id="next" aria-label="下一頁">→</button>
        </div>
      </section>

      <aside class="panel inspector">
        <div class="inspector-tabs">
          <button class="inspector-tab active" data-tab="findings">本頁判讀</button>
          <button class="inspector-tab" data-tab="framework">九步驟</button>
          <button class="inspector-tab" data-tab="review">老師覆核</button>
        </div>
        <div class="inspector-body" id="inspector-body"></div>
      </aside>
    </section>
  </main>

  <dialog id="playback-dialog">
    <div class="modal-head">
      <h2>PowerPoint 實際播放預覽</h2>
      <button id="close-playback" aria-label="關閉">×</button>
    </div>
    <video id="playback-video" controls preload="metadata"></video>
  </dialog>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>

  <script>
    const DATA = __DATA__;
    const storageKey = `physics-review:${DATA.unit_code}:${DATA.source_sha256.slice(0, 12)}`;
    const saved = JSON.parse(localStorage.getItem(storageKey) || "{}");
    const state = {
      slide: 1,
      filter: "all",
      query: "",
      viewMode: "slide",
      inspectorTab: "findings",
      reviews: saved.reviews || {}
    };
    const filters = [
      ["all", "全部"],
      ["attention", "需處理"],
      ["video", "有影片"],
      ["notes", "缺講稿"]
    ];
    const severityRank = { blocker: 4, major: 3, minor: 2, suggestion: 1 };

    function esc(value) {
      return String(value ?? "").replace(/[&<>"']/g, ch => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      })[ch]);
    }
    function currentSlide() {
      return DATA.slides.find(item => item.number === state.slide) || DATA.slides[0];
    }
    function slideSeverity(slide) {
      return slide.findings.reduce((best, item) =>
        (severityRank[item.severity] || 0) > (severityRank[best] || 0) ? item.severity : best
      , "");
    }
    function attention(slide) {
      return ["blocker", "major"].includes(slideSeverity(slide)) ||
        slide.media.some(item => ["weak", "partial"].includes(item.rating));
    }
    function filteredSlides() {
      const query = state.query.trim().toLowerCase();
      return DATA.slides.filter(slide => {
        if (state.filter === "attention" && !attention(slide)) return false;
        if (state.filter === "video" && !slide.media.length) return false;
        if (state.filter === "notes" && slide.has_notes) return false;
        if (!query) return true;
        const haystack = [
          slide.text,
          slide.notes,
          ...slide.findings.flatMap(item => [item.title, item.detail, item.action])
        ].join(" ").toLowerCase();
        return haystack.includes(query) || String(slide.number) === query;
      });
    }
    function save() {
      localStorage.setItem(storageKey, JSON.stringify({ reviews: state.reviews }));
    }
    function showToast(message) {
      const toast = document.getElementById("toast");
      toast.textContent = message;
      toast.classList.add("show");
      setTimeout(() => toast.classList.remove("show"), 1800);
    }
    function renderFilters() {
      document.getElementById("filters").innerHTML = filters.map(([key, label]) =>
        `<button class="filter ${state.filter === key ? "active" : ""}" data-filter="${key}">${label}</button>`
      ).join("");
    }
    function renderSlideList() {
      const slides = filteredSlides();
      document.getElementById("slide-list").innerHTML = slides.length ? slides.map(slide => {
        const severity = slideSeverity(slide);
        const summary = slide.findings[0]?.title || slide.text || "未擷取到文字";
        return `<button class="slide-card ${slide.number === state.slide ? "active" : ""}" data-slide="${slide.number}">
          <img class="thumb" src="${esc(slide.image)}" alt="第 ${slide.number} 頁縮圖">
          <span class="slide-meta">
            <span class="slide-line">
              <span class="slide-no">SLIDE ${String(slide.number).padStart(2, "0")}</span>
              <span class="dots">
                ${severity ? `<span class="dot ${severity}" title="${esc(severity)}"></span>` : ""}
                ${slide.media.length ? `<span class="dot video" title="有影片"></span>` : ""}
              </span>
            </span>
            <span class="slide-summary">${esc(summary)}</span>
          </span>
        </button>`;
      }).join("") : `<div class="empty">沒有符合條件的頁面</div>`;
    }
    function renderBadges(slide) {
      const badges = [];
      const severity = slideSeverity(slide);
      if (severity) badges.push(`<span class="badge ${severity}">${severity === "major" ? "重大" : "次要"}缺失</span>`);
      if (!slide.has_notes) badges.push(`<span class="badge no-notes">缺講稿</span>`);
      if (slide.media.length) badges.push(`<span class="badge ${slide.media[0].rating}">影片 ${esc(slide.media[0].rating)}</span>`);
      document.getElementById("slide-badges").innerHTML = badges.join("");
    }
    function renderStage(slide) {
      const stage = document.getElementById("stage");
      const videoTab = document.querySelector('[data-mode="video"]');
      videoTab.disabled = !slide.media.length;
      if (state.viewMode === "video" && slide.media.length) {
        stage.innerHTML = `<video controls preload="metadata" src="${esc(slide.media[0].path)}"></video>`;
      } else {
        state.viewMode = "slide";
        stage.innerHTML = `<img src="${esc(slide.image)}" alt="第 ${slide.number} 頁投影片">`;
      }
      document.querySelectorAll(".view-tab").forEach(button =>
        button.classList.toggle("active", button.dataset.mode === state.viewMode)
      );
    }
    function renderEvidenceRail(slide) {
      const media = slide.media[0];
      if (!media) {
        document.getElementById("evidence-rail").innerHTML = `
          <span class="rail-box"><span class="rail-label">頁面</span>${slide.number}</span>
          <span class="rail-arrow">→</span>
          <span class="rail-box"><span class="rail-label">講稿</span>${slide.has_notes ? "有" : "缺"}</span>
          <span class="rail-arrow">→</span>
          <span class="rail-box"><span class="rail-label">判讀</span>${slide.findings.length ? "需修正" : "待覆核"}</span>`;
        return;
      }
      document.getElementById("evidence-rail").innerHTML = `
        <span class="rail-box" title="${esc(media.role)}"><span class="rail-label">主張</span>${esc(media.role)}</span>
        <span class="rail-arrow">→</span>
        <span class="rail-box" title="${esc(media.reason)}"><span class="rail-label">證據</span>${esc(media.reason)}</span>
        <span class="rail-arrow">→</span>
        <span class="rail-box"><span class="rail-label">判定</span>${esc(media.rating)}</span>`;
    }
    function findingsHtml(slide) {
      const cards = slide.findings.length ? slide.findings.map(item => `
        <article class="finding ${esc(item.severity)}">
          <h3>${esc(item.title)}</h3>
          <p>${esc(item.detail)}</p>
          <p class="action"><strong>建議：</strong>${esc(item.action)}</p>
        </article>`).join("") : `<div class="empty">本頁沒有預先標記的重大缺失，仍請人工確認。</div>`;
      const media = slide.media.map(item => `
        <div class="media-card">
          <strong>${esc(item.media)} · <span class="badge ${esc(item.rating)}">${esc(item.rating)}</span></strong>
          ${esc(item.reason)}
        </div>`).join("");
      const note = `<div class="note-card"><strong>Speaker notes：</strong>
        ${slide.has_notes ? esc(slide.notes) : "未提供；自學教材需要補本頁目標、觀察焦點、解釋與轉場。"}</div>`;
      return `<p class="section-label">本頁缺失</p>${cards}
        ${media ? `<p class="section-label">影音關聯</p>${media}` : ""}
        <p class="section-label">自學支援</p>${note}`;
    }
    function frameworkHtml() {
      const steps = DATA.nine_steps.map(step => `
        <div class="step">
          <span class="step-code">${esc(step.code)}</span>
          <div class="step-name">${esc(step.label)}</div>
          <span class="badge ${esc(step.status)}">${statusLabel(step.status)}</span>
        </div>`).join("");
      const priorities = DATA.priority_actions.map((item, index) =>
        `<div class="priority-card"><strong>P${index + 1}</strong>　${esc(item)}</div>`
      ).join("");
      return `<p class="section-label">九步驟總覽</p><div class="step-grid">${steps}</div>
        <p class="section-label" style="margin-top:18px">上架前優先處理</p>${priorities}`;
    }
    function reviewHtml(slide) {
      const review = state.reviews[slide.number] || {};
      return `<p class="section-label">第 ${slide.number} 頁人工判定</p>
        <div class="review-choice">
          ${["pass", "revise", "hold"].map(value =>
            `<button class="choice ${review.decision === value ? "active" : ""}" data-review-value="${value}">${statusLabel(value)}</button>`
          ).join("")}
        </div>
        <p class="section-label">老師意見</p>
        <textarea id="review-note" placeholder="記錄要保留的優點、需修正處或判定理由…">${esc(review.note || "")}</textarea>
        <div class="autosave">內容只保存在這台電腦；按「匯出審查紀錄」可交給下一輪 Skill。</div>`;
    }
    function statusLabel(status) {
      return ({ complete: "完整", partial: "部分", insufficient: "不足", unknown: "待確認",
        pass: "通過", revise: "修改", hold: "暫緩" })[status] || status;
    }
    function renderInspector(slide) {
      const body = document.getElementById("inspector-body");
      body.innerHTML = state.inspectorTab === "findings" ? findingsHtml(slide) :
        state.inspectorTab === "framework" ? frameworkHtml() : reviewHtml(slide);
    }
    function renderViewer() {
      const slide = currentSlide();
      document.getElementById("slide-title").textContent = `第 ${slide.number} 頁`;
      renderBadges(slide);
      renderStage(slide);
      renderEvidenceRail(slide);
      document.getElementById("previous").disabled = slide.number === 1;
      document.getElementById("next").disabled = slide.number === DATA.slides.length;
      renderInspector(slide);
    }
    function render() {
      renderFilters();
      renderSlideList();
      renderViewer();
      const reviewed = Object.values(state.reviews).filter(item => item.decision || item.note).length;
      document.getElementById("decision").textContent = `${DATA.decision} · 已覆核 ${reviewed}/${DATA.slides.length}`;
    }
    function goToSlide(number) {
      if (number < 1 || number > DATA.slides.length) return;
      state.slide = number;
      state.viewMode = "slide";
      render();
      document.querySelector(".slide-card.active")?.scrollIntoView({ block: "nearest" });
    }
    function exportReview() {
      const payload = {
        schema_version: "1.0",
        unit_code: DATA.unit_code,
        unit_title: DATA.unit_title,
        source_sha256: DATA.source_sha256,
        exported_at: new Date().toISOString(),
        original_decision: DATA.decision,
        teacher_reviews: Object.entries(state.reviews).map(([slide, value]) => ({
          slide: Number(slide),
          decision: value.decision || "",
          note: value.note || ""
        }))
      };
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${DATA.unit_code || "unit"}-teacher-review.json`;
      link.click();
      URL.revokeObjectURL(url);
      showToast("審查紀錄已匯出");
    }

    document.getElementById("unit-title").textContent = `${DATA.unit_code}｜${DATA.unit_title}教材審查`;
    document.getElementById("unit-mark").textContent = (DATA.unit_code || "PHY").split("-")[0];
    document.getElementById("filters").addEventListener("click", event => {
      const button = event.target.closest("[data-filter]");
      if (!button) return;
      state.filter = button.dataset.filter;
      renderFilters();
      renderSlideList();
    });
    document.getElementById("slide-list").addEventListener("click", event => {
      const card = event.target.closest("[data-slide]");
      if (card) goToSlide(Number(card.dataset.slide));
    });
    document.getElementById("search").addEventListener("input", event => {
      state.query = event.target.value;
      renderSlideList();
    });
    document.getElementById("view-tabs").addEventListener("click", event => {
      const button = event.target.closest("[data-mode]");
      if (!button || button.disabled) return;
      state.viewMode = button.dataset.mode;
      renderStage(currentSlide());
    });
    document.querySelector(".inspector-tabs").addEventListener("click", event => {
      const button = event.target.closest("[data-tab]");
      if (!button) return;
      state.inspectorTab = button.dataset.tab;
      document.querySelectorAll(".inspector-tab").forEach(item =>
        item.classList.toggle("active", item === button)
      );
      renderInspector(currentSlide());
    });
    document.getElementById("inspector-body").addEventListener("click", event => {
      const choice = event.target.closest("[data-review-value]");
      if (!choice) return;
      const review = state.reviews[state.slide] || {};
      review.decision = choice.dataset.reviewValue;
      state.reviews[state.slide] = review;
      save();
      render();
    });
    document.getElementById("inspector-body").addEventListener("input", event => {
      if (event.target.id !== "review-note") return;
      const review = state.reviews[state.slide] || {};
      review.note = event.target.value;
      state.reviews[state.slide] = review;
      save();
    });
    document.getElementById("previous").addEventListener("click", () => goToSlide(state.slide - 1));
    document.getElementById("next").addEventListener("click", () => goToSlide(state.slide + 1));
    document.getElementById("export-review").addEventListener("click", exportReview);
    document.addEventListener("keydown", event => {
      if (["INPUT", "TEXTAREA", "VIDEO"].includes(event.target.tagName)) return;
      if (event.key === "ArrowLeft") goToSlide(state.slide - 1);
      if (event.key === "ArrowRight") goToSlide(state.slide + 1);
    });
    const dialog = document.getElementById("playback-dialog");
    const playback = document.getElementById("playback-video");
    document.getElementById("play-all").addEventListener("click", () => {
      playback.src = DATA.links.playback;
      dialog.showModal();
    });
    document.getElementById("close-playback").addEventListener("click", () => {
      playback.pause();
      dialog.close();
    });
    dialog.addEventListener("close", () => playback.pause());
    render();
  </script>
</body>
</html>
"""


def build_html(data: dict[str, Any]) -> str:
    title = f"{data['unit_code']} {data['unit_title']}".strip()
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</script", "<\\/script")
    return HTML_TEMPLATE.replace("__TITLE__", title).replace("__DATA__", payload)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an offline PPTX review workbench from a review package."
    )
    parser.add_argument("package_dir", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        help="Defaults to PACKAGE_DIR/review-workbench.html",
    )
    args = parser.parse_args()
    package_dir = args.package_dir.resolve()
    output = (
        args.output.resolve()
        if args.output
        else package_dir / "review-workbench.html"
    )
    data = build_workbench_data(package_dir)
    output.write_text(build_html(data), encoding="utf-8")
    print(
        json.dumps(
            {
                "workbench": str(output),
                "slides": len(data["slides"]),
                "unit_code": data["unit_code"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
