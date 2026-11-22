#!/usr/bin/env python3
"""A6 (2026-11-20): D1's playtest_hostility.yml from the shared hostility generator
(level_generation/projects/xeen/common/hostility/gen_hostility_tests.py, read only) with A2's rows: gremlins, arachnoids and crawlers
(the slots' and the placed kinds) hostile; the Sardaj (Yog's barbarians, q-d12) and Joe, Justine and Luna peaceful."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
R = _REPO_ROOT
src = open(f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py').read()
ns = {'__name__': 'gen_hostility_tests', '__file__': f'{R}/level_generation/projects/xeen/common/hostility/gen_hostility_tests.py'}
exec(compile(src[:src.index('\nfor key in sys.argv')], 'gen_hostility_tests.py', 'exec'), ns)
spec = {'title': 'D1 Castleview Vale',
        'foes': [11020, 11021, 11022, 11330, 11331, 11332, 11360, 11361, 11362],
        'slot': [11020, 11330, 11360], 'placed': [11021, 11022, 11361],
        'peaceful': [361, 377, 517, 11100, 11101, 11102, 11103],
        'pair': [11020, 11330, 11360],
        # M14's arrival text (a timer, once) holds the world still: closed first
        'after_entry': [{'advance_runtime': {'seconds': 3}}, {'assert': {'dialog': {'active': True}}},
                        {'press_action': {'action': 'cancel_dialog'}}, {'advance_runtime': {'seconds': 0.5}}],
        'at': [13312, -15872, 1000], 'pose': [13312, -14872, 2100]}
text = ns['scenario']('d1', spec)
text = text.replace('world: mm7', 'world: xeen').replace('written by output/studio_cal/hostility/gen_hostility_tests.py',
                                                         'written by output/studio_cal/d1/tools/gen_hostility_d1.py')
open(f'{R}/devdocs/xeen/briefs/d1/L4/playtest_hostility.yml', 'w').write(text)
print('wrote playtest_hostility.yml')
