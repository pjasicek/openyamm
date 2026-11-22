#!/usr/bin/env python3
"""A5 (2026-11-20, fifth session): X3's playtest_hostility.yml in the Xeen world, from the shared hostility generator
(level_generation/projects/xeen/common/hostility/gen_hostility_tests.py, read only) with A2's rows: swamp things, toads, zombies (the
slots), the evil rangers' camp and the night bats (placed); Mirabeth (MM7 Peasant 350), the workmen (359, 362, 368)
peaceful. Run after gen_walk.py (it reads the walk's new-game step)."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
R = _REPO_ROOT
src = open(f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py').read()
ns = {'__name__': 'gen_hostility_tests', '__file__': f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py'}
exec(compile(src[:src.index('\nfor key in sys.argv')], 'gen_hostility_tests.py', 'exec'), ns)
X, Y = (70 - 64) * 512, (64 - 50) * 512
spec = dict(title='X3 Lifeforce Lagoon',
            foes=[11460, 11461, 11462, 11450, 11451, 11452, 11250, 11251, 11252, 11130, 11131, 11132, 11310, 11311,
                  11312],
            slot=[], placed=[11131, 11310], peaceful=[350, 359, 362, 368],
            pair=[11460, 11450, 11250, 11131, 11310], at=[X, Y, 960], pose=[X, Y + 1000, 2000])
text = ns['scenario']('x3', spec)
text = text.replace('world: mm7', 'world: xeen').replace('written by output/studio_cal/hostility/gen_hostility_tests.py',
                                                         'written by output/studio_cal/x3/tools/gen_hostility_x3.py')
open(f'{R}/devdocs/xeen/briefs/x3/L4/playtest_hostility.yml', 'w').write(text)
print('wrote playtest_hostility.yml')
