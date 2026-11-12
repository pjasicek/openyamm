#!/usr/bin/env python3
"""One composer experiment for a gait-rollout clip (anim-stream fixes, 2026-11-11). Run from the fix project, which
holds a copy of the package's scripts/ (compose_gait.py), its jobs/ and work/ inputs.

    exp_job.py <pre_gait.glb> <job.json> <tag> '<python dict merged recursively into the job; None deletes a key>'
               [--audit-clips Standing,Jog] [--probe 'cmd {glb} {clip}']

Writes work/exp/<tag>.json and work/exp/<tag>.glb (the pre-gait GLB plus this one clip), then prints motion_audit's
region bad shares for the job's clip (and any --audit-clips) and the probe's last line.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'claude_shared'))
import motion_audit  # noqa: E402


def merge(base, update):
    for key, value in update.items():
        if value is None:
            base.pop(key, None)
        elif isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = value
    return base


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('pre')
    p.add_argument('job')
    p.add_argument('tag')
    p.add_argument('update', nargs='?', default='{}')
    p.add_argument('--audit-clips', default='')
    p.add_argument('--probe')
    args = p.parse_args()
    out = Path('work/exp')
    out.mkdir(parents=True, exist_ok=True)
    job = merge(json.loads(Path(args.job).read_text()), eval(args.update))
    jpath = out / f'{args.tag}.json'
    jpath.write_text(json.dumps(job))
    glb = out / f'{args.tag}.glb'
    log = out / f'{args.tag}.log'
    with open(log, 'w') as f:
        r = subprocess.run([sys.executable, 'scripts/compose_gait.py', args.pre, str(glb), str(jpath)], stdout=f,
                           stderr=subprocess.STDOUT)
    if r.returncode:
        print(args.tag, 'FAILED', log.read_text()[-600:])
        return
    a = motion_audit.Audit(glb)
    clips = [c for c in args.audit_clips.split(',') if c] + [job['clip']]
    parts = []
    for c in clips:
        res, _ = a.clip(c, 30)
        parts.append(c + ' ' + ' '.join(f'{k}:{v["bad_pct"]}' for k, v in res['deform'].items()))
    line = f'{args.tag} | ' + ' | '.join(parts)
    if args.probe:
        pr = subprocess.run(args.probe.format(glb=glb, clip=job['clip']), shell=True, capture_output=True, text=True)
        line += ' | ' + (pr.stdout.strip().splitlines() or [pr.stderr.strip()[-200:]])[-1]
    print(line)


if __name__ == '__main__':
    main()
