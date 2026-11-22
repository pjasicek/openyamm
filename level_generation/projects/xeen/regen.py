#!/usr/bin/env python3
"""Regenerate the Map Studio project of a Xeen map (devdocs/xeen/briefs/<map>/) from its generator in this folder.

    python3 level_generation/projects/xeen/regen.py <map> [<map> ...]           # write the project files
    python3 level_generation/projects/xeen/regen.py --check <map> ...           # write, compare, put the files back
    python3 level_generation/projects/xeen/regen.py --check all                 # every map with a generator
    python3 level_generation/projects/xeen/regen.py --build <map>               # also build and run the playtest
                                                                                  writers that read the build

A run is: the map's generator steps (python, each through tools/heavy.sh 8), then `oymap fmt` on the levels they write.
Maps whose playtests are written from a build (the planes, X8, X9, D7) need --build: the L4 is built with
`tools/heavy.sh 8 oymap build` into output/studio_cal/<map>/build, then the writer runs and L4 is formatted again.
--check snapshots the brief folder first, reports every file that differs from the snapshot after the run, and copies
the snapshot back, so it never leaves a change behind. Work output stays in output/studio_cal/<map>/ (git-ignored).
See README.md in this folder for the per-map table.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.realpath(os.path.join(HERE, '../../..'))
OYMAP = os.path.join(REPO, 'openyamm-studio/build-xeen/oymap')
HEAVY = os.path.join(REPO, 'tools/heavy.sh')

# map -> (generator steps [[script, args...]], levels to format, levels the generator rewrites that stay as committed)
L4 = ['L4']
ALL = ['L1', 'L2', 'L3', 'L4']
UPPER = ['L2', 'L3', 'L4']
GEN_L4 = [['gen.py', 'L4']]
GEN = [['gen.py']]
MAPS = {}
for m in ('dd01 dd02 dd03 dd04 dd05 dd07 dd08 dd09 dd10a dd10b dd10c dd12 dd14 dd15 dd17 dd18 dd19 dd20 dd21 dd22 '
          'dd25 dd26 fd01 xd10 xd11 xd15 xd16').split():
    MAPS[m] = (GEN_L4, L4, [])
for m in ('dd06 dd11a dd11b dd11c dd13 dd16 dd23 dd24 fd02 fd03 fd04 xd07 xd08 xd13 xd14 xd18 xd19 xd22 xd23 xd24 '
          'xd25 xd26').split():
    MAPS[m] = (GEN, L4, [])
for m in ('d1', 'd2', 'd4', 'd5', 'd6', 'x5', 'x6', 'x7'):
    MAPS[m] = ([['gen.py', 'devdocs/xeen/briefs/' + m]], UPPER, [])
for m in ('d3', 'x2', 'x4'):
    MAPS[m] = ([['gen.py', 'devdocs/xeen/briefs/' + m]], ALL, [])
MAPS['x1'] = ([['gen.py', 'devdocs/xeen/briefs/x1/L4']], L4, [])
MAPS['x3'] = ([['gen_l1.py'], ['gen.py']], ALL, [])
MAPS['xd06'] = ([['gen.py'], ['gen_plan.py']], L4, ['L1', 'L2', 'L3'])
MAPS['xd09'] = (GEN, ALL, ['L1', 'L2', 'L3'])
MAPS['xd12'] = ([['emit.py', 'L4']], L4, [])
MAPS['xd17'] = (GEN, UPPER, [])
MAPS['xd21'] = ([['gen.py'], ['plan.py']], L4, ['L1', 'L2', 'L3'])
MAPS['xd27'] = ([['make_l3.py'], ['gen.py', '--l3'], ['gen.py']], ['L3', 'L4'], [])
for m in ('p1', 'p2', 'p3', 'p4'):
    MAPS[m] = (GEN, UPPER, [])
for m in ('p5', 'x8', 'x9', 'd7'):
    MAPS[m] = ([['gen.py'], ['gen_plan.py'], ['gen_objects.py']], UPPER, [])
# playtest writers that read a fresh build of L4 (--build): map -> (script, assets root for the build)
BUILD_TESTS = {'p1': 'assets_dev', 'p2': 'assets_dev', 'p3': 'assets_dev', 'p4': 'assets_dev',
               'p5': 'assets_dev', 'x8': 'assets_dev', 'x9': 'assets_dev', 'd7': 'assets_dev'}
# playtest writers that need no build (they read ids.lock.yml and the generator's own tables)
TESTS = {m: [['gen_tests.py']] for m in ('dd07', 'fd02', 'fd03', 'fd04', 'xd15', 'xd16', 'xd18', 'xd19')}
TESTS.update({m: [['tests.py']] for m in ('dd17', 'fd01')})
TESTS['xd17'] = [['gen_playtests.py']]
for m in ('d1', 'd2', 'd3', 'd4', 'd6', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7'):
    TESTS[m] = [['gen_hostility_%s.py' % m]]
TESTS['p1'] = [['../common/gen_daily.py', 'p1']]


def run(cmd):
    print('+', ' '.join(cmd), flush=True)
    return subprocess.run(cmd, cwd=REPO).returncode == 0


def fmt(brief, levels):
    for lv in levels:
        subprocess.run([OYMAP, 'fmt', os.path.join(brief, lv)], cwd=REPO, stdout=subprocess.DEVNULL)


def regen(m, build):
    steps, levels, keep = MAPS[m]
    brief = os.path.join(REPO, 'devdocs/xeen/briefs', m)
    kept = tempfile.mkdtemp(prefix='xeen_keep_')
    for lv in keep:
        shutil.copytree(os.path.join(brief, lv), os.path.join(kept, lv))
    ok = True
    for step in steps + TESTS.get(m, []):
        ok &= run([HEAVY, '8', sys.executable, os.path.join(HERE, m, step[0])] + step[1:])
    if m in ('p5', 'x8', 'x9', 'd7'):   # their L3 (and D7's L2) take the L4 / L1 atmosphere as it is
        shutil.copy(os.path.join(brief, 'L4/atmosphere.yml'), os.path.join(brief, 'L3/'))
        if m == 'd7':
            shutil.copy(os.path.join(brief, 'L1/atmosphere.yml'), os.path.join(brief, 'L2/'))
    fmt(brief, levels)
    if build and m in BUILD_TESTS:
        out = os.path.join(REPO, 'output/studio_cal', m, 'build')
        ok &= run([HEAVY, '8', OYMAP, 'build', os.path.join(brief, 'L4'), '--out', out, '--assets', BUILD_TESTS[m]])
        ok &= run([HEAVY, '8', sys.executable, os.path.join(HERE, m, 'gen_playtests.py')])
        fmt(brief, L4)
    for lv in keep:
        shutil.rmtree(os.path.join(brief, lv))
        shutil.copytree(os.path.join(kept, lv), os.path.join(brief, lv))
    shutil.rmtree(kept)
    return ok


def differences(a, b):
    """Relative paths that differ between two folder trees (.oymap, the studio's own state, left out)."""
    out = []
    cmp = filecmp.dircmp(a, b, ignore=['.oymap'])
    stack = [('', cmp)]
    while stack:
        rel, c = stack.pop()
        out += [os.path.join(rel, f) + ' (only before)' for f in c.left_only]
        out += [os.path.join(rel, f) + ' (new)' for f in c.right_only]
        out += [os.path.join(rel, f) for f in c.diff_files]
        out += [os.path.join(rel, f) for f in c.common_files
                if f not in c.diff_files and not filecmp.cmp(os.path.join(c.left, f), os.path.join(c.right, f), False)]
        stack += [(os.path.join(rel, k), v) for k, v in c.subdirs.items()]
    return sorted(set(out))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('maps', nargs='+', help="map keys (dd01, x1, ...) or 'all'")
    ap.add_argument('--check', action='store_true', help='compare with the files before the run and put them back')
    ap.add_argument('--build', action='store_true', help='also build L4 and run the writers that read the build')
    args = ap.parse_args()
    maps = sorted(MAPS) if args.maps == ['all'] else args.maps
    for m in maps:
        if m not in MAPS:
            sys.exit('%s: no generator (see README.md: the project files are the source)' % m)
    failed = []
    for m in maps:
        brief = os.path.join(REPO, 'devdocs/xeen/briefs', m)
        snap = None
        if args.check:
            snap = tempfile.mkdtemp(prefix='xeen_snap_%s_' % m)
            shutil.copytree(brief, os.path.join(snap, m), symlinks=True)
        ok = regen(m, args.build)
        if args.check:
            diff = differences(os.path.join(snap, m), brief)
            shutil.rmtree(brief)
            shutil.copytree(os.path.join(snap, m), brief, symlinks=True)
            shutil.rmtree(snap)
            print('%s: %s' % (m, 'identical' if not diff and ok else
                              ('steps failed; ' if not ok else '') + 'differs: ' + ', '.join(diff)), flush=True)
            if diff or not ok:
                failed.append(m)
        elif not ok:
            failed.append(m)
    if failed:
        sys.exit('not reproduced or failed: ' + ' '.join(failed))


if __name__ == '__main__':
    main()
