#!/usr/bin/env python3
"""Identity check of the Xeen dungeons (D-89; lane A7, 2026-11-22).

For every brief whose L4 project.yml has `identity: {shape, family}`, compares the installed map with its assigned
shipped BLV (`family`, found in assets_dev/worlds/{mm8,mm7,mm6}/maps/<family>.blv):

- **family share:** the share of the installed map's textured area whose textures the family BLV also uses (D-89's
  drift: XD-23 never used d13, DD-11 not d43); below FAMILY_MIN it fails;
- **cave shape** (shape cave or mine): `oymap metrics`' cave_shape against the audit's numbers (floor uneven 30 %,
  ceiling spread 80, rough walls 18 %).

Usage: check_identity.py [<key> ...]   (default: every brief with an identity block). Exit 1 when any map fails.
Pictures meant once on the map's own story things (hides, banners, black exits) are counted outside the family, so
the share is a floor, not a target: 50 % keeps a map in its family's look.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

R = Path(__file__).resolve().parents[2]
OYMAP = R / 'openyamm-studio/build-xeen/oymap'
FAMILY_MIN = 0.5
CAVE = {'floor_uneven_share': 0.30, 'ceiling_spread': 80, 'wall_rough_share': 0.18}
# Maps whose look is carried on purpose by more than their `identity.family` (one line each, also in the map's NOTES):
# the family share is printed but does not fail.
EXCEPTIONS = {
    'xd09': "four homes, four families by design (7d24 stone, 6d16 wood, 6d18 iron, d37 diamond; 64 % together)",
    'dd09': "the bark is the world's own xdbark (A6), 35 %; 7d22's earth and roots below it (68 % together)",
    'dd14': "7d32's castle with 7d13's crypts as assigned (60 % together) and a grey block wall (`wall`) for the halls",
    # Orchestrator, 2026-11-22 (A7's DECIDE): the gremlin burrows stay dirt; only Hobstadt's hall is d43 cut stone.
    'dd11a': "dirt burrows by decision; d43's cut stone only in Hobstadt's hall (DD-11C)",
    'dd11b': "dirt burrows by decision; d43's cut stone only in Hobstadt's hall (DD-11C)",
    'dd11c': "dirt burrows by decision; d43's cut stone in Hobstadt's hall only",
}

# Cave-shape numbers just under the targets, accepted by the orchestrator (2026-11-22, A8's DECIDE): reported, not failed.
CAVE_EXCEPTIONS = {
    'dd10b': "mine drifts: floor 0.296 / rough 0.167 against 0.30 / 0.18, accepted",
    'dd10c': "the lava gallery's timbered mine: floor 0.16, accepted",
    'xd10': "deep reservoir rooms: rough 0.13, accepted",
}


def metrics(path, world, tmp):
    out = Path(tmp) / (Path(path).stem + f'.{world}.json')
    if not out.exists():
        subprocess.run([str(OYMAP), 'metrics', str(path), '--world', world, '--assets', str(R / 'assets_dev'),
                        '--out', str(out)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    return json.loads(out.read_text()) if out.exists() else None


def family_blv(name):
    hits = [p for w in ('mm8', 'mm7', 'mm6') for p in [R / f'assets_dev/worlds/{w}/maps/{name}.blv'] if p.exists()]
    return (hits[0], hits[0].parts[-3]) if hits else (None, None)


def main(keys):
    briefs = sorted((R / 'devdocs/xeen/briefs').glob('*/L4/project.yml'))
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        for pj in briefs:
            key = pj.parts[-3]
            if keys and key not in keys:
                continue
            ident = (yaml.safe_load(pj.read_text()) or {}).get('identity')
            if not ident:
                continue
            blv = R / f'assets_dev/worlds/xeen/maps/xeen_{key}.blv'
            if not blv.exists():
                print(f'{key}: not installed')
                continue
            m = metrics(blv, 'xeen', tmp)
            if not m:
                print(f'{key}: FAIL oymap metrics gave nothing')
                bad += 1
                continue
            notes = []
            fam, world = family_blv(str(ident.get('family')))
            if fam is None:
                notes.append(f"family {ident.get('family')}: no shipped BLV of that name")
                fail = True
            else:
                fm = metrics(fam, world, tmp)
                ftex = {t['name'].lower() for t in fm['palette']['by_area']} if fm else set()
                share = sum(t['share'] for t in m['palette']['by_area'] if t['name'].lower() in ftex)
                fail = share < FAMILY_MIN and key not in EXCEPTIONS
                notes.append(f"family {ident['family']} {share:.0%}"
                             + (f" (exception: {EXCEPTIONS[key]})" if share < FAMILY_MIN and key in EXCEPTIONS else ''))
            if ident.get('shape') in ('cave', 'mine'):
                cs = m.get('cave_shape') or {}
                low = [f'{k} {cs.get(k)}' for k, v in CAVE.items() if (cs.get(k) or 0) < v]
                notes.append('cave shape ' + (', '.join(low) + ' low' if low else 'ok')
                             + (f" (exception: {CAVE_EXCEPTIONS[key]})" if low and key in CAVE_EXCEPTIONS else ''))
                fail = fail or (bool(low) and key not in CAVE_EXCEPTIONS)
            bad += fail
            print(f"{key}: {'FAIL ' if fail else ''}{'; '.join(notes)}")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(set(sys.argv[1:])))
