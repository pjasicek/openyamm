#!/usr/bin/env python3
"""A6 (2026-11-20): X5's playtest_hostility.yml from the shared hostility generator
(level_generation/projects/xeen/common/hostility/gen_hostility_tests.py, read only) with A2's rows: wolves, barbarians, trolls, cyclopes
(the slots' and the placed kinds), the pocket's ogres and archers, Q-C6's Spirit Bones; Randon, Freeda, Thickbark (a
Treant), the Winter Druid and Kai Wu's monks peaceful."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
R = _REPO_ROOT
src = open(f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py').read()
ns = {'__name__': 'gen_hostility_tests', '__file__': f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py'}
exec(compile(src[:src.index('\nfor key in sys.argv')], 'gen_hostility_tests.py', 'exec'), ns)
spec = {'title': 'X5 Winterkill Tundra',
        'foes': [11410, 11411, 11412, 11100, 11101, 11102, 11070, 11071, 11072, 11080, 11081, 11060, 11061, 11130,
                 11241, 11260, 11261, 11263],
        'slot': [], 'placed': [11410, 11411, 11100, 11080, 11060, 11130, 11241],
        'peaceful': [361, 377, 451, 517, 583],
        'pair': [11410, 11100, 11070, 11080],
        'at': [-17408, -3072, 1100], 'pose': [-17408, -2072, 2200]}
text = ns['scenario']('x5', spec)
text = text.replace('world: mm7', 'world: xeen').replace('written by output/studio_cal/hostility/gen_hostility_tests.py',
                                                         'written by output/studio_cal/x5/tools/gen_hostility_x5.py')
open(f'{R}/devdocs/xeen/briefs/x5/L4/playtest_hostility.yml', 'w').write(text)
print('wrote playtest_hostility.yml')
