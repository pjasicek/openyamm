#!/usr/bin/env python3
"""Head bob of clips of a candidate GLB, measured exactly as claude_shared/postprocess/bob_audit.py does (head joint
peak-to-peak over the loop in per cent of its Standing height; pelvis share; uneven = once-per-loop over once-per-step).
bob_audit.py reads only installed bindings (walk and run), so this applies its measure to a candidate and to a sprint.

    bob_probe.py <glb> <clip>[,<clip>...]
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / 'claude_shared/postprocess'))
sys.path.insert(0, str(HERE.parents[2] / 'claude_shared/floor'))
import bob_audit  # noqa: E402
import bob_fix  # noqa: E402
import glb_pose  # noqa: E402


def main():
    model = glb_pose.Model(glb_pose.Glb(sys.argv[1]))
    head = bob_fix.find_joint(model, 'head')
    height = float(model.world(model.sample('Standing', 0.0))[head][1, 3])
    for clip in sys.argv[2].split(','):
        r = bob_audit.measure(model, clip, head, model.root_joints[0], height)
        print(f"{clip:9} bob {r['bob']:5.1f}%  pelvis share {r['pelvis']:4.2f}  uneven {r['uneven']:5.2f}  "
              f"(walk {bob_audit.WALK}, run {bob_audit.RUN})")


if __name__ == '__main__':
    main()
