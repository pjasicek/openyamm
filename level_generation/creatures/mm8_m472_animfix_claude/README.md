# mm8_m472: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.7** (`scale_keys.py --joints '*' --factor 0.7 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 4.9, 'arm': 12.9, 'head': 19.6, 'spine': 6.4, 'leg': 0.0, 'cloth': 0.1, 'other': 15.9} -> {'hand': 2.2, 'arm': 11.0, 'head': 11.3, 'spine': 5.1, 'leg': 0.0, 'cloth': 0.1, 'other': 14.4} {'peak_speed': (2.7, 2.04), 'amp_p90': (0.1976, 0.1526), 'body_share': (0.491, 0.416)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
