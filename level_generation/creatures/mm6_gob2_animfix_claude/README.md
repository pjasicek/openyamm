# mm6_gob2: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.5** (`scale_keys.py --joints '*' --factor 0.5 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 7.6, 'arm': 12.0, 'head': 7.6, 'spine': 20.8, 'leg': 2.8} -> {'hand': 7.6, 'arm': 3.2, 'head': 3.2, 'spine': 12.2, 'leg': 2.8} {'peak_speed': (2.59, 1.39), 'amp_p90': (0.2347, 0.1391), 'body_share': (0.98, 0.911)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
