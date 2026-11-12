# mm7_m190: anim fix (2026-11-11)

Stream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).

## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **0.3** (`scale_keys.py --joints '*' --factor 0.3 --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
Hit {'hand': 3.9, 'arm': 22.5, 'head': 12.0, 'spine': 40.9, 'leg': 0.9} -> {'hand': 3.0, 'arm': 6.1, 'head': 4.2, 'spine': 15.2, 'leg': 0.7} {'peak_speed': (2.22, 0.73), 'amp_p90': (0.196, 0.0665), 'body_share': (0.997, 0.289)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check all clean; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).

## Follow-up: spine-chain and beard weights, stronger Hit (2026-11-11, `followup-m190`)

Part 2 had to scale this Hit to 0.3 because the weights, not the clip, folded the chest and beard: the Meshy skin put
the chest, upper back, beard and braids on `B_Spine` (with clavicles, head, and thighs at the beard tip); `B_Spine1` and
`B_Spine2` carried no weight at all and `B_Neck` almost none (`review/weights/bind_before.png`). Before:
`work/before_followup/` (installed GLB and `actors.yml`; `actors.yml` is not changed by this follow-up).

**Weights** (`scripts/reweight_trunk.py`, defaults; mesh, UVs, normals, skin, inverse binds untouched; all eight
LOD/shadow meshes, the LODs labelled from the nearest LOD0 vertex; at most 4 influences on LOD0/2/3, 8 on LOD1):
- chest and back: the `B_Spine` share spread over `B_Spine` / `B_Spine1` / `B_Spine2` by height (linear tents at
  0.785 / 0.868 / 0.935 m); pelvis, neck, head, clavicle, upper-arm and thigh weights kept;
- beard (head-texture part of the torso shell in front, below 1.06 m, with the welded left braid) and the braid
  shells: the chin on `B_Head` (1.0 m), blending by 0.86 m to Head 0.1 / Neck 0.1 / chest 0.8, the chest share on the
  spine tents at the beard's own height, so the beard nods and turns with the chin and lies on the chest like cloth
  below the throat; its border blended into the chest over eight rings, none on the belly round the beard tip;
- LOD0: 1,834 of 8,155 vertices changed (beard 578 of 742, braid shells 410, shoulder guards 160, chest/back/neck
  686); `B_Spine1` now on 569 vertices (was 0), `B_Spine2` 361 (0), `B_Neck` 603 (142). Summary
  `review/followup_weight_change.txt`, weight colours `review/weights/bind_after.png`.
- Rejected on the way (numbers and sheets in `review/followup_trials/`): moving the clavicle, upper-arm, thigh and
  pelvis weights as well (worse waist and shoulder blades); the beard as one rigid mass on head and neck (Head 0.55,
  as first planned): it lifted off the chest whenever the head tilted back (Fidget, Hit recoil) and opened a gap and a
  stretched sheet down to the belt (`followup_trials/cand_g2_vs_installed.png`); a Gaussian (wider) spine blend.

**Hit** (`scripts/build_followup.sh`, from the full Hit in `work/before_hit/`): every joint x0.7 toward its first frame
(rotations and translations), then `B_Spine`, `B_Spine1`, `B_Spine2` and both clavicles x0.6 more (0.42 in all),
feet raised where it dips (`floor_fix.py --raise Hit`). Was x0.3 on every joint. The trunk and clavicles cannot go
higher on this body: their 27 deg flex and 30-39 deg shrug stretch the 23 cm deep back and shoulder blades (trunk at
0.49: arm 12.1 beyond Standing; uniform 0.6: spine 29 %). Hit amp p90 0.067 -> 0.143 H, peak speed 0.73 -> 1.74 H/s,
body share 0.29 -> 0.95.

**Motion audit** (`motion_audit.py`, own region map; `review/followup_cmp_audit.txt`, `followup_official_table.txt`):

| Clip | before (hand / arm / head / spine / leg) | after | worst-frame bad area cm2 |
|---|---|---|---|
| Hit | 3.0 / 6.1 / 4.2 / 15.2 / 0.7 | 3.7 / 11.9 / 7.7 / 7.5 / 0.7 (beyond Standing: 0.7 / 11.1 / 6.2 / 5.2 / -0.2) | 1395 -> 2109 (2.1x the motion) |
| Attack | 5.1 / 14.0 / 23.7 / 33.6 / 2.6 | 5.1 / 13.0 / 20.4 / 18.4 / 2.6 | 3898 -> 3394 |
| Death | 4.4 / 25.2 / 18.5 / 43.8 / 9.8 | 4.4 / 22.7 / 16.5 / 27.9 / 9.8 | 6495 -> 5532 |
| Dead | 3.5 / 8.4 / 5.4 / 22.6 / 2.0 | 3.5 / 9.0 / 4.0 / 12.7 / 2.0 | 2281 -> 2022 |
| Fidget | 3.9 / 15.1 / 14.1 / 16.0 / 3.0 | 3.9 / 15.0 / 11.0 / 13.0 / 3.1 | 2711 -> 2590 |
| Running | 4.3 / 12.5 / 7.1 / 12.6 / 7.4 | 4.3 / 13.1 / 4.6 / 7.9 / 7.4 | 3269 -> 2947 |
| Walking | 3.1 / 5.5 / 2.6 / 8.0 / 3.8 | 3.1 / 5.6 / 2.1 / 4.9 / 3.8 | 1550 -> 1366 |
| Walk2 | 3.1 / 6.1 / 3.6 / 9.1 / 4.8 | 3.1 / 6.0 / 2.9 / 6.6 / 4.7 | 1774 -> 1537 |
| Sprint | 4.3 / 11.8 / 10.8 / 17.6 / 7.6 | 4.3 / 11.6 / 8.0 / 11.4 / 7.6 | 3091 -> 2769 |
| Standing | 3.0 / 1.7 / 2.1 / 4.2 / 0.8 | 3.0 / 0.8 / 1.5 / 2.3 / 0.9 | 587 -> 418 |

Hit: every region under 12 % beyond Standing. Every other clip has less bad surface; the small region rises (Dead arm
+0.6, Running arm +0.6, Walking arm +0.1, Fidget and Standing leg +0.1) come from triangles changing region with their
dominant joint: on the before GLB's own region map (`scripts/fixed_regions.py`, `review/followup_fixed_map_table.txt`)
only Dead arm is higher (8.4 -> 8.6), Running arm drops 12.5 -> 11.9 and Fidget leg stays 3.0.

Checks (`review/followup_finish.txt`): winding 0; `glb_diff.py` vs the installed GLB: only Hit samplers and the
JOINTS/WEIGHTS accessors differ; floor audit 3 bindings ok (Dead 0.0 -> -0.06 units); gait audits Standard and MAW
unchanged (no walk/run change); every-binding regression 647 descriptors, 0 failed; viewer check 60 switches, no
console errors. Arm and hand gate: arm, hand and finger weights untouched; hand inside body 0 % in every clip; the
Hit is the production-gated Hit (G5/G6) scaled toward its first frame; axe vs body (`scripts/axe_clear.py`): Hit,
Attack, Walking, Running clear; two flagged Fidget/Death frames are the axe passing 6 cm from the helmet spike tip,
which neither the weights nor these clips changed. Sheets (top installed before, bottom after):
`review/followup_hit_viewer_before_after.png`, `review/followup_beard_viewer_before_after.png` (the dark slits beside
the beard in Walking and Hit are gone; the beard lies on the chest in Fidget), flat-shaded bad triangles in red
`review/followup/<Clip>_highlight.png` (Hit, Attack, Fidget, Death, Walking; `Hit_back_highlight.png` shows the
remaining shoulder-blade stretch of the stronger Hit).

Rebuild: `scripts/build_followup.sh`, then `python3 tools/install_model.py
level_generation/creatures/mm7_m190_animfix_claude/export/mm7_m190.glb --world mm7`. Revert: `python3
tools/install_model.py level_generation/creatures/mm7_m190_animfix_claude/work/before_followup/mm7_m190.glb --world mm7`.
