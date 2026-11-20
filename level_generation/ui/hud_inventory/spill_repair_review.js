"use strict";
(() => {
  const data = window.SPILL_REPAIRS, $ = id => document.getElementById(id);
  const publication = window.SPILL_PUBLICATION;
  for (const row of data.records) {
    row.hasRepair = Boolean(row.candidate);
    const accepted = publication?.records[row.target];
    if (!accepted) continue;
    row.publication = accepted;row.candidate = accepted.artifact;row.sha256 = accepted.sha256;
    if (accepted.resolution) {
      row.preview = accepted.resolution.proof;row.after_scan = accepted.after_scan;
      row.operation = {...row.operation, ...accepted.resolution.operation,
        changed_pixels:accepted.overall_changed_pixels,unresolved_pixels:0};
      row.mask = null;
    }
    row.status = "accepted_installed";
  }
  const storageKey = "openyamm-icon-spill-repairs-v1", viewKey = storageKey + "-view";
  const reasons = [["border_magenta", "Border magenta"], ["outline_spill", "Spill on outline"],
    ["interior_spill", "Spill inside image"], ["other", "Other"]];
  const read = (key, fallback) => {try {return JSON.parse(localStorage.getItem(key)) || fallback;} catch {return fallback;}};
  const decisions = read(storageKey, {schema: storageKey, decisions: {}});
  const saved = read(viewKey, {}), drafts = saved.drafts || {};
  let rows = [], current = null, reason = saved.reason || reasons[0][0];
  const decisionKey = row => JSON.stringify([row.target, row.before_sha256, row.sha256 || row.before_sha256]);
  const decision = row => {
    const local = decisions.decisions[decisionKey(row)];
    const acceptedAt = row.publication?.confirmed_at || publication?.published_at;
    if (!row.publication || Date.parse(local?.updated_at) > Date.parse(acceptedAt)) return local;
    return {status:"accept",note:"",updated_at:acceptedAt,
      authority:row.publication.confirmation || publication.authority};
  };
  // Read previous feedback without changing its keys, notes or decisions.
  const old = Object.values(read("openyamm-icon-spill-flags-v1", {flags: {}}).flags || {});
  const oldFlags = row => old.filter(flag => flag.target === row.target &&
    (!flag.sha256 || flag.sha256 === row.before_sha256));
  const persistView = () => {
    try {localStorage.setItem(viewKey, JSON.stringify({selected:current?.target, reason, drafts,
      search:$("search").value, group:$("group").value, filter:$("filter").value,
      background:$("background").value, zoom:$("zoom").value}));}
    catch {$("message").textContent = "Browser storage is full. Export your decisions.";}
  };
  function saveDecision(status) {
    if (!current) return;
    const key = decisionKey(current);
    if (status) decisions.decisions[key] = {target:current.target, before_sha256:current.before_sha256,
      candidate_sha256:current.sha256 || current.before_sha256, candidate:current.candidate || current.before,
      status, reason:status === "flag" ? reason : null, note:$("notes").value,
      updated_at:new Date().toISOString()};
    else delete decisions.decisions[key];
    try {localStorage.setItem(storageKey, JSON.stringify(decisions));
      $("message").textContent = status ? "Saved in this browser." : "Repair decision cleared.";}
    catch {$("message").textContent = "Could not save in browser. Export your decisions now.";}
    persistView(); refresh(current.target);
  }
  function setReason(value) {
    reason = value;
    for (const button of $("reasons").children) button.setAttribute("aria-pressed", String(button.dataset.reason === value));
    persistView();
  }
  for (const [value, label] of reasons) {
    const button = document.createElement("button");button.dataset.reason = value;button.textContent = label;
    button.onclick = () => setReason(value);$("reasons").append(button);
  }
  function displayImages() {
    for (const element of document.querySelectorAll(".view")) element.style.background = $("background").value;
    for (const id of ["native", "before", "after"]) {
      const image = $(id), fit = $("zoom").value === "fit";
      image.style.maxWidth = fit ? "100%" : "none";image.style.maxHeight = fit ? "100%" : "none";
      image.style.width = `${image.naturalWidth * (fit ? 1 : Number($("zoom").value)) * (id === "native" ? 2 : 1)}px`;
    }
    persistView();
  }
  function render() {
    const index = rows.indexOf(current);
    $("position").textContent = current ? `${index + 1} / ${rows.length}` : "0 / 0";
    $("prev").disabled = index <= 0;$("next").disabled = index < 0 || index >= rows.length - 1;
    for (const id of ["accept", "flag", "clear", "notes"]) $(id).disabled = !current;
    $("title").textContent = current?.target || "No matching assets";
    $("target").value = current?.target || "";
    if (!current) {
      for (const id of ["native", "before", "after", "proof"]) {$(id).removeAttribute("src");$(id).hidden = true;}
      for (const id of ["state", "resolutionNote", "originalFeedback", "facts", "links", "evidence"]) $(id).textContent = "";
      $("notes").value = "";return;
    }
    const review = decision(current);
    $("state").textContent = `${current.status.replaceAll("_", " ")} · ${review?.status || "not reviewed"}`;
    $("resolutionNote").textContent = current.publication?.resolution ?
      `Resolved comment: ${current.publication.resolution.note}\nFix: ${current.publication.resolution.operation.method.replaceAll("_"," ")}` : "";
    $("originalFeedback").textContent = oldFlags(current).map(flag => `Original flag: ${flag.reason_label || flag.reason} — ${flag.note || ""}`).join("\n");
    $("notes").value = drafts[decisionKey(current)] ?? review?.note ?? "";
    for (const [id,path] of [["native",current.native_reference],["before",current.before],
      ["after",current.candidate || current.before],["proof",current.preview]]) {
      $(id).hidden = !path;if (path) $(id).src = "/" + path;else $(id).removeAttribute("src");
    }
    const op = current.operation;
    $("facts").textContent = `${current.treatment} · ${op.changed_pixels} RGB pixels changed · ${op.unresolved_pixels} pixels left for local review\n` +
      `Alpha identical: ${op.alpha_identical} · Dimensions identical: ${op.dimensions_identical} · Offsets preserved: ${current.offsets_preserved}\n` +
      `Scanner: ${current.before_scan} → ${current.after_scan}. Scanner results are advisory; colored materials can still trigger them.\n` +
      (!current.candidate ? "No automatic repair: inspect the color in context." : "");
    $("evidence").textContent = JSON.stringify({original:current.source, actual_masters:current.master_backgrounds,
      master_evidence:current.master_evidence, technique:current.background_technique}, null, 2);
    $("links").replaceChildren();
    for (const [label,path] of [[publication ? "Open previous accepted" : "Open current",current.before],
      [publication ? "Open current accepted" : "Open candidate",current.candidate],
      ["Changed-pixel mask",current.mask]]) if(path) {
      const a = document.createElement("a");a.textContent = label;a.href = "/" + path;a.target = "_blank";a.rel = "noopener";$("links").append(a);
    }
    displayImages();
  }
  function refresh(preferred) {
    const query = $("search").value.toLowerCase(), group = $("group").value, filter = $("filter").value;
    rows = data.records.filter(row => {
      const items = ["inventory_items", "fitted_equipment_variants"].includes(row.treatment);
      const portraits = row.treatment.includes("portrait");
      if (group === "items" && !items || group === "portraits" && !portraits || group === "ui" && (items || portraits)) return false;
      if (query && !row.target.toLowerCase().includes(query)) return false;
      const status = decision(row)?.status;
      return filter === "all" || filter === "pending" && !status || filter === "resolved" && row.publication?.resolution || filter === "changed" && row.hasRepair ||
        filter === "unresolved" && (row.operation.unresolved_pixels > 0 || row.after_scan === "likely_spill") ||
        filter === "oldflag" && oldFlags(row).length || filter === status;
    });
    current = rows.find(row => row.target === preferred) || rows[0] || null;
    $("target").replaceChildren(...rows.map(row => new Option(row.target,row.target)));
    render();persistView();
  }
  function move(delta) {
    if (!rows.length) return;
    current = rows[Math.max(0, Math.min(rows.length - 1, rows.indexOf(current) + delta))];
    $("message").textContent = "";render();
  }
  for (const id of ["search", "group", "filter"]) {
    if (saved[id]) $(id).value = saved[id];
    $(id).oninput = () => refresh(current?.target);
  }
  for (const id of ["background", "zoom"]) {if (saved[id]) $(id).value = saved[id];$(id).oninput = displayImages;}
  for (const id of ["native", "before", "after"]) $(id).onload = displayImages;
  $("target").onchange = () => {current = rows.find(row => row.target === $("target").value);render();};
  $("prev").onclick = () => move(-1);$("next").onclick = () => move(1);
  $("accept").onclick = () => saveDecision("accept");$("flag").onclick = () => saveDecision("flag");$("clear").onclick = () => saveDecision(null);
  $("notes").oninput = () => {if (current) {drafts[decisionKey(current)] = $("notes").value;persistView();}};
  $("export").onclick = () => {
    const payload = {...decisions, recipe_sha256:data.recipe_sha256, exported_at:new Date().toISOString(),
      accepted_revision:publication?.authority,
      effective_decisions:Object.fromEntries(data.records.map(row=>[decisionKey(row),decision(row)]))};
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)], {type:"application/json"}));
    const a = document.createElement("a");a.href = url;a.download = "openyamm-spill-repairs.json";a.click();
    setTimeout(() => URL.revokeObjectURL(url),1000);
  };
  document.addEventListener("keydown", event => {
    if (event.target.closest("input,select,textarea,[contenteditable=true]") || event.ctrlKey || event.metaKey || event.altKey) return;
    if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "].includes(event.key)) return;
    event.preventDefault();if (event.repeat) return;
    if (event.key === "ArrowUp" || event.key === "ArrowDown") move(event.key === "ArrowUp" ? -1 : 1);
    else if (event.key === " ") saveDecision(event.shiftKey ? "accept" : "flag");
    else setReason(reasons[(reasons.findIndex(pair => pair[0] === reason) + (event.key === "ArrowRight" ? 1 : 3)) % 4][0]);
  });
  $("summary").textContent = publication ? `${data.records.length} accepted and installed · ${Object.values(publication.records).filter(row=>row.resolution).length} recent comments resolved` :
    `${data.summary.targets} entries · ${Object.entries(data.summary.status).map(([key,value]) => `${value} ${key.replaceAll("_", " ")}`).join(" · ")}`;
  if (publication) {
    $("heading").textContent = "Icon spill repairs — accepted and installed";
    $("beforeLabel").textContent = "Previous accepted x2";$("afterLabel").textContent = "Current accepted x2";
  }
  setReason(reason);refresh(saved.selected);
})();
