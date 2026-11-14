#!/usr/bin/env python3
"""Put the generated textures into the three Xeen dungeon projects (L4): exact swaps, each counted.

    retex.py [xd01 xd02 xd03] [--dry-run]

Each swap is (file, old, new, expected count); a count that differs stops the run before anything is written. The
projects' files before the change are kept in output/studio_cal/<xd>/textures_gen/backup/ (first run only)."""
import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIEFS = ROOT / 'devdocs/xeen/briefs'


def gong_slabs():
    """The great gong: six slabs (bases 480 to 640, widths 96 to 192) make one 192 x 192 disc. The studio build in
    use has no surface `offset`, so each slab's side shows its own strip of the one gong picture (xngong, cut by
    strips.py into xngong1, the top strip, to xngong6, the bottom), stretched once over it; ends and tops show the
    gong's bronze at scale 1.5."""
    swaps = []
    for index, (width, base) in enumerate(((96, 480), (160, 512), (192, 544), (192, 576), (160, 608), (96, 640))):
        old_surface = '{texture: ctflor5, size: [128, 128]}'
        side = f'{{texture: xngong{6 - index}, size: [128, 32], fit: true}}'
        edge = '{texture: xngong, size: [128, 128], scale: 1.5}'
        swaps.append((f'size: [{width}, 12], rise: 32, surface: {old_surface}, end_surface: {old_surface}, '
                      f'top_surface: {old_surface}, base: {base}',
                      f'size: [{width}, 12], rise: 32, surface: {side}, end_surface: {edge}, top_surface: {edge}, '
                      f'base: {base}'))
    return swaps


SWAPS = {
    'xd01': [
        ('L4/rooms.yml', "surface: {texture: sign01-1, size: [256, 128], fit: true}, notes: Joe's hand-painted sign",
         "surface: {texture: xnjoesign, size: [256, 128], fit: true}, notes: Joe's hand-painted sign", 1),
        ('L4/rooms.yml', "height: 128, surface: {texture: sign01-1, size: [256, 128], fit: true}}",
         "height: 128, surface: {texture: xnnotice, size: [128, 128], fit: true}}", 1),
        ('L4/rooms.yml', "surface: {texture: sign01-2, size: [128, 32], scale: 1.5}",
         "surface: {texture: xnheartsgn, size: [128, 32], fit: true}", 1),
        ('L4/rooms.yml', "surface: {texture: sign01-3, size: [128, 32], scale: 1.25}",
         "surface: {texture: xnfeedsgn, size: [128, 32], fit: true}", 1),
        ('L4/rooms.yml', "surface: {texture: sign06-1, size: [128, 256], fit: true}, notes: \"Joe's hand-painted house",
         "surface: {texture: xnrules, size: [128, 256], fit: true}, notes: \"Joe's hand-painted house", 1),
        ('L4/rooms.yml', "surface: {texture: sign06-1, size: [128, 256], fit: true}, notes: Joe's hand-painted 'Pest",
         "surface: {texture: xnpestntc, size: [128, 256], fit: true}, notes: Joe's hand-painted 'Pest", 1),
        ('L4/rooms.yml', "surface: {texture: warnsign, size: [256, 128], fit: true}, notes: \"KEEP OUT",
         "surface: {texture: xnkeepout, size: [256, 128], fit: true}, notes: \"KEEP OUT", 1),
        ('L4/rooms.yml', "surface: {texture: gt003b, size: [64, 64], fit: true}}",
         "surface: {texture: xnshutter, size: [256, 256], fit: true}}", 1),
        ('L4/rooms.yml', "surface: {texture: 7winerack, size: [128, 256]}",
         "surface: {texture: xntonics, size: [128, 256]}", 1),
        # The six tanks (rises of 64 and the cracked one of 48 on the tank shelf); the drain pool, gutter and trough
        # keep their slime.
        ('L4/rooms.yml', re.compile(r"(\{rise: (?:64|48), surface: )\{texture: 7slimywtr, size: \[128, 128\]\}"),
         r"\1{texture: xnbugtank, size: [64, 128], fit: true}", 6),
        ('L4/rooms.yml', "tanks of slime water (MM7 7slimywtr, a stand-in for glass: see NOTES.md, textures to generate)",
         "glass tanks of doom bugs in slime (xnbugtank, generated: see NOTES.md, generated textures)", 1),
        ('L4/objects.yml', "surface: {texture: gcrydoor, size: [128, 256], fit: true}",
         "surface: {texture: xnheartgt, size: [128, 256], fit: true}", 1),
        ('L4/objects.yml', "The gate painted red with a big flower for a heart (MM8 gcrydoor, the nearest painted gate "
                           "there is: a stand-in, see NOTES.md textures to generate)",
         "The plank gate painted red with a big white heart (xnheartgt, generated: see NOTES.md, generated textures)",
         1),
    ],
    'xd02': [
        # The six gold veins: each in its wall's own rock.
        ('L4/objects.yml', re.compile(r"off: \{texture: c1gold, size: \[256, 256\]\}\n(\s+)on: t3ll5"),
         r"off: {texture: xngold5, size: [256, 256]}\n\1on: t3ll5", 2),
        ('L4/objects.yml', re.compile(r"off: \{texture: c1gold, size: \[256, 256\]\}\n(\s+)on: t3ll6"),
         r"off: {texture: xngold6, size: [256, 256]}\n\1on: t3ll6", 3),
        ('L4/objects.yml', re.compile(r"off: \{texture: c1gold, size: \[256, 256\]\}\n(\s+)on: crstont"),
         r"off: {texture: xngoldcr, size: [256, 256]}\n\1on: crstont", 1),
        # Cart sides: the trestle car's and the east cart's side boards, the standing and tipped carts.
        ('L4/objects.yml', "height: 40, surface: {texture: ch1topb, size: [64, 64], fit: true}",
         "height: 40, surface: {texture: xncartsd, size: [128, 64], fit: true}", 4),
        ('L4/rooms.yml', re.compile(r"(rise: (?:72|144), surface: )\{texture: ch1topb, size: \[64, 64\], fit: true\}"),
         r"\1{texture: xncartsd, size: [128, 64], fit: true}", 6),
        ('L4/rooms.yml', re.compile(r"(\[\d+, \d+\]\], top_surface: )\{texture: ch1topb, size: \[64, 64\], fit: true\}"
                                    r"(, notes: \"?(?:An ore cart off|An abandoned cart on|The derailed cart))"),
         r"\1{texture: xncartsd, size: [128, 64], fit: true}\2", 3),
        # Pool basins and the gold pool's water.
        ('L4/rooms.yml', "{id: platform:blue_pool, rise: 28, surface: {texture: crstont, size: [256, 256]}",
         "{id: platform:blue_pool, rise: 28, surface: {texture: xnbasblu, size: [128, 128]}", 1),
        ('L4/rooms.yml', "{id: platform:gold_pool, rise: 28, surface: {texture: crstont, size: [256, 256]}",
         "{id: platform:gold_pool, rise: 28, surface: {texture: xnbasgld, size: [128, 128]}", 1),
        ('L4/rooms.yml', "top_surface: {texture: orertlga, size: [256, 256]}",
         "top_surface: {texture: xngoldwtr, size: [128, 128]}", 1),
        ('L4/rooms.yml', "{id: platform:red_pool, rise: 28, surface: {texture: crstont, size: [256, 256]}",
         "{id: platform:red_pool, rise: 28, surface: {texture: xnbasred, size: [128, 128]}", 1),
        ('L4/rooms.yml', "{id: platform:green_pool, rise: 28, surface: {texture: d7trim8, size: [64, 64]}",
         "{id: platform:green_pool, rise: 28, surface: {texture: xnbasgrn, size: [128, 128]}", 1),
        ('L4/rooms.yml', re.compile(r"(- id: level:blue_pool\n(?:.*\n){2,3}?\s+)edge: \{texture: crstont, size: \[256, 256\]\}"
                                    r"\n(\s+)surface: \{texture: crstont, size: \[256, 256\]\}"),
         r"\1edge: {texture: xnbasblu, size: [128, 128]}\n\2surface: {texture: xnbasblu, size: [128, 128]}", 1),
        ('L4/rooms.yml', re.compile(r"(- id: level:gold_pool\n(?:.*\n){2,3}?\s+)edge: \{texture: crstont, size: \[256, 256\]\}"
                                    r"\n(\s+)surface: \{texture: crstont, size: \[256, 256\]\}"),
         r"\1edge: {texture: xnbasgld, size: [128, 128]}\n\2surface: {texture: xnbasgld, size: [128, 128]}", 1),
        ('L4/rooms.yml', re.compile(r"(- id: level:red_pool\n(?:.*\n){2,3}?\s+)edge: \{texture: crstont, size: \[256, 256\]\}"
                                    r"\n(\s+)surface: \{texture: crstont, size: \[256, 256\]\}"),
         r"\1edge: {texture: xnbasred, size: [128, 128]}\n\2surface: {texture: xnbasred, size: [128, 128]}", 1),
        ('L4/rooms.yml', re.compile(r"(- id: level:green_pool\n(?:.*\n){2,3}?\s+)edge: \{texture: d7trim8, size: \[64, 64\]\}"
                                    r"\n(\s+)surface: \{texture: d7trim8, size: \[64, 64\]\}"),
         r"\1edge: {texture: xnbasgrn, size: [128, 128]}\n\2surface: {texture: xnbasgrn, size: [128, 128]}", 1),
        # Tally slates, chalk mark, the clan's warning, web, the hoist's grille, iron.
        ('L4/rooms.yml', "surface: {texture: sign22, size: [256, 64]}", "surface: {texture: xntally, size: [256, 128]}",
         4),
        ('L4/rooms.yml', "surface: {texture: runeeyvlij, size: [64, 64], fit: true}",
         "surface: {texture: xnchalk, size: [64, 64], fit: true}", 1),
        ('L4/rooms.yml', "surface: {texture: warnsign, size: [256, 128], fit: true}",
         "surface: {texture: xnclansgn, size: [256, 128], fit: true}", 1),
        ('L4/objects.yml', "{texture: web32n735s, size: [128, 128]}", "{texture: xnweb, size: [128, 128]}", 3),
        ('L4/objects.yml', re.compile(r"(id: door:hoist_gate\n(?:.*\n){4}\s+)surface: \{texture: d2ceil1, size: \[256, 256\], fit: true\}"
                                      r"\n(\s+)back_surface: \{texture: d2ceil1, size: \[256, 256\], fit: true\}"),
         r"\1surface: {texture: xngrille, size: [128, 256], fit: true}\n\2back_surface: {texture: xngrille, size: [128, 256], fit: true}",
         1),
        ('L4/rooms.yml', "{texture: ch004i, size: [64, 64]}", "{texture: xnrustirn, size: [64, 64]}", None),
        ('L4/objects.yml', "{texture: ch004i, size: [64, 64]}", "{texture: xnrustirn, size: [64, 64]}", None),
    ],
    'xd03': [
        ('L4/rooms.yml', "{texture: crstont, size: [256, 256]}", "{texture: xnquartz, size: [256, 256]}", None),
        ('L4/rooms.yml', "edge: {texture: d3ystlwl, size: [256, 256], fit: true}",
         "edge: {texture: xnquartzcv, size: [256, 256], fit: true}", 1),
        ('L4/objects.yml', "surface: {texture: d3ystlwl, size: [256, 256], fit: true}",
         "surface: {texture: xnquartzcv, size: [256, 256], fit: true}", 1),
        *[('L4/rooms.yml', old, new, 1) for old, new in gong_slabs()],
        ('L4/rooms.yml', "surface: {texture: ctceil3, size: [128, 128], fit: true}",
         "surface: {texture: xncrest, size: [128, 128], fit: true}", 1),
        ('L4/rooms.yml', "{texture: orfyrlga, size: [256, 256]}", "{texture: xnslag, size: [256, 256]}", 2),
        ('L4/wiring.yml', "to: orfyrlga", "to: xnslag", 2),
    ],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('maps', nargs='*', default=['xd01', 'xd02', 'xd03'])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    for key in args.maps:
        project = BRIEFS / key
        texts = {}
        for relative, old, new, expected in SWAPS[key]:
            path = project / relative
            text = texts.get(relative) or path.read_text()
            if isinstance(old, re.Pattern):
                text, count = old.subn(new, text)
            else:
                count = text.count(old)
                text = text.replace(old, new)
            label = old.pattern[:70] if isinstance(old, re.Pattern) else old[:70]
            print(f'{key} {relative}: {count} x {label}')
            if expected is not None and count != expected:
                sys.exit(f'{key}: expected {expected}, found {count}; nothing written')
            if expected is None and count == 0:
                sys.exit(f'{key}: nothing matched; nothing written')
            texts[relative] = text
        if args.dry_run:
            continue
        backup = ROOT / 'output/studio_cal' / key / 'textures_gen/backup'
        for relative, text in texts.items():
            path = project / relative
            saved = backup / relative
            if not saved.exists():
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, saved)
            path.write_text(text)
        print(key, 'written', sorted(texts))


if __name__ == '__main__':
    main()
