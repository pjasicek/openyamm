"""Runs every pending master job of the named pieces through Codex image workers, claimed at start.

    python3 scripts/codex_queue.py [--workers N] <piece> [...]     (default 16 workers; the user allows up to 16)

A job is pending when it has no raw/codex_run.log yet (a run started it before) and no raw/gen_1.png. Each worker
claims a job by creating its log exclusively, so two queues never run the same job.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import mm9_paperdoll as M


def claim(job):
    try:
        os.close(os.open(job / 'raw/codex_run.log', os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        return True
    except FileExistsError:
        return False


def work(job):
    if (job / 'raw/gen_1.png').exists() or not claim(job):
        return job, None
    return M.run_codex(job)


def main():
    arguments = sys.argv[1:]
    workers = 16
    if arguments[:1] == ['--workers']:
        workers = int(arguments[1])
        arguments = arguments[2:]
    jobs = [job for name in arguments for job in sorted((M.P.WORK / name).glob('t[0-9]'))
            if not (job / 'raw/codex_run.log').exists() and not (job / 'raw/gen_1.png').exists()]
    print('pending', len(jobs), flush=True)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for job, code in pool.map(work, jobs):
            if code is not None:
                print('DONE', job.relative_to(M.PROJECT), code,
                      sorted(p.name for p in (job / 'raw').glob('gen_*.png')), flush=True)


if __name__ == '__main__':
    main()
