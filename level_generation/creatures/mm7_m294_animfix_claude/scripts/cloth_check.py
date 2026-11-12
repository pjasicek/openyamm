#!/usr/bin/env python3
"""Validation of the cloth port: re-simulate an installed clip's chains (cloth_sim.py) on its own body motion and
compare the chain joints with the installed clip's (Blender robe_sim.py output). Prints the median and max distance
per chain set (cm). A port that reproduces the installed walk within a few cm moves the new clips' cloth the same way.

    cloth_check.py <glb> <clip> <cloth job json (the job's "cloth" list)>
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cloth_sim  # noqa: E402
import compose_gait  # noqa: E402


def main():
    body = compose_gait.Body(sys.argv[1])
    clip = sys.argv[2]
    cfgs = json.loads(Path(sys.argv[3]).read_text())['cloth']
    T = body.clip_length(clip)
    N = int(round(T * 120))
    _, worlds = body.clip_world(clip, np.arange(N) / N * T)
    for cfg in cfgs:
        cloth = cloth_sim.Cloth(body, cfg)
        X = cloth.simulate(worlds.copy(), T)
        new = cloth.key(worlds.copy(), X)
        d = []
        for bones in cloth.bones:
            for b in bones:
                n = body.idx[b]
                tip = lambda W: W[:, n, :3, 3] + W[:, n, :3, 1] * np.linalg.norm(body.model.rest[body.idx[bones[-1]]][0])
                d.append(np.linalg.norm(tip(new) - tip(worlds), axis=1))
        d = np.array(d)
        print(f"{cfg.get('key', 'cloak_chains'):13} vs installed {clip}: median {100 * np.median(d):.1f} cm, "
              f"p95 {100 * np.percentile(d, 95):.1f}, max {100 * d.max():.1f}; radii {[round(r, 3) for r in cloth.radii]}")


if __name__ == '__main__':
    main()
