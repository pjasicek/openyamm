# mm7_m475: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.6** (`scale_keys.py --joints '*' --factor 0.6 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 0.0, 'arm': 23.1, 'head': 4.5, 'spine': 11.2, 'leg': 0.0, 'cloth': 1.5} -> {'hand': 0.0, 'arm': 9.0, 'head': 1.0, 'spine': 4.7, 'leg': 0.0, 'cloth': 0.8} {'peak_speed': (2.79, 1.73), 'amp_p90': (0.1929, 0.1246), 'body_share': (0.337, 0.307)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
