/* MAW Guide: hash-routed sections over window.GUIDE (data/guide.js, built by tools/maw_site/build_site.py). */
(function () {
  "use strict";
  const G = window.GUIDE;
  const main = document.getElementById("main");

  // ---------------------------------------------------------------------------------------------------------------
  // Helpers

  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
  const store = {
    get(key, fallback) {
      try { const v = localStorage.getItem("mawguide." + key); return v == null ? fallback : JSON.parse(v); }
      catch (e) { return fallback; }
    },
    set(key, value) { try { localStorage.setItem("mawguide." + key, JSON.stringify(value)); } catch (e) { /* ignore */ } },
  };
  const byId = (list, key = "id") => Object.fromEntries(list.map((x) => [x[key], x]));
  const maps = byId(G.maps);
  const continents = byId(G.continents);
  const classes = byId(G.classes || []);
  const poiIndex = {};
  G.maps.forEach((m) => { poiIndex[m.id] = byId(m.pois || []); });
  const types = G.poiTypes;
  const MASTERY_ORDER = { Expert: 1, Master: 2, Grandmaster: 3 };
  const mapName = (id) => (maps[id] ? maps[id].name : id);
  const fmt = (n) => Number(n).toLocaleString("en-US");
  const modes = G.modes || [];
  const GROUP_NAMES = { classic: "Classic", new: "New in MAW", racial: "Racial", other: "Other" };
  const continentOfName = Object.fromEntries(G.continents.map((c) => [c.name, c.id]));
  // "MM6 Enroth": the game a continent comes from, in its colour.
  function contBadge(id, withName = true) {
    const c = continents[id] || continents[continentOfName[id]];
    if (!c) return esc(id);
    return `<span class="cont cont-${c.id}">${esc(c.world.toUpperCase())}</span>${withName ? " " + esc(c.name) : ""}`;
  }

  function mapLink(map, poi, label) {
    return maps[map] ? `<a href="#map-${esc(map)}${poi ? "-" + esc(poi) : ""}">${esc(label || mapName(map))}</a>` : esc(label || map);
  }
  function showBtn(map, poi, label) {
    return maps[map] ? `<button type="button" class="btn" data-show-map="${esc(map)}" data-show-poi="${esc(poi || "")}">${esc(label || "Show")}</button>` : "";
  }
  function range(lo, hi) { return lo === hi ? `${lo}` : `${lo}–${hi}`; }
  function levelText(levels, mode) {
    if (!levels) return "";
    if (mode === "free") return range(levels.free[0], levels.free[2]);
    if (mode === "horizontal") return range(levels.horizontal[0], levels.horizontal[1]) + (levels.horizontal_cap ? `<span class="muted"> → ${levels.horizontal_cap}</span>` : "");
    if (mode === "madness") return levels.madness ? String(levels.madness) : "–";
    return "";
  }
  function levelSort(levels, mode) {
    if (!levels) return 9999;
    if (mode === "free") return levels.free[0] * 1000 + levels.free[2];
    if (mode === "horizontal") return levels.horizontal[0] * 1000 + levels.horizontal[1];
    return levels.madness || 9999;
  }
  function seg(id, options, current) {
    return `<div class="seg" id="${id}" role="group">${options.map(([v, n]) => `<button type="button" data-v="${esc(v)}" aria-pressed="${v === current}">${esc(n)}</button>`).join("")}</div>`;
  }
  function bindSeg(el, onChange) {
    el.addEventListener("click", (e) => {
      const b = e.target.closest("button[data-v]");
      if (!b) return;
      el.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b ? "true" : "false"));
      onChange(b.dataset.v);
    });
  }
  function segValue(el) { const b = el.querySelector('[aria-pressed="true"]'); return b ? b.dataset.v : ""; }

  function table(el, opts) {
    let sortKey = opts.sort || null;
    let asc = opts.asc !== false;
    let open = null;
    function draw() {
      let rows = opts.rows();
      if (sortKey) {
        const col = opts.columns.find((c) => c.key === sortKey);
        const val = col.sort || ((r) => r[sortKey]);
        rows = rows.slice().sort((a, b) => {
          const x = val(a), y = val(b);
          const d = typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y));
          return asc ? d : -d;
        });
      }
      if (opts.group) {
        const groups = new Map();
        rows.forEach((r) => { const k = opts.group(r); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(r); });
        rows = [...groups.keys()].flatMap((k) => [{ __group: k, __rows: groups.get(k) }, ...groups.get(k)]);
      }
      const head = opts.columns.map((c) => `<th class="${c.sortable === false ? "" : "sortable"} ${c.key === sortKey ? "sorted" + (asc ? " asc" : "") : ""} ${c.num ? "num" : ""}" data-key="${c.key}">${esc(c.label)}</th>`).join("");
      const body = rows.length ? rows.map((r, i) => {
        if (r.__group !== undefined) return `<tr class="group-row"><th colspan="${opts.columns.length}">${opts.groupLabel(r.__group, r.__rows)}</th></tr>`;
        const key = String(opts.rowKey ? opts.rowKey(r) : i);
        const tds = opts.columns.map((c) => `<td class="${c.num ? "num" : ""} ${c.cls || ""}">${c.render ? c.render(r) : esc(r[c.key])}</td>`).join("");
        const detail = opts.detail && open === key ? `<tr class="detail"><td colspan="${opts.columns.length}">${opts.detail(r)}</td></tr>` : "";
        return `<tr class="${opts.detail ? "clickable" : ""} ${opts.rowClass ? opts.rowClass(r) : ""}" data-key="${esc(key)}">${tds}</tr>${detail}`;
      }).join("") : `<tr><td colspan="${opts.columns.length}" class="empty">Nothing matches.</td></tr>`;
      el.innerHTML = `<div class="table-wrap"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
    }
    el.addEventListener("click", (e) => {
      const th = e.target.closest("th.sortable");
      if (th) {
        const key = th.dataset.key;
        if (sortKey === key) asc = !asc; else { sortKey = key; asc = true; }
        draw();
        return;
      }
      if (e.target.closest("a, button")) return;
      const tr = e.target.closest("tr.clickable");
      if (tr && opts.detail) { open = open === tr.dataset.key ? null : tr.dataset.key; draw(); }
    });
    draw();
    return { draw };
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Interactive map (one image per floor; MM6-MM8 maps have one)

  const TRAVEL_TYPES = new Set(["entrance", "exit", "teleporter"]);
  const defaultHidden = Object.keys(types).filter((t) => !types[t].shown);
  let hiddenTypes = new Set(store.get("hidden", defaultHidden));
  let showLabels = store.get("labels", false);

  class MapView {
    constructor(root, map, opts = {}) {
      this.map = map;
      this.opts = opts;
      this.floor = 0;
      this.s = 1; this.tx = 0; this.ty = 0;
      this.sel = null;
      root.innerHTML = `
        <div class="mv ${opts.dialog ? "dialog-map" : ""} ${opts.compact ? "compact" : ""}">
          <div class="mv-bar">
            <div class="mv-floors">${map.floors.length > 1 ? map.floorNames.map((n, i) => `<button type="button" class="btn" data-floor="${i}">${esc(n)}</button>`).join("") : ""}</div>
            <div class="mv-zoom">
              ${opts.compact ? `<a class="btn" href="#map-${esc(map.id)}${opts.focus ? "-" + esc(opts.focus) : ""}">Open ${esc(map.name)}</a>` : `<button type="button" class="btn" data-act="labels" aria-pressed="${showLabels}">${showLabels ? "Hide labels" : "Show labels"}</button>`}
              <button type="button" class="btn" data-act="in" aria-label="Zoom in">+</button>
              <button type="button" class="btn" data-act="out" aria-label="Zoom out">−</button>
              <button type="button" class="btn" data-act="fit">Fit</button>
            </div>
          </div>
          <div class="mv-view" tabindex="0" aria-label="${esc(map.name)} map; drag to pan, scroll or pinch to zoom">
            <div class="mv-stage"><img alt="${esc(map.name)}" draggable="false"><div class="mv-pins"></div></div>
            <div class="mv-tip" hidden></div>
          </div>
          <div class="mv-legend" ${opts.compact ? "hidden" : ""}></div>
          <div class="mv-info" ${opts.compact ? "hidden" : ""}><span class="muted">Select a marker for details. Drag to pan, scroll or pinch to zoom.</span></div>
        </div>`;
      this.root = root;
      this.view = root.querySelector(".mv-view");
      this.stage = root.querySelector(".mv-stage");
      this.img = root.querySelector("img");
      this.pins = root.querySelector(".mv-pins");
      this.tip = root.querySelector(".mv-tip");
      this.info = root.querySelector(".mv-info");
      this.legend = root.querySelector(".mv-legend");
      this.bind();
      const startPoi = poiIndex[map.id][opts.focus];
      this.setFloor(startPoi ? startPoi.f : 0, true);
      if (opts.focus) this.focus(opts.focus); else requestAnimationFrame(() => this.fit());
    }
    get floorData() { return this.map.floors[this.floor]; }
    setFloor(i, quiet) {
      this.floor = i;
      const f = this.floorData;
      this.img.src = f.img;
      this.img.width = f.w; this.img.height = f.h;
      // The frame takes the image's shape (up to a height limit), so a plan is not lost in empty space.
      if (!this.opts.compact) this.view.style.aspectRatio = `${f.w} / ${f.h}`;
      this.root.querySelectorAll("[data-floor]").forEach((b) => b.classList.toggle("active", Number(b.dataset.floor) === i));
      this.renderPins();
      this.renderLegend();
      if (!quiet) this.fit();
    }
    visiblePois() { return this.map.pois.filter((p) => p.f === this.floor && (!hiddenTypes.has(p.t) || p.id === this.sel)); }
    renderPins() {
      const f = this.floorData;
      const small = new Set(["house", "npc", "chest", "ladder", "lever"]);
      this.pins.innerHTML = this.visiblePois().map((p) => {
        const T = types[p.t];
        const lbl = this.labels() && !small.has(p.t) ? `<span class="lbl">${esc(p.n)}</span>` : "";
        return `<button type="button" class="pin ${small.has(p.t) ? "small" : ""} ${this.sel === p.id ? "sel" : ""}" data-id="${esc(p.id)}" style="left:${(p.u * f.w).toFixed(1)}px;top:${(p.v * f.h).toFixed(1)}px;--c:${T.color}" aria-label="${esc(T.name + ": " + p.n)}">${small.has(p.t) ? "" : esc(T.glyph)}${lbl}</button>`;
      }).join("");
    }
    labels() { return showLabels; }
    renderLegend() {
      const counts = {};
      this.map.pois.forEach((p) => { if (p.f === this.floor) counts[p.t] = (counts[p.t] || 0) + 1; });
      this.legend.innerHTML = Object.keys(types).filter((t) => counts[t]).map((t) => {
        const T = types[t];
        return `<button type="button" class="legend-chip ${hiddenTypes.has(t) ? "off" : ""}" data-type="${t}" style="--c:${T.color}" aria-pressed="${!hiddenTypes.has(t)}"><span class="g">${esc(T.glyph)}</span>${esc(T.name)} <span class="n">${counts[t]}</span></button>`;
      }).join("") + `<button type="button" class="legend-chip" data-type="*all">All</button><button type="button" class="legend-chip" data-type="*none">None</button>`;
    }
    apply() {
      this.stage.style.transform = `translate(${this.tx}px, ${this.ty}px) scale(${this.s})`;
      this.stage.style.setProperty("--inv", (1 / this.s).toFixed(4));
    }
    fitScale() {
      const f = this.floorData;
      const w = this.view.clientWidth || 800, h = this.view.clientHeight || 600;
      return Math.min(w / f.w, h / f.h);
    }
    fit() {
      const f = this.floorData;
      const w = this.view.clientWidth || 800, h = this.view.clientHeight || 600;
      this.s = this.fitScale();
      this.tx = (w - f.w * this.s) / 2;
      this.ty = (h - f.h * this.s) / 2;
      this.apply();
    }
    focusScale() { return this.opts.compact ? this.fitScale() * 2.5 : Math.max(this.fitScale() * 2.2, Math.min(1.1, this.fitScale() * 4)); }
    zoomAt(k, px, py) {
      this.touched = true;
      const fit = this.fitScale();
      const s = Math.min(Math.max(this.s * k, fit * 0.6), Math.max(fit * 12, 4));
      k = s / this.s;
      this.tx = px - (px - this.tx) * k;
      this.ty = py - (py - this.ty) * k;
      this.s = s;
      this.apply();
    }
    centerOn(u, v, s) {
      const f = this.floorData;
      const w = this.view.clientWidth || 800, h = this.view.clientHeight || 600;
      this.s = s;
      this.tx = w / 2 - u * f.w * s;
      this.ty = h / 2 - v * f.h * s;
      const iw = f.w * s, ih = f.h * s;
      this.tx = iw > w ? Math.min(0, Math.max(w - iw, this.tx)) : (w - iw) / 2;
      this.ty = ih > h ? Math.min(0, Math.max(h - ih, this.ty)) : (h - ih) / 2;
      this.apply();
    }
    focus(id) {
      const p = poiIndex[this.map.id][id];
      if (!p) { this.fit(); return; }
      this.sel = id;
      if (p.f !== this.floor) this.setFloor(p.f, true); else { this.renderPins(); this.renderLegend(); }
      requestAnimationFrame(() => this.centerOn(p.u, p.v, this.focusScale()));
      this.select(id);
    }
    // An entrance or exit leads to its map, shown at the marker that leads back here.
    travel(id) {
      const p = poiIndex[this.map.id][id];
      if (!p || !p.map || !maps[p.map] || !TRAVEL_TYPES.has(p.t)) return false;
      const back = (maps[p.map].pois || []).find((q) => q.map === this.map.id && TRAVEL_TYPES.has(q.t));
      location.hash = `#map-${p.map}${back ? "-" + back.id : ""}`;
      return true;
    }
    select(id) {
      this.sel = id;
      this.renderPins();
      const p = poiIndex[this.map.id][id];
      this.info.innerHTML = poiInfo(this.map, p);
      if (this.opts.onSelect) this.opts.onSelect(p);
    }
    bind() {
      const pointers = new Map();
      let start = null, moved = false, pinch = null;
      const rel = (e) => { const r = this.view.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
      const tipFor = (p) => (p.map && maps[p.map] && TRAVEL_TYPES.has(p.t) ? `<span class="muted">Click to go to</span> ` : "") + `<b>${esc(p.n)}</b>${p.k ? ` <span class="muted">${esc(p.k)}</span>` : ""}${p.teach ? "<br>" + esc(p.teach.join(", ")) : p.d ? "<br>" + esc(p.d) : ""}`;
      this.view.addEventListener("pointerdown", (e) => {
        if (e.button !== 0 && e.pointerType === "mouse") return;
        this.view.setPointerCapture(e.pointerId);
        pointers.set(e.pointerId, rel(e));
        moved = false;
        start = { x: e.clientX, y: e.clientY, tx: this.tx, ty: this.ty, target: e.target };
        if (pointers.size === 2) {
          const [a, b] = [...pointers.values()];
          pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), s: this.s };
        }
      });
      this.view.addEventListener("pointermove", (e) => {
        if (!pointers.has(e.pointerId)) {
          const pin = e.target.closest(".pin");
          if (pin && e.pointerType === "mouse") {
            const p = poiIndex[this.map.id][pin.dataset.id];
            const [x, y] = rel(e);
            this.tip.hidden = false;
            this.tip.innerHTML = tipFor(p);
            this.tip.style.left = Math.min(x + 14, this.view.clientWidth - 260) + "px";
            this.tip.style.top = (y + 14) + "px";
          } else this.tip.hidden = true;
          return;
        }
        pointers.set(e.pointerId, rel(e));
        if (pointers.size === 2 && pinch) {
          const [a, b] = [...pointers.values()];
          const d = Math.hypot(a[0] - b[0], a[1] - b[1]);
          this.zoomAt((pinch.s * d / pinch.d) / this.s, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
          moved = true;
          return;
        }
        const dx = e.clientX - start.x, dy = e.clientY - start.y;
        if (Math.abs(dx) + Math.abs(dy) > 4) moved = true;
        if (moved) {
          this.view.classList.add("dragging");
          this.touched = true;
          this.tx = start.tx + dx; this.ty = start.ty + dy;
          this.apply();
        }
      });
      const end = (e) => {
        if (!pointers.has(e.pointerId)) return;
        pointers.delete(e.pointerId);
        if (pointers.size < 2) pinch = null;
        this.view.classList.remove("dragging");
        if (!moved && start && pointers.size === 0) {
          const pin = start.target.closest && start.target.closest(".pin");
          if (pin && !this.travel(pin.dataset.id)) this.select(pin.dataset.id);
        }
        if (pointers.size === 1) {
          const [p] = [...pointers.values()];
          const r = this.view.getBoundingClientRect();
          start = { x: p[0] + r.left, y: p[1] + r.top, tx: this.tx, ty: this.ty, target: this.view };
        }
      };
      this.view.addEventListener("pointerup", end);
      this.view.addEventListener("pointercancel", end);
      this.view.addEventListener("pointerleave", () => { this.tip.hidden = true; });
      this.view.addEventListener("wheel", (e) => {
        e.preventDefault();
        const [x, y] = rel(e);
        this.zoomAt(Math.exp(-e.deltaY * (e.deltaMode ? 0.05 : 0.0016)), x, y);
      }, { passive: false });
      this.view.addEventListener("dblclick", (e) => { const [x, y] = rel(e); this.zoomAt(2, x, y); });
      this.view.addEventListener("keydown", (e) => {
        const step = 60;
        const cx = this.view.clientWidth / 2, cy = this.view.clientHeight / 2;
        if (e.key === "+" || e.key === "=") this.zoomAt(1.4, cx, cy);
        else if (e.key === "-") this.zoomAt(1 / 1.4, cx, cy);
        else if (e.key === "ArrowLeft") { this.tx += step; this.apply(); }
        else if (e.key === "ArrowRight") { this.tx -= step; this.apply(); }
        else if (e.key === "ArrowUp") { this.ty += step; this.apply(); }
        else if (e.key === "ArrowDown") { this.ty -= step; this.apply(); }
        else return;
        e.preventDefault();
      });
      this.root.addEventListener("click", (e) => {
        const fb = e.target.closest("[data-floor]");
        if (fb) { this.setFloor(Number(fb.dataset.floor)); return; }
        const act = e.target.closest("[data-act]");
        if (act) {
          const cx = this.view.clientWidth / 2, cy = this.view.clientHeight / 2;
          if (act.dataset.act === "in") this.zoomAt(1.5, cx, cy);
          if (act.dataset.act === "out") this.zoomAt(1 / 1.5, cx, cy);
          if (act.dataset.act === "fit") this.fit();
          if (act.dataset.act === "labels") {
            showLabels = !showLabels; store.set("labels", showLabels);
            act.textContent = showLabels ? "Hide labels" : "Show labels";
            act.setAttribute("aria-pressed", showLabels);
            this.renderPins();
          }
          return;
        }
        const chip = e.target.closest(".legend-chip");
        if (chip) {
          const t = chip.dataset.type;
          if (t === "*all") hiddenTypes = new Set();
          else if (t === "*none") hiddenTypes = new Set(Object.keys(types));
          else if (hiddenTypes.has(t)) hiddenTypes.delete(t); else hiddenTypes.add(t);
          store.set("hidden", [...hiddenTypes]);
          this.renderPins(); this.renderLegend();
          if (this.opts.onFilter) this.opts.onFilter();
        }
      });
      if (window.ResizeObserver) {
        // Until the reader pans or zooms, keep the view fitted (or on the selected marker) as the layout settles.
        new ResizeObserver(() => {
          if (this.touched) return;
          if (this.sel) { const p = poiIndex[this.map.id][this.sel]; if (p) this.centerOn(p.u, p.v, this.focusScale()); } else this.fit();
        }).observe(this.view);
      }
    }
  }

  function poiInfo(map, p) {
    const T = types[p.t];
    const parts = [`<span class="t">${esc(T.name)}${p.k ? " · " + esc(p.k) : ""}</span><h3>${esc(p.n)}</h3>`];
    if (p.d) parts.push(`<div>${esc(p.d)}</div>`);
    if (p.teach) parts.push(`<div><b>Teaches:</b> ${p.teach.map((l) => `<a href="#teachers" data-filter="${esc(l.replace(/^(Expert|Master|Grandmaster) /, ""))}">${esc(l)}</a>`).join(", ")}</div>`);
    if (p.promos) parts.push(`<div><b>Promotion:</b> ${esc(p.promos.join("; "))} · <a href="#promotions">Promotions</a></div>`);
    if (p.people && p.people.length) parts.push(`<div class="muted">${esc(p.people.join(", "))}</div>`);
    if (p.map) parts.push(`<div>Leads to ${mapLink(p.map)}</div>`);
    if (map.mm9) parts.push(`<div><a href="${esc(map.mm9)}-${esc(p.id)}" target="_blank" rel="noopener">Open in the MM9 guide ↗</a></div>`);
    return parts.join("");
  }

  // Map dialog, used from every section's "Show" buttons.
  const dialog = document.getElementById("map-dialog");
  function openMapDialog(mapId, poi) {
    const m = maps[mapId];
    if (!m || !m.floors.length) { location.hash = `#map-${mapId}`; return; }
    document.getElementById("dlg-title").textContent = m.name;
    document.getElementById("dlg-open").href = `#map-${mapId}${poi ? "-" + poi : ""}`;
    if (typeof dialog.showModal === "function") dialog.showModal(); else dialog.setAttribute("open", "");
    new MapView(document.getElementById("dlg-body"), m, { dialog: true, focus: poi || null });
  }
  document.getElementById("dlg-close").addEventListener("click", () => dialog.close());
  document.getElementById("dlg-open").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  let pendingFilter = null;
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-show-map]");
    if (b) { e.preventDefault(); openMapDialog(b.dataset.showMap, b.dataset.showPoi); return; }
    const f = e.target.closest("[data-filter]");
    if (f) pendingFilter = f.dataset.filter;
    if (dialog.open && e.target.closest(".mv-info a")) dialog.close();
  });

  // ---------------------------------------------------------------------------------------------------------------
  // Navigation

  const NAV = [
    { title: "Guide", items: [["start", "Start"], ["progression", "Progression"], ["planner", "Where to go"], ["locations", "Locations", G.maps.length],
      ["teachers", "Teachers", (G.teachers || []).length], ["classes", "Classes", (G.classes || []).length],
      ["promotions", "Promotions"], ["chedian", "Chedian (MM9)"], ["crafting", "Crafting"], ["tips", "Tips and HUD"]] },
    { title: "Reference", items: [["combat", "Combat and auras"], ["loot", "Loot"], ["spells", "Spells"], ["deviations", "Deviations from MAW"]] },
  ];
  function sectionOf(r) {
    const head = r.split("-")[0];
    if (head === "map") { const m = maps[r.split("-")[1]]; return "continent-" + (m ? m.continent : ""); }
    if (head === "class") return "classes";
    return r;
  }
  function renderNav(r) {
    const sec = sectionOf(r);
    document.getElementById("nav").innerHTML = NAV.map((g) => `<div class="nav-group"><div class="nav-title">${esc(g.title)}</div>${g.items.map(([id, name, count]) => {
      let sub = "";
      if (id === "locations" && (sec === "locations" || sec.startsWith("continent-"))) {
        sub = `<div class="nav-sub">${G.continents.map((c) => `<a class="nav-link ${sec === "continent-" + c.id ? "active" : ""}" href="#continent-${c.id}">${contBadge(c.id)}</a>`).join("")}</div>`;
      } else if (id === "classes" && sec === "classes") {
        const groups = [...new Set((G.classes || []).map((c) => c.group))];
        sub = `<div class="nav-sub">${groups.map((g) => `<div class="nav-head">${esc(GROUP_NAMES[g] || g)}</div>${G.classes.filter((c) => c.group === g).map((c) => `<a class="nav-link ${r === "class-" + c.id ? "active" : ""}" href="#class-${esc(c.id)}">${esc(c.name)}</a>`).join("")}`).join("")}</div>`;
      } else if (id === sec && G.content && G.content[id]) {
        const heads = [...G.content[id].matchAll(/<h2 id="([^"]+)">([\s\S]*?)<\/h2>/g)];
        if (heads.length > 1) sub = `<div class="nav-sub">${heads.map((h) => `<a class="nav-link" href="#${id}/${esc(h[1])}">${esc(h[2].replace(/<[^>]+>/g, ""))}</a>`).join("")}</div>`;
      }
      return `<a class="nav-link ${sec === id ? "active" : ""}" href="#${id}">${esc(name)}${count ? ` <span class="count">${count}</span>` : ""}</a>${sub}`;
    }).join("")}</div>`).join("");
  }
  function pageHead(title, crumbs, lead) {
    return `<div class="page-head">${crumbs ? `<div class="crumbs">${crumbs}</div>` : ""}<h1>${esc(title)}</h1>${lead ? `<p>${lead}</p>` : ""}</div>`;
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Prose sections with generated blocks

  function pageContent(name, title) {
    const html = (G.content || {})[name];
    if (!html) { main.innerHTML = pageHead(title) + `<p class="muted">This section is not written yet.</p>`; return; }
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    const heads = [...tmp.querySelectorAll("h2[id]")];
    const rail = heads.length > 2 ? `<nav class="rail" aria-label="On this page">${heads.map((h) => `<a href="#${name}/${h.id}">${esc(h.textContent)}</a>`).join("")}</nav>` : "";
    main.innerHTML = pageHead(title) + rail + `<article class="prose">${html}</article>`;
    // Links to a person's marker by name (data-map, data-find): marker ids follow the map data, names do not.
    main.querySelectorAll("a[data-find]").forEach((a) => {
      const m = maps[a.dataset.map];
      const p = m && m.pois.find((x) => x.n === a.dataset.find);
      a.href = p ? `#map-${m.id}-${p.id}` : `#map-${a.dataset.map}`;
    });
    main.querySelectorAll("[data-guide]").forEach((el) => {
      const block = BLOCKS[el.dataset.guide];
      if (block) block(el);
    });
  }

  const BLOCKS = {
    "map-levels": (el) => mapLevelTable(el, null),
    "map-levels-chedian": (el) => mapLevelTable(el, "chedian"),
    "teachers": (el) => teacherTable(el),
    "class-table": (el) => classGrid(el),
    "promotion-table": (el) => promotionTable(el),
    "mitigation-calculator": (el) => mitigationCalculator(el),
  };

  // Damage taken = hit / (value / (half + L) + 1), never below 10 %: armour halves at 200 + L, resistance at 100 + L.
  function mitigationCalculator(el) {
    el.innerHTML = `<div class="card toolbar"><select class="field" id="mc-k" aria-label="Kind"><option value="200">Armour Class</option><option value="100">Resistance</option></select>
      <label>Value <input class="field" id="mc-v" type="number" min="0" value="600" style="width:7em"></label>
      <label>Monster level <input class="field" id="mc-l" type="number" min="1" value="100" style="width:6em"></label>
      <span id="mc-r"></span></div>`;
    const k = el.querySelector("#mc-k"), v = el.querySelector("#mc-v"), l = el.querySelector("#mc-l"), r = el.querySelector("#mc-r");
    const calc = () => {
      const half = Number(k.value) + Math.max(1, Number(l.value) || 1);
      const taken = Math.max(0.1, 1 / (Math.max(0, Number(v.value) || 0) / half + 1));
      r.innerHTML = `Cuts <b>${(100 - taken * 100).toFixed(1)} %</b> of each hit; <b>${half}</b> would halve it at this level.`;
    };
    [k, v, l].forEach((x) => x.addEventListener("input", calc));
    calc();
  }

  // A map's monsters, loot and crowding as five-step bars (build_site.map_stats: quintiles over all maps).
  function tierBar(tier, kind, title) {
    if (!tier) return "";
    return `<span class="tier tier-${kind}" title="${esc(title)}">${[1, 2, 3, 4, 5].map((i) => `<i class="${i <= tier ? "on" : ""}"></i>`).join("")}</span>`;
  }
  const STAT_COLUMNS = [
    { key: "n", label: "Monsters", num: true, cls: "nowrap", render: (m) => (m.stats ? `${tierBar(m.stats.n_tier, "n", `${m.stats.n} at MAW difficulty, ${m.stats.n_nm} at Nightmare`)} ${m.stats.n}` : "–"), sort: (m) => (m.stats ? m.stats.n : -1) },
    { key: "loot", label: "Loot", cls: "nowrap", render: (m) => (m.stats && m.stats.loot_tier ? tierBar(m.stats.loot_tier, "loot", `${m.stats.n} kills at about level ${Math.round(m.levels.band[1])} (Free band): drops follow the monster's level and number`) : "–"), sort: (m) => (m.stats ? m.stats.loot_tier || 0 : -1) },
    { key: "crowd", label: "Crowding", cls: "nowrap", render: (m) => (m.stats && m.stats.crowd_tier ? tierBar(m.stats.crowd_tier, "crowd", `${m.stats.crowd} monsters per 100 tiles of floor (${m.stats.area} tiles): tight packs, little room to pull`) : m.kind === "outdoor" ? `<span class="muted" title="Outdoors you can keep your distance">open</span>` : "–"), sort: (m) => (m.stats ? m.stats.crowd_tier || 0 : -1) },
  ];

  const STAT_NOTE = `<p class="muted" style="font-size:.88rem;margin:6px 0">Bars rank every map in fifths. <b>Monsters</b>: how many at MAW difficulty (more on Hard and up). <b>Loot</b>: kills × their level, what drops and completion pay follow. <b>Crowding</b>: monsters per floor area, indoor maps only; outdoors you can keep your distance. Hover a bar for its numbers.</p>`;

  function mapLevelTable(el, continent) {
    el.innerHTML = `<div class="toolbar">${continent ? "" : seg("ml-c", [["", "All"], ...G.continents.map((c) => [c.id, `${c.world.toUpperCase()} ${c.name}`])], "")}
      <input class="field" id="ml-q" type="search" placeholder="Filter maps" aria-label="Filter maps">
      ${seg("ml-k", [["", "All"], ["outdoor", "Outdoor"], ["dungeon", "Indoor"]], "")}</div>${STAT_NOTE}<div id="ml-t"></div>`;
    const q = el.querySelector("#ml-q"), cSeg = el.querySelector("#ml-c"), kSeg = el.querySelector("#ml-k");
    const t = table(el.querySelector("#ml-t"), {
      rows: () => {
        const text = q.value.trim().toLowerCase();
        const c = continent || (cSeg ? segValue(cSeg) : ""), k = segValue(kSeg);
        return G.maps.filter((m) => m.levels && (!c || m.continent === c) && (!k || (k === "outdoor" ? m.kind === "outdoor" : m.kind !== "outdoor")) &&
          (!text || (m.name + " " + m.file + " " + (m.region || "")).toLowerCase().includes(text)));
      },
      sort: "free",
      rowClass: (m) => `tint tint-${m.continent}`,
      columns: [
        { key: "name", label: "Map", render: (m) => `${mapLink(m.id)}${m.levels.horizontal_cap ? ' <span class="tag">starter</span>' : ""}` },
        ...(continent ? [] : [{ key: "continent", label: "Continent", cls: "nowrap", render: (m) => contBadge(m.continent), sort: (m) => continents[m.continent].world }]),
        { key: "kind", label: "Kind", render: (m) => esc(m.kind) },
        { key: "free", label: "Free", num: true, render: (m) => levelText(m.levels, "free"), sort: (m) => levelSort(m.levels, "free") },
        { key: "horizontal", label: "Horizontal", num: true, render: (m) => levelText(m.levels, "horizontal"), sort: (m) => levelSort(m.levels, "horizontal") },
        { key: "madness", label: "Beyond Madness", num: true, render: (m) => levelText(m.levels, "madness"), sort: (m) => levelSort(m.levels, "madness") },
        ...STAT_COLUMNS,
        { key: "refill", label: "Refills", num: true, render: (m) => m.refill_days ? `${m.refill_days} days` : (m.continent === "chedian" ? "–" : "never"), sort: (m) => m.refill_days || 99999 },
      ],
    });
    q.addEventListener("input", t.draw);
    if (cSeg) bindSeg(cSeg, t.draw);
    bindSeg(kSeg, t.draw);
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Locations

  function thumbOf(m) { return m.thumb || (m.floors[0] && m.floors[0].img) || ""; }
  function levelChip(m) { return m.levels ? `<span class="lvl" title="Free progression levels">${range(m.levels.free[0], m.levels.free[2])}</span>` : ""; }

  function pageLocations() {
    main.innerHTML = pageHead("Locations", "", "Every map of the four continents with MAW's monster levels, and an interactive map of each with its teachers, shops, promoters, entrances and exits. Pick a continent.") +
      `<div class="grid-cards">${G.continents.map((c) => {
        const ms = G.maps.filter((m) => m.continent === c.id);
        return `<a class="card home-card" href="#continent-${c.id}"><strong>${esc(c.name)}</strong><span>${esc(c.game)} · ${ms.filter((m) => m.kind === "outdoor").length} outdoor, ${ms.filter((m) => m.kind !== "outdoor").length} indoor maps</span></a>`;
      }).join("")}</div><h2>All maps by level</h2><div id="levels"></div>`;
    mapLevelTable(document.getElementById("levels"), null);
  }

  function pageContinent(id) {
    const c = continents[id];
    if (!c) return pageMissing();
    const ms = G.maps.filter((m) => m.continent === id);
    let groups = "";
    if (id === "chedian") {
      groups = G.chedianRegions.map((r) => `<section class="region-row"><h2>${esc(r.name)}</h2><div class="thumbs">${r.maps.filter((m) => maps[m]).map((mid) => {
        const m = maps[mid];
        return `<a class="thumb" href="#map-${mid}"><img src="${esc(thumbOf(m))}" alt="" loading="lazy"><span>${esc(m.name)} ${levelChip(m)}</span><small>${esc(m.kind)}${m.floors.length > 1 ? ", " + m.floors.length + " levels" : ""}</small></a>`;
      }).join("")}</div></section>`).join("");
    } else {
      // Outdoor maps, each with the places entered from it.
      const placed = new Set();
      const outdoors = ms.filter((m) => m.kind === "outdoor").sort((a, b) => levelSort(a.levels, "free") - levelSort(b.levels, "free"));
      const cards = outdoors.map((o) => {
        const inside = ms.filter((m) => m.kind !== "outdoor" && (m.entrances || []).some((e) => e.map === o.id));
        inside.forEach((m) => placed.add(m.id));
        inside.sort((a, b) => levelSort(a.levels, "free") - levelSort(b.levels, "free"));
        return `<div class="thumb"><a href="#map-${o.id}"><img src="${esc(thumbOf(o))}" alt="" loading="lazy"></a><a href="#map-${o.id}"><span>${esc(o.name)}</span> ${levelChip(o)}</a>
          ${inside.length ? `<div class="subs">${inside.map((m) => `<a href="#map-${m.id}">${esc(m.name)} ${levelChip(m)}</a>`).join("")}</div>` : ""}</div>`;
      }).join("");
      const rest = ms.filter((m) => m.kind !== "outdoor" && !placed.has(m.id));
      groups = `<div class="thumbs">${cards}</div>` + (rest.length ? `<section class="region-row"><h2>Reached from other places</h2><div class="chips">${rest.map((m) => `<a class="chip" href="#map-${m.id}">${esc(m.name)} ${levelChip(m)}</a>`).join("")}</div></section>` : "");
    }
    main.innerHTML = pageHead(c.name, `<a href="#locations">Locations</a> · ${esc(c.game)}`, `Levels are MAW's Free progression band for each map: the levels its three native monster families are set to. The table below adds Horizontal and Beyond Madness.`) +
      (id === "chedian" ? chedianNote() : "") + groups + `<h2>Maps of ${esc(c.name)}</h2><div id="levels"></div>`;
    mapLevelTable(document.getElementById("levels"), id);
  }

  function chedianNote() {
    return `<div class="card">Chedian is MAW's newest continent: its bands are MAW's first balance pass for MM9 and may still move. <a href="#chedian">What MAW changes on Chedian</a>: the Jarls' bounties, the Hag's skill reset, extra monsters, promotions. Quests, monsters and shops of each map are in the <a href="${esc(G.mm9Guide)}" target="_blank" rel="noopener">MM9 guide ↗</a>.</div>`;
  }

  function pageMap(id, poi) {
    const m = maps[id];
    if (!m) return pageMissing();
    const c = continents[m.continent];
    main.innerHTML = pageHead(m.name, `<a href="#locations">Locations</a> · <a href="#continent-${c.id}">${esc(c.name)}</a>${m.region ? " · " + esc(m.region) : ""} · ${esc(m.kind)} · <span class="mono">${esc(m.file)}</span>`) +
      (m.continent === "chedian" ? chedianNote() : "") +
      `<div class="map-facts" id="map-facts"></div>` +
      (m.floors.length ? `<div class="map-layout"><div id="mv"></div><aside class="poi-panel"><input class="field" id="poi-filter" type="search" placeholder="Filter points on this map" aria-label="Filter points"><div class="poi-list" id="poi-list"></div></aside></div>`
        : `<div class="no-map">No map image of this place.</div>`);
    document.getElementById("map-facts").innerHTML = mapFacts(m);
    if (!m.floors.length) return;
    const list = document.getElementById("poi-list");
    const filter = document.getElementById("poi-filter");
    const mv = new MapView(document.getElementById("mv"), m, {
      focus: poi || null,
      onFilter: () => drawList(),
      onSelect: (p) => { if (location.hash !== `#map-${id}-${p.id}`) history.replaceState(null, "", `#map-${id}-${p.id}`); },
    });
    function drawList() {
      const q = filter.value.trim().toLowerCase();
      const groups = {};
      m.pois.filter((p) => !hiddenTypes.has(p.t) && (!q || (p.n + " " + (p.d || "") + " " + (p.teach || []).join(" ") + " " + (p.people || []).join(" ")).toLowerCase().includes(q)))
        .forEach((p) => { (groups[p.t] = groups[p.t] || []).push(p); });
      list.innerHTML = Object.keys(types).filter((t) => groups[t]).map((t) => `<h4>${esc(types[t].name)} (${groups[t].length})</h4>` +
        groups[t].slice(0, 300).map((p) => `<button type="button" data-poi="${esc(p.id)}" style="--c:${types[t].color}"><span class="dot"></span><span>${esc(p.n)}</span>${m.floors.length > 1 ? `<small>${esc(m.floorNames[p.f])}</small>` : p.k ? `<small>${esc(p.k)}</small>` : ""}</button>`).join("")).join("") ||
        `<div class="empty">No points match.</div>`;
    }
    filter.addEventListener("input", drawList);
    list.addEventListener("click", (e) => { const b = e.target.closest("[data-poi]"); if (b) mv.focus(b.dataset.poi); });
    drawList();
    parentMaps(m);
  }

  // An indoor map's ways in: each map it is entered from (outdoor ones first), zoomed to the entrance marker.
  function parentMaps(m) {
    if (m.kind === "outdoor") return;
    const seen = new Set();
    const ins = (m.entrances || []).filter((e) => maps[e.map] && maps[e.map].floors.length && poiIndex[e.map][e.poi] && !seen.has(e.map) && seen.add(e.map))
      .sort((a, b) => (maps[a.map].kind === "outdoor" ? 0 : 1) - (maps[b.map].kind === "outdoor" ? 0 : 1)).slice(0, 2);
    if (!ins.length) return;
    main.insertAdjacentHTML("beforeend", `<section class="section"><h2>Way in</h2><div class="parents">${ins.map((e, i) => `<div class="card"><h3>${mapLink(e.map, e.poi)} <span class="muted">· entrance</span></h3><div id="parent-${i}"></div></div>`).join("")}</div></section>`);
    ins.forEach((e, i) => new MapView(document.getElementById(`parent-${i}`), maps[e.map], { compact: true, focus: e.poi }));
  }

  function mapFacts(m) {
    const cards = [];
    if (m.levels) {
      const L = m.levels;
      cards.push(`<div class="card"><h3>Monster levels</h3><dl class="kv">
        <dt>Free</dt><dd><span class="lvl">${L.free.join(" / ")}</span> <span class="muted">low / mid / high family</span></dd>
        <dt>Horizontal</dt><dd><span class="lvl">${range(L.horizontal[0], L.horizontal[1])}</span>${L.horizontal_cap ? ` <span class="muted">starter map: grows with you up to ${L.horizontal_cap}</span>` : ""}</dd>
        ${L.madness ? `<dt>Beyond Madness</dt><dd><span class="lvl">${L.madness}</span></dd>` : ""}
        <dt>Refills</dt><dd>${m.refill_days ? `every ${m.refill_days} days` : m.continent === "chedian" ? "–" : "never"}</dd>
        ${m.stats ? `<dt>Monsters</dt><dd>${STAT_COLUMNS[0].render(m)} <span class="muted">at MAW, ${m.stats.n_nm} at Nightmare</span></dd>
        <dt>Loot</dt><dd>${STAT_COLUMNS[1].render(m)}</dd><dt>Crowding</dt><dd>${STAT_COLUMNS[2].render(m)}</dd>` : ""}</dl>
        <p class="muted" style="font-size:.85rem;margin-top:6px">Under Free progression, levels banked on other continents are added. <a href="#progression">How levels work</a></p></div>`);
    }
    const ways = m.kind === "outdoor" ? [] : (m.entrances || []).map((e) => `${mapLink(e.map, e.poi)}`);
    const exits = [];
    const seen = new Set();
    (m.pois || []).filter((p) => (p.t === "exit" || p.t === "entrance") && p.map && maps[p.map]).forEach((p) => {
      if (seen.has(p.map)) return; seen.add(p.map);
      exits.push(`<a class="chip" href="#map-${p.map}">${esc(mapName(p.map))}${maps[p.map].levels ? " " + levelChip(maps[p.map]) : ""}</a>`);
    });
    if (ways.length || exits.length) {
      cards.push(`<div class="card"><h3>Ways in and out</h3>${ways.length ? `<p>Entered from ${ways.join(", ")}.</p>` : ""}${exits.length ? `<div class="chips" style="margin-top:6px">${exits.join("")}</div>` : ""}</div>`);
    }
    const lessons = (G.teachers || []).filter((t) => (t.at || []).some((a) => a.map === m.id));
    if (lessons.length) {
      lessons.sort((a, b) => a.skill.localeCompare(b.skill) || MASTERY_ORDER[a.mastery] - MASTERY_ORDER[b.mastery]);
      cards.push(`<div class="card"><h3>Teachers here</h3><div class="chips">${lessons.map((t) => { const a = t.at.find((x) => x.map === m.id); return `<a class="chip" href="#map-${m.id}-${esc(a.poi)}"><span class="mastery-${esc(t.mastery)}">${esc(t.mastery[0])}</span> ${esc(t.skill)}</a>`; }).join("")}</div></div>`);
    }
    const promos = (m.pois || []).filter((p) => p.promos);
    if (promos.length) {
      cards.push(`<div class="card"><h3>Promotions here</h3>${promos.map((p) => `<p><a href="#map-${m.id}-${esc(p.id)}">${esc(p.n)}</a>: ${esc(p.promos.join("; "))}</p>`).join("")}</div>`);
    }
    if (m.mm9) cards.push(`<div class="card"><h3>MM9 guide</h3><p>Quests, monsters and shops of this map: <a href="${esc(m.mm9)}" target="_blank" rel="noopener">open in the MM9 guide ↗</a></p></div>`);
    return cards.join("");
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Teachers

  function atButtons(t) {
    const at = (t.at || [])[0];
    if (at) return showBtn(at.map, at.poi, "Map");
    return "";
  }
  function placeText(t) {
    const house = t.house ? esc(t.house) : "";
    const map = t.map ? Path(t.map) : "";
    const where = map && maps[map] ? mapLink(map, (t.at || []).find((a) => a.map === map)?.poi, t.map_name || mapName(map)) : esc(t.map_name || t.region || "");
    const via = t.kind === "entrance" && t.marker_map && maps[Path(t.marker_map)] ? ` <span class="muted">via ${mapLink(Path(t.marker_map))}</span>` : "";
    return `${house}${house && where ? ", " : ""}${where}${via}`;
  }
  function Path(file) { return String(file || "").replace(/\.(odm|blv)$/i, ""); }

  // The OpenYAMM skills an MM9 lesson teaches, when they differ from its name.
  function skillList(x) {
    const list = Array.isArray(x.skills) ? x.skills.join(", ") : String(x.skills || "").replace(/,(?=\S)/g, ", ");
    return list && list !== x.skill ? `<br><span class="muted">${esc(list)}</span>` : "";
  }

  function teacherTable(el) {
    const skills = [...new Set((G.teachers || []).map((t) => t.skill))].sort();
    const modeIds = modes.map((m) => [m.id, m.name]);
    const mode0 = store.get("mode", modeIds.length ? modeIds[0][0] : "");
    el.innerHTML = `<div class="toolbar">${seg("tc", [["", "All"], ...G.continents.map((c) => [c.name, `${c.world.toUpperCase()} ${c.name}`])], store.get("tcont", ""))}
      <input class="field" id="tf" type="search" placeholder="Filter by skill, teacher or place" aria-label="Filter teachers">
      <select class="field" id="ts" aria-label="Skill"><option value="">All skills</option>${skills.map((s) => `<option>${esc(s)}</option>`).join("")}</select>
      <select class="field" id="tm" aria-label="Mastery"><option value="">All masteries</option>${Object.keys(MASTERY_ORDER).map((m) => `<option>${m}</option>`).join("")}</select>
      ${modeIds.length ? `<label class="muted">Needs for <select class="field" id="tmode" aria-label="Progression mode">${modeIds.map(([v, n]) => `<option value="${esc(v)}" ${v === mode0 ? "selected" : ""}>${esc(n)}</option>`).join("")}</select></label>` : ""}</div><div id="tt"></div>`;
    const f = el.querySelector("#tf"), s = el.querySelector("#ts"), mm = el.querySelector("#tm"), c = el.querySelector("#tc"), md = el.querySelector("#tmode");
    if (pendingFilter) { f.value = pendingFilter; pendingFilter = null; }
    const t = table(el.querySelector("#tt"), {
      rows: () => {
        const words = f.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
        const cont = segValue(c);
        return (G.teachers || []).filter((x) => (!cont || x.continent === cont) && (!s.value || x.skill === s.value) && (!mm.value || x.mastery === mm.value) &&
          words.every((w) => `${x.name} ${x.skill} ${x.mastery} ${x.house || ""} ${x.map_name || ""} ${x.region || ""} ${x.continent}`.toLowerCase().includes(w)));
      },
      sort: "skill",
      rowClass: (x) => `tint tint-${continentOfName[x.continent] || ""}`,
      columns: [
        { key: "skill", label: "Skill", render: (x) => `<b>${esc(x.skill)}</b>${skillList(x)}`, sort: (x) => x.skill + (MASTERY_ORDER[x.mastery] || 0) + x.continent },
        { key: "mastery", label: "Mastery", render: (x) => `<span class="mastery-${esc(x.mastery)}">${esc(x.mastery)}</span>`, sort: (x) => MASTERY_ORDER[x.mastery] || 0 },
        { key: "name", label: "Teacher", render: (x) => `${esc(x.name)}${x.moved ? ' <span class="tag moved" title="MAW also places this teacher here">MAW</span>' : ""}` },
        { key: "continent", label: "Continent", cls: "nowrap", render: (x) => contBadge(x.continent), sort: (x) => (continents[continentOfName[x.continent]] || {}).world || "" },
        { key: "place", label: "Where", sortable: false, render: placeText },
        { key: "needs", label: "Needs", num: true, cls: "nowrap", render: (x) => { const n = x.needs ? x.needs[md ? md.value : ""] : null; return n ? `skill ${n}` : "–"; }, sort: (x) => (x.needs ? x.needs[md ? md.value : ""] || 0 : 0) },
        { key: "gold", label: "Price", num: true, render: (x) => (x.gold ? fmt(x.gold) : "–") },
        { key: "at", label: "", sortable: false, cls: "nowrap", render: atButtons },
      ],
    });
    [f, s, mm].forEach((x) => x.addEventListener("input", t.draw));
    if (md) md.addEventListener("input", () => { store.set("mode", md.value); t.draw(); });
    bindSeg(c, (v) => { store.set("tcont", v); t.draw(); });
  }

  function pageTeachers() {
    main.innerHTML = pageHead("Teachers", "", "Every Expert, Master and Grandmaster lesson on the four continents, as the game's journal trainer finder lists them under MAW, with the skill level each mastery needs in your progression mode. MAW also seats some teachers in extra houses so every continent has them; those are tagged MAW.") +
      `<div id="teach"></div>` + teacherlessBlock();
    teacherTable(document.getElementById("teach"));
  }
  function teacherlessBlock() {
    const list = G.teacherless || [];
    if (!list.length) return "";
    return `<h2>Skills without teachers</h2><p class="muted">These skills reach their masteries on their own at these skill levels.</p><div class="table-wrap"><table><thead><tr><th>Skill</th>${modes.map((m) => `<th class="num">${esc(m.name)}</th>`).join("")}</tr></thead><tbody>${list.map((s) => `<tr><td><b>${esc(s.skill)}</b></td>${modes.map((m) => `<td class="num">${s.levels && s.levels[m.id] ? s.levels[m.id].join(" / ") : "–"}</td>`).join("")}</tr>`).join("")}</tbody></table></div><p class="muted">Expert / Master / Grandmaster.</p>`;
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Classes and promotions

  const CAP_NAMES = { N: "Novice", E: "Expert", M: "Master", G: "Grandmaster", S: "Supreme", "-": "cannot learn", "": "cannot learn" };
  function cap(v) {
    const k = v && v !== "-" ? v[0].toUpperCase() : "-";
    return k === "-" ? `<span class="cap cap-none" title="cannot learn">–</span>` : `<span class="cap cap-${k}" title="${CAP_NAMES[k]}">${k}</span>`;
  }
  function classIcon(cls, size) { return cls.icon ? `<img src="${esc(cls.icon)}" alt="" width="${size}" height="${size}">` : `<span></span>`; }
  function perLevel(tier, key) { return tier[key] == null ? "–" : tier[key]; }
  const SP_NAMES = { personality: "SP", fixed: "SP (fixed pool)", energy: "Energy", none: "" };
  // Tiers by promotion step: "Master Archer / Sniper" for the two final classes.
  function tierSteps(c) {
    const steps = [];
    c.tiers.forEach((t) => { const s = steps.find((x) => x.step === t.step); if (s) s.names.push(t.name); else steps.push({ step: t.step, names: [t.name], t }); });
    return steps;
  }

  function classGrid(el) {
    const groups = [...new Set((G.classes || []).map((c) => c.group))];
    el.innerHTML = `<div class="toolbar">${seg("cg", [["", "All"], ...groups.map((g) => [g, GROUP_NAMES[g] || g])], "")}</div><div class="class-grid" id="cgrid"></div>`;
    const draw = () => {
      const g = segValue(el.querySelector("#cg"));
      el.querySelector("#cgrid").innerHTML = (G.classes || []).filter((c) => !g || c.group === g).map((c) => {
        const steps = tierSteps(c);
        const sp = SP_NAMES[c.sp_kind] || "SP";
        return `<a class="card class-card" href="#class-${esc(c.id)}">${classIcon(c, 44)}<strong>${esc(c.name)}</strong>
          <span class="line">${esc(steps.map((s) => s.names.join(" / ")).join(" → "))}</span>
          <span class="nums">HP ${esc(steps.map((s) => perLevel(s.t, "hp")).join(" / "))}${c.sp_kind === "personality" ? ` · SP ${esc(steps.map((s) => perLevel(s.t, "sp")).join(" / "))}` : sp ? ` · ${esc(sp)}` : ""} per level</span></a>`;
      }).join("");
    };
    bindSeg(el.querySelector("#cg"), draw);
    draw();
    const notes = G.shared_notes || [];
    if (notes.length) el.insertAdjacentHTML("afterbegin", `<ul>${notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>`);
    const races = G.races || [];
    if (races.length) {
      el.insertAdjacentHTML("beforeend", `<h2 id="races">Races</h2><p class="muted">Any race may take any class; these perks come with the race.</p><div class="table-wrap"><table><thead><tr><th>Race</th><th>Perks</th></tr></thead><tbody>${races.map((r) => `<tr><td><b>${esc(r.race)}</b></td><td><ul style="margin:0;padding-left:18px">${r.notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul></td></tr>`).join("")}</tbody></table></div>`);
    }
  }

  function pageClass(id) {
    const c = classes[id];
    if (!c) return pageMissing();
    const tiers = c.tiers;
    const hasSp = c.sp_kind === "personality" || tiers.some((t) => t.sp);
    const spName = SP_NAMES[c.sp_kind] || "SP";
    const extra = (t, key) => (t.elder ? ` <span class="muted">(Elder ${t.elder[key]}, Ultimate ${t.ultimate[key]})</span>` : "");
    const tierTable = `<div class="table-wrap"><table><thead><tr><th>Class</th><th class="num">HP / level</th>${hasSp ? `<th class="num">${esc(spName)} / level</th>` : ""}</tr></thead><tbody>${tiers.map((t) => `<tr><td>${esc(t.name)}</td><td class="num">${esc(perLevel(t, "hp"))}${extra(t, "hp")}</td>${hasSp ? `<td class="num">${esc(perLevel(t, "sp"))}${extra(t, "sp")}</td>` : ""}</tr>`).join("")}</tbody></table></div>`;
    const start = c.starting ? [c.starting.free && c.starting.free.length ? `Starts with ${c.starting.free.join(", ")}` : "", c.starting.choice && c.starting.choice.length ? `picks more from ${c.starting.choice.join(", ")}` : ""].filter(Boolean).join("; ") : "";
    const base = [c.base_hp != null ? `Base HP ${c.base_hp}` : "", c.base_sp ? `base ${spName} ${c.base_sp}` : "", start].filter(Boolean).join(" · ");
    const skills = `<div class="table-wrap"><table><thead><tr><th>Skill</th>${tiers.map((t) => `<th>${esc(t.name)}</th>`).join("")}</tr></thead><tbody>${(c.skills || []).map((s) => `<tr><td>${esc(s.skill)}</td>${s.caps.map((v) => `<td>${cap(v)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
    main.innerHTML = pageHead(c.name, `<a href="#classes">Classes</a> · ${esc(GROUP_NAMES[c.group] || c.group)}`) +
      `<div class="class-head">${classIcon(c, 64)}<div class="tierline">${tierSteps(c).map((s) => `<span class="t">${esc(s.names.join(" / "))}</span>`).join('<span class="arrow">→</span>')}</div></div>` +
      (base ? `<p class="muted">${esc(base)}</p>` : "") +
      `<div class="two-col"><section class="section"><h2>Tiers</h2>${tierTable}</section>` +
      (c.notes && c.notes.length ? `<section class="section prose"><h2>Mechanics</h2><ul>${c.notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul></section>` : "") + `</div>` +
      `<section class="section"><h2>Promotions</h2>${promotionSteps(c)}</section>` +
      `<section class="section"><h2>Mastery limits</h2><p class="muted">The highest mastery each tier can learn: N Novice, E Expert, M Master, G Grandmaster, S Supreme.</p>${skills}</section>`;
  }

  function promotionSteps(c) {
    const steps = c.promotions || [];
    if (!steps.length) return `<p class="muted">No promotion.</p>`;
    return `<div class="table-wrap"><table><thead><tr><th>Continent</th><th>Promotes to</th><th>Who and where</th><th>Task</th><th></th></tr></thead><tbody>${steps.map((s) => {
      const where = [s.giver, s.house].filter(Boolean).map(esc).join(", ");
      const map = s.map && maps[Path(s.map)] ? mapLink(Path(s.map), s.at && s.at.map === Path(s.map) ? s.at.poi : null, s.map_name) : esc(s.map_name || "");
      const tags = (s.path ? ` <span class="tag">${esc(s.path)} path</span>` : "") + (s.counts === false ? ` <span class="tag" title="Does not count for MAW's cross-continent promotion or Elder / Ultimate">quest only</span>` : "");
      return `<tr class="tint tint-${continentOfName[s.continent] || ""}"><td class="nowrap">${contBadge(s.continent)}</td><td>${esc(s.tier)}${s.step === "final" ? "" : ' <span class="muted">(middle)</span>'}${tags}</td><td>${where}${map ? `<br><span class="muted">${map}</span>` : ""}</td><td>${esc(s.task || "")}</td><td class="nowrap">${s.at ? showBtn(s.at.map, s.at.poi, "Map") : ""}</td></tr>`;
    }).join("")}</tbody></table></div>`;
  }

  function promotionTable(el) {
    const conts = G.continents.map((c) => c.name);
    el.innerHTML = `<div class="table-wrap"><table><thead><tr><th>Class</th>${conts.map((c) => `<th>${contBadge(c)}</th>`).join("")}</tr></thead><tbody>${(G.classes || []).filter((c) => (c.promotions || []).length).map((c) => `<tr><td><a href="#class-${esc(c.id)}"><b>${esc(c.name)}</b></a></td>${conts.map((cont) => {
      const steps = c.promotions.filter((s) => s.continent === cont);
      return `<td>${steps.length ? steps.map((s) => `<div><span class="muted">${esc(s.tier)}${s.path ? " (" + esc(s.path) + ")" : ""}:</span> ${s.at ? `<a href="#map-${esc(s.at.map)}-${esc(s.at.poi)}">${esc(s.giver || s.house || "")}</a>` : esc(s.giver || s.house || "")}</div>`).join("") : '<span class="muted">–</span>'}</td>`;
    }).join("")}</tr>`).join("")}</tbody></table></div>`;
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Where to go: every map's monster levels for the party's banks (MawMonsterLevels.cpp, MawExperienceCurve.cpp)

  // MAW's experience curve: 1000 x level per level, steeper by 1 % a level above 100.
  const EXP_TABLE = (() => {
    const t = [0, 0];
    for (let l = 2; l <= 2000; l++) t[l] = t[l - 1] + 1000 * (l - 1) * Math.max(1 + (l - 101) * 0.01, 1);
    return t;
  })();
  const expStep = (l) => 1000 * l * Math.max(1 + (l - 100) * 0.01, 1);
  function expForLevel(l) {
    if (l <= 1) return 0;
    const w = Math.floor(l);
    return w >= 2000 ? EXP_TABLE[2000] + (l - 2000) * expStep(2000) : EXP_TABLE[w] + (l - w) * expStep(w);
  }
  function levelForExp(e) {
    if (e <= 0) return 1;
    let lo = 1, hi = 2000;
    if (e >= EXP_TABLE[2000]) return 2000 + (e - EXP_TABLE[2000]) / expStep(2000);
    while (hi - lo > 1) { const m = (lo + hi) >> 1; if (EXP_TABLE[m] <= e) lo = m; else hi = m; }
    return lo + (e - EXP_TABLE[lo]) / expStep(lo);
  }
  // Levels added on top of a floor, as the experience they would take at vanilla's 1000 x level.
  function bolstered(floor, levels) {
    floor = Math.max(floor, 0);
    if (levels <= 0) return floor + levels;
    const top = floor + levels;
    return levelForExp(expForLevel(floor) + 500 * (top * (top - 1) - floor * (floor - 1)));
  }
  const mawRound = (v) => (v >= 0 ? Math.floor(v + 0.5) : -Math.floor(-v + 0.5));
  // The levels of a map's three native families (normal tier) for a mode and the levels banked off its continent.
  function familyLevels(m, mode, outside) {
    const L = m.levels;
    const band = L.band || L.free;
    const mean = (band[0] + band[1] + band[2]) / 3;
    const bolster = Math.max(outside - 4, 0);
    return band.map((slot) => {
      let level;
      if (mode === "free") level = bolstered(bolster, slot);
      else if (mode === "madness" && L.madness && !L.madness_start) {
        const offset = (slot - mean) * 2;
        level = Math.max(offset >= 0 ? bolstered(L.madness, offset) : 2 * L.madness - bolstered(L.madness, -offset), 5);
      } else if (L.starter) level = Math.max(Math.min(slot * 2.5, bolstered(bolster, slot)), 1);
      else level = Math.max(slot * 2.5 - 9 + (mean - slot) * (mode === "madness" ? 1 : 1.5), 5);
      return mawRound(Math.max(level, 1));
    });
  }

  function pagePlanner() {
    const saved = store.get("planner", { mode: "free", banks: { enroth: 30, antagarich: 0, jadame: 0, chedian: 0 }, kind: "", cont: "" });
    main.innerHTML = pageHead("Where to go", "", "Enter the levels you earned on each continent (the journal's Progress tab shows them; together they are about your party's level) and your progression. The list shows the maps whose monsters fit you best, with their levels as the game sets them for you now. Bosses and the strong tier sit above these numbers.") +
      `<div class="card section"><div class="toolbar">${seg("pl-mode", [["free", "Free"], ["horizontal", "Horizontal"], ["madness", "Beyond Madness"]], saved.mode)}
        ${G.continents.map((c) => `<label class="nowrap">${contBadge(c.id)} <input class="field" type="number" min="0" max="2000" data-bank="${c.id}" value="${Number(saved.banks[c.id] || 0)}" style="width:5.5em"></label>`).join("")}</div>
        <div class="toolbar">${seg("pl-kind", [["", "All maps"], ["dungeon", "Dungeons"], ["outdoor", "Outdoor"]], saved.kind)}
        ${seg("pl-cont", [["", "Any continent"], ...G.continents.map((c) => [c.id, c.world.toUpperCase()])], saved.cont)}
        <span id="pl-sum" class="muted"></span></div></div><div id="pl-out"></div>`;
    const modeSeg = document.getElementById("pl-mode"), kindSeg = document.getElementById("pl-kind"), contSeg = document.getElementById("pl-cont");
    const inputs = [...main.querySelectorAll("[data-bank]")];
    function draw() {
      const banks = Object.fromEntries(inputs.map((i) => [i.dataset.bank, Math.max(0, Number(i.value) || 0)]));
      const mode = segValue(modeSeg), kind = segValue(kindSeg), cont = segValue(contSeg);
      store.set("planner", { mode, banks, kind, cont });
      const party = Object.values(banks).reduce((a, b) => a + b, 0) || 1;
      document.getElementById("pl-sum").textContent = `Party level ≈ ${party}`;
      const rows = G.maps.filter((m) => m.levels && !m.levels.arena && m.kind !== "city" && !(m.levels.free[0] <= 1 && m.levels.free[2] <= 1)
          && (!cont || m.continent === cont) && (!kind || (kind === "outdoor" ? m.kind === "outdoor" : m.kind !== "outdoor"))
          && (mode !== "madness" || m.levels.madness))
        .map((m) => {
          const lv = familyLevels(m, mode, party - (banks[m.continent] || 0));
          return { m, lv, d: lv[1] - party };
        });
      const near = Math.max(5, Math.round(party * 0.1));
      const verdict = (d) => (Math.abs(d) <= near ? ["Your level", "fit"] : d > 0 ? (d <= near * 3 ? ["A step up", "up"] : ["Too strong", "far"]) : ["Easy", "low"]);
      const pick = (list, n) => list.slice(0, n);
      const fit = rows.filter((r) => Math.abs(r.d) <= near).sort((a, b) => Math.abs(a.d) - Math.abs(b.d));
      const up = rows.filter((r) => r.d > near && r.d <= near * 3).sort((a, b) => a.d - b.d);
      const low = rows.filter((r) => r.d < -near).sort((a, b) => b.d - a.d);
      const table = (list, title, note) => `<h2>${title} <span class="muted" style="font-size:.9rem">${list.length}</span></h2>${note ? `<p class="muted">${note}</p>` : ""}` + (list.length ? `<div class="table-wrap"><table><thead><tr><th>Map</th><th>Continent</th><th>Kind</th><th class="num">Levels</th><th class="num">vs party</th><th class="num">Monsters</th><th>Loot</th><th>Crowding</th></tr></thead><tbody>${list.map((r) => {
        const [label, cls] = verdict(r.d);
        return `<tr class="tint tint-${r.m.continent}"><td>${mapLink(r.m.id)}${r.m.levels.starter && mode !== "free" ? ' <span class="tag">grows with you</span>' : ""}</td><td class="nowrap">${contBadge(r.m.continent)}</td><td>${esc(r.m.kind)}</td><td class="num"><span class="lvl">${esc(r.lv[0] === r.lv[2] ? r.lv[0] : r.lv[0] + "–" + r.lv[2])}</span></td><td class="num nowrap"><span class="fit-${cls}">${r.d > 0 ? "+" : ""}${r.d}</span></td>${STAT_COLUMNS.map((c) => `<td class="${c.num ? "num " : ""}${c.cls}">${c.render(r.m)}</td>`).join("")}</tr>`;
      }).join("")}</tbody></table></div>` : `<p class="muted">None.</p>`);
      document.getElementById("pl-out").innerHTML =
        STAT_NOTE + table(pick(fit, 30), "Your level", `Middle family within ${near} levels of the party.`) +
        table(pick(up, 15), "A step up", "Harder: go with good gear, or once the first list is done.") +
        `<details><summary class="muted">Easier maps (${low.length})</summary>${table(pick(low, 40), "Easy", "Quick clears for completion rewards and materials.")}</details>`;
    }
    inputs.forEach((i) => i.addEventListener("input", draw));
    [modeSeg, kindSeg, contSeg].forEach((x) => bindSeg(x, draw));
    draw();
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Start

  function pageStart() {
    pageContent("start", "MAW Player's Guide");
    const cards = [
      ["progression", "Progression", "Free versus Horizontal, with worked examples"],
      ["planner", "Where to go", "Enter your levels: the maps that fit your party"],
      ["locations", "Locations", `${G.maps.length} maps on four continents, with interactive maps`],
      ["teachers", "Teachers", `${(G.teachers || []).length} lessons, searchable`],
      ["classes", "Classes", `${(G.classes || []).length} classes: tiers, numbers, mastery limits`],
      ["promotions", "Promotions", "How promotions stack: Elder and Ultimate"],
      ["crafting", "Crafting", "What to craft, and when"],
      ["tips", "Tips and HUD", "Reading the screen, keys, hidden rules"],
    ];
    main.insertAdjacentHTML("beforeend", `<h2>Sections</h2><div class="grid-cards">${cards.map(([r, n, d]) => `<a class="card home-card" href="#${r}"><strong>${esc(n)}</strong><span>${esc(d)}</span></a>`).join("")}</div>`);
  }

  function pageMissing() { main.innerHTML = pageHead("Not found", "", `Nothing here. <a href="#start">Back to the start</a>.`); }

  // ---------------------------------------------------------------------------------------------------------------
  // Search

  const searchIndex = [];
  G.maps.forEach((m) => searchIndex.push({ n: m.name, k: `${continents[m.continent].name} map`, h: `#map-${m.id}`, x: m.file }));
  (G.teachers || []).forEach((t) => searchIndex.push({ n: `${t.mastery} ${t.skill}`, k: `${t.name}, ${t.continent}`, h: (t.at || [])[0] ? `#map-${t.at[0].map}-${t.at[0].poi}` : "#teachers", x: t.name }));
  (G.classes || []).forEach((c) => searchIndex.push({ n: c.name, k: "Class", h: `#class-${c.id}`, x: c.tiers.map((t) => t.name).join(" ") }));
  G.maps.forEach((m) => (m.pois || []).forEach((p) => {
    if (["vendor", "guild", "service", "transport", "castle", "promoter", "teacher", "bonus"].includes(p.t)) {
      searchIndex.push({ n: p.n, k: `${p.k || types[p.t].name}, ${m.name}`, h: `#map-${m.id}-${p.id}`, x: (p.people || []).join(" ") });
    }
  }));
  Object.entries(G.content || {}).forEach(([section, html]) => {
    const re = /<h2 id="([^"]+)">([\s\S]*?)<\/h2>/g;
    let match;
    while ((match = re.exec(html))) searchIndex.push({ n: match[2].replace(/<[^>]+>/g, ""), k: section[0].toUpperCase() + section.slice(1), h: `#${section}/${match[1]}` });
  });
  const sInput = document.getElementById("search"), sResults = document.getElementById("search-results");
  let hot = 0;
  function runSearch() {
    const q = sInput.value.trim().toLowerCase();
    if (q.length < 2) { sResults.hidden = true; return; }
    const hits = searchIndex.filter((e) => e.n.toLowerCase().includes(q) || (e.x && e.x.toLowerCase().includes(q)))
      .sort((a, b) => (a.n.toLowerCase().startsWith(q) ? 0 : 1) - (b.n.toLowerCase().startsWith(q) ? 0 : 1)).slice(0, 40);
    hot = 0;
    sResults.innerHTML = hits.length ? hits.map((e, i) => `<a href="${e.h}" class="${i === 0 ? "hot" : ""}">${esc(e.n)}<small>${esc(e.k)}</small></a>`).join("") : `<div class="empty">No matches</div>`;
    sResults.hidden = false;
  }
  sInput.addEventListener("input", runSearch);
  sInput.addEventListener("keydown", (e) => {
    const links = [...sResults.querySelectorAll("a")];
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!links.length) return;
      hot = (hot + (e.key === "ArrowDown" ? 1 : links.length - 1)) % links.length;
      links.forEach((a, i) => a.classList.toggle("hot", i === hot));
    } else if (e.key === "Enter" && links[hot]) {
      location.hash = links[hot].getAttribute("href");
      sResults.hidden = true;
    } else if (e.key === "Escape") sResults.hidden = true;
  });
  sResults.addEventListener("click", () => { sResults.hidden = true; sInput.value = ""; });
  document.addEventListener("click", (e) => { if (!e.target.closest(".search")) sResults.hidden = true; });

  // ---------------------------------------------------------------------------------------------------------------
  // Theme and router

  const root = document.documentElement;
  const savedTheme = store.get("theme", null);
  if (savedTheme) root.dataset.theme = savedTheme;
  document.getElementById("theme-btn").addEventListener("click", () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : !window.matchMedia("(prefers-color-scheme: light)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    store.set("theme", root.dataset.theme);
  });

  const side = document.getElementById("side"), menuBtn = document.getElementById("menu-btn");
  menuBtn.addEventListener("click", () => {
    const open = !side.classList.contains("open");
    side.classList.toggle("open", open);
    menuBtn.setAttribute("aria-expanded", open);
  });
  side.addEventListener("click", (e) => { if (e.target.closest("a.nav-link")) { side.classList.remove("open"); menuBtn.setAttribute("aria-expanded", "false"); } });

  const TITLES = { start: "MAW Player's Guide", progression: "Progression", promotions: "Promotions", crafting: "Crafting",
    tips: "Tips and HUD", chedian: "Chedian (MM9)", combat: "Combat and auras", loot: "Loot", spells: "Spells", deviations: "Deviations from MAW", classes: "Classes" };
  let lastRoute = null;
  function route() {
    const full = decodeURIComponent(location.hash.replace(/^#/, "")) || "start";
    const [r, anchor] = full.split("/");
    if (dialog.open) dialog.close();
    // Selecting a marker rewrites the hash of the map being shown; do not rebuild the page for that.
    if (lastRoute && lastRoute.startsWith("map-") && r.startsWith("map-") && r.split("-")[1] === lastRoute.split("-")[1] && document.getElementById("mv")) {
      lastRoute = r;
      return;
    }
    if (anchor && r === lastRoute) { const el = document.getElementById(anchor); if (el) el.scrollIntoView(); return; }
    lastRoute = r;
    window.scrollTo(0, 0);
    renderNav(r);
    const [head, ...rest] = r.split("-");
    if (head === "start") pageStart();
    else if (head === "locations") pageLocations();
    else if (head === "continent") pageContinent(rest[0]);
    else if (head === "map") pageMap(rest[0], rest[1]);
    else if (head === "teachers") pageTeachers();
    else if (head === "planner") pagePlanner();
    else if (head === "class") pageClass(rest.join("-"));
    else if (TITLES[head]) pageContent(head, TITLES[head]);
    else pageMissing();
    if (anchor) { const el = document.getElementById(anchor); if (el) el.scrollIntoView(); }
    document.title = (main.querySelector("h1") ? main.querySelector("h1").textContent + " · " : "") + "MAW Guide";
  }
  window.addEventListener("hashchange", route);
  route();
})();
