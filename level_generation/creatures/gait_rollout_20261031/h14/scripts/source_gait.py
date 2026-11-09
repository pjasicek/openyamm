#!/usr/bin/env python3
"""Package h14 copy of ../h08/scripts/source_gait.py, scaled to the four MM7 human peasants.
Natural speed, stride and cadence of library locomotion clips (npz from extract_source.py), scaled to our bodies.

Stride by distance: the planted foot slides backwards under the hips at the clip's ground speed. Measured per foot as
the median backward speed of the ankle relative to the hips while it is in the lowest 12 % of its height range; speed
x cycle = stride. Scaled to each body by leg length (hip-knee-ankle). Also: flight share (both feet up), peak knee
lift (thigh angle forward of vertical), hip height over leg length, foot pitch range.

    source_gait.py <npz> [...]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gaitlib  # noqa: E402


def analyse(path):
    src = gaitlib.Source(path)
    out = {'name': Path(path).stem, 'T': src.period, 'cycles': src.cycles, 'L': src.leg_length}
    out.update(src.stats())
    return out


def main():
    bodies = {m: gaitlib.Body(m, str(gaitlib.ROOT / f'assets_source/worlds/mm7/models/mm7_{m}.glb'))
              for m in ('m342', 'm352', 'm362', 'm372')}
    print(f"{'source':44} {'T':>5} {'cyc':>3} {'v m/s':>6} {'S m':>5} {'v/L':>5} {'flight':>6} {'knee':>5} "
          f"{'hipH/L':>6} | m342 v (S) | m352 | m362 | m372")
    for path in sys.argv[1:]:
        r = analyse(path)
        cells = ' | '.join(f"{r['v'] * b.leg_length / r['L']:.2f} ({r['S'] * b.leg_length / r['L']:.2f})"
                           for b in bodies.values())
        print(f"{r['name'][:44]:44} {r['T']:5.2f} {r['cycles']:3d} {r['v']:6.2f} {r['S']:5.2f} {r['v'] / r['L']:5.2f} "
              f"{r['flight']:6.2f} {r['knee']:5.0f} {r['hip_height'] / r['L']:6.2f} | {cells}")
    for name, b in bodies.items():
        print(f'{name}: leg {b.leg_length:.3f} m, hip height standing {b.standing_hip_height:.3f} m')


if __name__ == '__main__':
    main()
