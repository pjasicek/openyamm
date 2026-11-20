# mm8_m480: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.7** (`scale_keys.py --joints '*' --factor 0.7 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 0.9, 'arm': 18.7, 'head': 8.3, 'spine': 13.6, 'leg': 2.1, 'other': 0.1} -> {'hand': 0.9, 'arm': 7.9, 'head': 2.9, 'spine': 8.7, 'leg': 2.1, 'other': 0.1} {'peak_speed': (3.11, 2.21), 'amp_p90': (0.2736, 0.207), 'body_share': (1.0, 0.98)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check (see finish.txt: not all clean); arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).

Floor follow-up (same day): scaling the pelvis translation let the feet dip 2.6 cm (3.3–4.9 world units) during the
scaled Hit; `claude_shared/floor/floor_fix.py work/before_hit/<stem>_scaled.glb export/<stem>.glb --raise Hit` raised
68 of 73 keys onto the floor and was installed; floor audit now 0 problems, region shares unchanged.
