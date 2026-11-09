"""Candidates, picks, fit and review of finished pieces in one step (the full pass of 2026-11-05).

    python3 scripts/finish_piece.py <piece> [...] [--pick <piece>:t<N>=gen_<n>.png ...]

Per master doll type the pick is, in order: an explicit --pick, the generation an earlier fit used
(work/<piece>/fitted/fit.json, so the reviewed prototype picks stay), else the generation the fitter had to fill
least. A piece with `same_art_as` in pieces.yml reuses that piece's generations (its targets must be identical).
Writes work/<piece>/review/picks.json and prints one line per piece: picks, fill shares and the review checks.
"""
import json
import shutil
import sys

import mm9_paperdoll as M

P = M.P


def fill_share(raw, target):
    _, report = P.fitter.fit_generated_art(P.Image.open(raw), target, None, 242, 2, 150, 'hybrid', 'magenta', True)
    return report['filled_pixels'] / report['target_alpha_pixels']


def borrow(name, source):
    """Copy the source piece's generations into this piece's jobs, after checking the targets are identical."""
    for job in sorted((P.WORK / name).glob('t[0-9]')):
        other = P.WORK / source / job.name
        if P.sha256(job / 'target.png') != P.sha256(other / 'target.png'):
            raise SystemExit(f'{name} {job.name}: target differs from {source}')
        for raw in sorted((other / 'raw').glob('gen_*.png')):
            shutil.copy2(raw, job / 'raw' / raw.name)


def finish(name, explicit):
    piece = P.pieces()[name]
    if piece.get('same_art_as'):
        borrow(name, piece['same_art_as'])
    earlier = {}
    fit_json = P.WORK / name / 'fitted/fit.json'
    if fit_json.exists():
        for key, record in json.loads(fit_json.read_text()).items():
            if 'shared_from' not in record.get('fit', {}):
                earlier[key] = record['raw'].rsplit('/', 1)[1]
    picks, fills = {}, {}
    for doll_type in P.master_types(piece):
        job = P.WORK / name / f't{doll_type}'
        target = P.Image.open(job / 'target.png')
        shares = {raw.name: round(100 * fill_share(raw, target), 1) for raw in sorted((job / 'raw').glob('gen_*.png'))}
        if not shares:
            raise SystemExit(f'{name} t{doll_type}: no generations')
        key = f't{doll_type}'
        picks[key] = explicit.get((name, key)) or earlier.get(key) or min(shares, key=shares.get)
        fills[key] = shares
    P.candidates(name)
    P.fit(name, [f'{key}={raw}' for key, raw in picks.items()])
    P.review(name)
    checks = json.loads((P.WORK / name / 'review/checks.json').read_text())
    (P.WORK / name / 'review/picks.json').write_text(json.dumps({'picks': picks, 'fill_percent': fills}, indent=2) + '\n')
    bad = {key: {k: v for k, v in check.items() if v and k != 'partial_alpha' and k != 'pair_common_rgba_differences'}
           for key, check in checks.items()}
    bad = {key: value for key, value in bad.items() if value}
    summary = ' '.join(f"{key}={raw}({fills[key][raw]}%)" for key, raw in picks.items())
    print('PIECE', name, piece['name'], summary, 'ISSUES' if bad else 'ok', bad if bad else '', flush=True)


def main():
    arguments = sys.argv[1:]
    explicit = {}
    names = []
    while arguments:
        argument = arguments.pop(0)
        if argument == '--pick':
            spec = arguments.pop(0)
            piece, rest = spec.split(':', 1)
            key, raw = rest.split('=', 1)
            explicit[(piece, key)] = raw
        else:
            names.append(argument)
    for name in names:
        finish(name, explicit)


if __name__ == '__main__':
    main()
