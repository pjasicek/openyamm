#!/usr/bin/env python3
"""Rebase (A5, 2026-11-20): X1's playtest_hostility.yml from the shared hostility generator
(level_generation/projects/xeen/common/hostility/gen_hostility_tests.py, read only) with X1's kinds of the rebase: the placed zombies'
stand-in MM7 Ghoul (454-456) joins the foes, the placed kinds and the pair spawned side by side."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
R = _REPO_ROOT
src = open(f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py').read()
ns = {'__name__': 'gen_hostility_tests', '__file__': f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py'}
exec(compile(src[:src.index('\nfor key in sys.argv')], 'gen_hostility_tests.py', 'exec'), ns)
import sys
sys.path.insert(0, f'{R}/level_generation/projects/xeen/x1')
spec = dict(ns['SPECS']['x1'])
WORLD = '--world' in sys.argv     # the Xeen world: A2's rows (orcs, toads, skeletons; placed snakes and zombies)
if WORLD:
    # the fuller X1 (D-1.3, installed 2026-11-20): the placed pests and bats of the level 2-4 band join the foes
    # (11340 Doom Bug, 11380 Slime, 11390 Sewer Rat, 11300 Giant Bat; gen.py ROAD_PESTS)
    pests = [11340, 11380, 11390, 11300]
    spec['foes'] = [11030, 11031, 11032, 11450, 11451, 11452, 11240, 11241, 11242, 11480, 11250] + pests
    spec['slot'] = [11450]
    spec['placed'] = [11480, 11250] + pests
    spec['pair'] = [11030, 11450, 11240, 11480, 11250] + pests
else:
    ghouls = [454, 455, 456]
    spec['foes'] = ns['fam']('goblin', 'fly', 'skeleton') + ghouls
    spec['placed'] = [226, 454]
    spec['pair'] = [226, 271, 397, 454]
text = ns['scenario']('x1', spec)
if WORLD:
    text = text.replace("world: mm7", "world: xeen").replace('written by output/studio_cal/hostility/gen_hostility_tests.py',
                                          'written by output/studio_cal/x1/tools/gen_hostility_x1.py')
open(f'{R}/devdocs/xeen/briefs/x1/L4/playtest_hostility.yml', 'w').write(text)
print('wrote playtest_hostility.yml')
