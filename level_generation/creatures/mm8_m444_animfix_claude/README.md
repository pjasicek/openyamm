# mm8_m444: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.7** (`scale_keys.py --joints '*' --factor 0.7 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 2.4, 'arm': 14.0, 'head': 3.7, 'spine': 20.1, 'leg': 0.1} -> {'hand': 2.0, 'arm': 10.6, 'head': 2.0, 'spine': 9.1, 'leg': 0.0} {'peak_speed': (3.49, 2.34), 'amp_p90': (0.2127, 0.1508), 'body_share': (0.439, 0.39)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
