#!/usr/bin/env python3
"""A5 (2026-11-20): X4's playtest_hostility.yml in the Xeen world, from the shared hostility generator
(level_generation/projects/xeen/common/hostility/gen_hostility_tests.py, read only) with A2's rows: the renegade knights (D-11.2, 11680-11682),
ogres, gargoyles and the barbarians; the townsfolk, A4's NPC figures and the King's Guard (11143) peaceful.
The arena: the east savannah by the Wayfarers' well road, [90, 66], away from both towns."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
R = _REPO_ROOT
src = open(f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py').read()
ns = {'__name__': 'gen_hostility_tests', '__file__': f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py'}
exec(compile(src[:src.index('\nfor key in sys.argv')], 'gen_hostility_tests.py', 'exec'), ns)
spec = dict(ns['SPECS']['x2'])
spec['title'] = 'X4 Burlock Savannah'
spec['foes'] = [11680, 11681, 11682, 11060, 11061, 11062, 11540, 11541, 11542, 11100, 11101, 11102]
spec['slot'] = []
spec['placed'] = [11100, 11101, 11102, 11060, 11061, 11680, 11682]
spec['peaceful'] = [371, 368, 362, 377, 350, 354, 11143]
spec['pair'] = [11680, 11060, 11540, 11100]
spec['at'] = [13312, -1024, 1200]
spec['pose'] = [13312, 0, 2600]
text = ns['scenario']('x4', spec)
text = text.replace('world: mm7', 'world: xeen').replace('written by output/studio_cal/hostility/gen_hostility_tests.py',
                                                         'written by output/studio_cal/x4/tools/gen_hostility_x4.py')
open(f'{R}/devdocs/xeen/briefs/x4/L4/playtest_hostility.yml', 'w').write(text)
print('wrote playtest_hostility.yml')
