#!/usr/bin/env python3
"""A5 (2026-11-20): X6's playtest_hostility.yml in the Xeen world, from the shared hostility generator
(level_generation/projects/xeen/common/hostility/gen_hostility_tests.py, read only) with A2's rows: sand worms 11440-11442, werewolves
11420-11422, elemental golems 11590-11592 (the slots); the caravaners (MMerge peasants) peaceful. The arena: the
pan's open ground south of the road at [70, 66], away from Sphinx Wells and every encounter area's edge."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
R = _REPO_ROOT
src = open(f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py').read()
ns = {'__name__': 'gen_hostility_tests', '__file__': f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py'}
exec(compile(src[:src.index('\nfor key in sys.argv')], 'gen_hostility_tests.py', 'exec'), ns)
spec = dict(ns['SPECS']['x2'])
spec['title'] = 'X6 Desert of the Sphinx'
spec['foes'] = [11440, 11441, 11442, 11420, 11421, 11422, 11590, 11591, 11592]
spec['slot'] = []
spec['placed'] = []
spec['peaceful'] = [371, 368, 362, 377, 350, 354]
spec['pair'] = [11440, 11420, 11590]
spec['at'] = [3072, -1024, 1300]
spec['pose'] = [3072, 0, 2600]
text = ns['scenario']('x6', spec)
text = text.replace('world: mm7', 'world: xeen').replace('written by output/studio_cal/hostility/gen_hostility_tests.py',
                                                         'written by output/studio_cal/x6/tools/gen_hostility_x6.py')
open(f'{R}/devdocs/xeen/briefs/x6/L4/playtest_hostility.yml', 'w').write(text)
print('wrote playtest_hostility.yml')
