"""Runs every prepared master job of the named pieces through Codex, four at a time across pieces.
Usage: python3 scripts/codex_all.py <piece> [...]   (jobs that already have raw/gen_1.png are skipped)"""
import sys
from concurrent.futures import ThreadPoolExecutor
import mm9_paperdoll as M

jobs = [job for name in sys.argv[1:] for job in sorted((M.P.WORK / name).glob('t[0-9]'))
        if not (job / 'raw/gen_1.png').exists()]
with ThreadPoolExecutor(max_workers=4) as pool:
    for job, code in pool.map(M.run_codex, jobs):
        print('DONE', job.relative_to(M.PROJECT), code, sorted(p.name for p in (job / 'raw').glob('gen_*.png')), flush=True)
