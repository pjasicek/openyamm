#!/usr/bin/env python3
"""Add the kits' new textures to the world's registry (assets_dev/worlds/xeen/source/textures.yml) and count the
budget. Entries of the kit projects (kit_textures/towns, kit_textures/landmarks) are rewritten on every run; the
other entries are kept as they are.

  register.py          rewrite the kit entries, print counts per kit and the world total against 450
"""
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REGISTRY = ROOT / 'assets_dev/worlds/xeen/source/textures.yml'
PROJECTS = [HERE / 'kit_textures/towns', HERE / 'kit_textures/landmarks']
KIT_MAPS = {'cloudside_town': ['X1', 'X2', 'X3', 'X4', 'X5'], 'darkside_town': ['D1', 'D4'], 'sandcaster': ['D3'],
            'royal_castle': ['XD-07', 'XD-13', 'DD-03', 'D1'], 'towers': ['XD-04', 'XD-11', 'XD-12', 'DD-02', 'DD-05',
                                                                          'DD-06', 'DD-07', 'DD-08'],
            'ancient': ['D6', 'D5', 'DD-15', 'DD-16', 'DD-17', 'DD-22', 'XD-19', 'FD-01']}
KEYS = ['X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'X7', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7']
MARK = '  # ---- kit textures (level_generation/xeen_art/register.py writes everything below) ----'


def maps_for(spec):
    found = [k for k in KEYS if re.search(rf'\b{k}\b', str(spec.get('where', '')))]
    return found or KIT_MAPS.get(spec['dungeon'], [])


def entry(name, spec, project):
    area = ' '.join(str(spec.get('where') or spec['what']).split())[:140].replace('"', "'")
    family = f"{spec['dungeon']}; {spec.get('family', '')}".replace('"', "'")
    return [f'  - name: {name}', f'    family: "{family}"', f'    area: "{area}"',
            f'    maps: [{", ".join(maps_for(spec))}]', f'    size: {list(spec["size"])}', f'    kind: {spec["kind"]}',
            f'    maker: codex image generation, {project.relative_to(ROOT)} (xtex.py --project), 2026-11-20',
            f'    source: {(project / "finished" / f"{name}.png").relative_to(ROOT)}',
            '    installed: world (2026-11-20)' if (ROOT / f'assets_dev/worlds/xeen/textures_x4/{name}.oytex').exists()
            else '    installed: no']


def main():
    text = REGISTRY.read_text()
    if MARK in text:
        text = text[:text.index(MARK)].rstrip('\n') + '\n'
    lines = [MARK]
    per_kit = {}
    for project in PROJECTS:
        specs = project / 'specs.yml'
        if not specs.exists():
            continue
        for name, spec in yaml.safe_load(specs.read_text())['textures'].items():
            if not (project / 'finished' / f'{name}.png').exists():
                continue
            lines += entry(name, spec, project)
            per_kit[spec['dungeon']] = per_kit.get(spec['dungeon'], 0) + 1
    REGISTRY.write_text(text + '\n'.join(lines) + '\n')
    data = yaml.safe_load(REGISTRY.read_text())
    names = [t['name'] for t in data['textures']]
    assert len(names) == len(set(names)), 'duplicate names'
    for kit, count in per_kit.items():
        print(f'{kit}: {count} new (cap 30)')
    print(f'world: {len(names)} new textures (cap 450)')


if __name__ == '__main__':
    main()
