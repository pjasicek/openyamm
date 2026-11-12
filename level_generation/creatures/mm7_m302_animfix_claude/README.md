# mm7_m302: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.5** (`scale_keys.py --joints '*' --factor 0.5 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 3.4, 'arm': 22.1, 'head': 7.9, 'spine': 31.5, 'leg': 0.4} -> {'hand': 2.9, 'arm': 11.2, 'head': 0.5, 'spine': 15.4, 'leg': 0.2} {'peak_speed': (2.76, 1.3), 'amp_p90': (0.2136, 0.1106), 'body_share': (1.0, 0.854)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
