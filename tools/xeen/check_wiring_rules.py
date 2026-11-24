#!/usr/bin/env python3
"""Wiring rules of the Xeen dungeon projects (devdocs/xeen/briefs/<map>/L4), from the player's pins 2026-11-24.

  hide.panel_wall    error    (F46) an event hides a wall panel that is not a covering panel (`cover: true`): the
                              panel is the wall itself, so hiding it opens a hole onto the void (XD-27's sail).
  ask.goal           error    (F47) a Yes/No question in front of a quest goal (destroy, burn): "No" only leaves the
                              thing as it is, so the click should just do it (XD-05's drums; F13's rule for touch
                              effects). A question kept as a real choice (KEEP below, with its reason) is listed
                              as `kept`.
  click.covered      warning  (F47) a clicked platform with a part standing on its top that is not clicked (XD-02's
                              winch: its iron head and bars answer nothing, the drum under them is 80 high). The fix
                              is `part_of: <platform id>` on the part (rooms.yml, since 2026-11-24): it runs the
                              platform's click.

Usage: tools/xeen/check_wiring_rules.py [--maps xd05,xd27 | all] [--json FILE]   exit 1 on an error.
Sites waiting for their map's rebuild are listed in OPEN below and reported as `open`, not errors; remove a site from
OPEN when its map is rebuilt.
"""
import argparse
import glob
import json
import os
import re
import sys

import yaml

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRIEFS = f'{R}/devdocs/xeen/briefs'
GOAL = re.compile(r'\b(destroy|burn)\b[^?]*\?\s*$', re.IGNORECASE)
# D-121 (2026-11-24, the decider on F47): the questions that stay, each a real choice with a cost or a consequence.
# Every other destroy question is a click (XD-23's fire pit, XD-16's skulls, FD-04's three lesser shrines and the Lord
# Xeen Machine became clicks with their line on the status line).
KEEP = {
    ('dd13', 'evt:pit_e'): "Q-D11's war or peace: burning a fort's pit while its Ogres are out is the war path, and "
                           "the forts can be left for the peace (D-121)",
    ('dd13', 'evt:pit_w'): "as evt:pit_e: the other fort's pit, the same war-or-peace choice (Q-D11, D-121)",
    ('fd04', 'evt:shrine_ultimate'): "the Shrine of Ultimate Evil: 70 Fire damage and the party thrown out of the "
                                     "dungeon to X7, no experience; the tell is in the question (D-57 Q26, D-121)",
}
# Sites found 2026-11-24 whose maps are not rebuilt yet (each map's own lane, or the next dungeon pass).
OPEN = set()


def load(path):
    return yaml.safe_load(open(path)) if os.path.exists(path) else None


def check(key):
    l4 = f'{BRIEFS}/{key}/L4'
    rooms = load(f'{l4}/rooms.yml') or {}
    wiring = load(f'{l4}/wiring.yml') or {}
    panels = {}
    platforms = {}
    for room in rooms.get('rooms') or []:
        for wall in room.get('walls') or []:
            for panel in wall.get('panels') or []:
                if panel.get('id'):
                    panels[panel['id']] = panel
        for platform in room.get('platforms') or []:
            platforms.setdefault(room['id'], []).append(platform)
    findings = []
    clicked = set()
    for event in wiring.get('events') or []:
        if event.get('trigger') in (None, 'click') and str(event.get('source', '')).startswith('platform:'):
            clicked.add(event['source'])
        for effect in (event.get('effects') or []) + (event.get('else_effects') or []):
            if isinstance(effect, dict) and isinstance(effect.get('hide'), str) and effect['hide'].startswith('panel:'):
                panel = panels.get(effect['hide'])
                if panel is not None and not panel.get('cover'):
                    findings.append(('hide.panel_wall', 'error', f"{event['id']} hides {effect['hide']}, a piece of "
                                     "the wall (no `cover: true`): it opens a hole onto the void"))
        question = event.get('question')
        if isinstance(question, dict):
            text = str(question.get('message') or '') + ' ' + str(question.get('ask') or '')
            yes = any(str(a).lower() in ('yes', 'y') for a in question.get('answers') or [])
            if yes and (GOAL.search(str(question.get('message') or '')) or 'destroy' in text.lower()):
                kept = KEEP.get((key, event['id']))
                findings.append(('ask.goal', 'kept' if kept else 'error',
                                 f"{event['id']} asks \"{question.get('message')}\" before a quest goal: "
                                 + (f"kept: {kept}" if kept else "the click should do it")))
    for room, items in platforms.items():
        for top in items:
            if not top.get('id') in clicked:
                continue
            outline = top.get('outline')
            if outline:
                xs = [p[0] for p in outline]
                ys = [p[1] for p in outline]
            elif top.get('at') and top.get('size'):
                xs = [top['at'][0] - top['size'][0] / 2, top['at'][0] + top['size'][0] / 2]
                ys = [top['at'][1] - top['size'][1] / 2, top['at'][1] + top['size'][1] / 2]
            else:
                continue
            height = (top.get('base') or 0) + (top.get('rise') or 0)
            for other in items:
                if other is top or other.get('id') in clicked or other.get('base') is None \
                        or other.get('part_of') == top.get('id'):
                    continue
                if abs(other['base'] - height) > 2:
                    continue
                o = other.get('outline') or []
                if o and all(min(xs) - 8 <= p[0] <= max(xs) + 8 and min(ys) - 8 <= p[1] <= max(ys) + 8 for p in o):
                    findings.append(('click.covered', 'warning', f"{top['id']} is clicked but "
                                     f"{other.get('notes') or 'a part'} standing on it is not"))
    return [(rule, 'open' if (key, rule) in OPEN and severity != 'kept' else severity, what)
            for rule, severity, what in findings]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--maps', default='all')
    ap.add_argument('--json')
    a = ap.parse_args()
    keys = sorted(os.path.basename(os.path.dirname(os.path.dirname(p))) for p in glob.glob(f'{BRIEFS}/*/L4/wiring.yml'))
    if a.maps != 'all':
        keys = a.maps.split(',')
    report = {}
    errors = 0
    for key in keys:
        findings = check(key)
        if findings:
            report[key] = findings
        for rule, severity, what in findings:
            errors += severity == 'error'
            print(f'{key}: {severity} {rule}: {what}')
    print(f'{errors} errors over {len(keys)} projects')
    if a.json:
        json.dump(report, open(a.json, 'w'), indent=1)
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
