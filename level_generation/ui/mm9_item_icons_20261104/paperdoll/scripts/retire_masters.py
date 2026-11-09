"""Sets master jobs up for a fresh generation after their target changed (pieces.yml edited):

    python3 scripts/retire_masters.py <tag> <piece> t<N> [t<N> ...]

Moves each job's raw generations, runs.json and codex log into raw/old_<tag>/ (kept for comparison), re-prepares the
piece so the job inputs follow pieces.yml, and drops the piece's picks.json so the finisher fits it again.
"""
import sys

import mm9_paperdoll as M

P = M.P


def main():
    tag, name, *types = sys.argv[1:]
    for key in types:
        raw = P.WORK / name / key / 'raw'
        old = raw / f'old_{tag}'
        old.mkdir(exist_ok=True)
        for file in sorted(raw.iterdir()):
            if file.is_file():
                file.rename(old / file.name)
    M.design(name)
    P.prepare(name)
    picks = P.WORK / name / 'review/picks.json'
    if picks.exists():
        picks.rename(picks.with_name('picks_before_' + tag + '.json'))


if __name__ == '__main__':
    main()
