#!/usr/bin/env python3
"""Write an in-game check tour for Xeen tiers (lane S): each group of monster ids is spawned in a row about 500 units
ahead of the party in XD-21 (party at -2560 320 0 facing +Y), captured frozen, then killed (rendering unfrozen while they fall) before the next group.

    make_tour.py <out tour.yml> <capture dir> [--close-dialog] <name>=<id>,<id>,... ...

--close-dialog presses Escape first, for a map whose entry text opens a dialogue (XD-21 since 2026-11-20: the
robbers' den text); with it open, actors are paused and `actor kill` leaves them standing.

Run it with tools/run_game.sh --isolated ... --map xeen_xd21.blv --position -2560 320 0 --yaw-radians 1.5708
--pitch-degrees -8 --set debug.actor_models=true --set debug.immortal=true --set debug.menu_input_tour_path=<tour>."""
import sys

out, capture_dir, groups = sys.argv[1], sys.argv[2], sys.argv[3:]
close = '--close-dialog' in groups
groups = [g for g in groups if g != '--close-dialog']
lines = [f'output_dir: {capture_dir}', 'exit: true', 'steps:', '- expect: gameplay', '- wait: 0.5']
if close:
    lines += ['- key: Escape', '- wait: 0.5']
lines += ['- console: render freeze on']
for group in groups:
    name, ids = group.split('=')
    ids = ids.split(',')
    spacing = 480 / max(len(ids) - 1, 1) if len(ids) > 1 else 0
    x0 = -2560 - spacing * (len(ids) - 1) / 2
    for i, monster in enumerate(ids):
        y = 860 if i % 2 else 820
        lines.append(f'- console: actor spawn {monster} 1 {round(x0 + i * spacing)} {y} 0')
        # Killed actors keep their standing pose while rendering is frozen: let the deaths play before the next group.
    lines += ['- wait: 0.4', f'- capture: {name}', '- console: actor kill 3000', '- console: render freeze off',
              '- wait: 2.5', '- console: render freeze on']
lines += ['- console: render freeze off', '- wait: 0.3']
open(out, 'w').write('\n'.join(lines) + '\n')
print('WROTE', out, len(groups), 'groups')
