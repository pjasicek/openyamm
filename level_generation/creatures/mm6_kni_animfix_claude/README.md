# mm6_kni: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.5** (`scale_keys.py --joints '*' --factor 0.5 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 4.6, 'arm': 8.7, 'head': 14.6, 'spine': 30.0, 'leg': 0.5} -> {'hand': 3.4, 'arm': 6.1, 'head': 4.0, 'spine': 9.8, 'leg': 0.3} {'peak_speed': (2.15, 1.23), 'amp_p90': (0.165, 0.0853), 'body_share': (1.0, 0.648)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
