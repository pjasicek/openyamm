/* MM9 Chedian Guide: hash-routed sections over window.GUIDE (data/guide.js, built by tools/mm9_site/build_site.py). */
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
      try { const v = localStorage.getItem("mm9guide." + key); return v == null ? fallback : JSON.parse(v); }
      catch (e) { return fallback; }
    },
    set(key, value) { try { localStorage.setItem("mm9guide." + key, JSON.stringify(value)); } catch (e) { /* ignore */ } },
  };
  const byId = (list, key = "id") => Object.fromEntries(list.map((x) => [x[key], x]));
  const maps = byId(G.maps);
  const quests = byId(G.quests);
  const monsters = byId(G.monsters);
  const items = byId(G.items);
  const regions = byId(G.regions);
  const regionOfMap = {};
  G.regions.forEach((r) => r.maps.forEach((m) => { regionOfMap[m] = r; }));
  const poiIndex = {};
  G.maps.forEach((m) => { poiIndex[m.id] = byId(m.pois); });
  const types = G.poiTypes;
  const MASTERY_ORDER = { Learn: 0, Expert: 1, Master: 2, Grandmaster: 3 };
  const mapName = (id) => (maps[id] ? maps[id].name : id);
  const fmt = (n) => Number(n).toLocaleString("en-US");

  function mapLink(map, poi, label) {
    return `<a href="#map-${map}${poi ? "-" + poi : ""}" data-map="${esc(map)}" data-poi="${esc(poi || "")}" class="maplink">${esc(label || mapName(map))}</a>`;
  }
  function showBtn(map, poi, label) {
    return `<button type="button" class="btn" data-show-map="${esc(map)}" data-show-poi="${esc(poi || "")}">${esc(label || "Map")}</button>`;
  }
  function atLinks(at, withName) {
    if (!at || !at.length) return `<span class="muted">not placed</span>`;
    return at.map((a) => `${withName && a.name ? esc(a.name) + ", " : ""}${mapLink(a.map, a.poi)} ${showBtn(a.map, a.poi, "Show")}`).join("<br>");
  }
  function iconHtml(item, size = 40) {
    if (!item || item.icon < 0) return `<span class="icon" style="width:${size}px;height:${size}px"></span>`;
    const A = G.iconAtlas;
    const k = size / A.cell;
    const x = (item.icon % A.cols) * size;
    const y = Math.floor(item.icon / A.cols) * size;
    return `<span class="icon" role="img" aria-label="${esc(item.name)}" style="width:${size}px;height:${size}px;background-image:url(${A.src});background-size:${A.cols * A.cell * k}px ${A.rows * A.cell * k}px;background-position:-${x}px -${y}px"></span>`;
  }
  function shotHtml(src, alt, size) {
    return `<a class="shot ${size || ""}" href="${src}" target="_blank" rel="noopener"><img src="${src}" alt="${esc(alt)} in game" loading="lazy"></a>`;
  }
  function poiOf(ref) { return ref && poiIndex[ref.map] ? poiIndex[ref.map][ref.poi] : null; }
  function typeChip(t) {
    const T = types[t];
    return `<span class="chip" style="--c:${T.color}"><span class="dot"></span>${esc(T.name)}</span>`;
  }

  // Sortable, filterable tables: columns = [{key, label, num, render, sort}], rows = data objects.
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
        // Groups in their own fixed order; the chosen sort applies inside each group.
        const groups = new Map();
        rows.forEach((r) => { const k = opts.group(r); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(r); });
        const keys = [...groups.keys()].sort((a, b) => opts.groupOrder(a, groups.get(a)) - opts.groupOrder(b, groups.get(b)) || String(a).localeCompare(String(b)));
        rows = keys.flatMap((k) => [{ __group: k, __rows: groups.get(k) }, ...groups.get(k)]);
      }
      const head = opts.columns.map((c) => `<th class="${c.sortable === false ? "" : "sortable"} ${c.key === sortKey ? "sorted" + (asc ? " asc" : "") : ""} ${c.num ? "num" : ""}" data-key="${c.key}">${esc(c.label)}</th>`).join("");
      const body = rows.length ? rows.map((r, i) => {
        if (r.__group !== undefined) return `<tr class="group-row"><th colspan="${opts.columns.length}">${opts.groupLabel(r.__group, r.__rows)}</th></tr>`;
        const key = String(opts.rowKey ? opts.rowKey(r) : i);
        const tds = opts.columns.map((c) => `<td class="${c.num ? "num" : ""} ${c.cls || ""}">${c.render ? c.render(r) : esc(r[c.key])}</td>`).join("");
        const detail = opts.detail && open === key ? `<tr class="detail"><td colspan="${opts.columns.length}">${opts.detail(r)}</td></tr>` : "";
        return `<tr class="${opts.detail ? "clickable" : ""}" data-key="${esc(key)}">${tds}</tr>${detail}`;
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
      if (tr && opts.detail) {
        open = open === tr.dataset.key ? null : tr.dataset.key;
        draw();
      }
    });
    draw();
    return { draw, open(key) { open = String(key); draw(); } };
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Interactive map

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
      this.only = opts.only ? new Set(opts.only) : null;
      this.ids = opts.ids ? new Set(opts.ids) : null;
      this.labels = opts.compact ? true : showLabels;
      root.innerHTML = `
        <div class="mv ${opts.dialog ? "dialog-map" : ""} ${opts.compact ? "compact" : ""}">
          <div class="mv-bar">
            <div class="mv-floors">${map.floors.length > 1 ? map.floorNames.map((n, i) => `<button type="button" class="btn" data-floor="${i}">${esc(opts.compact ? n.replace("Level ", "") : n)}</button>`).join("") : ""}</div>
            <div class="mv-zoom">
              ${opts.compact ? `<a class="btn" href="#map-${map.id}">${esc(map.name)} ↗</a>` : `<button type="button" class="btn" data-act="labels" aria-pressed="${showLabels}">${showLabels ? "Hide labels" : "Show labels"}</button>`}
              <button type="button" class="btn" data-act="in" aria-label="Zoom in">+</button>
              <button type="button" class="btn" data-act="out" aria-label="Zoom out">−</button>
              <button type="button" class="btn" data-act="fit">Fit</button>
            </div>
          </div>
          <div class="mv-view" tabindex="0" aria-label="${esc(map.name)} map; drag to pan, scroll or pinch to zoom">
            <div class="mv-stage"><img alt="${esc(map.name)}" draggable="false"><div class="mv-pins"></div></div>
            <div class="mv-tip" hidden></div>
          </div>
          <div class="mv-legend"></div>
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
      if (opts.focusName && !opts.focus) {
        const needle = opts.focusName.toLowerCase();
        const hit = map.pois.find((p) => (!this.only || this.only.has(p.t)) && p.n.toLowerCase().includes(needle))
          || map.pois.find((p) => p.n.toLowerCase().includes(needle));
        if (hit) opts.focus = hit.id;
      }
      if (this.only && opts.focus) this.keep = opts.focus;
      const firstId = this.ids ? [...this.ids].find((id) => poiIndex[map.id][id]) : null;
      const startPoi = poiIndex[map.id][opts.focus] || poiIndex[map.id][firstId];
      this.setFloor(startPoi ? startPoi.f : 0, true);
      if (opts.compact) {
        // Inline maps open showing the whole map; the focused point is only highlighted.
        if (opts.focus && poiIndex[map.id][opts.focus]) { this.keep = this.keep || opts.focus; this.renderPins(); this.select(opts.focus, true); }
        requestAnimationFrame(() => this.fit());
      } else if (opts.focus) this.focus(opts.focus);
      else this.fit();
    }
    get floorData() { return this.map.floors[this.floor]; }
    setFloor(i, quiet) {
      this.floor = i;
      const f = this.floorData;
      this.img.src = f.img;
      this.img.width = f.w; this.img.height = f.h;
      this.root.querySelectorAll("[data-floor]").forEach((b) => b.classList.toggle("active", Number(b.dataset.floor) === i));
      this.renderPins();
      this.renderLegend();
      if (!quiet) this.fit();
    }
    visiblePois() {
      if (this.ids) return this.map.pois.filter((p) => p.f === this.floor && (this.ids.has(p.id) || (this.only && this.only.has(p.t))));
      if (this.only) return this.map.pois.filter((p) => p.f === this.floor && (this.only.has(p.t) || p.id === this.keep));
      return this.map.pois.filter((p) => p.f === this.floor && !hiddenTypes.has(p.t));
    }
    renderPins() {
      const f = this.floorData;
      const small = new Set(["door", "monster", "breakable", "trap", "ladder", "loot", "npc"]);
      this.pins.innerHTML = this.visiblePois().map((p) => {
        const T = types[p.t];
        // A quest's own points always get a full, labelled marker.
        if (this.ids && this.ids.has(p.id)) {
          return `<button type="button" class="pin ${this.sel === p.id ? "sel" : ""}" data-id="${esc(p.id)}" style="left:${(p.u * f.w).toFixed(1)}px;top:${(p.v * f.h).toFixed(1)}px;--c:${T.color}" aria-label="${esc(T.name + ": " + p.n)}">${esc(T.glyph)}<span class="lbl">${esc(p.n)}</span></button>`;
        }
        const lbl = this.labels && !small.has(p.t) ? `<span class="lbl">${esc(p.n)}</span>` : "";
        return `<button type="button" class="pin ${small.has(p.t) ? "small" : ""} ${this.sel === p.id ? "sel" : ""}" data-id="${esc(p.id)}" style="left:${(p.u * f.w).toFixed(1)}px;top:${(p.v * f.h).toFixed(1)}px;--c:${T.color}" aria-label="${esc(T.name + ": " + p.n)}">${small.has(p.t) ? "" : esc(T.glyph)}${lbl}</button>`;
      }).join("");
    }
    renderLegend() {
      if (this.only) {
        const present = new Set(this.visiblePois().map((p) => p.t));
        this.legend.innerHTML = Object.keys(types).filter((t) => present.has(t)).map((t) => `<span class="legend-key" style="--c:${types[t].color}"><span class="g">${esc(types[t].glyph)}</span>${esc(types[t].name)}</span>`).join("");
        return;
      }
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
    // Zoom to the box around some points (a quest's), never past four times the whole-map view.
    fitTo(points) {
      if (!points.length) { this.fit(); return; }
      const f = this.floorData;
      const w = this.view.clientWidth || 800, h = this.view.clientHeight || 600;
      const xs = points.map((p) => p.u * f.w), ys = points.map((p) => p.v * f.h);
      const bw = Math.max(...xs) - Math.min(...xs) + f.w * 0.12, bh = Math.max(...ys) - Math.min(...ys) + f.h * 0.12;
      const fit = this.fitScale();
      const s = Math.min(Math.max(Math.min(w / bw, h / bh), fit), fit * 4);
      const cu = (Math.max(...xs) + Math.min(...xs)) / 2 / f.w, cv = (Math.max(...ys) + Math.min(...ys)) / 2 / f.h;
      this.centerOn(cu, cv, s);
    }
    zoomAt(k, px, py) {
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
      // Keep the image over the whole view where it is large enough: no empty band beside a point near an edge.
      const iw = f.w * s, ih = f.h * s;
      this.tx = iw > w ? Math.min(0, Math.max(w - iw, this.tx)) : (w - iw) / 2;
      this.ty = ih > h ? Math.min(0, Math.max(h - ih, this.ty)) : (h - ih) / 2;
      this.apply();
    }
    focus(id) {
      const p = poiIndex[this.map.id][id];
      if (!p) { this.fit(); return; }
      if (!this.only && hiddenTypes.has(p.t)) { hiddenTypes.delete(p.t); store.set("hidden", [...hiddenTypes]); }
      this.sel = id;
      if (p.f !== this.floor) this.setFloor(p.f, true); else { this.renderPins(); this.renderLegend(); }
      requestAnimationFrame(() => this.centerOn(p.u, p.v, this.opts.compact ? this.fitScale() * 1.6 : Math.max(this.fitScale() * 2.2, Math.min(1.1, this.fitScale() * 4))));
      this.select(id, true);
    }
    select(id, quiet) {
      this.sel = id;
      this.pins.querySelectorAll(".pin.sel").forEach((b) => b.classList.remove("sel"));
      const el = this.pins.querySelector(`[data-id="${CSS.escape(id)}"]`);
      if (el) el.classList.add("sel");
      const p = poiIndex[this.map.id][id];
      this.info.innerHTML = poiInfo(this.map, p);
      if (this.opts.compact && !quiet) this.showTipFor(p);
      if (this.opts.onSelect) this.opts.onSelect(p);
    }
    showTipFor(p) {
      const el = this.pins.querySelector(`[data-id="${CSS.escape(p.id)}"]`);
      if (!el) return;
      const r = el.getBoundingClientRect(), v = this.view.getBoundingClientRect();
      this.tip.hidden = false;
      this.tip.innerHTML = `<b>${esc(p.n)}</b>${p.d ? "<br>" + esc(p.d) : ""}`;
      this.tip.style.left = Math.max(4, Math.min(r.left - v.left + 14, this.view.clientWidth - 240)) + "px";
      this.tip.style.top = Math.min(r.top - v.top + 14, this.view.clientHeight - 60) + "px";
    }
    bind() {
      const pointers = new Map();
      let start = null, moved = false, pinch = null;
      const rel = (e) => { const r = this.view.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
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
            this.tip.innerHTML = `<b>${esc(p.n)}</b>${p.d ? "<br>" + esc(p.d) : ""}`;
            this.tip.style.left = Math.min(x + 14, this.view.clientWidth - 240) + "px";
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
          if (pin) this.select(pin.dataset.id);
        }
        if (pointers.size === 1) {
          const [p] = [...pointers.values()];
          const r = this.view.getBoundingClientRect();
          start = { x: p[0] + r.left, y: p[1] + r.top, tx: this.tx, ty: this.ty, target: this.view };
        }
      };
      this.view.addEventListener("pointerup", end);
      this.view.addEventListener("pointercancel", end);
      this.view.addEventListener("pointerleave", () => { if (!this.opts.compact) this.tip.hidden = true; });
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
        let first = true;
        new ResizeObserver(() => { if (first) { first = false; return; } if (!this.sel) this.fit(); }).observe(this.view);
      }
    }
  }

  function poiInfo(map, p) {
    const T = types[p.t];
    const parts = [`<span class="t">${esc(T.name)}</span><h3>${esc(p.n)}</h3>`];
    if (p.shot) parts.push(shotHtml(p.shot, p.n, "small"));
    if (p.d) parts.push(`<div>${esc(p.d)}</div>`);
    const links = [];
    if (p.map) links.push(`Leads to ${mapLink(p.map)}`);
    if (p.mon && monsters[p.mon]) links.push(`<a href="#monster-${p.mon}">Bestiary entry</a>`);
    if (p.quests) links.push("Quests: " + p.quests.map((q) => `<a href="#quest-${q}">${esc(quests[q].title)}</a>`).join(", "));
    if (p.t === "teacher") links.push(`<a href="#teachers" data-filter="${esc(p.n)}">All lessons</a>`);
    if (p.promo) links.push(`<a href="#quests-promotion">${esc(p.promo)} promotion</a>`);
    if (p.dock) links.push(`<a href="#travel">Schedule</a>`);
    if (p.vendor || p.service) links.push(`<a href="#shops">Shops and services</a>`);
    if (links.length) parts.push(`<div>${links.join(" · ")}</div>`);
    if (!poiIndex[map.id]) return parts.join("");
    return parts.join("");
  }

  // Map dialog, used from every section's "Show" buttons.
  const dialog = document.getElementById("map-dialog");
  function openMapDialog(mapId, poi) {
    const m = maps[mapId];
    if (!m) return;
    document.getElementById("dlg-title").textContent = m.name;
    const open = document.getElementById("dlg-open");
    open.href = `#map-${mapId}${poi ? "-" + poi : ""}`;
    if (typeof dialog.showModal === "function") dialog.showModal(); else dialog.setAttribute("open", "");
    new MapView(document.getElementById("dlg-body"), m, { dialog: true, focus: poi || null });
  }
  document.getElementById("dlg-close").addEventListener("click", () => dialog.close());
  document.getElementById("dlg-open").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); });
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-show-map]");
    if (b) { e.preventDefault(); openMapDialog(b.dataset.showMap, b.dataset.showPoi); return; }
    const f = e.target.closest("[data-filter]");
    if (f) pendingFilter = f.dataset.filter;
    if (dialog.open && e.target.closest(".mv-info a")) dialog.close();
  });
  let pendingFilter = null;

  // ---------------------------------------------------------------------------------------------------------------
  // Navigation

  const SECTIONS = [
    { id: "quests", name: "Quests", count: G.quests.length, subs: [["quests-main", "Main story"], ["quests-side", "Side quests"], ["quests-promotion", "Promotions"]] },
    { id: "maps", name: "Maps", count: G.maps.length },
    { id: "travel", name: "Travel", count: G.travel.schedules.length },
    { id: "teachers", name: "Teachers", count: G.teachers.length },
    { id: "shops", name: "Shops", count: G.vendors.length + G.services.length },
    { id: "bestiary", name: "Bestiary", count: G.monsters.length },
    { id: "items", name: "Items", count: G.items.length, subs: G.itemCategories.map((c) => ["items-" + c.id, c.name]).concat([["items-setbonus", "Set bonuses"], ["items-enchants", "Enchantments"]]) },
    { id: "faq", name: "FAQ", count: G.faq.length },
  ];
  function sectionOf(route) {
    const head = route.split("-")[0];
    return { quest: "quests", map: "maps", monster: "bestiary", item: "items" }[head] || head;
  }
  function renderNav(route) {
    const sec = sectionOf(route);
    const nav = document.getElementById("nav");
    nav.innerHTML = `<div class="nav-group">${SECTIONS.map((s) => {
      let sub = "";
      if (s.id === sec && s.subs) {
        sub = `<div class="nav-sub">${s.subs.map(([r, n]) => `<a class="nav-link ${route === r ? "active" : ""}" href="#${r}">${esc(n)}</a>`).join("")}</div>`;
      } else if (s.id === sec && s.id === "maps") {
        sub = `<div class="nav-sub">${G.regions.map((r) => `<div class="nav-head">${esc(r.name)}</div>${r.maps.filter((m) => maps[m]).map((m) => `<a class="nav-link ${route.startsWith("map-" + m) && (route === "map-" + m || route.startsWith("map-" + m + "-")) ? "active" : ""}" href="#map-${m}">${esc(mapName(m))}</a>`).join("")}`).join("")}</div>`;
      }
      return `<a class="nav-link ${sec === s.id && !s.subs ? "active" : ""}" href="#${s.subs ? s.subs[0][0] : s.id}">${esc(s.name)} <span class="count">${s.count}</span></a>${sub}`;
    }).join("")}</div>`;
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Pages

  function pageHead(title, crumbs, lead) {
    return `<div class="page-head">${crumbs ? `<div class="crumbs">${crumbs}</div>` : ""}<h1>${esc(title)}</h1>${lead ? `<p class="muted">${lead}</p>` : ""}</div>`;
  }

  function pageHome() {
    const npcCount = G.maps.reduce((n, m) => n + m.pois.filter((p) => ["teacher", "vendor", "quest", "promoter", "service", "transport", "hireling"].includes(p.t)).length, 0);
    const cards = [
      ["quests-main", "Quests", `${G.quests.filter((q) => q.cat === "main").length} story, ${G.quests.filter((q) => q.cat === "side").length} side, ${G.promotions.length} promotions`],
      ["maps", "Maps", `${G.maps.length} maps, ${fmt(G.maps.reduce((n, m) => n + m.pois.length, 0))} marked points`],
      ["travel", "Travel", `${new Set(G.travel.schedules.map((s) => s.vessel)).size} ships and coaches, route planner`],
      ["teachers", "Teachers", `${G.teachers.length} lessons from Learn to Grandmaster`],
      ["shops", "Shops", `${G.vendors.length} shops, ${G.spellbooks.length} spellbooks, ${G.services.length} temples, taverns and banks`],
      ["bestiary", "Bestiary", `${G.monsters.length} monsters with stats and loot`],
      ["items-weapons", "Items", `${G.items.length} items, ${G.items.filter((i) => i.cat === "artifacts").length} artifacts and relics, ${G.sets.length} sets`],
      ["faq", "FAQ", G.faq.map((f) => f.short).join(", ")],
    ];
    main.innerHTML = pageHead("Chedian", "", `Might and Magic IX as rebuilt in OpenYAMM: every map with its teachers, shops, quest givers, chests and mechanisms; ${npcCount} named NPCs placed. Data comes straight from the game's world package.`) +
      `<div class="grid-cards">${cards.map(([r, n, d]) => `<a class="card home-card" href="#${r}"><strong>${esc(n)}</strong><span class="muted">${esc(d)}</span></a>`).join("")}</div>` +
      `<div class="section"><h2>Regions</h2><div class="thumbs">${G.regions.filter((r) => !r.passage).map((r) => {
        const hub = maps[r.hub];
        return hub ? `<a class="thumb" href="#map-${r.hub}"><img src="${hub.thumb}" alt="" loading="lazy"><span>${esc(r.name)}</span><small>${r.maps.length} maps</small></a>` : "";
      }).join("")}</div></div>`;
  }

  // Quests ---------------------------------------------------------------------------------------------------------
  // A document, not cards: chapter, section, quest; each quest's text with its compact maps beside it.

  const walk = G.walkthroughs || {};
  // Every point tagged with a quest, by quest.
  const questPois = {};
  G.maps.forEach((m) => m.pois.forEach((p) => (p.quests || []).forEach((k) => { (questPois[k] = questPois[k] || []).push({ map: m.id, poi: p.id }); })));
  const MECHANISMS = new Set(["exit", "lever", "secret", "trap", "teleporter", "ladder", "hint"]);
  let openWalkthroughs = store.get("openWalk", false);

  // Each person once, with the maps they stand on.
  function people(list) {
    const byName = new Map();
    list.forEach((g) => { if (!byName.has(g.name)) byName.set(g.name, []); if (!byName.get(g.name).some((x) => x.map === g.map)) byName.get(g.name).push(g); });
    return [...byName.entries()].map(([name, at]) => `<b>${esc(name)}</b> <span class="muted">(${at.map((g) => mapLink(g.map, g.poi)).join(", ")})</span>`).join("; ");
  }
  function inlineMap(view) {
    return `<figure class="inline-map" data-map="${esc(view.map)}" data-ids="${esc((view.ids || []).join(","))}" data-show="${esc((view.show || []).join(","))}" data-focus="${esc(view.focus || "")}"><div class="im-body"><div class="im-wait">${esc(mapName(view.map))}</div></div>${view.caption ? `<figcaption>${esc(view.caption)}</figcaption>` : ""}</figure>`;
  }
  // The quest's own points: its people, its steps and everything tagged with it, grouped by map (giver's map first).
  function questViews(q, entry) {
    const refs = [];
    const push = (r) => { if (r && r.poi && poiIndex[r.map] && poiIndex[r.map][r.poi]) refs.push({ map: r.map, poi: r.poi }); };
    if (entry && entry.from) push(entry.from); else q.givers.forEach(push);
    if (entry && entry.to) push(entry.to); else if (!entry) q.handoffs.forEach(push);
    (entry && entry.points || []).forEach(push);
    q.steps.forEach(push);
    (questPois[q.id] || []).forEach(push);
    const byMap = new Map();
    refs.forEach((r) => { if (!byMap.has(r.map)) byMap.set(r.map, new Set()); byMap.get(r.map).add(r.poi); });
    if (entry && entry.maps && entry.maps.length) {
      return entry.maps.map((v) => ({ map: v.map, ids: [...(byMap.get(v.map) || [])], show: (v.show || []).filter((t) => MECHANISMS.has(t)), focus: v.focus, caption: v.caption }));
    }
    return [...byMap.entries()].slice(0, 3).map(([map, ids]) => ({ map, ids: [...ids] }));
  }
  function questBlock(q, entry, level) {
    const h = level || "h4";
    const promo = q.promo ? ` <span class="chip">${esc(q.promo)} promotion</span>` : "";
    const summary = (entry && entry.summary) || (q.stages.find((s) => s.text) || {}).text || "";
    const from = entry && entry.from ? [entry.from] : q.givers;
    const to = entry && entry.to ? [entry.to] : (entry ? [] : q.handoffs.filter((x) => !from.some((g) => g.name === x.name)));
    const facts = [];
    facts.push(from.length ? `<dt>Take it from</dt><dd>${people(from)}</dd>` : `<dt>Starts</dt><dd class="muted">from events, not a person</dd>`);
    if (to.length) facts.push(`<dt>Report to</dt><dd>${people(to)}</dd>`);
    if (q.level) facts.push(`<dt>Level</dt><dd><span class="level-badge">~${q.level.rec}</span> <span class="muted">monsters ${q.level.lo}–${q.level.hi} in ${q.level.maps.map((m) => mapLink(m)).join(", ")}</span></dd>`);
    if (entry && entry.requires) facts.push(`<dt>Needs</dt><dd>${esc(entry.requires)}</dd>`);
    if (entry && entry.reward) facts.push(`<dt>Reward</dt><dd class="reward">${esc(entry.reward)}</dd>`);
    let how = "";
    if (entry && entry.steps && entry.steps.length) {
      how = `<ol class="steps">${entry.steps.map((x) => `<li>${esc(x)}</li>`).join("")}</ol>` +
        (entry.tips && entry.tips.length ? `<ul class="tips">${entry.tips.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "") +
        (entry.figures || []).map((f) => `<figure class="story-figure"><a href="${esc(f.img)}" target="_blank" rel="noopener"><img src="${esc(f.img)}" alt="${esc(f.caption || "")}" loading="lazy"></a>${f.caption ? `<figcaption>${esc(f.caption)}</figcaption>` : ""}</figure>`).join("");
    } else {
      how = `<p class="muted">No written walkthrough yet.</p>` +
        (q.steps.length ? `<p>Quest points: ${q.steps.map((st) => `${esc(st.name)} (${mapLink(st.map, st.poi)})`).join("; ")}</p>` : "");
    }
    const journal = `<details class="journal"><summary>Journal notes (${q.stages.length})</summary><ol>${q.stages.map((st) => `<li>${esc(st.text) || "<span class=muted>(no text)</span>"}</li>`).join("")}</ol></details>`;
    return `<article class="story-quest" id="q-${q.id}">
      <div class="sq-text"><${h}><a href="#quest-${q.id}">${esc(q.title)}</a>${q.level ? ` <span class="level-badge" title="Recommended party level">L${q.level.rec}</span>` : ""}${promo}</${h}>
        ${summary ? `<p class="summary">${esc(summary)}</p>` : ""}
        <dl class="facts">${facts.join("")}</dl>
        <details class="walkthrough" ${openWalkthroughs ? "open" : ""}><summary>Walkthrough</summary>${how}${journal}</details></div>
      <div class="sq-maps">${questViews(q, entry).map(inlineMap).join("")}</div></article>`;
  }
  let mapObserver = null;
  function mountInlineMaps(root) {
    if (mapObserver) mapObserver.disconnect();
    const mount = (fig) => {
      const m = maps[fig.dataset.map];
      if (!m || fig.dataset.mounted) return;
      fig.dataset.mounted = "1";
      const ids = fig.dataset.ids ? fig.dataset.ids.split(",") : [];
      const show = fig.dataset.show ? fig.dataset.show.split(",") : [];
      new MapView(fig.querySelector(".im-body"), m, { compact: true, ids, only: show, focusName: fig.dataset.focus || null });
    };
    const figs = [...root.querySelectorAll(".inline-map")];
    if (!window.IntersectionObserver) { figs.forEach(mount); return; }
    mapObserver = new IntersectionObserver((entries) => entries.forEach((e) => { if (e.isIntersecting) { mount(e.target); mapObserver.unobserve(e.target); } }), { rootMargin: "400px" });
    figs.forEach((f) => mapObserver.observe(f));
  }
  function walkToggle() {
    return `<label class="walk-toggle"><input type="checkbox" id="walk-all" ${openWalkthroughs ? "checked" : ""}> Open every walkthrough</label>`;
  }
  function bindWalkToggle() {
    const box = document.getElementById("walk-all");
    if (!box) return;
    box.addEventListener("change", () => {
      openWalkthroughs = box.checked;
      store.set("openWalk", openWalkthroughs);
      main.querySelectorAll("details.walkthrough").forEach((d) => { d.open = openWalkthroughs; });
    });
  }
  function questTabs(active) {
    return `<div class="tabs">${[["quests-main", "Main story"], ["quests-side", "Side quests"], ["quests-promotion", "Promotions"]].map(([r, n]) => `<a href="#${r}" class="${r === active ? "active" : ""}">${n}</a>`).join("")}</div>`;
  }
  function storyToc() {
    const written = Object.fromEntries((G.story || []).map((c) => [c.id, c]));
    return `<nav class="toc" aria-label="Chapters">${G.chapters.map((cfg) => written[cfg.id] || { id: cfg.id, title: cfg.name, sections: [] }).map((c) => `<a href="#quests-main" data-jump="ch-${c.id}">${esc(c.title)}</a>${c.id === 1 ? `<span class="toc-sub">${c.sections.map((sec, i) => `<a href="#quests-main" data-jump="ch-${c.id}-${i}">${esc(sec.title.split(":")[0])}</a>`).join("")}</span>` : ""}`).join("")}</nav>`;
  }
  function pageQuests(kind) {
    const route = "quests-" + kind;
    if (kind === "main") {
      const written = new Set((G.story || []).flatMap((c) => c.sections.flatMap((sec) => (sec.quests || []).map((e) => e.quest))));
      const storyChapters = Object.fromEntries((G.story || []).map((c) => [c.id, c]));
      const chapterHtml = G.chapters.map((cfg) => storyChapters[cfg.id] || { id: cfg.id, title: cfg.name, intro: "", sections: [] }).map((c) => {
        const missing = G.quests.filter((q) => q.cat === "main" && q.chapter === c.id && !written.has(q.id));
        return `<section class="story-chapter" id="ch-${c.id}"><h2>${esc(c.title)}</h2>${c.intro ? `<p class="lead">${esc(c.intro)}</p>` : ""}
          ${c.sections.map((sec, i) => {
            const giver = sec.giver ? ` <span class="giver">${esc(sec.giver.npc)}, ${mapLink(sec.giver.map, sec.giver.poi)}</span>` : "";
            const sectionTitle = c.sections.length > 1 || sec.title !== c.title ? `<h3 id="ch-${c.id}-${i}">${esc(sec.title)}</h3>${giver}${sec.intro ? `<p>${esc(sec.intro)}</p>` : ""}` : "";
            return `<div class="story-section">${sectionTitle}${(sec.quests || []).map((e) => quests[e.quest] ? questBlock(quests[e.quest], walk[e.quest] || e) : "").join("")}</div>`;
          }).join("")}
          ${missing.map((q) => questBlock(q, null)).join("")}</section>`;
      }).join("");
      main.innerHTML = pageHead("Main story", "Quests", "The walkthrough in story order. Maps beside each quest show only what that quest needs; open a map for everything.") + questTabs(route) + walkToggle() + storyToc() + `<div class="story">${chapterHtml || ""}</div>`;
    } else if (kind === "side") {
      const groups = {};
      G.quests.filter((q) => q.cat === "side").forEach((q) => {
        const g = q.givers[0] || q.handoffs[0];
        const r = g ? (regionOfMap[g.map] || { name: "Elsewhere" }).name : "Without a placed giver";
        (groups[r] = groups[r] || []).push(q);
      });
      const order = G.regions.map((r) => r.name).concat(["Elsewhere", "Without a placed giver"]);
      main.innerHTML = pageHead("Side quests", "Quests", "Grouped by where the quest giver stands.") + questTabs(route) + walkToggle() +
        `<div class="story">${order.filter((r) => groups[r]).map((r) => `<section class="story-chapter"><h2>${esc(r)}</h2>${groups[r].map((q) => questBlock(q, walk[q.id], "h3")).join("")}</section>`).join("")}</div>`;
    } else {
      main.innerHTML = pageHead("Promotions", "Quests", "Each MM9 promotion quest promotes the OpenYAMM class lines listed; every eligible party member is promoted at once.") + questTabs(route) + walkToggle() +
        `<div class="story">${G.promotions.map((p) => {
          const qs = p.quests.map((k) => quests[k]).filter(Boolean);
          const at = p.at[0];
          return `<section class="story-chapter"><h2>${esc(p.to)} <span class="muted">from ${esc(p.from)}</span></h2>
            <p class="who">Promoter: ${p.at.length ? p.at.map((a) => `${esc(a.name)} (${mapLink(a.map, a.poi)})`).join("; ") : "a map event"} · Classes: ${p.classes.map(([a, b]) => `${esc(a)} → <b>${esc(b)}</b>`).join(", ") || "–"}</p>
            ${p.note ? `<p>${esc(p.note)}</p>` : ""}
            ${qs.length ? qs.map((q) => questBlock(q, walk[q.id], "h3")).join("") : (at ? `<article class="story-quest"><div class="sq-text"><p>No separate quest note.</p></div><div class="sq-maps">${inlineMap({ map: at.map, ids: [at.poi] })}</div></article>` : "")}
          </section>`;
        }).join("")}</div>`;
    }
    mountInlineMaps(main);
    bindWalkToggle();
    main.querySelectorAll("[data-jump]").forEach((a) => a.addEventListener("click", (e) => {
      e.preventDefault();
      const el = document.getElementById(a.dataset.jump);
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    }));
  }
  function pageQuest(id) {
    const q = quests[id];
    if (!q) return pageMissing();
    const sub = { main: "Main story", side: "Side quests", promotion: "Promotions" }[q.cat];
    const chapter = q.cat === "main" ? (G.chapters.find((c) => c.id === q.chapter) || {}).name : "";
    main.innerHTML = pageHead(q.title, `<a href="#quests-${q.cat}">${sub}</a>${chapter ? " · " + esc(chapter) : ""}`) +
      `<div class="story">${questBlock(q, walk[q.id], "h2")}</div>`;
    main.querySelector(".walkthrough").open = true;
    mountInlineMaps(main);
  }

  // Maps ---------------------------------------------------------------------------------------------------------

  function pageMaps() {
    main.innerHTML = pageHead("Maps", "", "Original MM9 map art with every point of interest from the rebuilt maps. Pick a map; toggle marker types in its legend.") +
      `<div class="map-index">${G.regions.map((r) => `<section class="region-row"><h2>${esc(r.name)}</h2><div class="thumbs">${r.maps.filter((m) => maps[m]).map((id) => {
        const m = maps[id];
        return `<a class="thumb" href="#map-${id}"><img src="${m.thumb}" alt="" loading="lazy"><span>${esc(m.name)}</span><small>${esc(m.kind)}${m.floors.length > 1 ? ", " + m.floors.length + " levels" : ""}</small></a>`;
      }).join("")}</div></section>`).join("")}</div>`;
  }

  function pageMap(id, poi) {
    const m = maps[id];
    if (!m) return pageMissing();
    const region = regionOfMap[id];
    main.innerHTML = pageHead(m.name, `<a href="#maps">Maps</a> · ${esc(region ? region.name : "")} · ${esc(m.kind)}`) +
      `<div class="map-layout"><div id="mv"></div><aside class="poi-panel"><input class="field" id="poi-filter" type="search" placeholder="Filter points on this map" aria-label="Filter points"><div class="poi-list" id="poi-list"></div></aside></div><div class="map-facts" id="map-facts"></div>`;
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
      m.pois.filter((p) => !hiddenTypes.has(p.t) && (!q || (p.n + " " + (p.d || "")).toLowerCase().includes(q)))
        .forEach((p) => { (groups[p.t] = groups[p.t] || []).push(p); });
      list.innerHTML = Object.keys(types).filter((t) => groups[t]).map((t) => `<h4>${esc(types[t].name)} (${groups[t].length})</h4>` +
        groups[t].slice(0, 300).map((p) => `<button type="button" data-poi="${esc(p.id)}" style="--c:${types[t].color}"><span class="dot"></span><span>${esc(p.n)}</span>${m.floors.length > 1 ? `<small>${esc(m.floorNames[p.f])}</small>` : ""}</button>`).join("")).join("") ||
        `<div class="empty">No points match.</div>`;
    }
    filter.addEventListener("input", drawList);
    list.addEventListener("click", (e) => { const b = e.target.closest("[data-poi]"); if (b) mv.focus(b.dataset.poi); });
    drawList();

    // Facts: exits, monsters, containers.
    const exits = {};
    m.pois.filter((p) => p.t === "exit").forEach((p) => { exits[p.map] = exits[p.map] || p; });
    const mons = {};
    m.pois.filter((p) => p.t === "monster" && monsters[p.mon]).forEach((p) => { mons[p.mon] = (mons[p.mon] || 0) + 1; });
    const chests = {};
    m.pois.filter((p) => p.t === "chest" || p.t === "loot").forEach((p) => { const k = p.lvl ? "Level " + p.lvl : "Gold / search"; chests[k] = (chests[k] || 0) + 1; });
    document.getElementById("map-facts").innerHTML =
      (m.shot ? `<div class="card section arrival"><h3>On arrival</h3>${shotHtml(m.shot, m.name)}</div>` : "") +
      (() => {
        const here = [...new Set(m.pois.flatMap((p) => p.quests || []))].map((k) => quests[k]).filter(Boolean);
        return here.length ? `<div class="card section"><h3>Quests here</h3><div class="chips">${here.map((q) => `<a class="chip" href="#quest-${q.id}">${esc(q.title)}${q.promo ? ` <span class="muted">${esc(q.promo)}</span>` : ""}</a>`).join("")}</div></div>` : "";
      })() +
      `<div class="card section"><h3>Exits</h3>${Object.keys(exits).length ? `<div class="chips">${Object.entries(exits).map(([to, p]) => `<a class="chip" href="#map-${to}">${esc(mapName(to))}${p.d ? " · " + esc(p.d) : ""}</a>`).join("")}</div>` : `<span class="muted">None</span>`}</div>` +
      `<div class="card section"><h3>Monsters placed</h3>${Object.keys(mons).length ? `<div class="chips">${Object.entries(mons).sort((a, b) => monsters[a[0]].level - monsters[b[0]].level).map(([mid, n]) => `<a class="chip" href="#monster-${mid}">${n}× ${esc(monsters[mid].name)} <span class="muted">L${monsters[mid].level}</span></a>`).join("")}</div>` : `<span class="muted">None</span>`}</div>` +
      `<div class="card section"><h3>Treasure</h3>${Object.keys(chests).length ? `<div class="chips">${Object.entries(chests).sort().map(([k, n]) => `<span class="chip">${n}× ${esc(k)}</span>`).join("")}</div>` : `<span class="muted">None</span>`}</div>`;
  }

  // Travel -------------------------------------------------------------------------------------------------------

  const VESSEL_COLORS = ["#0e7490", "#b45309", "#7c3aed", "#be123c", "#15803d", "#1d4ed8", "#a16207", "#c026d3", "#0f766e", "#9f1239"];
  const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

  function travelGraph() {
    const edges = {};
    const add = (a, b, e) => { (edges[a] = edges[a] || []).push(Object.assign({ to: b }, e)); };
    G.travel.links.forEach((l) => add(l.from, l.to, { kind: "walk", days: l.days }));
    G.travel.schedules.forEach((s) => { if (s.from) add(s.from, s.to, { kind: "ship", days: s.days, s }); });
    return edges;
  }
  function planRoute(from, to) {
    const edges = travelGraph();
    const dist = { [from]: [0, 0] }, prev = {};
    const queue = [from];
    const done = new Set();
    while (queue.length) {
      queue.sort((a, b) => dist[a][0] - dist[b][0] || dist[a][1] - dist[b][1]);
      const cur = queue.shift();
      if (done.has(cur)) continue;
      done.add(cur);
      if (cur === to) break;
      (edges[cur] || []).forEach((e) => {
        const nd = [dist[cur][0] + e.days, dist[cur][1] + 1];
        const old = dist[e.to];
        if (!old || nd[0] < old[0] || (nd[0] === old[0] && nd[1] < old[1])) {
          dist[e.to] = nd; prev[e.to] = { from: cur, e };
          queue.push(e.to);
        }
      });
    }
    if (!dist[to]) return null;
    const steps = [];
    for (let at = to; at !== from; at = prev[at].from) steps.unshift(prev[at]);
    return { days: dist[to][0], steps };
  }

  function pageTravel() {
    const vessels = [...new Set(G.travel.schedules.map((s) => s.vessel))];
    const vColor = Object.fromEntries(vessels.map((v, i) => [v, VESSEL_COLORS[i % VESSEL_COLORS.length]]));
    const options = G.regions.map((r) => `<optgroup label="${esc(r.name)}">${r.maps.filter((m) => maps[m]).map((m) => `<option value="${m}">${esc(mapName(m))}</option>`).join("")}</optgroup>`).join("");
    main.innerHTML = pageHead("Travel", "", "How the regions of Chedian connect: walking borders with their travel days, and the ships and coaches by weekday. The world map is a schematic; each tile is the region's own map.") +
      `<div class="section"><div class="world-wrap world" id="world"></div><div class="vessels" id="vessels"></div></div>
       <div class="card planner"><h2>Route planner</h2>
         <div class="toolbar"><label class="muted" for="from">From</label><select class="field" id="from">${options}</select>
         <label class="muted" for="to">To</label><select class="field" id="to">${options}</select></div>
         <div id="route"></div></div>
       <div class="section"><h2>Ships and coaches</h2><div id="sched"></div></div>
       <div class="section"><h2>Walking borders</h2><div id="borders"></div></div>`;
    const from = document.getElementById("from"), to = document.getElementById("to");
    from.value = store.get("from", "sturmfordcity"); to.value = store.get("to", "thronheimcity");
    if (!from.value) from.value = "sturmfordcity";
    if (!to.value) to.value = "thronheimcity";
    let activeVessel = null;
    let routeRegions = [];

    function drawWorld() {
      const CW = 215, CH = 175, PAD = 30, TW = 150, TH = 100;
      const xs = G.regions.map((r) => r.pos[0]), ys = G.regions.map((r) => r.pos[1]);
      const W = (Math.max(...xs) + 1) * CW + PAD * 2, H = (Math.max(...ys) + 1) * CH + PAD * 2;
      const centre = (r) => [PAD + r.pos[0] * CW + TW / 2 + 10, PAD + r.pos[1] * CH + TH / 2 + 10];
      const pairs = {};
      const addPair = (a, b, days, via) => {
        const k = [a.id, b.id].sort().join("|");
        if (!pairs[k] || (days && days < pairs[k].days) || !pairs[k].days) pairs[k] = { a, b, days: Math.max(pairs[k] ? pairs[k].days : 0, days), via };
      };
      // A passage (the Connecting Tunnels) joins the regions on either side; it is the link, not a place on the map.
      const passageEnds = {};
      G.travel.links.forEach((l) => {
        const a = regionOfMap[l.from], b = regionOfMap[l.to];
        if (!a || !b || a === b) return;
        if (a.passage || b.passage) {
          const p = a.passage ? a : b, other = a.passage ? b : a;
          // days into the passage from a region, and out of it into a region
          const ends = (passageEnds[p.id] = passageEnds[p.id] || { p, regions: {} });
          const end = (ends.regions[other.id] = ends.regions[other.id] || { r: other, into: 0, out: 0 });
          if (b.passage) end.into = Math.max(end.into, l.days); else end.out = Math.max(end.out, l.days);
          return;
        }
        addPair(a, b, l.days);
      });
      Object.values(passageEnds).forEach(({ p, regions: ends }) => {
        const list = Object.values(ends);
        for (let i = 0; i < list.length; i++) for (let j = i + 1; j < list.length; j++) {
          const days = Math.min(list[i].into + list[j].out, list[j].into + list[i].out);
          addPair(list[i].r, list[j].r, days, p);
        }
      });
      const boats = {};
      G.travel.schedules.forEach((s) => {
        const a = regionOfMap[s.from], b = regionOfMap[s.to];
        if (!a || !b || a === b) return;
        const k = s.vessel + "|" + [a.id, b.id].sort().join("|");
        boats[k] = { a, b, v: s.vessel };
      });
      let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Schematic world map of Chedian"><rect class="sea" width="${W}" height="${H}" rx="10"></rect>`;
      Object.values(boats).forEach((b, i) => {
        if (activeVessel && b.v !== activeVessel) return;
        const [x1, y1] = centre(b.a), [x2, y2] = centre(b.b);
        const bend = ((i % 5) - 2) * 14;
        const mx = (x1 + x2) / 2 - (y2 - y1) * bend / 300, my = (y1 + y2) / 2 + (x2 - x1) * bend / 300;
        svg += `<path class="boat-link ${activeVessel ? "hi" : "faint"}" d="M${x1},${y1} Q${mx},${my} ${x2},${y2}" stroke="${vColor[b.v]}"></path>`;
      });
      Object.values(pairs).forEach((p) => {
        const [x1, y1] = centre(p.a), [x2, y2] = centre(p.b);
        svg += `<line class="land-link" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"></line>`;
      });
      for (let i = 0; i + 1 < routeRegions.length; i++) {
        const [x1, y1] = centre(routeRegions[i]), [x2, y2] = centre(routeRegions[i + 1]);
        svg += `<line class="route-link" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}"></line>`;
      }
      G.regions.filter((r) => !r.passage).forEach((r) => {
        const x = PAD + r.pos[0] * CW + 10, y = PAD + r.pos[1] * CH + 10;
        const hub = maps[r.hub];
        const hi = routeRegions.includes(r);
        svg += `<a href="#map-${r.hub}" class="node ${hi ? "hi" : ""}"><rect class="frame" x="${x - 4}" y="${y - 4}" width="${TW + 8}" height="${TH + 30}" rx="8"></rect>` +
          (hub ? `<image href="${hub.thumb}" x="${x}" y="${y}" width="${TW}" height="${TH}" preserveAspectRatio="xMidYMid slice"></image>` : "") +
          `<text x="${x + 2}" y="${y + TH + 18}">${esc(r.name)}</text></a>`;
      });
      Object.values(pairs).forEach((p) => {
        if (!p.days && !p.via) return;
        const [x1, y1] = centre(p.a), [x2, y2] = centre(p.b);
        const label = (p.via ? `via ${p.via.name}` : "") + (p.via && p.days ? ", " : "") + (p.days ? `${p.days} d` : "");
        const inner = p.via ? `<a href="#map-${p.via.hub}">${esc(label)}</a>` : esc(label);
        svg += `<text class="days" x="${(x1 + x2) / 2}" y="${(y1 + y2) / 2}" text-anchor="middle">${inner}</text>`;
      });
      document.getElementById("world").innerHTML = svg + "</svg>";
      document.getElementById("vessels").innerHTML = `<span class="muted">Ships and coaches:</span>` + vessels.map((v) => `<button type="button" class="vessel-chip ${activeVessel === v ? "active" : ""}" data-vessel="${esc(v)}" style="--c:${vColor[v]}"><span class="dot"></span>${esc(v)}</button>`).join("") +
        `<span class="muted">Solid lines: walking borders (days).</span>`;
    }
    document.getElementById("vessels").addEventListener("click", (e) => {
      const b = e.target.closest("[data-vessel]");
      if (!b) return;
      activeVessel = activeVessel === b.dataset.vessel ? null : b.dataset.vessel;
      drawWorld(); drawSchedule();
    });

    function drawRoute() {
      store.set("from", from.value); store.set("to", to.value);
      const el = document.getElementById("route");
      if (from.value === to.value) { el.innerHTML = `<p class="muted">Pick two different maps.</p>`; routeRegions = []; drawWorld(); return; }
      const r = planRoute(from.value, to.value);
      if (!r) { el.innerHTML = `<p>No route found from the exits and schedules.</p>`; routeRegions = []; drawWorld(); return; }
      routeRegions = [];
      [from.value].concat(r.steps.map((s) => s.e.to)).forEach((m) => { const reg = regionOfMap[m]; if (reg && !reg.passage && routeRegions[routeRegions.length - 1] !== reg) routeRegions.push(reg); });
      el.innerHTML = `<p><b>${r.days} day${r.days === 1 ? "" : "s"}</b> of travel, ${r.steps.length} step${r.steps.length === 1 ? "" : "s"}.</p><ol class="steps">${r.steps.map((s) => {
        if (s.e.kind === "ship") {
          const sc = s.e.s;
          return `<li>Take <b>${esc(sc.vessel)}</b> (${esc(sc.kind)}) from ${mapLink(s.from, sc.at[0] && sc.at[0].poi)} to ${mapLink(s.e.to)}: ${esc(sc.day)}s, ${sc.days} d, ${sc.price} gold${sc.gated ? ` <span class="chip gated">after a quest</span>` : ""}</li>`;
        }
        const exit = maps[s.from].pois.find((p) => p.t === "exit" && p.map === s.e.to);
        return `<li>Walk from ${mapLink(s.from, exit && exit.id)} to ${mapLink(s.e.to)}${s.e.days ? `: ${s.e.days} d` : ""}</li>`;
      }).join("")}</ol>`;
      drawWorld();
    }
    from.addEventListener("change", drawRoute);
    to.addEventListener("change", drawRoute);

    function drawSchedule() {
      const el = document.getElementById("sched");
      const list = G.travel.schedules.filter((s) => !activeVessel || s.vessel === activeVessel);
      const byVessel = {};
      list.forEach((s) => { (byVessel[s.vessel] = byVessel[s.vessel] || []).push(s); });
      el.innerHTML = Object.entries(byVessel).map(([v, ss]) => {
        const at = ss[0].at[0];
        return `<div class="card section"><h3><span class="chip" style="--c:${vColor[v]}"><span class="dot"></span>${esc(v)}</span> <span class="muted">${esc(ss[0].kind)} at ${at ? mapLink(at.map, at.poi) : "?"}</span> ${at ? showBtn(at.map, at.poi, "Show") : ""}</h3>
          <div class="week">${DAYS.map((d) => { const s = ss.filter((x) => x.day === d); return `<div><b>${d.slice(0, 3)}</b>${s.length ? s.map((x) => `${mapLink(x.to)} <span class="muted num">${x.days} d, ${x.price} g</span>${x.gated ? ` <span class="chip gated" title="Runs after a quest">quest</span>` : ""}`).join("<br>") : `<span class="muted">–</span>`}</div>`; }).join("")}</div></div>`;
      }).join("");
    }
    const borders = {};
    G.travel.links.forEach((l) => {
      const a = maps[l.from], b = maps[l.to];
      if (!a || !b || a.kind === "dungeon" || b.kind === "dungeon") return;
      const k = [l.from, l.to].sort().join("|");
      borders[k] = borders[k] && borders[k].days >= l.days ? borders[k] : l;
    });
    table(document.getElementById("borders"), {
      rows: () => Object.values(borders),
      sort: "from",
      columns: [
        { key: "from", label: "From", render: (l) => mapLink(l.from), sort: (l) => mapName(l.from) },
        { key: "to", label: "To", render: (l) => mapLink(l.to), sort: (l) => mapName(l.to) },
        { key: "days", label: "Days", num: true, render: (l) => l.days || "–" },
      ],
    });
    drawSchedule();
    drawRoute();
  }

  // Teachers -----------------------------------------------------------------------------------------------------

  function pageTeachers() {
    const skills = [...new Set(G.teachers.map((t) => t.skill))].sort();
    const racialMasters = [...new Set(G.teachers.filter((t) => t.racial && t.mastery === "Grandmaster").map((t) => `${t.name} in ${t.region}`))];
    const racialLead = racialMasters.length ? ` The racial abilities (Dark Elf, Vampire and Dragon) are taught by every training hall's keeper up to Master, and up to Grandmaster by ${esc(racialMasters.join(" and "))}: each member learns the ability they have, as far as their race and class allow.` : "";
    main.innerHTML = pageHead("Teachers", "", "MM9 trains its skills one by one: a lesson in an MM9 skill teaches the OpenYAMM skills listed under it. \"Learn\" is the first lesson, sold by shops, taverns, temples and training halls." + racialLead) +
      `<div class="toolbar"><input class="field" id="tf" type="search" placeholder="Filter by teacher, skill or region" aria-label="Filter teachers">
       <select class="field" id="ts" aria-label="Skill"><option value="">All skills</option>${skills.map((s) => `<option>${esc(s)}</option>`).join("")}</select>
       <select class="field" id="tm" aria-label="Mastery"><option value="">All masteries</option>${Object.keys(MASTERY_ORDER).map((m) => `<option>${m}</option>`).join("")}</select></div><div id="tt"></div>`;
    const f = document.getElementById("tf"), s = document.getElementById("ts"), mm = document.getElementById("tm");
    if (pendingFilter) { f.value = pendingFilter; pendingFilter = null; }
    const t = table(document.getElementById("tt"), {
      rows: () => {
        const q = f.value.trim().toLowerCase();
        return G.teachers.filter((x) => (!s.value || x.skill === s.value) && (!mm.value || x.mastery === mm.value) &&
          (!q || `${x.name} ${x.skill} ${x.skills} ${x.region}`.toLowerCase().includes(q)));
      },
      sort: "skill",
      columns: [
        { key: "skill", label: "Skill", render: (x) => `<b>${esc(x.skill)}</b>${x.skills !== x.skill ? `<br><span class="muted">${esc(x.skills)}</span>` : ""}`, sort: (x) => x.skill + (MASTERY_ORDER[x.mastery] || 0) },
        { key: "mastery", label: "Mastery", render: (x) => `<span class="mastery-${esc(x.mastery)}">${esc(x.mastery)}</span>`, sort: (x) => MASTERY_ORDER[x.mastery] || 0 },
        { key: "name", label: "Teacher" },
        { key: "region", label: "Region" },
        { key: "rank", label: "Needs", render: (x) => (x.rank ? `skill ${x.rank}` : "–") + (x.gold ? `, ${fmt(x.gold)} g` : "") + (x.gated ? ` <span class="chip gated">quest</span>` : "") + (x.racial ? ` <span class="chip">own ability</span>` : ""), sort: (x) => x.rank },
        { key: "at", label: "Where", sortable: false, cls: "nowrap", render: (x) => atLinks(x.at) },
      ],
    });
    [f, s, mm].forEach((el) => el.addEventListener("input", t.draw));
  }

  // Shops ----------------------------------------------------------------------------------------------------------

  function pageShops() {
    const vendorById = Object.fromEntries(G.vendors.map((v) => [v.id, v]));
    const BOOK_ORDER = { Normal: 0, Expert: 1, Master: 2, Grandmaster: 3 };
    const treasureText = (v) => (v.treasure.length ? `${v.treasure[0]} <span class="muted">special ${v.treasure[1]}</span>` : `<span class="muted">set list</span>`);
    const tiersText = (t) => (t.length ? (t[0] === t[1] ? `${t[0]}` : `${t[0]}–${t[1]}`) : "–");
    const types = [...new Set(G.vendors.map((v) => v.type))].sort();
    const schools = [...new Set(G.spellbooks.map((b) => b.school))];
    main.innerHTML = pageHead("Shops", "", "Weapon, armour, general and apothecary shops stock by their town's treasure level, as MM6–MM8 shops do: the standard shelf at the town's level, the special shelf one level higher, which decides the item tiers (1–6) and how many items carry enchantments. Spellbook shops and libraries sell set lists. A shop shows one of its stock lists each time it restocks, in turn. Prices are the item's value times the shop's multiplier, before the Merchant skill.") +
      `<h2 class="shop-section">Weapons and armour by town</h2><p class="muted">The weapon and armour shops of each town, from the earliest chapter's to the last.</p><div id="sw"></div>
       <h2 class="shop-section" id="spell-tiers">Spells by school and mastery</h2><p class="muted">Where each school's spells of each mastery are sold, shop by shop. Type a mastery and a school, such as <i>master water</i>, or a spell, a shop or a town; open a shop for its map.</p>
       <div class="toolbar"><input class="field" id="tf" type="search" placeholder="Master water, Body, Thjorgard…" aria-label="Filter spell masteries"></div><div id="tiers" class="spell-tiers"></div>
       <h2 class="shop-section">Spellbooks</h2><p class="muted">Every spellbook and where it is sold: on every restock, or on some of the shop's stock lists.</p>
       <div class="toolbar"><input class="field" id="bf" type="search" placeholder="Filter by spell or shop" aria-label="Filter spellbooks">
       <select class="field" id="bs" aria-label="School"><option value="">All schools</option>${schools.map((x) => `<option>${esc(x)}</option>`).join("")}</select>
       <select class="field" id="bm" aria-label="Mastery"><option value="">All masteries</option>${Object.keys(BOOK_ORDER).map((x) => `<option>${x}</option>`).join("")}</select></div><div id="sb"></div>
       <h2 class="shop-section">All shops</h2><div class="toolbar"><input class="field" id="sf" type="search" placeholder="Filter shops" aria-label="Filter shops">
       <select class="field" id="sy" aria-label="Shop type"><option value="">All types</option>${types.map((x) => `<option>${esc(x)}</option>`).join("")}</select></div><div id="st"></div>
       <h2 class="shop-section">Temples, taverns, banks and training</h2><div id="sv"></div>`;

    // Weapons and armour: one row per town, its weapon and armour shops together.
    const towns = new Map();
    G.vendors.filter((v) => v.type === "Weapon" || v.type === "Armor").forEach((v) => {
      if (!towns.has(v.region)) towns.set(v.region, { region: v.region, shops: [] });
      towns.get(v.region).shops.push(v);
    });
    const townRows = [...towns.values()].map((t) => {
      const tiers = t.shops.flatMap((v) => v.tiers);
      const prices = t.shops.map((v) => v.price);
      return { ...t, treasure: t.shops[0].treasure, tiers: tiers.length ? [Math.min(...tiers), Math.max(...tiers)] : [],
        enchanted: Math.round(t.shops.reduce((n, v) => n + v.enchanted, 0) / t.shops.length),
        price: [Math.min(...prices), Math.max(...prices)] };
    });
    table(document.getElementById("sw"), {
      rows: () => townRows, sort: "treasure",
      columns: [
        { key: "region", label: "Town", render: (t) => `<b>${esc(t.region)}</b>` },
        { key: "treasure", label: "Treasure level", render: treasureText, sort: (t) => (t.treasure[0] || 0) * 10 + t.price[0] / 100 },
        { key: "tiers", label: "Item tiers", num: true, render: (t) => tiersText(t.tiers), sort: (t) => t.tiers[1] || 0 },
        { key: "enchanted", label: "Enchanted", num: true, render: (t) => `${t.enchanted}%` },
        { key: "price", label: "Prices", num: true, render: (t) => (t.price[0] === t.price[1] ? `×${t.price[0]}` : `×${t.price[0]}–${t.price[1]}`), sort: (t) => t.price[0] },
        { key: "shops", label: "Shops", sortable: false, render: (t) => t.shops.map((v) => `${esc(v.name)} <span class="muted">${v.type === "Armor" ? "armour" : "weapons"}</span> ${v.at[0] ? showBtn(v.at[0].map, v.at[0].poi, "Show") : ""}`).join("<br>") },
      ],
    });

    // Spells by school and mastery: one block per tier ("Master Water Magic"), its shops below it, each opening its map.
    const tiers = [];
    G.spellbooks.forEach((b) => {
      let tier = tiers.find((x) => x.school === b.school && x.mastery === b.mastery);
      if (!tier) tiers.push(tier = { school: b.school, mastery: b.mastery, books: [] });
      tier.books.push(b);
    });
    tiers.sort((a, b) => schools.indexOf(a.school) - schools.indexOf(b.school) || BOOK_ORDER[a.mastery] - BOOK_ORDER[b.mastery]);
    tiers.forEach((tier) => {
      const byShop = new Map();
      tier.books.forEach((b) => b.shops.forEach((sh) => {
        if (!byShop.has(sh.id)) byShop.set(sh.id, []);
        byShop.get(sh.id).push({ book: b, pages: sh.pages, of: sh.of });
      }));
      tier.shops = [...byShop.entries()].map(([id, sold]) => ({ v: vendorById[id], sold }))
        .sort((a, b) => b.sold.length - a.sold.length || a.v.price - b.v.price);
      tier.label = `${tier.mastery} ${tier.school} Magic`;
      tier.words = `${tier.label} ${tier.books.map((b) => b.name).join(" ")} ${tier.shops.map((s) => `${s.v.name} ${s.v.region} ${s.v.at.map((a) => mapName(a.map)).join(" ")}`).join(" ")}`
        .toLowerCase().split(/[^a-z0-9']+/).filter(Boolean);
    });
    const tf = document.getElementById("tf"), tiersEl = document.getElementById("tiers");
    function shopLine(tier, s) {
      const v = s.v;
      const all = s.sold.length === tier.books.length;
      const spells = s.sold.map((x) => `${esc(x.book.name)}${x.pages === x.of ? "" : ` <span class="muted">(${x.pages} of ${x.of} restocks)</span>`}`).join(", ");
      const prices = s.sold.map((x) => Math.round(x.book.value * v.price));
      const price = Math.min(...prices) === Math.max(...prices) ? `${fmt(prices[0])} g` : `${fmt(Math.min(...prices))}–${fmt(Math.max(...prices))} g`;
      const where = [v.region, ...v.at.map((a) => mapName(a.map)).filter((n) => n !== v.region)].concat(v.at.length ? [] : ["not placed"]);
      return `<details class="tier-shop" data-vendor="${v.id}"><summary><span class="ts-name"><b>${esc(v.name)}</b> <span class="muted">${where.map(esc).join(" · ")}</span></span>
          <span class="ts-what">${all ? `all ${tier.books.length} spells` : `${s.sold.length} of ${tier.books.length}`}: ${spells} <span class="muted">· ${price}</span></span></summary>
          <div class="tier-maps">${v.at.map((a) => `<div class="tier-map" data-map="${esc(a.map)}" data-poi="${esc(a.poi)}"></div>`).join("") || `<p class="muted">This shop is not placed on a map.</p>`}</div></details>`;
    }
    function drawTiers() {
      const words = tf.value.trim().toLowerCase().split(/[^a-z0-9']+/).filter(Boolean);
      const shown = tiers.filter((tier) => words.every((w) => tier.words.some((x) => x.startsWith(w))));
      tiersEl.innerHTML = shown.length ? shown.map((tier) => `<section class="spell-tier"><h3><span class="mastery-${tier.mastery === "Normal" ? "Learn" : esc(tier.mastery)}">${esc(tier.mastery)}</span> ${esc(tier.school)} Magic
          <span class="muted tier-spells">${tier.books.map((b) => esc(b.name)).join(", ")}</span></h3>
          ${tier.shops.length ? tier.shops.map((s) => shopLine(tier, s)).join("") : `<p class="muted">Not sold in any shop.</p>`}</section>`).join("")
        : `<p class="muted">No school and mastery matches.</p>`;
    }
    tiersEl.addEventListener("toggle", (e) => {
      const d = e.target;
      if (!d.open || d.dataset.mounted) return;
      d.dataset.mounted = "1";
      d.querySelectorAll(".tier-map").forEach((el) => {
        const m = maps[el.dataset.map];
        if (m) new MapView(el, m, { compact: true, ids: [el.dataset.poi], focus: el.dataset.poi });
      });
    }, true);
    tf.addEventListener("input", drawTiers);
    drawTiers();

    // Spellbooks: one row per spell.
    const bf = document.getElementById("bf"), bs = document.getElementById("bs"), bm = document.getElementById("bm");
    const soldAt = (b) => b.shops.slice().sort((x, y) => y.pages / y.of - x.pages / x.of || vendorById[x.id].price - vendorById[y.id].price).map((sh) => {
      const v = vendorById[sh.id];
      const when = sh.pages === sh.of ? "every restock" : `${sh.pages} of ${sh.of} restocks`;
      return `${esc(v.name)}, ${esc(v.region)} <span class="muted">${when}, ${fmt(Math.round(b.value * v.price))} g</span> ${v.at[0] ? showBtn(v.at[0].map, v.at[0].poi, "Show") : ""}`;
    }).join("<br>") || `<span class="muted">not sold</span>`;
    const bt = table(document.getElementById("sb"), {
      rows: () => {
        const q = bf.value.trim().toLowerCase();
        return G.spellbooks.filter((b) => (!bs.value || b.school === bs.value) && (!bm.value || b.mastery === bm.value) &&
          (!q || `${b.name} ${b.school} ${b.shops.map((sh) => vendorById[sh.id].name + " " + vendorById[sh.id].region).join(" ")}`.toLowerCase().includes(q)));
      },
      sort: "spell",
      columns: [
        { key: "spell", label: "Spell", render: (b) => `<b>${esc(b.name)}</b>`, sort: (b) => b.spell },
        { key: "school", label: "School", sort: (b) => b.spell },
        { key: "mastery", label: "Mastery", render: (b) => `<span class="mastery-${b.mastery === "Normal" ? "Learn" : esc(b.mastery)}">${esc(b.mastery)}</span>`, sort: (b) => BOOK_ORDER[b.mastery] * 100 + b.spell },
        { key: "value", label: "Value", num: true, render: (b) => `${fmt(b.value)} g` },
        { key: "shops", label: "Sold at (price before Merchant)", sortable: false, render: soldAt },
      ],
    });
    [bf, bs, bm].forEach((el) => el.addEventListener("input", bt.draw));

    // All shops.
    const f = document.getElementById("sf"), sy = document.getElementById("sy");
    const match = (x) => { const q = f.value.trim().toLowerCase(); return !q || JSON.stringify(x).toLowerCase().includes(q); };
    const st = table(document.getElementById("st"), {
      rows: () => G.vendors.filter((v) => (!sy.value || v.type === sy.value) && match(v)), sort: "region",
      columns: [
        { key: "name", label: "Shop", render: (v) => `<b>${esc(v.name)}</b><br><span class="muted">${esc(v.sells)}</span>` },
        { key: "type", label: "Type" },
        { key: "region", label: "Region" },
        { key: "treasure", label: "Treasure level", render: treasureText, sort: (v) => v.treasure[0] || 0 },
        { key: "tiers", label: "Item tiers", num: true, render: (v) => tiersText(v.tiers), sort: (v) => v.tiers[1] || 0 },
        { key: "enchanted", label: "Enchanted", num: true, render: (v) => (v.treasure.length ? `${v.enchanted}%` : "–"), sort: (v) => v.enchanted },
        { key: "price", label: "Prices", num: true, render: (v) => `×${v.price}` },
        { key: "restock", label: "Restock", num: true, render: (v) => `${v.restock} d <span class="muted">${v.pages} lists of ${v.perPage}</span>`, sort: (v) => v.restock },
        { key: "at", label: "Where", sortable: false, cls: "nowrap", render: (v) => atLinks(v.at, true) },
      ],
    });
    const sv = table(document.getElementById("sv"), {
      rows: () => G.services.filter(match), sort: "region",
      columns: [
        { key: "name", label: "Place", render: (v) => `<b>${esc(v.name)}</b>` },
        { key: "type", label: "Type" },
        { key: "region", label: "Region" },
        { key: "trainMax", label: "Trains to", num: true, render: (v) => v.trainMax || "–" },
        { key: "learn", label: "Teaches (Learn)", sortable: false, render: (v) => esc(v.learn.join(", ")) || "–" },
        { key: "at", label: "Where", sortable: false, cls: "nowrap", render: (v) => atLinks(v.at, true) },
      ],
    });
    f.addEventListener("input", () => { st.draw(); sv.draw(); });
    sy.addEventListener("input", st.draw);
  }

  // Bestiary -------------------------------------------------------------------------------------------------------

  function treasureText(t) {
    if (!t) return "–";
    if (t.raw) return esc(t.raw);
    const parts = [];
    if (t.gold) parts.push(`${t.gold} gold`);
    if (t.level) parts.push(`${t.chance}% L${t.level} ${t.kind === "Any" ? "item" : t.kind.toLowerCase()}`);
    return parts.join(", ") || "–";
  }
  function monsterDetail(m) {
    const attacks = m.attacks.map((a, i) => `${i ? "Attack 2" : "Attack 1"}: ${esc(a.type)} ${esc(a.dmg)}${a.missile ? " (" + esc(a.missile) + ")" : ""}${i && a.chance ? `, ${a.chance}%` : ""}`);
    const spells = m.spells.map((s) => `${esc(s.spell)}, ${s.chance}%`);
    const pic = m.img ? `<a class="shot portrait" href="${m.img}" target="_blank" rel="noopener"><img src="${m.img}" alt="${esc(m.name)}" loading="lazy"></a>` : "";
    return `<div class="monster-detail">${pic}<div class="section"><dl class="kv">
      <dt>Attacks</dt><dd>${attacks.join("<br>") || "–"}</dd>
      <dt>Spells</dt><dd>${spells.join("<br>") || "–"}</dd>
      <dt>Movement</dt><dd>${esc(m.move)}${m.fly ? ", flies" : ""}; AI ${esc(m.ai)}; speed ${m.speed}; recovery ${m.recovery}</dd>
      <dt>Loot</dt><dd>${treasureText(m.treasure)}</dd>
      ${m.special ? `<dt>Special</dt><dd>${esc(m.special)}</dd>` : ""}
      <dt>Found in</dt><dd>${m.maps.map((x) => `${mapLink(x.map)} ×${x.count}`).join(", ")}</dd></dl>
      <div class="resist">${Object.entries(m.resist).map(([k, v]) => `<span>${k} <b>${esc(v || "0")}</b></span>`).join("")}</div></div></div>`;
  }
  function pageBestiary(focusId) {
    main.innerHTML = pageHead("Bestiary", "", "Monsters placed on the MM9 maps, by family, weakest to strongest; A, B and C are a family's three tiers. Click a row for its picture, attacks, spells, resistances, loot and where it lives.") +
      `<div class="toolbar"><input class="field" id="bf" type="search" placeholder="Filter by name or map" aria-label="Filter monsters"></div><div id="bt"></div>`;
    const f = document.getElementById("bf");
    const t = table(document.getElementById("bt"), {
      rows: () => {
        const q = f.value.trim().toLowerCase();
        return G.monsters.filter((m) => !q || (m.name + " " + m.family + " " + m.maps.map((x) => mapName(x.map)).join(" ")).toLowerCase().includes(q));
      },
      rowKey: (m) => m.id,
      sort: "level",
      group: (m) => m.family || "",
      groupOrder: (k, rows) => (k ? Math.min(...rows.map((m) => m.level)) : 100000),
      groupLabel: (k, rows) => k
        ? `${esc(k)} <span class="muted">levels ${Math.min(...rows.map((m) => m.level))}–${Math.max(...rows.map((m) => m.level))}</span>`
        : "Unique <span class=\"muted\">named and one-of-a-kind</span>",
      columns: [
        { key: "name", label: "Monster", render: (m) => `${m.tier ? `<span class="tier">${esc(m.tier)}</span> ` : ""}<b>${esc(m.name)}</b>${m.img ? ` <span class="muted" title="Has a picture">▸</span>` : ""}` },
        { key: "level", label: "Lvl", num: true, sort: (m) => m.level + (m.tier ? "ABC".indexOf(m.tier) / 10 : 0) },
        { key: "hp", label: "HP", num: true },
        { key: "ac", label: "AC", num: true },
        { key: "xp", label: "XP", num: true, render: (m) => fmt(m.xp) },
        { key: "attacks", label: "Attack", sortable: false, render: (m) => m.attacks[0] ? `${esc(m.attacks[0].type)} ${esc(m.attacks[0].dmg)}` : "–" },
        { key: "treasure", label: "Loot", sortable: false, render: (m) => treasureText(m.treasure) },
        { key: "maps", label: "Maps", num: true, render: (m) => m.maps.length, sort: (m) => m.maps.length },
      ],
      detail: monsterDetail,
    });
    f.addEventListener("input", t.draw);
    if (focusId && monsters[focusId]) {
      t.open(focusId);
      const row = main.querySelector(`tr[data-key="${focusId}"]`);
      if (row) row.scrollIntoView({ block: "center" });
    }
  }

  // Items ----------------------------------------------------------------------------------------------------------

  function statText(i) {
    if (!i.mod1) return "–";
    if (["weapons"].includes(i.cat) || ["Weapon", "Weapon2", "Weapon1or2", "Missile"].includes(i.equip)) return `${esc(i.mod1)}${i.mod2 ? "+" + esc(i.mod2) : ""}`;
    return `AC ${esc(i.mod1)}${i.mod2 ? "+" + esc(i.mod2) : ""}`;
  }
  function itemTabs(active) {
    return `<div class="tabs">${G.itemCategories.map((c) => `<a href="#items-${c.id}" class="${active === c.id ? "active" : ""}">${esc(c.name)}</a>`).join("")}<a href="#items-setbonus" class="${active === "setbonus" ? "active" : ""}">Set bonuses</a><a href="#items-enchants" class="${active === "enchants" ? "active" : ""}">Enchantments</a></div>`;
  }
  function pageItems(cat, focusId) {
    if (cat === "setbonus") return pageSets();
    if (cat === "enchants") return pageEnchants();
    const c = G.itemCategories.find((x) => x.id === cat);
    if (!c) return pageMissing();
    const notes = {
      artifacts: "Artifacts and relics come only from black chests (treasure level 7); a black chest with none left to find gives gold and a level 6 item.",
      sets: "Wearing the whole set gives the set bonus; see Set bonuses.",
      readables: "Letters, notes and books; most are quest material.",
    };
    main.innerHTML = pageHead(c.name, "Items", notes[cat] || "Tier is the treasure level the item drops at (0: never random).") + itemTabs(cat) +
      `<div class="toolbar"><input class="field" id="if" type="search" placeholder="Filter ${esc(c.name.toLowerCase())}" aria-label="Filter items"></div><div id="it"></div>`;
    const f = document.getElementById("if");
    const equipable = !["quest", "readables", "misc", "books"].includes(cat);
    const columns = [
      { key: "icon", label: "", sortable: false, render: (i) => iconHtml(i) },
      { key: "name", label: "Item", render: (i) => `<b class="rarity-${esc(i.rarity)}">${esc(i.name)}</b>${i.skill ? `<br><span class="muted">${esc(i.skill)}</span>` : ""}` },
    ];
    if (equipable) columns.push({ key: "mod1", label: "Damage / AC", render: statText, sort: (i) => parseInt(i.mod1, 10) || 0 });
    columns.push({ key: "fx", label: "Effects", sortable: false, render: (i) => i.fx.length ? `<span class="fx">${esc(i.fx.join(", "))}</span>` : (i.flags.includes("SkillLearning") ? "Teaches its skill" : "–") });
    if (equipable) columns.push({ key: "tier", label: "Tier", num: true });
    columns.push({ key: "value", label: "Value", num: true, render: (i) => fmt(i.value) });
    const t = table(document.getElementById("it"), {
      rows: () => {
        const q = f.value.trim().toLowerCase();
        return G.items.filter((i) => i.cat === cat && (!q || `${i.name} ${i.skill} ${i.fx.join(" ")} ${i.desc}`.toLowerCase().includes(q)));
      },
      rowKey: (i) => i.id,
      sort: equipable ? "tier" : "name",
      columns,
      detail: (i) => `<div class="section"><p class="desc">${esc(i.desc) || "No description."}</p><dl class="kv">
        ${i.classes ? `<dt>Not usable by</dt><dd>${esc(i.classes.split(",").join(", "))}</dd>` : ""}
        ${i.set ? `<dt>Set</dt><dd><a href="#items-setbonus">${esc(i.set)}</a></dd>` : ""}
        ${i.flags.length ? `<dt>Flags</dt><dd>${esc(i.flags.join(", "))}</dd>` : ""}<dt>Id</dt><dd class="mono">${i.id}</dd></dl></div>`,
    });
    f.addEventListener("input", t.draw);
    if (focusId) t.open(focusId);
  }
  function pageSets() {
    main.innerHTML = pageHead("Set bonuses", "Items", "Each set's own bonus applies while all its pieces are worn, on top of the pieces' own effects.") + itemTabs("setbonus") +
      `<div class="quest-list">${G.sets.map((s) => `<article class="card section"><div class="quest-head"><h3>${esc(s.name)} set</h3><span class="muted">${s.pieces} pieces</span></div>
        <div class="fx">${esc(s.fx.join(", "))}</div>
        <div class="chips">${s.items.map((id) => { const i = items[id]; return `<a class="chip" href="#item-${id}">${iconHtml(i, 28)} ${esc(i.name)}${i.fx.length ? ` <span class="muted">${esc(i.fx.join(", "))}</span>` : ""}</a>`; }).join("")}</div></article>`).join("")}</div>`;
  }
  function pageEnchants() {
    main.innerHTML = pageHead("Enchantments", "Items", "Random enchantments on dropped and sold items: a standard bonus (\"of Might\") on armor and jewelry, or a special one on weapons and armor. Slots list where each can roll.") + itemTabs("enchants") +
      `<h2>Standard bonuses</h2><div id="es"></div><h2>Special bonuses</h2><div id="ep"></div>`;
    table(document.getElementById("es"), {
      rows: () => G.enchants.standard, sort: "stat",
      columns: [{ key: "stat", label: "Stat" }, { key: "suffix", label: "Name" }, { key: "slots", label: "Slots", sortable: false, render: (e) => esc(e.slots.join(", ")) }],
    });
    table(document.getElementById("ep"), {
      rows: () => G.enchants.special, sort: "level",
      columns: [
        { key: "name", label: "Name", render: (e) => `<b>${esc(e.name)}</b>` },
        { key: "bonus", label: "Effect", render: (e) => esc(e.bonus) },
        { key: "level", label: "Level", render: (e) => esc(e.level) },
        { key: "value", label: "Value", num: true, sort: (e) => Number(e.value) || 0 },
        { key: "slots", label: "Slots", sortable: false, render: (e) => esc(e.slots.join(", ")) },
      ],
    });
  }

  // FAQ -----------------------------------------------------------------------------------------------------------

  // [text](#route) links in the hand-written answers; everything else is escaped.
  function faqText(text) {
    return esc(text).replace(/\[([^\]]+)\]\((#[\w-]+)\)/g, (m, label, href) => `<a href="${href}">${label}</a>`);
  }
  // The MM6-MM8 skills MM9 teaches under another skill, where each is learnt and who teaches its masteries.
  function skillLessons() {
    const norm = (s) => s.toLowerCase().replace(/[^a-z]/g, "");
    const VENUES = { Weapon: "weapon shops", Armor: "armour shops", Magic: "magic shops", Library: "libraries", Apothecary: "apothecaries", "General Store": "general stores", Tavern: "taverns", Temple: "temples", Training: "training halls" };
    const rows = new Map();
    G.teachers.filter((x) => !x.racial && x.mastery !== "Learn").forEach((x) => {
      const list = x.skills.split(", ");
      if (list.length < 2) return;
      list.filter((s) => !norm(s).startsWith(norm(x.skill))).forEach((s) => { if (!rows.has(s)) rows.set(s, { skill: s, mm9: x.skill, learn: new Map() }); });
    });
    G.teachers.filter((x) => x.mastery === "Learn" && rows.has(x.skill)).forEach((x) => {
      const learn = rows.get(x.skill).learn;
      const kind = VENUES[x.venue] || (x.venue || "").toLowerCase();
      learn.set(kind, (learn.get(kind) || 0) + 1);
    });
    const body = [...rows.values()].map((r) => `<tr><td><a href="#teachers" data-filter="${esc(r.skill)}"><b>${esc(r.skill)}</b></a></td>
      <td>${r.learn.size ? [...r.learn.entries()].map(([k, n]) => `${esc(k)} <span class="muted">(${n})</span>`).join(", ") : `<span class="muted">no Learn lesson</span>`}</td>
      <td>MM9's ${esc(r.mm9.replace(/(?<=[a-z])(?=[A-Z])/g, " "))} trainers</td></tr>`).join("");
    return `<div class="table-wrap"><table><thead><tr><th>Skill</th><th>Learn at</th><th>Expert to Grandmaster</th></tr></thead><tbody>${body}</tbody></table></div>`;
  }
  function pageFaq() {
    main.innerHTML = pageHead("FAQ", "", "Short answers to common questions, with links to the guide's full pages.") +
      `<div class="faq">${G.faq.map((f) => `<section class="faq-entry" id="faq-${esc(f.id)}"><h2>${esc(f.q)}</h2>
        ${f.answer.map((p) => `<p>${faqText(p)}</p>`).join("")}
        ${f.table === "skill-lessons" ? skillLessons() : ""}
        ${(f.figures || []).length ? `<div class="faq-figures">${f.figures.map((g) => `<figure class="story-figure"><a href="${esc(g.img)}" target="_blank" rel="noopener"><img src="${esc(g.img)}" alt="${esc(g.caption || "")}" loading="lazy"></a>${g.caption ? `<figcaption>${esc(g.caption)}</figcaption>` : ""}</figure>`).join("")}</div>` : ""}
      </section>`).join("")}</div>`;
  }

  function pageMissing() {
    main.innerHTML = pageHead("Not found", "", `Nothing here. <a href="#home">Back to the start</a>.`);
  }

  // ---------------------------------------------------------------------------------------------------------------
  // Search

  const searchIndex = [];
  G.quests.forEach((q) => searchIndex.push({ n: q.title, k: "Quest", h: `#quest-${q.id}` }));
  G.maps.forEach((m) => {
    searchIndex.push({ n: m.name, k: "Map", h: `#map-${m.id}` });
    m.pois.forEach((p) => {
      if (["teacher", "vendor", "quest", "promoter", "service", "transport", "hireling", "npc"].includes(p.t)) {
        searchIndex.push({ n: p.n, k: `${types[p.t].name}, ${m.name}`, h: `#map-${m.id}-${p.id}`, x: p.d || "" });
      }
    });
  });
  G.monsters.forEach((m) => searchIndex.push({ n: m.name, k: `Monster L${m.level}`, h: `#monster-${m.id}` }));
  G.items.forEach((i) => searchIndex.push({ n: i.name, k: "Item", h: `#item-${i.id}` }));
  G.vendors.forEach((v) => searchIndex.push({ n: v.name, k: `${v.type} shop, ${v.region}`, h: v.at[0] ? `#map-${v.at[0].map}-${v.at[0].poi}` : "#shops" }));
  const sInput = document.getElementById("search"), sResults = document.getElementById("search-results");
  let hot = 0;
  function runSearch() {
    const q = sInput.value.trim().toLowerCase();
    if (q.length < 2) { sResults.hidden = true; return; }
    const hits = searchIndex.filter((e) => e.n.toLowerCase().includes(q) || (e.x && e.x.toLowerCase().includes(q)))
      .sort((a, b) => (a.n.toLowerCase().startsWith(q) ? 0 : 1) - (b.n.toLowerCase().startsWith(q) ? 0 : 1)).slice(0, 30);
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
  // Router

  const side = document.getElementById("side"), menuBtn = document.getElementById("menu-btn");
  menuBtn.addEventListener("click", () => {
    const open = !side.classList.contains("open");
    side.classList.toggle("open", open);
    menuBtn.setAttribute("aria-expanded", open);
  });
  side.addEventListener("click", (e) => { if (e.target.closest("a.nav-link")) { side.classList.remove("open"); menuBtn.setAttribute("aria-expanded", "false"); } });

  let lastRoute = null;
  function route() {
    const r = decodeURIComponent(location.hash.replace(/^#/, "")) || "home";
    if (dialog.open) dialog.close();
    // Selecting a marker rewrites the hash of the map being shown; do not rebuild the page for that.
    if (lastRoute && lastRoute.startsWith("map-") && r.startsWith("map-") && r.split("-")[1] === lastRoute.split("-")[1] && document.getElementById("mv")) {
      lastRoute = r;
      return;
    }
    lastRoute = r;
    window.scrollTo(0, 0);
    renderNav(r);
    const [head, ...rest] = r.split("-");
    const arg = rest.join("-");
    if (head === "home") pageHome();
    else if (head === "quests") pageQuests(["main", "side", "promotion"].includes(arg) ? arg : "main");
    else if (head === "quest") pageQuest(arg);
    else if (head === "maps") pageMaps();
    else if (head === "map") pageMap(rest[0], rest[1]);
    else if (head === "travel") pageTravel();
    else if (head === "teachers") pageTeachers();
    else if (head === "shops") pageShops();
    else if (head === "faq") pageFaq();
    else if (head === "bestiary") pageBestiary();
    else if (head === "monster") pageBestiary(Number(arg));
    else if (head === "items") pageItems(arg || "weapons");
    else if (head === "item") { const i = items[Number(arg)]; if (i) { renderNav("items-" + i.cat); pageItems(i.cat, i.id); } else pageMissing(); }
    else pageMissing();
    document.title = (main.querySelector("h1") ? main.querySelector("h1").textContent + " · " : "") + "MM9 Chedian Guide";
  }
  window.addEventListener("hashchange", route);
  route();
})();
