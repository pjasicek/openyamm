#!/usr/bin/env python3
"""A5 (2026-11-20): X2's playtest_hostility.yml in the Xeen world, from the shared hostility generator
(level_generation/projects/xeen/common/hostility/gen_hostility_tests.py, read only) with A2's rows: sprites, evil rangers, ogres, the lake's
water dragons; Ligono (MM7's Ghost 270, a peaceful figure by the map's relations) with the townsfolk."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
R = _REPO_ROOT
src = open(f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py').read()
ns = {'__name__': 'gen_hostility_tests', '__file__': f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py'}
exec(compile(src[:src.index('\nfor key in sys.argv')], 'gen_hostility_tests.py', 'exec'), ns)
spec = dict(ns['SPECS']['x2'])
spec['foes'] = [11530, 11531, 11532, 11130, 11131, 11132, 11060, 11061, 11062, 11640, 11184]
spec['slot'] = []
spec['placed'] = [11131, 11061, 11184]   # 11184: Q-C2's two apprentices (hidden until the strongbox)
spec['peaceful'] = list(spec['peaceful']) + [270]
spec['pair'] = [11130, 11060, 11531, 11640]
text = ns['scenario']('x2', spec)
text = text.replace('world: mm7', 'world: xeen').replace('written by output/studio_cal/hostility/gen_hostility_tests.py',
                                                         'written by output/studio_cal/x2/tools/gen_hostility_x2.py')
open(f'{R}/devdocs/xeen/briefs/x2/L4/playtest_hostility.yml', 'w').write(text)
print('wrote playtest_hostility.yml')
