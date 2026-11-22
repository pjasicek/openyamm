#!/usr/bin/env python3
"""A5 (2026-11-20): X7's playtest_hostility.yml in the Xeen world, from the shared hostility generator
(level_generation/projects/xeen/common/hostility/gen_hostility_tests.py, read only) with A2's rows: orcs 11030-11032, hydras 11660-11662,
dragons 11640-11642 (the slots), Lava Golems 11593 and Orcs 11030 placed; Sablewing's body (368) peaceful. The arena:
the Firestone Gap's level pad at [62, 65.5], away from every encounter area."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
R = _REPO_ROOT
src = open(f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py').read()
ns = {'__name__': 'gen_hostility_tests', '__file__': f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py'}
exec(compile(src[:src.index('\nfor key in sys.argv')], 'gen_hostility_tests.py', 'exec'), ns)
spec = dict(ns['SPECS']['x2'])
spec['title'] = 'X7 Mount Firestone'
spec['foes'] = [11030, 11031, 11032, 11660, 11661, 11662, 11640, 11641, 11642, 11593]
spec['slot'] = []
spec['placed'] = [11593, 11030]
spec['peaceful'] = [368]
spec['pair'] = [11030, 11660, 11640, 11593]
spec['at'] = [-1024, -768, 2300]
spec['pose'] = [-1024, 232, 3400]
text = ns['scenario']('x7', spec)
text = text.replace('world: mm7', 'world: xeen').replace('written by output/studio_cal/hostility/gen_hostility_tests.py',
                                                         'written by output/studio_cal/x7/tools/gen_hostility_x7.py')
open(f'{R}/devdocs/xeen/briefs/x7/L4/playtest_hostility.yml', 'w').write(text)
print('wrote playtest_hostility.yml')
