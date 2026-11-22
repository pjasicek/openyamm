#!/usr/bin/env python3
"""Render the MU-6 dungeon graphs (*.graph.yml beside this script) to SVG.

Usage: python3 render_graphs.py [key ...]

Each graph file names its rooms (`spaces`), their floor and a review grid cell (`at: [column, row]`, the row
counted inside the floor's band), the connections (`links`), the states that open them (`states`) and the exits.
The picture: one horizontal band per floor (highest on top), rooms as boxes coloured by kind, connections drawn
in one style per kind, dashed state lines from the room that holds a key, lever or boss to the connection it
opens, and a legend. Rooms without `at` are placed in critical-path order on their floor.

Standard library plus PyYAML. The script prints every overlap it finds; it should print none.
"""

import math
import pathlib
import sys
from xml.sax.saxutils import escape

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("render_graphs.py needs PyYAML (python3 -m pip install pyyaml)")

HERE = pathlib.Path(__file__).resolve().parent

KIND_FILL = {
    "room": "#f3e6c8",
    "hall": "#e9d29a",
    "stair": "#cfe8c9",
    "corridor": "#e2e2e2",
    "cave": "#dcc7b0",
    "shaft": "#c9def0",
}
KIND_NAME = {
    "room": "room",
    "hall": "hall",
    "stair": "stair or lift core",
    "corridor": "corridor, ledge, bridge",
    "cave": "cave",
    "shaft": "shaft",
}

EDGE = {
    "open": {"stroke": "#7a7a7a", "width": 2.0, "dash": None, "arrow": False},
    "door": {"stroke": "#2f2f2f", "width": 2.4, "dash": None, "arrow": False},
    "locked": {"stroke": "#b3261e", "width": 2.8, "dash": None, "arrow": False},
    "secret": {"stroke": "#4a4a4a", "width": 2.0, "dash": "1.5 4.5", "arrow": False},
    "one_way": {"stroke": "#2f2f2f", "width": 2.2, "dash": None, "arrow": True},
    "lift": {"stroke": "#1f6fb2", "width": 5.0, "dash": None, "arrow": False},
    "stair": {"stroke": "#2e7d32", "width": 2.6, "dash": "10 3", "arrow": False},
    "teleport": {"stroke": "#7b3fa0", "width": 2.4, "dash": "9 3 2 3", "arrow": True},
    "drop": {"stroke": "#8d5a2b", "width": 2.4, "dash": "6 4", "arrow": True},
}
EDGE_NAME = {
    "open": "open way",
    "door": "door",
    "locked": "locked door (key named)",
    "secret": "secret or illusory",
    "one_way": "one-way",
    "lift": "lift or moving cage",
    "stair": "stairs or ladder",
    "teleport": "teleport or throw",
    "drop": "drop (one-way down)",
}
STATE_COLOUR = {
    "lever": "#e07b00",
    "map_var": "#e07b00",
    "puzzle": "#e07b00",
    "item": "#b3261e",
    "kill": "#7a1010",
    "qbit": "#6a3fb5",
    "stage": "#6a3fb5",
    "award": "#6a3fb5",
    "password": "#0f7c7c",
}

BOX_H = 56
ROW_H = 100
BAND_GAP = 14
LEFT = 118
RIGHT = 28
TOP = 86


def wrap(text, limit):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if not cur:
            cur = w
        elif len(cur) + 1 + len(w) <= limit:
            cur += " " + w
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def rect_contains(r, x, y, pad=0.0):
    return r[0] - pad <= x <= r[2] + pad and r[1] - pad <= y <= r[3] + pad


def rects_overlap(a, b, pad=0.0):
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def border_point(r, tx, ty):
    """Point on rectangle r's border on the way from its centre towards (tx, ty)."""
    cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    hw, hh = (r[2] - r[0]) / 2, (r[3] - r[1]) / 2
    s = min(hw / abs(dx) if dx else 1e9, hh / abs(dy) if dy else 1e9)
    return cx + dx * s, cy + dy * s


def quad(p0, c, p1, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0], u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1])


class Graph:
    def __init__(self, path):
        self.path = path
        self.data = yaml.safe_load(path.read_text())
        self.key = self.data["key"]
        self.warnings = []

    # ---------- layout ----------
    def layout(self):
        d = self.data
        spaces = d["spaces"]
        exits = d.get("exits", [])
        self.space_by_id = {s["id"]: s for s in spaces}
        crit = d.get("critical_path", [])
        order = {}
        for i, sid in enumerate(crit):
            order.setdefault(sid, i)
        # place rooms without a grid cell in critical-path order on their floor
        used = {}
        for s in spaces + exits:
            if "at" in s:
                fl = s.get("floor", self.space_by_id.get(s.get("space"), {}).get("floor", 0))
                used.setdefault(fl, set()).add(tuple(s["at"]))
        for s in sorted([s for s in spaces if "at" not in s], key=lambda s: order.get(s["id"], 999)):
            fl = s["floor"]
            col = 0
            while (col, 0) in used.setdefault(fl, set()):
                col += 1
            s["at"] = [col, 0]
            used[fl].add((col, 0))
        for e in exits:
            e.setdefault("floor", self.space_by_id[e["space"]]["floor"])
        nodes = spaces + exits
        self.ncols = max(n["at"][0] for n in nodes) + 1
        self.cell_w = max(176, min(250, 1220 / self.ncols))
        self.box_w = self.cell_w - 46
        floors = sorted({n["floor"] for n in nodes}, reverse=True)
        self.floor_info = {f["floor"]: f for f in d.get("floors", [])}
        self.bands = []
        y = TOP
        for fl in floors:
            rows = max(n["at"][1] for n in nodes if n["floor"] == fl) + 1
            h = rows * ROW_H + 10
            self.bands.append((fl, y, h))
            y += h + BAND_GAP
        self.body_bottom = y
        band_y = {fl: by for fl, by, _ in self.bands}
        self.rect = {}
        for n in nodes:
            col, row = n["at"]
            x = LEFT + col * self.cell_w + (self.cell_w - self.box_w) / 2
            yy = band_y[n["floor"]] + 10 + row * ROW_H + (ROW_H - BOX_H) / 2 - 6
            self.rect[n["id"]] = (x, yy, x + self.box_w, yy + BOX_H)
        self.width = LEFT + self.ncols * self.cell_w + RIGHT
        ids = list(self.rect)
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                if rects_overlap(self.rect[a], self.rect[b]):
                    self.warnings.append(f"boxes overlap: {a} {b}")

    # ---------- routing ----------
    def route(self, a, b, offset_bias=0.0, avoid_labels=False):
        ra, rb = self.rect[a], self.rect[b]
        ca = ((ra[0] + ra[2]) / 2, (ra[1] + ra[3]) / 2)
        cb = ((rb[0] + rb[2]) / 2, (rb[1] + rb[3]) / 2)
        others = [r for k, r in self.rect.items() if k not in (a, b)]
        dx, dy = cb[0] - ca[0], cb[1] - ca[1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length, dx / length
        offsets = [offset_bias] + [offset_bias + s * k for k in (34, 64, 96, 130, 170, 215) for s in (1, -1)]
        best = None
        for off in offsets:
            mid = ((ca[0] + cb[0]) / 2 + nx * off * 2, (ca[1] + cb[1]) / 2 + ny * off * 2)
            p0 = border_point(ra, *mid)
            p1 = border_point(rb, *mid)
            pts = [quad(p0, mid, p1, t / 24) for t in range(25)]
            hits = sum(1 for p in pts[1:-1] for r in others if rect_contains(r, p[0], p[1], 5))
            if best is None or hits < best[0]:
                best = (hits, p0, mid, p1, pts)
            if hits == 0:
                break
        hits, p0, mid, p1, pts = best
        if hits:
            self.warnings.append(f"edge crosses a box: {a} -> {b}")
        return p0, mid, p1, pts

    def place_label(self, pts, w, h):
        """Centre for a label of w x h on the curve pts; returns (x, y, anchor) where anchor is the curve point
        when the label had to be moved off the curve (a leader is drawn), else None."""
        n = len(pts) - 1
        cands = []
        for off in (0, 18, -18, 30, -30, 42, -42, 56, -56):
            for t in (0.5, 0.4, 0.6, 0.32, 0.68, 0.25, 0.75):
                cands.append((off, t))
        for off, t in cands:
            i = int(round(t * n))
            x, y = pts[i]
            j0, j1 = max(0, i - 1), min(n, i + 1)
            tx, ty = pts[j1][0] - pts[j0][0], pts[j1][1] - pts[j0][1]
            ln = math.hypot(tx, ty) or 1.0
            cx, cy = x - ty / ln * off, y + tx / ln * off
            r = (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
            if any(rects_overlap(r, br, 3) for br in self.rect.values()):
                continue
            if any(rects_overlap(r, lr, 2) for lr in self.labels):
                continue
            self.labels.append(r)
            return cx, cy, ((x, y) if off else None)
        x, y = pts[len(pts) // 2]
        self.warnings.append("label overlaps: " + str(round(x)) + "," + str(round(y)))
        self.labels.append((x - w / 2, y - h / 2, x + w / 2, y + h / 2))
        return x, y, None

    # ---------- drawing ----------
    def render(self):
        self.layout()
        d = self.data
        out = []
        self.labels = []
        legend_h = 214
        height = self.body_bottom + legend_h
        w = self.width
        out.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{height:.0f}" '
            f'viewBox="0 0 {w:.0f} {height:.0f}" font-family="DejaVu Sans, Verdana, Arial, sans-serif">'
        )
        out.append("<defs>")
        for name, col in [("a_dark", "#2f2f2f"), ("a_tel", "#7b3fa0"), ("a_drop", "#8d5a2b"), ("a_lift", "#1f6fb2")]:
            out.append(
                f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
                f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
            )
        for k, col in STATE_COLOUR.items():
            out.append(
                f'<marker id="s_{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
                f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{col}"/></marker>'
            )
        out.append("</defs>")
        out.append(f'<rect x="0" y="0" width="{w:.0f}" height="{height:.0f}" fill="#fbfaf6" stroke="#bbb"/>')
        # header
        title = f'{d["map"]} {d["name"]}'
        out.append(f'<text x="20" y="32" font-size="22" font-weight="bold" fill="#222">{escape(title)}</text>')
        mon = d["monsters"]
        boss = f', {mon["boss"]}' if mon.get("boss") else ""
        sub = (
            f'{d["stands_on"]} · class {d["class"]} · party {d["party"][0]} → {d["party"][1]} · '
            f'monsters {mon["levels"][0]}–{mon["levels"][1]}{boss}, {mon["count"]} · treasure {d["treasure"]["level"]}'
            f' · {d["role_short"]}'
        )
        out.append(f'<text x="20" y="56" font-size="13.5" fill="#444">{escape(sub)}</text>')
        nsp = len(d["spaces"])
        cnt = sum(s.get("monsters", 0) for s in d["spaces"])
        chests = sum(1 for s in d["spaces"] if s.get("chest"))
        nl = len(d.get("loops", []))
        stats = f"{nsp} rooms · {cnt} monsters placed · {chests} chests · {nl} loop{'' if nl == 1 else 's'}"
        out.append(f'<text x="20" y="75" font-size="12" fill="#666">{escape(stats)}</text>')
        # floor bands
        for i, (fl, by, bh) in enumerate(self.bands):
            fill = "#f1eee4" if i % 2 == 0 else "#f7f5ee"
            out.append(f'<rect x="10" y="{by}" width="{w - 20:.0f}" height="{bh}" rx="6" fill="{fill}" stroke="#ddd8c8"/>')
            info = self.floor_info.get(fl, {})
            label = f"Floor {fl:+d}" if fl else "Floor 0"
            out.append(f'<text x="20" y="{by + 22}" font-size="13" font-weight="bold" fill="#555">{label}</text>')
            ly = by + 38
            for line in wrap(info.get("name", ""), 13)[:3]:
                out.append(f'<text x="20" y="{ly}" font-size="11" fill="#777">{escape(line)}</text>')
                ly += 13
            if "height" in info:
                out.append(f'<text x="20" y="{ly}" font-size="11" fill="#999">z {info["height"]}</text>')
        # edges
        edge_svg, label_svg, state_svg = [], [], []
        self.edge_mid = {}
        pair_count = {}
        for ln in d["links"]:
            key = tuple(sorted((ln["from"], ln["to"])))
            pair_count[key] = pair_count.get(key, 0) + 1
            bias = 0 if pair_count[key] == 1 else 26 * (pair_count[key] - 1)
            p0, mid, p1, pts = self.route(ln["from"], ln["to"], bias)
            st = EDGE[ln["kind"]]
            dpath = f"M{p0[0]:.1f},{p0[1]:.1f} Q{mid[0]:.1f},{mid[1]:.1f} {p1[0]:.1f},{p1[1]:.1f}"
            attrs = f'fill="none" stroke="{st["stroke"]}" stroke-width="{st["width"]}"'
            if st["dash"]:
                attrs += f' stroke-dasharray="{st["dash"]}"'
            arrow = st["arrow"] or ln.get("one_way")
            if arrow:
                mk = {"teleport": "a_tel", "drop": "a_drop", "lift": "a_lift"}.get(ln["kind"], "a_dark")
                attrs += f' marker-end="url(#{mk})"'
            edge_svg.append(f'<path d="{dpath}" {attrs}/>')
            if ln["kind"] == "lift":
                edge_svg.append(f'<path d="{dpath}" fill="none" stroke="#fff" stroke-width="1.6"/>')
            self.edge_mid[ln["id"]] = pts
            label = ln.get("label")
            if label:
                fs = 11
                tw = len(label) * fs * 0.58 + 22
                lx, ly, anchor = self.place_label(pts, tw, 17)
                if anchor:
                    label_svg.append(
                        f'<path d="M{anchor[0]:.1f},{anchor[1]:.1f} L{lx:.1f},{ly:.1f}" stroke="#888" '
                        f'stroke-width="1" fill="none"/><circle cx="{anchor[0]:.1f}" cy="{anchor[1]:.1f}" r="2.2" fill="#888"/>'
                    )
                colour = st["stroke"] if ln["kind"] in ("locked", "teleport", "drop", "lift", "stair") else "#333"
                gated = ln.get("opened_by") or ln["kind"] == "locked"
                label_svg.append(
                    f'<rect x="{lx - tw / 2:.1f}" y="{ly - 8.5:.1f}" width="{tw:.1f}" height="17" rx="4" '
                    f'fill="#fffdf7" stroke="{colour if gated else "#ccc"}" stroke-width="{1.4 if gated else 0.8}"/>'
                )
                tx = lx - tw / 2 + 6
                if ln["kind"] == "locked" or (ln.get("opened_by") and self.state_kind(ln["opened_by"]) == "item"):
                    # small key glyph
                    label_svg.append(
                        f'<circle cx="{tx + 3:.1f}" cy="{ly:.1f}" r="3" fill="none" stroke="#b3261e" stroke-width="1.6"/>'
                        f'<path d="M{tx + 6:.1f},{ly:.1f} h7 m-2,0 v3 m-3,-3 v2" stroke="#b3261e" stroke-width="1.6" fill="none"/>'
                    )
                    tx += 15
                elif gated:
                    sc = STATE_COLOUR.get(self.state_kind(ln["opened_by"]), "#e07b00")
                    label_svg.append(f'<rect x="{tx:.1f}" y="{ly - 4:.1f}" width="8" height="8" fill="{sc}"/>')
                    tx += 12
                label_svg.append(
                    f'<text x="{tx:.1f}" y="{ly + 4:.1f}" font-size="{fs}" fill="{colour}">{escape(label)}</text>'
                )
        # state lines: from the room that holds the key/lever/boss to the link it opens
        for stt in d.get("states", []):
            src = stt.get("where")
            if src not in self.rect or not stt.get("draw", True):
                continue
            col = STATE_COLOUR.get(stt["kind"], "#e07b00")
            for lid in stt.get("opens", []):
                if lid not in self.edge_mid:
                    self.warnings.append(f"state {stt['id']} opens unknown link {lid}")
                    continue
                pts = self.edge_mid[lid]
                tx, ty = pts[len(pts) // 2]
                r = self.rect[src]
                p0 = border_point(r, tx, ty)
                # bow the line so it does not lie on top of an edge
                mx, my = (p0[0] + tx) / 2, (p0[1] + ty) / 2
                dx, dy = tx - p0[0], ty - p0[1]
                ln = math.hypot(dx, dy) or 1
                best = None
                for off in (40, -40, 80, -80, 120, -120, 170, -170, 230, -230, 0):
                    c = (mx - dy / ln * off, my + dx / ln * off)
                    smp = [quad(p0, c, (tx, ty), t / 20) for t in range(2, 19)]
                    hits = sum(1 for p in smp for k, rr in self.rect.items() if k != src and rect_contains(rr, *p, 3))
                    if best is None or hits < best[0]:
                        best = (hits, c)
                    if hits == 0:
                        break
                c = best[1]
                if best[0]:
                    self.warnings.append(f"state line crosses a box: {stt['id']} -> {lid}")
                state_svg.append(
                    f'<path d="M{p0[0]:.1f},{p0[1]:.1f} Q{c[0]:.1f},{c[1]:.1f} {tx:.1f},{ty:.1f}" fill="none" '
                    f'stroke="{col}" stroke-width="1.7" stroke-dasharray="5 4" opacity="0.9" '
                    f'marker-end="url(#s_{stt["kind"] if stt["kind"] in STATE_COLOUR else "lever"})"/>'
                )
                state_svg.append(f'<circle cx="{p0[0]:.1f}" cy="{p0[1]:.1f}" r="3.2" fill="{col}"/>')
        out.extend(edge_svg)
        out.extend(state_svg)
        # boxes
        for s in d["spaces"]:
            out.extend(self.box(s))
        for e in d.get("exits", []):
            out.extend(self.exit_pill(e))
        out.extend(label_svg)
        # check labels against labels and boxes once more
        for i, a in enumerate(self.labels):
            for b in self.labels[i + 1:]:
                if rects_overlap(a, b):
                    self.warnings.append("two labels overlap")
        out.extend(self.legend(self.body_bottom + 4, w))
        out.append("</svg>")
        return "\n".join(out)

    def state_kind(self, sid):
        for s in self.data.get("states", []):
            if s["id"] == sid:
                return s["kind"]
        self.warnings.append(f"unknown state {sid}")
        return "lever"

    def box(self, s):
        x0, y0, x1, y1 = self.rect[s["id"]]
        res = []
        stroke, sw = "#666", 1.3
        if s.get("set_piece"):
            stroke, sw = "#c08a00", 3.6
        if s.get("boss"):
            stroke, sw = "#b3261e", 3.6
        fill = KIND_FILL.get(s["kind"], "#eee")
        res.append(
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" rx="7" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        )
        chars = int((x1 - x0 - 12) / 6.9)
        lines = wrap(s["name"], chars)
        if len(lines) > 2:
            lines = lines[:2]
            lines[1] = lines[1][: max(0, chars - 1)] + "…"
        ty = y0 + (16 if len(lines) == 2 else 21)
        for line in lines:
            res.append(
                f'<text x="{(x0 + x1) / 2:.1f}" y="{ty:.1f}" font-size="12" font-weight="bold" fill="#1d1d1d" '
                f'text-anchor="middle">{escape(line)}</text>'
            )
            ty += 14
        # foot line: kind and size on the left, monsters (or the boss) right-aligned before the chest badge
        m = s.get("monsters", 0)
        right = s.get("boss_label") or (f"{m} m" if m else "")
        right_x = x1 - (36 if s.get("chest") else 6)
        foot = f'{s["kind"]} {s["size"]}'
        if len(foot) * 6.0 + len(right) * 6.6 + 10 > right_x - x0 - 6:
            foot = s["size"]
        if len(foot) * 6.0 + len(right) * 6.6 + 10 > right_x - x0 - 6:
            foot = ""
        res.append(f'<text x="{x0 + 6:.1f}" y="{y1 - 6:.1f}" font-size="10.5" fill="#555">{escape(foot)}</text>')
        if right:
            colour = "#b3261e" if s.get("boss_label") else "#9b1c1c"
            res.append(
                f'<text x="{right_x:.1f}" y="{y1 - 6:.1f}" font-size="10.5" font-weight="bold" '
                f'fill="{colour}" text-anchor="end">{escape(right)}</text>'
            )
        if s.get("chest"):
            res.append(
                f'<rect x="{x1 - 30:.1f}" y="{y1 - 17:.1f}" width="26" height="13" rx="2" fill="#e8b923" stroke="#8a6a00"/>'
                f'<text x="{x1 - 17:.1f}" y="{y1 - 7.2:.1f}" font-size="9.5" font-weight="bold" fill="#3a2a00" '
                f'text-anchor="middle">T{s["chest"]}</text>'
            )
        tag = None
        if s.get("boss"):
            tag = ("BOSS", "#b3261e")
        elif s.get("set_piece"):
            tag = ("SET PIECE", "#c08a00")
        if tag:
            tw = len(tag[0]) * 6.4 + 10
            res.append(
                f'<rect x="{x1 - tw - 4:.1f}" y="{y0 - 8:.1f}" width="{tw:.1f}" height="14" rx="3" fill="{tag[1]}"/>'
                f'<text x="{x1 - 4 - tw / 2:.1f}" y="{y0 + 2.5:.1f}" font-size="9.5" font-weight="bold" fill="#fff" '
                f'text-anchor="middle">{tag[0]}</text>'
            )
        if s.get("goal"):
            res.append(
                f'<rect x="{x0 + 4:.1f}" y="{y0 - 8:.1f}" width="40" height="14" rx="3" fill="#2e6b3a"/>'
                f'<text x="{x0 + 24:.1f}" y="{y0 + 2.5:.1f}" font-size="9.5" font-weight="bold" fill="#fff" '
                f'text-anchor="middle">GOAL</text>'
            )
        return res

    def exit_pill(self, e):
        x0, y0, x1, y1 = self.rect[e["id"]]
        y0 += 8
        y1 -= 8
        h = y1 - y0
        res = [
            f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{h:.1f}" rx="{h / 2:.1f}" '
            f'fill="#e3ecf8" stroke="#3b5b8c" stroke-width="1.6"/>'
        ]
        chars = int((x1 - x0 - 16) / 6.3)
        lines = wrap(e["label"], chars)[:2]
        ty = y0 + (h / 2 + 4 if len(lines) == 1 else h / 2 - 3)
        for line in lines:
            res.append(
                f'<text x="{(x0 + x1) / 2:.1f}" y="{ty:.1f}" font-size="11" fill="#1f3a66" '
                f'text-anchor="middle">{escape(line)}</text>'
            )
            ty += 13
        # connector to its room
        sp = e["space"]
        p0, mid, p1, pts = self.route(e["id"], sp)
        kind = e.get("kind", "both")
        attrs = 'fill="none" stroke="#3b5b8c" stroke-width="2.2"'
        if kind == "out":
            dpath = f"M{p1[0]:.1f},{p1[1]:.1f} Q{mid[0]:.1f},{mid[1]:.1f} {p0[0]:.1f},{p0[1]:.1f}"
            attrs += ' stroke-dasharray="7 3" marker-end="url(#a_dark)"'
        else:
            dpath = f"M{p0[0]:.1f},{p0[1]:.1f} Q{mid[0]:.1f},{mid[1]:.1f} {p1[0]:.1f},{p1[1]:.1f}"
        return [f'<path d="{dpath}" {attrs}/>'] + res

    def legend(self, y, w):
        res = [f'<rect x="10" y="{y}" width="{w - 20:.0f}" height="200" rx="6" fill="#ffffff" stroke="#ddd8c8"/>']
        res.append(f'<text x="22" y="{y + 20}" font-size="12.5" font-weight="bold" fill="#333">Legend</text>')
        # room kinds
        x, yy = 22, y + 34
        for k, fill in KIND_FILL.items():
            res.append(f'<rect x="{x}" y="{yy}" width="26" height="16" rx="3" fill="{fill}" stroke="#666"/>')
            res.append(f'<text x="{x + 32}" y="{yy + 12}" font-size="11" fill="#333">{KIND_NAME[k]}</text>')
            yy += 21
        # marks
        x2 = 22 + 205
        yy = y + 34
        marks = [
            ('<rect x="{x}" y="{y}" width="26" height="16" rx="3" fill="#f3e6c8" stroke="#c08a00" stroke-width="3"/>',
             "set piece (gold frame)"),
            ('<rect x="{x}" y="{y}" width="26" height="16" rx="3" fill="#f3e6c8" stroke="#b3261e" stroke-width="3"/>',
             "boss (red frame)"),
            ('<rect x="{x}" y="{y}" width="26" height="13" rx="2" fill="#e8b923" stroke="#8a6a00"/>',
             "chest, treasure tier"),
            ('<text x="{x}" y="{y12}" font-size="11" font-weight="bold" fill="#9b1c1c">6 m</text>',
             "monsters placed"),
            ('<rect x="{x}" y="{y}" width="26" height="14" rx="3" fill="#2e6b3a"/>', "quest goal"),
            ('<rect x="{x}" y="{y}" width="26" height="16" rx="8" fill="#e3ecf8" stroke="#3b5b8c"/>',
             "exit to another map"),
        ]
        for tpl, text in marks:
            res.append(tpl.format(x=x2, y=yy, y12=yy + 12))
            res.append(f'<text x="{x2 + 32}" y="{yy + 12}" font-size="11" fill="#333">{text}</text>')
            yy += 21
        # edges
        x3 = x2 + 200
        yy = y + 38
        col = 0
        for k, st in EDGE.items():
            xx = x3 + col * 215
            attrs = f'stroke="{st["stroke"]}" stroke-width="{st["width"]}" fill="none"'
            if st["dash"]:
                attrs += f' stroke-dasharray="{st["dash"]}"'
            if st["arrow"]:
                mk = {"teleport": "a_tel", "drop": "a_drop"}.get(k, "a_dark")
                attrs += f' marker-end="url(#{mk})"'
            res.append(f'<path d="M{xx},{yy} h44" {attrs}/>')
            if k == "lift":
                res.append(f'<path d="M{xx},{yy} h44" stroke="#fff" stroke-width="1.6"/>')
            res.append(f'<text x="{xx + 52}" y="{yy + 4}" font-size="11" fill="#333">{EDGE_NAME[k]}</text>')
            yy += 21
            if yy > y + 38 + 21 * 4.5:
                yy = y + 38
                col += 1
        # state lines
        xx = x3 + 2 * 215
        yy = y + 38
        for k, text in [("lever", "lever, button, puzzle"), ("item", "key found here"), ("kill", "boss kill"),
                        ("qbit", "quest state or stage"), ("password", "password")]:
            c = STATE_COLOUR[k]
            res.append(
                f'<path d="M{xx},{yy} h40" stroke="{c}" stroke-width="1.7" stroke-dasharray="5 4" fill="none" '
                f'marker-end="url(#s_{k})"/><circle cx="{xx}" cy="{yy}" r="3.2" fill="{c}"/>'
            )
            res.append(f'<text x="{xx + 50}" y="{yy + 4}" font-size="11" fill="#333">{text}</text>')
            yy += 21
        res.append(
            f'<text x="22" y="{y + 190}" font-size="10.5" fill="#666">Dashed state lines run from the room that '
            f'holds the key, lever or boss to the gate they open; a label with a small square names the state.</text>'
        )
        return res


def main(argv):
    keys = set(argv[1:])
    files = sorted(HERE.glob("*.graph.yml"))
    bad = 0
    for f in files:
        g = Graph(f)
        if keys and g.key not in keys:
            continue
        svg = g.render()
        out = HERE / f"{g.key}.svg"
        out.write_text(svg)
        print(f"{out.name}: {g.width:.0f} px wide, {len(g.data['spaces'])} rooms, {len(g.data['links'])} links")
        for w in g.warnings:
            print("   warning:", w)
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
