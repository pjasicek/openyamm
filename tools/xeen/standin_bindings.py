#!/usr/bin/env python3
"""Actor-model bindings for the Xeen descriptors whose family has no model of its own yet (for S, the 3D lane).

Each Xeen monster row has its own descriptor ("Xeen Goblin A", "Xeen Gettlewaithe"), so a map_stats slot can name
the family; a descriptor draws as a 3D model only through a binding in a world's models/actors.yml, and S owns
assets_dev/worlds/xeen/models/. This prints (or writes with --out) one binding per Xeen descriptor, copied from the
stand-in descriptor's installed binding (source/monsters.yml `stand_in`, the `model_stand_in` of ROADMAP 5.3), with
the descriptor and any scale_reference renamed. S merges the entries into worlds/xeen/models/actors.yml and replaces
a family's entries when its colour tiers or new model exist. Families with `sprites:` instead of `stand_in:` are
skipped: S has bound them to their own model, so they have real bindings (the fragment lists their keys in a comment).

    python3 tools/xeen/standin_bindings.py --out /path/to/fragment.yml [--family goblins ...]

A stand-in from MM9's actors.yml carries that file's top-level keys (attack_timing: clip, gait: intent, ...) only in
MM9's file: the fragment lists such entries under a comment so S can decide.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import xeenlib  # noqa: E402


def installed_bindings():
    """descriptor -> (binding dict, world id) from every world's actors.yml but Xeen's."""
    bindings = {}
    for path in sorted(xeenlib.WORLDS.glob('*/models/actors.yml')):
        world = path.parent.parent.name
        if world == xeenlib.WORLD_ID:
            continue
        for entry in (xeenlib.load_yaml(path) or {}).get('actors') or []:
            bindings.setdefault(entry['descriptor'], (entry, world))
    return bindings


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--family', action='append', default=[],
                        help='only these monsters.yml families (`characters`: the named characters)')
    args = parser.parse_args()

    source = xeenlib.load_yaml(xeenlib.SOURCE / 'monsters.yml') or {}
    bindings = installed_bindings()
    entries, mm9_entries, missing, own_model = [], [], [], []

    def add_pairs(pairs, rename, owner):
        for descriptor, stand_in_descriptor in pairs:
            found = bindings.get(stand_in_descriptor)
            if found is None:
                missing.append(f'{descriptor} (stand-in {stand_in_descriptor} has no binding)')
                continue
            binding, world = found
            entry = dict(binding)
            entry['descriptor'] = descriptor
            # A tier sized from its family's A tier is sized from the Xeen A tier; any other reference stays.
            if entry.get('scale_reference') in rename:
                entry['scale_reference'] = rename[entry['scale_reference']]
            (mm9_entries if world == 'mm9' else entries).append(entry)

    for family_key, family in (source.get('families') or {}).items():
        if args.family and family_key not in args.family:
            continue
        if family.get('sprites'):
            own_model.append(family_key)
            continue
        stand_in = family['stand_in']
        rename = {f'{stand_in} {letter}': f"{family['picture']} {letter}" for letter in 'ABC'}
        pairs = []
        for letter, tier in (family.get('tiers') or {}).items():
            pairs.append((f"{family['picture']} {letter}", f"{stand_in} {tier.get('look', letter)}"))
        for boss in family.get('bosses') or []:
            pairs.append((boss.get('picture') or f"Xeen {boss['name']}", f"{stand_in} {boss.get('look', 'C')}"))
        add_pairs(pairs, rename, family_key)

    # Named peaceful characters (monsters.yml `characters`): one descriptor each, its stand-in a descriptor name.
    for character in source.get('characters') or []:
        if args.family and 'characters' not in args.family:
            continue
        add_pairs([(character.get('picture') or f"Xeen {character['name']}", character['stand_in'])], {},
                  character['key'])

    text = ('# Stand-in bindings for the Xeen descriptors (tools/xeen/standin_bindings.py): copies of the installed\n'
            '# bindings of source/monsters.yml stand_in families, renamed. For S to merge into models/actors.yml.\n')
    text += xeenlib.dump_yaml({'actors': entries})
    if mm9_entries:
        text += ('\n# From MM9\'s actors.yml, whose top-level attack_timing: clip, fidget_variants and gait: intent these\n'
                 '# bindings were made for:\n' + xeenlib.dump_yaml({'actors_from_mm9': mm9_entries}))
    if missing:
        text += '\n# No installed binding to copy:\n' + ''.join(f'#   {line}\n' for line in missing)
    if own_model:
        text += '\n# Skipped, bound to their own model (`sprites:`): ' + ', '.join(own_model) + '\n'
    if args.out:
        args.out.write_text(text, encoding='utf-8')
        print(f'{len(entries) + len(mm9_entries)} bindings, {len(missing)} without one: {args.out}')
    else:
        print(text)


if __name__ == '__main__':
    main()
