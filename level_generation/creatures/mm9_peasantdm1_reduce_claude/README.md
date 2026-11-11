# MM9 PeasantDM1 (`mm9_peasantdm1`, dwarf townsman, rows 8/13/14) reduction: candidate d r55 ready for review (2026-11-05)

Batch: [REDUCTION_AGENT_TOWNSFOLK.md](../../../devdocs/mm9_rework/overnight/REDUCTION_AGENT_TOWNSFOLK.md) /
[REDUCTION_BRIEF_20261104.md](../../../devdocs/mm9_rework/overnight/REDUCTION_BRIEF_20261104.md) (prio-2 townsfolk, face exact), ledger
row 86 of [REDUCTION_LEDGER.md](../REDUCTION_LEDGER.md). Lease `mm9reduce:peasantdm1` (owner peasantdm1-reduce-20261105); the creature's
`mm9:peasantdm1` lease was free (released 2026-11-01). Source: installed `assets_source/worlds/mm9/models/mm9_peasantdm1.glb` (sha256
366854191073, identical to `../mm9_peasantdm1_claude/export/mm9_pdm1.glb`), copied to `before/` (rollback). No Meshy, no credits, no
repaint. **Not installed.** `../mm9_peasantdm1_claude/` was only read.

Family: DM3 is a reshaped variant of DM1's body, reduced separately in `../mm9_peasantdm3_reduce_claude/` (its scripts and keep set d were
copied here and renamed; DM3's project was only read). DM1 has **no linings** (twins.py: 0 pairs in both primitives), so the lining
re-emission, hole fill and lining gate of the DM3 chain are inert here.

| | LOD0 | body prim (tunic, legs, boots, frills, buttons) | head prim (head shell, hair bob, hands) | LOD1 | LOD2 | LOD3 |
|---|---:|---:|---:|---:|---:|---:|
| installed | 7,586 | 3,817 | 3,769 | 3,791 | 1,363 | 453 |
| **d r55 (`export/mm9_peasantdm1.glb`, sha256 5c45c774c6a0)** | **6,186 (-18.5 %)** | 3,327 | 2,859 | 3,092 | 1,112 | 368 |

Per group (free faces cut): hands 1,267 -> 785 (0.6, every finger), hair bob 1,043 -> 677 (0.65), scalp under the bob 227 -> 169 and
beard 17 -> 13 (0.75), tunic 1,138 -> 964 and legs + calf frills 1,410 -> 1,094 (the 3.5 mm distance guard stops both early). Every
vertex is an installed vertex; clips, skin, nodes, materials, variants and all 9 images identical (`same_clips.py`).

## Protected share (measured first)
`scripts/survey_dm1.py`: body = tunic 1,811 (collar, sleeves, forearms), legs 1,207 (trousers + boots), calf frills 257 + 231, five small
pieces 311 (medallion, buckle, buttons, a 63-face frill patch); head = head shell 1,310 (face, beard, neck, ears, scalp under the hair),
hair bob 1,060, MPFB hands 700 + 699. Keep set d (`scripts/make_sets_dm3.py d`): face window + every shell face not painted hair in both
tiers (`head_parts.py`: no head region mask on DM1, so a colour rule: tier A hue >= 19.5 deg or v < 0.62 and tier B not bright skin;
`review/head_parts.png`) + ear box + neck/beard faces within 2 cm of the body (so the whole visible beard stays exact); collar (1 cm),
graft junction (3 cm), cuff (tunic within 5 cm of a hand vertex), soles, small pieces, zero-UV faces with a 6 mm halo, hand-contact
faces (`hand_contact_dm3.py`, 4 cm in any clip, 92), the sleeve-poke walls and see-through cover faces (below; 310 with their rings) and
a 4 cm zone at the right back armpit. Protected: 2,484 faces (32.7 %).
`SMALL_MAX=200` puts the calf frills in the legs group (they were "small" under DM3's 300 limit).

## Route and ladder (one ratio, four keep-set steps)
`scripts/mpqem.py` (pose-aware half-edge collapse, DM3 copy): chart guard `MP_CHART=1`, texture guard over both tiers (body ramped; head
= each tier's own colour image, `tex_extract.py` adapted), `MP_W5=4`, distance guard 3.5 mm, seam slides on the hands,
`MP_GROUPS=1:0.6,2:0.65,3:0.55,6:0.75,7:0.75`, tunic at r55.

| run | change | LOD0 | p99 / max mm | IoU / SSIM | open edges (src 490) | result |
|---|---|---:|---|---|---:|---|
| a | DM3 set (cuff 2 cm, graft 1.5 cm) | 6,054 | 2.82 / 9.82 | .9969 / .9954 | 490 | ladder PASS; sleeve poke worse (L Running 4.9 -> 6.9 mm, R Running 27.9 -> 31.5) |
| b | cuff 5 cm, graft 3 cm | 6,094 | 2.81 / 9.82 | .9970 / .9955 | 490 | L poke equal, R still +3.6 mm |
| c | b + the outer sleeve walls the poke rays hit kept exact | 6,116 | 2.80 / 9.82 | .9971 / .9955 | 490 | poke identical; see-through AttackMelee torso 20 -> 62 px (right back armpit, frame 30) |
| **d** | **c + the installed faces that covered c's new hole pixels, and a 4 cm zone round the armpit, exact** | **6,186** | **2.78 / 7.52** | **.9972 / .9957** | **490** | **PASS, picked** |

Limits for 1.211 m: p99 3.63, max 18.2 mm. Run c: `scripts/probe_poke.py` (the creature's sleeve-poke gate with the hit face recorded)
over every frame of the poking clips of the installed model gave 15 body faces; they and two rings around them stay exact. Run d:
`scripts/probe_see.py` (see-through gate copy: renders the candidate as the gate does and casts each hole pixel's ray into the
installed mesh at the same frame; the first front face hit is a face whose cut opened the hole) over AttackMelee gave 10 faces (7 body
faces new), added to the same keep with two rings (`work/poke_see_faces.npy`), plus `HOLES` zone (-0.156, 0.785, -0.112) r 4 cm.
Run d was a fourth step: a targeted fix of a measured gate regression, not a new ratio ladder.

## Gates, installed -> d r55 (`review/gates_before/`, `review/gates_d55/`)
- **UV audit** (`review/uv_audit_d55.json`): **0 escaping LOD0 faces in both primitives**. LOD1-3 escapes from the LOD tool at the
  installed level (LOD1 144/131 vs 130/113, LOD2 156/144 vs 140/130, LOD3 65/70 vs 73/88).
- Arm and hand (`--outer-only`): hand/forearm intrusion identical in every clip (Talk L 1.4 cm 3 f as installed, all else 0); finger
  stretch max equal or lower in every clip, p99 up by up to 0.12 (Rock R 1.63 -> 1.75; longer edges after the 0.6 hand cut).
- Jitter vs MM9's clips: 0 fails both (largest shoulder-skin change AttackMelee L 0.09 -> 0.88 mm/f2, limit 2.0).
- Sleeve poke: **identical in every clip** (the creature's known wrist-fold readings, R Running 27.9 mm etc.).
- Hair (`hair_beard_gate.py`, SEL=hair, `HAIR_Y=1.25` = the whole bob): stretch 1.000 in every clip both (rigid on the head); surface
  contact gap equal in every clip, approach equal or smaller (AttackMelee 0.90 -> 0.69 cm, Hit 0.62 -> 0.53).
- See-through (`scripts/see_through.sh`, the Dwarf boy gate, every clip, 16 views; DM1's own project did not run it): worst px per zone
  equal within 3 px (boot L 24 = 24, boot R 23 -> 22, collar 20 -> 21, head 14 = 14, sleeve L 201 = 201, sleeve R 282 -> 281, torso
  103 -> 100, trousers L 25 -> 27, trousers R 11 = 11); frames with holes equal or fewer except collar 234 -> 237 and trousers R
  per clip (Dump 12 -> 15); per clip at most +3 px (Dump trousers L 24 -> 27, Hammer sleeve R 277 -> 280). Run c's AttackMelee torso
  20 -> 62 px is back to 20.
- Detached 0 = 0, winding 0, bones 12 checked 0 stretching, flat 0.00, texture quality body 53.4 % both, head 41.4 -> 41.3 %.
- LODs (`scripts/lod_check.py`): height 1.211 m at every LOD (installed LOD2 1.209, LOD3 1.199); LOD0/LOD1 floor equal to installed in
  every clip; LOD2/LOD3 lowest point -0.2..+0.5 cm (installed LOD3 +0.2..+1.3 cm: floated); 0 stretched faces in any clip.

## Review
Viewer (installed and reduced, both tiers, 15 clips; `run_creature_review.py check`: 60 switches, 0 failed, no console errors):
http://127.0.0.1:8912/level_generation/creatures/mm9_peasantdm1_reduce_claude/review/viewer/
Sheets read (installed left/above): `review/sheet_face_d55.png` and `review/sheet_face_diff_d55.png` (face skin, beard and ears black in
all ten; differences on the hair bob shading and the collar), `review/sheet_body_d55_a.png`, `review/close_d55_b_hands.png` (wrists,
bands, hands), `review/close_d55_a_hem.png` (front, back, 3/4, boots and frills), `review/close_d55_b_motion.png` (Fidget, AttackMelee,
Talk, Death). Same views read on run c (identical head, hands and hair cut): `review/close_c55_a_hands.png`, `review/close_c55_b_fingers.png`,
`review/close_c55_a_hair.png` (bob from behind above and level, beard from the side), `review/close_c55_b_hem.png`,
`review/close_c55_a_motion.png`, `review/sheet_body_c55_b.png`; see-through `review/gates_c55/see_through_torso_AttackMelee_30_az045_el20.png`.
From run a (same face/body result): `review/sheet_face_a55.png`, `review/sheet_body_a55_a.png`, `review/ladder_sheet_a.png`.
Generated, not opened: `review/sheet_body_d55_b.png`, `review/close_d55_{a_hands,{a,b}_fingers,{a,b}_hair,b_hem,a_motion,{a,b}_arms,{a,b}_cuffs}.png`.
Look at: the hair bob silhouette at the closest zoom (0.65), knuckles (0.6), the Rock clip's right fingers.

## Build (project folder)
```sh
BL="scripts/cap.sh /snap/bin/blender --background --factory-startup --threads 4 --python-exit-code 1"; G=../claude_shared/gltf_venv/bin/python
REA_GLB=level_generation/creatures/mm9_peasantdm1_reduce_claude/before/mm9_peasantdm1.glb REA_NODE=PeasantDM1 $BL -P scripts/import_source.py   # from the repo root
$BL -P scripts/dump_mesh.py; $G scripts/twins.py; $G scripts/tex_extract.py; $G scripts/head_parts.py; $G scripts/hand_contact_dm3.py
$G scripts/probe_poke.py before/mm9_peasantdm1.glb work/poke_faces.npy --clips "R:Running:*,R:Fidget2:*,R:Rock:*,R:Hammer:*,R:Dump:*,L:Running:*,L:Fidget:*,L:AttackMelee:*,L:RubBeard:*"
# + scripts/probe_see.py (Blender, run c's candidate vs before/, clips=AttackMelee) -> work/probe_see_attack.json -> work/poke_see_faces.npy
SMALL_MAX=200 HANDS=hand_contact.npy CUFF=0.05 GRAFT=0.03 POKE=poke_see_faces.npy POKE_RING=2 HOLES="-0.156,0.785,-0.112,0.04" $G scripts/make_sets_dm3.py d
work/run_d.sh            # MP_DMAX_MM=3.5 MP_CHART=1 MP_W5=4 MP_SEAM_GROUPS=1 SETS=d MP_GROUPS=1:0.6,2:0.65,3:0.55,6:0.75,7:0.75; run_mp.sh d 0.55
scripts/build_mp.sh mp_d_r55 export/mm9_peasantdm1.glb
$G ../claude_shared/reduction_uv_audit.py export/mm9_peasantdm1.glb before/mm9_peasantdm1.glb --json review/uv_audit_d55.json
scripts/gates.sh export/mm9_peasantdm1.glb d55; SEL=hair HAIR_Y=1.25 $G scripts/hair_beard_gate.py export/mm9_peasantdm1.glb review/gates_d55/hair.json export/mm9_peasantdm1.glb
work/blender_queue.sh    # see-through d55, lod_check d55 (before/installed ran earlier)
$G scripts/viewer_tiers.py export/mm9_peasantdm1.glb red; scripts/shots.sh; scripts/close_shots_dm1.sh; $G scripts/shot_sheets.py d55
```
Install (orchestrator, on the OK): `check_winding.py export/mm9_peasantdm1.glb` (0), `tools/install_model.py export/mm9_peasantdm1.glb
--world mm9 --name mm9_peasantdm1.glb`, the `mm9_actor_models_build_every_binding` regression, and add to
`../mm9_peasantdm1_claude/README.md`: "LOD0 reduced post-install on <date> by `mm9_peasantdm1_reduce_claude`; a rebuild from this
project must re-run that reduction". Rollback: `before/mm9_peasantdm1.glb`.

## Not checked
In game (not installed; binding regression and floor audit after install); motion at speed by eye (frames, gates, stills only); LOD1-3
and shadow meshes by eye (numbers only); fingertips only at two rest-pose close-ups; the miner clips (Rock, Hammer, Dump, RubBeard) only
by gates, not by eye.

## MM9 sockets (2026-11-10)

The installed model carries MM9's attach points as `Socket_<name>` nodes for held items (scene `held_items`, MM9's AttachProp), added after this project's install by [`mm9_held_items_claude/scripts/add_sockets.py`](../../props/mm9_held_items_claude/scripts/add_sockets.py) (`Socket_RHand1`). A rebuild installed from here drops them: run that script again and install its export (`tools/install_model.py --world mm9`).
