#!/usr/bin/env python3
"""A5 (2026-11-20): D3's playtest_hostility.yml in the Xeen world, from the shared hostility generator
(level_generation/projects/xeen/common/hostility/gen_hostility_tests.py, read only) with A2's rows: mantis ants 11370-11372, cobras
11490-11492, sand worms 11440-11442 (the slots), Hell Hornets 11350 and Hornet Swarms 11351 (placed); the townsfolk
(MMerge peasants) peaceful. The arena: the river meadows north of the venom fork, [72, 62], away from the towns."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
R = _REPO_ROOT
src = open(f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py').read()
ns = {'__name__': 'gen_hostility_tests', '__file__': f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py'}
exec(compile(src[:src.index('\nfor key in sys.argv')], 'gen_hostility_tests.py', 'exec'), ns)
spec = dict(ns['SPECS']['x2'])
spec['title'] = 'D3 Sandcaster and the Aging Forest'
spec['foes'] = [11370, 11371, 11372, 11490, 11491, 11492, 11440, 11441, 11442, 11350, 11351]
spec['slot'] = []
spec['placed'] = [11350, 11351]
spec['peaceful'] = [371, 368, 362, 377, 350, 354]
spec['pair'] = [11370, 11490, 11440, 11350]
spec['at'] = [4096, 1024, 1100]
spec['pose'] = [4096, 2048, 2600]
text = ns['scenario']('d3', spec)
text = text.replace('world: mm7', 'world: xeen').replace('written by output/studio_cal/hostility/gen_hostility_tests.py',
                                                         'written by output/studio_cal/d3/tools/gen_hostility_d3.py')
open(f'{R}/devdocs/xeen/briefs/d3/L4/playtest_hostility.yml', 'w').write(text)
print('wrote playtest_hostility.yml')
