#!/usr/bin/env python3
"""Pass two, fix 5: the Deep Line cart as XD-02's ore carts (rusted iron, sides that stand up), not a plank pallet."""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import sys
sys.path.insert(0, _REPO_ROOT + '/output/studio_cal/xd03/pass2')
import yio
L = _REPO_ROOT + '/devdocs/xeen/briefs/xd03/L4/'
objects = yio.load(L + 'objects.yml')
iron = {'texture': 'xnrustirn', 'size': [64, 64]}
for m in objects['movers']:
    if m['id'] == 'mover:deep_cart':
        m['surface'] = dict(iron)
        for p in m['parts']:
            if p.get('notes') in ('Front board', 'Side board'):
                p['height'] = 64
                p['surface'] = dict(iron)
            if p.get('notes') == 'Wheel':
                p['surface'] = {'texture': 'ch004i', 'size': [64, 64]}
        m['notes'] = ("The Deep Line cart: one of XD-02's riveted iron ore carts (xnrustirn) at the top of the line's"
                      " last pitch; stepping onto it sends it down the trestle to the buffer stop (and back up), with"
                      " the party in it.")
yio.save(L + 'objects.yml', objects)
