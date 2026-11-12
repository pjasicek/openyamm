#!/usr/bin/env python3
"""Build the before/after compare viewer for every MM6-MM8 model changed by the 2026-11-11 audit fixes.

    python3 level_generation/creatures/audit_mm678_20261111/compare_viewer/build.py

Before = the GLBs at the assets_source repository's HEAD (committed 2026-11-11 12:11, before the fixes), exported to
before/ (git-ignored, about 1 GB); after = the installed files in assets_source. Bindings come from the main
repository's HEAD actors.yml (before) and the working copy (after), per descriptor: skin variant, scale, yaw offset and
attachments. Notes come from the fixes/ ledgers. Writes manifest.json beside index.html. Serve the repository root
(claude_shared/serve_review.py 8912) and open
http://127.0.0.1:8912/level_generation/creatures/audit_mm678_20261111/compare_viewer/
"""
import json
from pathlib import Path
import re
import subprocess

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SOURCE = REPO / 'assets_source'
FIXES = HERE.parent / 'fixes'
ROOT_URL = '../../../../'
STREAMS = {'LEDGER_texpass.md': 'texture', 'LEDGER_anim.md': 'clips', 'LEDGER_attacks.md': 'attack',
           'LEDGER_rebuild.md': 'rebuild'}


def git(*args, cwd=REPO):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True).stdout


def changed_sources():
    out = git('status', '--porcelain', 'worlds/mm6', 'worlds/mm7', 'worlds/mm8', cwd=SOURCE).decode()
    return {line[3:].strip() for line in out.splitlines() if line[3:].strip().endswith('.glb')}


def bindings(text):
    result = {}
    for actor in yaml.safe_load(text)['actors']:
        model = actor.get('model')
        if not model:
            continue
        result.setdefault(model, []).append({
            'descriptor': actor['descriptor'], 'skin': actor.get('skin'), 'scale': actor.get('scale', 1.0),
            'yaw': actor.get('yaw_offset', 0.0),
            'attachments': [{'model': a['model'], 'node': a['node']} for a in actor.get('attachments') or []
                            if a.get('model') and a.get('node')],
            'clips': {**(actor.get('clips') or {}),
                      **{k: v for k, v in (actor.get('animation') or {}).items() if k in ('run', 'cast', 'sprint')}},
        })
    return result


def ledger_notes():
    notes = {}
    for name, stream in STREAMS.items():
        path = FIXES / name
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if not line.startswith('|') or line.startswith('|---') or line.startswith('| Model'):
                continue
            cells = [c.strip() for c in line.strip('|').split('|')]
            if len(cells) < 4:
                continue
            ids = set(re.findall(r'\b(mm[678]_[0-9a-z_]+|mm[678]:[0-9a-z_]+|m\d{3}|7m\d{3})\b', cells[0]))
            text = re.sub(r'`', '', cells[3])[:420]
            status = cells[1]
            for ident in ids:
                key = ident.replace(':', '_')
                notes.setdefault(key, []).append({'stream': stream, 'status': status[:60], 'text': text})
    return notes


def note_for(stem, notes):
    found = list(notes.get(stem, []))
    short = stem.split('_', 1)[1]
    if re.fullmatch(r'm\d{3}|7m\d{3}', short):
        found += notes.get(short, [])
    seen, out = set(), []
    for n in found:
        key = (n['stream'], n['text'][:80])
        if key not in seen:
            seen.add(key)
            out.append(n)
    return out


def main():
    changed = changed_sources()
    notes = ledger_notes()
    before_dir = HERE / 'before'
    entries = []
    exported = set()

    def before_url(path):
        if path in changed:
            target = before_dir / path
            if path not in exported:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(git('show', f'HEAD:{path}', cwd=SOURCE))
                exported.add(path)
            return f'before/{path}'
        return ROOT_URL + 'assets_source/' + path

    def after_url(path):
        return ROOT_URL + 'assets_source/' + path

    for world in ('mm6', 'mm7', 'mm8'):
        rel = f'assets_dev/worlds/{world}/models/actors.yml'
        old = bindings(git('show', f'HEAD:{rel}'))
        new = bindings((REPO / rel).read_text())
        for model in sorted(set(old) | set(new)):
            path = model
            attach_paths = {a['model'] for b in old.get(model, []) + new.get(model, []) for a in b['attachments']}
            if path not in changed and not any(p in changed for p in attach_paths):
                continue
            stem = Path(path).stem
            if any(e['stem'] == stem for e in entries):
                for e in entries:
                    if e['stem'] == stem and world not in e['worlds']:
                        e['worlds'].append(world)
                continue
            tiers = []
            names = [b['descriptor'] for b in new.get(model, [])] or [b['descriptor'] for b in old.get(model, [])]
            for name in names:
                b = next((x for x in old.get(model, []) if x['descriptor'] == name), None)
                a = next((x for x in new.get(model, []) if x['descriptor'] == name), None)
                side = {}
                for key, binding, url in (('before', b, before_url), ('after', a, after_url)):
                    binding = binding or a or b
                    side[key] = {
                        'skin': binding['skin'], 'scale': binding['scale'], 'yaw': binding['yaw'],
                        'attachments': [{'url': url(x['model']), 'node': x['node']}
                                        for x in binding['attachments']],
                        'clips': binding['clips'],
                    }
                tiers.append({'descriptor': name, **side})
            entries.append({
                'stem': stem, 'worlds': [world], 'name': re.sub(r'\s+[A-Ca-c]$', '', names[0]),
                'before': before_url(path), 'after': after_url(path),
                'notes': note_for(stem, notes), 'tiers': tiers,
            })
    for e in entries:
        streams = sorted({n['stream'] for n in e['notes']})
        e['streams'] = streams or ['other']
    entries.sort(key=lambda e: (e['worlds'][0], e['name']))
    (HERE / 'manifest.json').write_text(json.dumps({'models': entries}, indent=1))
    print(len(entries), 'models;', len(exported), 'before GLBs exported')
    unmatched = [e['stem'] for e in entries if not e['notes']]
    print('without ledger notes:', unmatched)


if __name__ == '__main__':
    main()
