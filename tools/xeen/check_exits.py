#!/usr/bin/env python3
"""Exit look check (F12, the user 2026-11-21): every way out of a Xeen dungeon looks like MM7's and MM8's, a black face
(7solid01) in its doorway, not a daylight picture or a door that turns out to lead outside.

  tools/xeen/check_exits.py [<key>...] [--assets ROOT] [--no-built]
      (keys as in devdocs/xeen/briefs/<key>/, default every L4 project; the built maps are read from ROOT, default
      assets_dev; --no-built checks the project files only)

Errors:
- `exits.not_black`: an `exits:` object of objects.yml whose surface is not 7solid01.
- `exits.door_leaf`: a door whose click leaves the map (its wiring event has an `exit` effect) with a front picture
  that is not 7solid01 (a shut door that is really an exit; the gated doors that throw the party out on a failed
  check are listed in SPECIAL until their design is settled).
- `exits.hidden` / `switches.hidden` (on the built map, the Discord report of 2026-11-23: "How do I leave the Orc
  Dungeon without going to Mount Firestone?"): the face of an `exits:` or `switches:` object with another face of the
  map standing in front of it, looking the same way, within 64 over at least half of it (a rough wall's joints stand
  up to 48 into the room in front of an object hung on the plan's wall line), so nothing reaches it with a click.
  `tools/xeen/cave_shape.py` (`flat_behind_panels`) keeps a rough wall flat behind such objects.
SPECIAL lists the exits kept on purpose (ladders, grates, water, sky and cloud ways, a throne): one line of reason
each; add a line there, never a texture to the rule. Exit 1 on an error.
"""
import glob
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BRIEFS = os.path.join(ROOT, 'devdocs', 'xeen', 'briefs')
BLACK = '7solid01'
SPECIAL = {
    ('dd01', 'exit:hatch'): 'a ladder up through the hatch (MM6 d1ladder exits)',
    ('dd18', 'exit:shaft'): 'a ladder up the shaft',
    ('dd20', 'exit:shaft'): 'a ladder up the jetty shaft',
    ('dd01', 'exit:outfall'): 'the outfall grate the sewer drains through',
    ('dd26', 'exit:grate'): 'the iron grate at the stair head',
    ('xd01', 'exit:river'): 'the river itself (water you swim out by)',
    ('xd04', 'exit:cloud_stair'): 'the stair of cloud to the sky (X8)',
    ('p1', 'exit:way_up'): "the crater's way up on the Plane of Fire",
}


def load(path):
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}


def front_textures(door):
    out = []
    if door.get('surface'):
        out.append(door['surface'].get('texture'))
    for row in door.get('pictures') or []:
        for picture in row:
            out.append(picture.get('texture'))
    return out


def check(key):
    errors = []
    l4 = os.path.join(BRIEFS, key, 'L4')
    objects = load(os.path.join(l4, 'objects.yml'))
    wiring = load(os.path.join(l4, 'wiring.yml'))
    for ex in objects.get('exits') or []:
        texture = (ex.get('surface') or {}).get('texture')
        if texture != BLACK and (key, ex['id']) not in SPECIAL:
            errors.append(f'error exits.not_black: {key} {ex["id"]} shows {texture}, not the black exit face {BLACK}')
    leaving = set()
    for event in wiring.get('events') or []:
        source = str(event.get('source', ''))
        if source.startswith('door:') and any(isinstance(e, dict) and ('exit' in e or 'leave' in e)
                                              for e in (event.get('effects') or []) + (event.get('else_effects') or [])):
            leaving.add(source)
    for door in objects.get('doors') or []:
        if door.get('id') in leaving and (key, door['id']) not in SPECIAL:
            bad = [t for t in front_textures(door) if t != BLACK]
            if bad:
                errors.append(f'error exits.door_leaf: {key} {door["id"]} leads out of the map but shows {bad}')
    return errors


OYMAP = os.path.join(ROOT, 'openyamm-studio', 'build-xeen', 'oymap')
COVER_DEPTH = 64.0


def _ray_hits(origins, direction, poly, normal):
    """For each origin, the distance along `direction` to the planar polygon, or inf."""
    denom = float(np.dot(normal, direction))
    out = np.full(len(origins), np.inf)
    if abs(denom) < 1e-6:
        return out
    t = (poly[0] - origins) @ normal / denom
    axis = int(np.argmax(np.abs(normal)))
    i, j = [k for k in range(3) if k != axis]
    for n, (o, tn) in enumerate(zip(origins, t)):
        if tn <= 0.5 or tn > COVER_DEPTH:
            continue
        x, y = o[i] + direction[i] * tn, o[j] + direction[j] * tn
        inside = False
        for a in range(len(poly)):
            x1, y1, x2, y2 = poly[a][i], poly[a][j], poly[(a + 1) % len(poly)][i], poly[(a + 1) % len(poly)][j]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                inside = not inside
        if inside:
            out[n] = tn
    return out


def check_hidden(key, assets):
    """exits.hidden / switches.hidden on the built map under `assets`."""
    l4 = os.path.join(BRIEFS, key, 'L4')
    project = load(os.path.join(l4, 'project.yml'))
    stem = project.get('id')
    path = os.path.join(assets, 'worlds', 'xeen', 'maps', f'{stem}.blv')
    if project.get('kind') != 'indoor' or not os.path.exists(path):
        return []
    objects = load(os.path.join(l4, 'objects.yml'))
    wiring = load(os.path.join(l4, 'wiring.yml'))
    lock = load(os.path.join(l4, 'ids.lock.yml'))
    numbers = {k: v for section in lock.values() if isinstance(section, dict) for k, v in section.items()}
    kind_of = {o['id']: kind for kind in ('exits', 'switches') for o in objects.get(kind) or [] if 'id' in o}
    wanted = {}
    for event in wiring.get('events') or []:
        source = event.get('source')
        if source in kind_of and isinstance(numbers.get(event.get('id')), int):
            wanted[numbers[event['id']]] = source
    if not wanted:
        return []
    with tempfile.NamedTemporaryFile(suffix='.json') as t:
        subprocess.run([OYMAP, 'export', path, '--world', 'xeen', '--assets', assets, '--out', t.name], check=True,
                       capture_output=True)
        data = json.load(open(t.name))
    m = data['map']
    vertices = np.array(m['vertices'], float)
    faces = m['faces']
    solid = [(i, vertices[f['vertices']], np.array(f['plane_normal'], float) / 65536) for i, f in enumerate(faces)
             if not f.get('is_portal') and not f['attributes'] & 0x2000]
    boxes_lo = np.array([p.min(0) for _, p, _ in solid]) - 1
    boxes_hi = np.array([p.max(0) for _, p, _ in solid]) + 1
    # each clicked thing's faces: it is hidden when every one of them is (a lever's handle has a back to its post)
    result = {}
    for i, f in enumerate(faces):
        source = wanted.get(f['cog_triggered'])
        if not source:
            continue
        poly = vertices[f['vertices']]
        normal = np.array(f['plane_normal'], float) / 65536
        centre = poly.mean(0)
        samples = [centre] + [centre + s * ((1 - u) * (poly[k] - centre) + u * (poly[(k + 1) % len(poly)] - centre))
                              for k in range(len(poly)) for s in (0.25, 0.5, 0.75) for u in (0.0, 0.5)]
        origins = np.array(samples) + normal * 0.5
        lo = np.minimum(origins.min(0), (origins + normal * COVER_DEPTH).min(0))
        hi = np.maximum(origins.max(0), (origins + normal * COVER_DEPTH).max(0))
        near = np.nonzero(((boxes_hi >= lo) & (boxes_lo <= hi)).all(1))[0]
        best = np.full(len(origins), np.inf)
        by = set()
        for n in near:
            j, p, nj = solid[n]
            # only a face that looks the same way: a wall standing in front, not the back of a block it stands on;
            # never a face of the same clicked thing
            if (j == i or faces[j]['cog_triggered'] == f['cog_triggered']
                    or float(np.dot(nj, normal)) < 0.7):
                continue
            d = _ray_hits(origins, normal, p, nj)
            closer = d < best
            if closer.any():
                best = np.where(closer, d, best)
                by.add(faces[j]['texture'])
        covered = int(np.isfinite(best).sum())
        hidden = covered * 2 >= len(origins)
        entry = result.setdefault(source, {'hidden': True, 'faces': [], 'by': set(), 'near': np.inf,
                                           'event': f['cog_triggered']})
        entry['hidden'] = entry['hidden'] and hidden
        entry['faces'].append(i)
        if hidden:
            entry['by'] |= by
            entry['near'] = min(entry['near'], float(best[np.isfinite(best)].min()))
    errors = []
    for source, e in result.items():
        if e['hidden']:
            errors.append(f'error {kind_of[source]}.hidden: {key} {source} (faces {e["faces"]}, event {e["event"]}) '
                          f'lies behind {sorted(e["by"])}, {e["near"]:.0f} in front of it: no click reaches it')
    return errors


def main():
    args = sys.argv[1:]
    assets = os.path.join(ROOT, 'assets_dev')
    if '--assets' in args:
        n = args.index('--assets')
        assets = os.path.abspath(args[n + 1])
        del args[n:n + 2]
    built = '--no-built' not in args
    args = [a for a in args if a != '--no-built']
    keys = args or sorted(os.path.basename(os.path.dirname(p)) for p in glob.glob(f'{BRIEFS}/*/L4'))
    errors = [e for key in keys for e in check(key) + (check_hidden(key, assets) if built else [])]
    for e in errors:
        print(e)
    print(f'{len(keys)} projects, {len(errors)} errors; {len(SPECIAL)} special exits kept')
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
