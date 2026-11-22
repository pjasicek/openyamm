#!/usr/bin/env python3
"""Assemble devdocs/xeen/mockups/act6_fd01_graph_a8.md from act6_graphs/notes_fd01.md and fd01.graph.yml
(lane A8, session 16; a copy of a8_s13/make_act6_page.py with Q numbers from Q63 on, after A8's DD-26 page's Q56-Q62).
Usage: make_fd01_page.py

Each notes file holds one map's section, then "**DECIDE items (...)**" (a numbered list), "**Requests to other
lanes**" (bullets "- **A2:** ..." or "- A2: ..." with indented sub-bullets) and "**State and next steps.**". The page
keeps each map's section, numbers every DECIDE item once across the page (Q1..Qn), builds the surface-door table from
the graphs' `exits`, and groups the requests by lane.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import re
import sys
from pathlib import Path

import yaml

M = Path(_REPO_ROOT + '/devdocs/xeen/mockups')
G = M / 'act6_graphs'
ALL = ['fd01']
Q0 = 62   # A8's Act V pages hold Q1-Q55, the DD-26 page Q56-Q62
keys = sys.argv[1:] or [k for k in ALL if (G / f'notes_{k}.md').exists()]
LANES = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'AU', 'S']


def split_notes(text):
    """Return (section, decide_lines, request_lines, state_text)."""
    def cut(t, marker):
        i = t.find(marker)
        return (t, '') if i < 0 else (t[:i], t[i:])
    sec, rest = cut(text, '**DECIDE items')
    dec, rest = cut(rest, '**Requests to other lanes**')
    req, state = cut(rest, '**State and next steps')
    dec_lines = dec.splitlines()[1:]
    req_lines = req.splitlines()[1:]
    return sec.rstrip() + '\n', dec_lines, req_lines, state.strip()


def decide_items(lines):
    """Group a numbered markdown list into items (each a list of lines, first line without its number)."""
    items = []
    for ln in lines:
        m = re.match(r'^(\d+)\.\s+(.*)$', ln)
        if m:
            items.append([m.group(2)])
        elif items and (ln.startswith('   ') or ln.startswith('\t')):
            items[-1].append(ln.strip())
        elif items and ln.strip() and not ln.startswith('**'):
            items[-1].append(ln.strip())
    return items


def lane_requests(lines):
    """Map lane -> list of text lines."""
    out = {}
    cur = None
    for ln in lines:
        m = re.match(r'^- \*{0,2}(A\d|AU|S)\b[^:]*:\*{0,2}\s*(.*)$', ln)
        if m:
            cur = m.group(1)
            out.setdefault(cur, [])
            if m.group(2).strip():
                out[cur].append(m.group(2).strip())
        elif cur and ln.startswith('  ') and ln.strip():
            out[cur].append(ln.strip().lstrip('- ').strip())
    return out


rows, doors, sections, questions, requests, spans = [], [], [], [], {}, []
qn = Q0
for k in keys:
    g = yaml.safe_load(open(G / f'{k}.graph.yml'))
    sp = g.get('spaces', []) or []
    mon = g.get('monsters') or {}
    kx = str(mon.get('kill_xp', '-')).split(' (')[0]
    rows.append(f"| {g['map']} {g['name']} | {str(g.get('stands_on', '')).split(' ')[0]} | {g.get('class')} | "
                f"{len(sp)} | {mon.get('count', 0)} | {kx} | {sum(1 for s in sp if s.get('chest'))} | "
                f"{len(g.get('loops', []) or [])} |")
    for e in g.get('exits', []) or []:
        doors.append(f"| {g['map']} | {e.get('label', '')} | {e.get('arrival', '')} | {e.get('neighbour', '')} |")
    raw = (G / f'notes_{k}.md').read_text()
    first = qn + 1
    # a map's own "DECIDE n" becomes the page's number
    raw = re.sub(r'DECIDE (\d+)', lambda m: f"Q{first + int(m.group(1)) - 1}", raw)
    sec, dec, req, state = split_notes(raw)
    items = decide_items(dec)
    qs = []
    for it in items:
        qn += 1
        # join wrapped lines: a line that does not start a bullet continues the line before it
        joined = []
        for ln in it:
            if joined and not ln.startswith('- '):
                joined[-1] += ' ' + ln
            else:
                joined.append(ln)
        it = joined
        # keep the item's option bullets as a list under its first line
        qs.append(f"**Q{qn}.** " + it[0] + ("\n\n" + "\n".join(it[1:]) if len(it) > 1 else ""))
    span = f"Q{first}–Q{qn}" if items else "none"
    spans.append(f"{g['map']} 1–{len(items)} = {span}")
    sections.append(sec + f"\nOpen questions: {span} below. {state}\n")
    questions.append(f"### {g['map']} {g['name']}\n\n" + "\n\n".join(qs) + "\n")
    for lane, lines in lane_requests(req).items():
        requests.setdefault(lane, []).append((g['map'], lines))

head = f"""# FD-01 Alamar Depths: dungeon graph, lane A8 (MU-6)

Review page for phase 6, 2026-11-21, lane A8 (`xeen-a8`, session 16), for a decider. It holds **FD-01 Alamar Depths**
(Story M39, Prince Roland; the Key to the Dragon Tower; Q-D26's hatch), the last of the world's 82 maps to be drawn.
D-57 Q7 set its share of the FD-01 + FD-02 row (60 monsters at 55-80, 68.0k; FD-02 took 26 at 31.07k, so FD-01 plans 34
at 36.93k, room 30.1k-43.7k), and D-61 Q14 sends D7's roof hatch into it after M33. A review document, not a brief; L1
starts from the graph file once the questions below are answered. **Every open question is numbered once, continuing
A8's pages** (DD-26's ended at Q62): Q63-Q{qn}.

**Reading the picture:** as on A8's DD-26 page ([act6_dungeon_graphs_a8.md](act6_dungeon_graphs_a8.md)) and A7's Act VI
page ([act6_dungeon_graphs_a7.md](act6_dungeon_graphs_a7.md)): one band per floor; box colour by kind; gold frame set
piece, green tag quest goal, red "3 m" monsters placed, gold "T6" a chest of that tier; one line style per connection
kind; a gate's label names the state that opens it (orange dashed lines: the levers and the grate's bolt; the red key
label: the skull door, which reads the Cube). Blue pills are exits.

**Files:** [act6_graphs/](act6_graphs/): `fd01.graph.yml`, `fd01.svg`, `notes_fd01.md`. Redraw with
`python3 devdocs/xeen/mockups/act6_graphs/render_graphs.py fd01` (no overlap printed); PNG
`output/studio_cal/fd01/png/fd01.png` (headless Chrome, looked at). The source read: `output/studio_cal/fd01/`
(`maze0052_ascii.txt`, `maze0052_evt.txt`, `tools/ascii_maze.py`, `tools/regions.py`). This page is assembled by
`output/studio_cal/fd01/tools/make_fd01_page.py` from the notes file.

**Rules used** (A8's earlier pages'): sizes and counts inside the class bands (MAPS, Dungeons) and MAPS §0's rows, kill
XP per member L(L+10) per kill over four within the decider's range; A2's rows by id; every dead end holds a chest, a
find or a goal; no riddle the game does not answer; only engine words that exist; lamps where they can hang; props by
the walls; rewards at MM6-MM8 size; every exit the `exit` preset (D-24), and the map's own Yes/No on a hatch exit into a
BLV (D-66); a hook's text before a choice ends on the request (D-65 B1); a stand-in with a title reads right (D-66);
Xeen's indoor radius cap 60 (D-67); inside entrances named after the map they are entered from (D-37); the first room
past a map door quiet (D-11.3). Map qbit block proposed: FD-01 117840-117879.

| Dungeon | Stands on | Class | Rooms | Monsters | Kill XP per member | Chests | Loops |
| --- | --- | --- | --: | --: | --- | --: | --: |
""" + "\n".join(rows) + "\n\n---\n\n"

doors_md = ("## The surface maps' doors against the graphs\n\nOutside points from the installed "
            "(`xeen_d6.studio.yml`, `xeen_d7.studio.yml`, A6); inside arrival proposed here (D-37 name).\n\n"
            "| Map | Door | Inside arrival (proposed) | Outside |\n| --- | --- | --- | --- |\n" + "\n".join(doors) + "\n")

q_md = ("## Open questions (Q63–Q%d)\n\nEach gives the options with the proposed default first and marked "
        "\"(a, proposed)\", the evidence and what depends on it. The graph files hold the same questions under "
        "`open_questions`.\n\n" % qn) + "\n".join(questions)

r_md = ("## Requests by lane\n\nA number such as \"2 (a)\" in a request is the map's own DECIDE item and option: "
        + "; ".join(spans) + ".\n\n")
for lane in LANES:
    if lane not in requests:
        continue
    r_md += f"**{lane}**\n"
    for mp, lines in requests[lane]:
        r_md += f"- {mp}: " + " ".join(lines) + "\n"
    r_md += "\n"

out = M / 'act6_fd01_graph_a8.md'
tmp = out.with_suffix('.md.tmp')
tmp.write_text(head + "\n---\n\n".join(sections) + "\n---\n\n" + doors_md + "\n" + q_md + "\n" + r_md)
tmp.rename(out)
print(out, len(rows), 'maps,', qn, 'questions')
