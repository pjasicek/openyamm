"use strict";
(() => {
  const report = window.SPILL_REPORT;
  const FLAGS_KEY = "openyamm-icon-spill-flags-v1";
  const VIEW_KEY = "openyamm-icon-spill-view-v1";
  const reasons = [
    {id: "border_magenta", label: "Border magenta / possible bad crop"},
    {id: "outline_spill", label: "Spill on outline"},
    {id: "interior_spill", label: "Spill inside image"},
    {id: "other", label: "Other"},
  ];
  const get = id => document.getElementById(id);
  const filterIds = ["scope", "status", "color", "reviewFilter", "search"];
  const main = document.querySelector("main");
  const keyFor = row => JSON.stringify([row.scope, row.target || "", row.path, row.sha256, row.crop || null]);
  const rows = report.records.map(row => ({...row, reviewKey: keyFor(row)}));
  const cards = new Map();
  let flags = {}, view = {}, filtered = [], selected = null, shown = 40, reasonIndex = 0;
  let storageError = false;

  function notice(text, error = false) {
    get("saveState").textContent = text;
    get("saveState").classList.toggle("error", error);
  }
  function readFlags() {
    const raw = localStorage.getItem(FLAGS_KEY);
    if (!raw) return {};
    const saved = JSON.parse(raw);
    if (saved.schema !== "openyamm-icon-spill-flags-v1" || !saved.flags ||
        typeof saved.flags !== "object" || Array.isArray(saved.flags)) {
      throw new Error("Unrecognized saved flag data; it has not been overwritten.");
    }
    return saved.flags;
  }
  try {
    flags = readFlags();
    view = JSON.parse(localStorage.getItem(VIEW_KEY) || "{}");
  } catch (error) {
    storageError = true;
    notice("Could not read saved review: " + error.message, true);
  }
  view.drafts ||= {};
  for (const id of filterIds) {
    if (typeof view.filters?.[id] === "string") get(id).value = view.filters[id];
  }
  const savedReason = reasons.findIndex(reason => reason.id === view.reason);
  if (savedReason >= 0) reasonIndex = savedReason;

  function saveView() {
    if (storageError) return;
    view.filters = Object.fromEntries(filterIds.map(id => [id, get(id).value]));
    view.selected = selected?.reviewKey || null;
    view.reason = reasons[reasonIndex].id;
    try { localStorage.setItem(VIEW_KEY, JSON.stringify(view)); }
    catch (error) { notice("Review position/notes could not be saved: " + error.message, true); }
  }
  function changeFlag(remove = false) {
    if (!selected || storageError) return;
    // Read immediately before writing so another review tab's unrelated flags survive.
    try {
      const latest = readFlags();
      if (remove) delete latest[selected.reviewKey];
      else latest[selected.reviewKey] = {
        scope: selected.scope, target: selected.target || null, path: selected.path,
        sha256: selected.sha256, crop: selected.crop || null,
        source_sha256: selected.native?.sha256 || null,
        reason: reasons[reasonIndex].id, reason_label: reasons[reasonIndex].label,
        note: get("notes").value, updated_at: new Date().toISOString(),
      };
      localStorage.setItem(FLAGS_KEY, JSON.stringify({schema: "openyamm-icon-spill-flags-v1", flags: latest}));
      flags = latest;
      const oldIndex = filtered.findIndex(row => row.reviewKey === selected.reviewKey);
      refresh(selected.reviewKey, oldIndex);
      notice((remove ? "Flag removed." : "Flag saved in this browser.") + " Export flags to hand off your feedback.");
    } catch (error) {
      notice("Flag was NOT saved: " + error.message, true);
    }
  }
  function updateCard(row) {
    const card = cards.get(row.reviewKey);
    if (!card) return;
    const flag = flags[row.reviewKey];
    card.classList.toggle("selected", row.reviewKey === selected?.reviewKey);
    card.classList.toggle("flagged", Boolean(flag));
    card.setAttribute("aria-current", row.reviewKey === selected?.reviewKey ? "true" : "false");
    card.querySelector(".flag-label").textContent = flag ? "Flagged: " + flag.reason_label : "Unflagged";
  }
  function updateToolbar() {
    const index = filtered.findIndex(row => row.reviewKey === selected?.reviewKey);
    get("position").textContent = index < 0 ? "No matching item" : `${index + 1} / ${filtered.length}`;
    get("selectedName").textContent = selected ? selected.target || selected.path.split("/").at(-1) : "";
    get("previous").disabled = index <= 0;
    get("next").disabled = index < 0 || index >= filtered.length - 1;
    get("flag").disabled = !selected || storageError;
    get("unflag").disabled = !selected || !flags[selected.reviewKey] || storageError;
    get("notes").disabled = !selected;
    get("flagCount").textContent = `${Object.keys(flags).length} saved flags`;
    [...get("reasons").children].forEach((button, i) => button.setAttribute("aria-pressed", String(i === reasonIndex)));
  }
  function select(row, scroll = false) {
    const previous = selected;
    selected = row || null;
    const saved = selected && flags[selected.reviewKey];
    if (saved) reasonIndex = Math.max(0, reasons.findIndex(reason => reason.id === saved.reason));
    get("notes").value = selected ? view.drafts[selected.reviewKey] ?? saved?.note ?? "" : "";
    if (previous) updateCard(previous);
    if (selected) updateCard(selected);
    updateToolbar();
    saveView();
    if (scroll && selected) {
      const card = cards.get(selected.reviewKey);
      card.focus({preventScroll: true});
      card.scrollIntoView({block: "start"});
    }
  }
  function renderCards() {
    main.replaceChildren();
    cards.clear();
    for (const row of filtered.slice(0, shown)) {
      const card = document.createElement("article");
      card.tabIndex = 0;
      card.dataset.reviewKey = row.reviewKey;
      const title = document.createElement("strong");
      title.textContent = `${row.target || row.path.split("/").at(-1)} — ${row.metrics.status}`;
      const flag = document.createElement("p");
      flag.className = "flag-label";
      const text = document.createElement("p");
      text.textContent = row.scope + " | " + Object.entries(row.metrics.colors)
        .filter(([, value]) => value.suspect_pixels)
        .map(([color, value]) => `${color}: ${value.alpha_weighted_pixels} weighted px (${value.status})`).join(" | ");
      card.append(title, flag, text);
      const img = document.createElement("img");
      img.loading = "lazy";
      img.src = row.preview || report.root_url + "/" + row.path;
      img.alt = row.preview ? "Original, dark/light comparison and enlarged spill detail" : "Scanned artwork";
      if (!row.preview) img.className = "standalone";
      card.append(img);
      const link = document.createElement("a");
      link.href = report.root_url + "/" + row.path;
      link.textContent = row.path;
      link.target = "_blank";
      link.rel = "noopener";
      card.append(link);
      const detail = document.createElement("details"), summary = document.createElement("summary");
      summary.textContent = "Measurements / provenance";
      detail.append(summary);
      detail.addEventListener("toggle", () => {
        if (detail.open && !detail.querySelector("pre")) {
          const pre = document.createElement("pre");
          const {reviewKey, ...data} = row;
          pre.textContent = JSON.stringify(data, null, 2);
          detail.append(pre);
        }
      });
      card.append(detail);
      card.addEventListener("click", event => {
        if (!event.target.closest("a,button,summary,details")) {
          select(row);
          card.focus({preventScroll: true});
        }
      });
      card.addEventListener("focus", () => { if (selected?.reviewKey !== row.reviewKey) select(row); });
      cards.set(row.reviewKey, card);
      main.append(card);
      updateCard(row);
    }
    get("more").hidden = shown >= filtered.length;
  }
  function refresh(preferred = selected?.reviewKey, fallbackIndex = 0) {
    const [scope, status, color, review, search] = filterIds.map(id => get(id).value.toLowerCase());
    filtered = rows.filter(row => (!scope || row.scope === scope) && (!status || row.metrics.status === status) &&
      (!color || ["likely_spill", "color_material_review", "trace"].includes(row.metrics.colors[color].status)) &&
      (!review || (review === "flagged") === Boolean(flags[row.reviewKey])) &&
      (!search || ((row.target || "") + " " + row.path).toLowerCase().includes(search)));
    let index = filtered.findIndex(row => row.reviewKey === preferred);
    if (index < 0) index = Math.min(Math.max(0, fallbackIndex), filtered.length - 1);
    shown = Math.max(40, Math.ceil((index + 1) / 40) * 40);
    get("count").textContent = `${filtered.length} matching items`;
    renderCards();
    select(filtered[index]);
  }
  function move(delta) {
    if (!filtered.length) return;
    const current = filtered.findIndex(row => row.reviewKey === selected?.reviewKey);
    const index = Math.max(0, Math.min(filtered.length - 1, current + delta));
    if (index >= shown) { shown = Math.ceil((index + 1) / 40) * 40; renderCards(); }
    select(filtered[index], true);
  }
  function setReason(index) {
    reasonIndex = (index + reasons.length) % reasons.length;
    updateToolbar();
    saveView();
  }
  for (const [index, reason] of reasons.entries()) {
    const button = document.createElement("button");
    button.dataset.reason = reason.id;
    button.textContent = reason.label;
    button.addEventListener("click", () => setReason(index));
    get("reasons").append(button);
  }
  document.addEventListener("keydown", event => {
    if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.isComposing) return;
    if (event.target.closest("input,textarea,select,a,summary,[contenteditable]:not([contenteditable=false])")) return;
    if (event.target.closest("button:not([data-reason])") && event.code === "Space") return;
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
      event.preventDefault();
      if (event.key === "ArrowUp") move(-1);
      else if (event.key === "ArrowDown") move(1);
      else setReason(reasonIndex + (event.key === "ArrowRight" ? 1 : -1));
    } else if (event.code === "Space" || event.key === " ") {
      event.preventDefault();
      if (!event.repeat) changeFlag();
    }
  });
  get("previous").onclick = () => move(-1);
  get("next").onclick = () => move(1);
  get("flag").onclick = () => changeFlag();
  get("unflag").onclick = () => changeFlag(true);
  get("notes").addEventListener("input", () => {
    if (!selected) return;
    view.drafts[selected.reviewKey] = get("notes").value;
    saveView();
    if (flags[selected.reviewKey]) {
      notice("Notes changed. Press Space outside the text box, or Flag / update reason, to save the flag.");
    }
  });
  get("export").onclick = () => {
    const data = {schema: "openyamm-icon-spill-review-v1", exported_at: new Date().toISOString(),
      manifest: report.manifest, manifest_sha256: report.manifest_sha256, flags};
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2) + "\n"], {type: "application/json"}));
    link.download = "openyamm-spill-review.json";
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  };
  get("more").onclick = () => { shown += 40; renderCards(); };
  for (const id of filterIds) get(id).addEventListener("input", () => refresh());
  window.addEventListener("storage", event => {
    if (event.key === FLAGS_KEY) {
      try { flags = readFlags(); refresh(); }
      catch (error) { notice("Could not load flags changed in another tab: " + error.message, true); }
    }
  });
  new ResizeObserver(() => {
    document.documentElement.style.setProperty("--toolbar-height", (document.querySelector("header").offsetHeight + 12) + "px");
  }).observe(document.querySelector("header"));
  get("summary").textContent = JSON.stringify(report.summary, null, 2);
  refresh(view.selected);
})();
