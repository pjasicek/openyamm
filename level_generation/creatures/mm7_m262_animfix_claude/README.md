# mm7_m262: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.7** (`scale_keys.py --joints '*' --factor 0.7 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 3.3, 'arm': 15.2, 'head': 22.1, 'spine': 20.8, 'leg': 4.6, 'tail': 0.0, 'wing': 2.5} -> {'hand': 2.8, 'arm': 12.1, 'head': 11.8, 'spine': 8.4, 'leg': 4.6, 'tail': 0.0, 'wing': 0.7} {'peak_speed': (4.45, 3.02), 'amp_p90': (0.4115, 0.2836), 'body_share': (1.0, 0.997)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
