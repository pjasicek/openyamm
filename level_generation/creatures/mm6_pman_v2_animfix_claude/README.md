# mm6_pman_v2: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.6** (`scale_keys.py --joints '*' --factor 0.6 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 3.0, 'arm': 15.3, 'head': 1.5, 'spine': 20.9, 'leg': 0.0} -> {'hand': 1.3, 'arm': 10.7, 'head': 1.3, 'spine': 9.4, 'leg': 0.0} {'peak_speed': (2.4, 1.41), 'amp_p90': (0.1836, 0.1156), 'body_share': (0.361, 0.307)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
