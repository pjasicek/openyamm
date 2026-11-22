#!/usr/bin/env python3
"""DD-25 test rows: A4's tools/xeen/gen_towns.py run with source/towns/dd25.yml taken as built (its `planned` flag
dropped in memory only), and its rows for houses 4701-4706 (house_data.txt, house_animations.txt) and the house column
of NPCs 5401-5406 (npc.txt) written into the scratch root's COPY of the world's tables. Nothing under assets_dev is
touched. `house_rows.py <root>`; prints what it changed. A4 writes the real rows when it drops `planned: true`."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import sys
from pathlib import Path

R = Path(_REPO_ROOT)
sys.path.insert(0, str(R / 'tools/xeen'))
import gen_towns  # noqa: E402

HOUSES = {str(h) for h in range(4701, 4707)}
NPCS = {str(n) for n in range(5401, 5407)}


def main():
    root = Path(sys.argv[1])
    tables = root / 'worlds/xeen/data_tables'
    for f in ('house_data.txt', 'house_animations.txt', 'npc.txt'):
        if (tables / f).stat().st_nlink != 1:
            raise SystemExit(f'refusing: {tables / f} is hard-linked')
    towns = gen_towns.load_towns()
    for t in towns:
        if t.get('key') == 'DD-25':
            t.pop('planned', None)
    out = gen_towns.Generator(towns).generate()
    for name in ('house_data.txt', 'house_animations.txt'):
        new = {row[0]: row for row in out[name] if row and row[0] in HOUSES}
        lines = (tables / name).read_text().splitlines()
        kept = [ln for ln in lines if ln.split('\t')[0] not in HOUSES]
        kept += ['\t'.join(new[k]) for k in sorted(new)]
        (tables / name).write_text('\n'.join(kept) + '\n')
        print(name, 'rows', sorted(new))
    gen_npc = {row[0]: row for row in out['npc.txt'] if row and row[0] in NPCS}
    lines = (tables / 'npc.txt').read_text().splitlines()
    res = []
    for ln in lines:
        cells = ln.split('\t')
        if cells[0] in gen_npc:
            cells[6] = gen_npc[cells[0]][6]
            print('npc', cells[0], cells[1], 'house', cells[6])
            ln = '\t'.join(cells)
        res.append(ln)
    (tables / 'npc.txt').write_text('\n'.join(res) + '\n')


if __name__ == '__main__':
    main()
