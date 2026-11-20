# mm7_m254: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.4** (`scale_keys.py --joints '*' --factor 0.4 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 3.1, 'arm': 20.7, 'head': 5.3, 'spine': 6.2, 'leg': 0.0} -> {'hand': 0.9, 'arm': 9.5, 'head': 2.1, 'spine': 4.6, 'leg': 0.0} {'peak_speed': (2.61, 1.13), 'amp_p90': (0.2024, 0.088), 'body_share': (1.0, 0.469)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
