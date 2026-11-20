# mm8_m476: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.5** (`scale_keys.py --joints '*' --factor 0.5 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 2.4, 'arm': 16.7, 'head': 2.4, 'spine': 42.3, 'leg': 1.0} -> {'hand': 1.9, 'arm': 6.6, 'head': 1.3, 'spine': 30.0, 'leg': 0.8} {'peak_speed': (2.73, 1.42), 'amp_p90': (0.1828, 0.0966), 'body_share': (0.979, 0.752)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check (see finish.txt: not all clean); arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
