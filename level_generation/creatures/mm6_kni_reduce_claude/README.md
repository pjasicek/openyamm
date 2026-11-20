# MM6 Knight (`kni`, KnightPlate A/B/C) reduction (2026-10-14)

User: "do mm6_kni next". No-retexture route ([RETOPOLOGY_PLAYBOOK.md](../RETOPOLOGY_PLAYBOOK.md)) on the installed
`mm6_kni.glb` (8,403 tris: Codex round 3 had already cut it from 12.8k, `../mm6_kni_codex/`) and its held
`mm6_kni_sword.glb` (1,985). Scripts copied from `../mm6_ogr_reduce_claude/`. No Meshy credits.
Limits for the 1.9 m bind height: p99 5.7 mm, max 28.5 mm.

## Body: per-region budgets

The body is 60+ separate plate pieces. Gauntlets 1,116 + 1,128 faces (27 %), cuirass 815, cape 566, helmet 522.
Groups (`scripts/make_groups.py`): 1 helmet (head-dominated faces), 2/3 gauntlets, 4 cape, 0 the rest; pieces up to
80 faces (knee cops, crest strips, rivets, small plates) kept exactly. `scripts/run_groups.sh` as for the Ogre.

| config | triangles | p99 / max mm | finding |
|---|---:|---|---|
| uniform 85 / 75 / 65 % | 7,141 / 6,301 / 5,461 | 2.8-5.9 / 28-34 | max at the right knee cop and the helmet crest |
| helmet 80 %, gauntlets 50-60 %, cape 45 %, rest 85/75 % | 6,103-6,487 | 5.7-6.6 / 43.7 | fails: cape in the Death fall |
| cape 80 % (`c80`) | 6,463 / 6,081 | 4.2-5.4 / 28.2 | notch on the right tasset top edge (also uniform) |
| **after the weld fix, `w80` rest 80 %, one drift-lock round (`d80`)** | **6,281** | 4.8 / 25.9 | **pick**; IoU 0.993, SSIM 0.992 |
| `w80` rest 70 % | 5,889 | 6.0 / 26.2 | fails p99 |

**Weld bug (fixed in `scripts/import_source.py`):** the import welded every coincident vertex pair, including seam
duplicates that carry different weights. The fauld's outer layer took a `B_Pelvis` corner (the source has
`B_R_Thigh` there) and folded behind the tasset in every pose; keeping the fauld or the tasset exactly, or
piece-aware weights (`piece_weights` from `../mm6_djn_reduce_claude/`, also ported), did not help. The weld now
merges only duplicates with identical weights (32 vertices kept apart). The notch is gone with no extra kept faces.

Pick `d80r74` (`work/keep_d.npy`, `work/groups_a.npy`, ratios helmet 0.8 / gauntlets 0.5 / cape 0.8, rest 0.8):
gauntlets 2,244 -> 1,122. Texture drift: 3 faces above 40 (15 cm2) on the first step; one lock round (+50 kept
faces, +10 tris) leaves one face of 2.4 cm2.

**LOD maps:** the installed file had per-LOD materials with their own LOD normal maps (Codex round 3).
`tools/build_actor_lods.py` points every rebuilt LOD at the LOD0 material, so `scripts/prune_materials.py` drops the
nine unused LOD materials and three LOD normal maps (11.3 -> 9.8 MB; about 7 MiB less texture memory with mips).
It treats any `{"index": n}` in a material as a texture reference, so `openyamm_region_mask` stays.

## Sword

Parts (`scripts/sword_parts.py`, each part decimated on its own): grip wrap 868, blade 410, pommel 140 / 92 / 63,
guard 132, guard collar 68, grip core 116, gems 48 + 48.
- The plain prop ladder auto-picked 35 % (693) with the blade cut uniformly. On its own the blade breaks below 70 %
  (max 5 % of the sword length at 50-60 %); 70 % keeps it at 0.41 %.
- **Pick `a35` (989):** grip wrap 35 % (302; hidden in the fist, wrap pattern still visible), blade 70 % (286), the
  other parts 50 %, gems kept. Normals by angle (`PROP_NORMALS_ANGLE=35`): transferred normals took the far side of
  the thin blade (a black streak, even with the blade kept exactly). LODs 989 / 451 / 180 (the old 1,131 LOD1 is
  dropped as no longer coarser).
- Grip (`scripts/grip_gate_posed.py`, sword at the posed `Sword` joint): hand vertices near the grip scale with the
  gauntlet's vertex count, nearest 1.6 vs 0.8 mm from the axis (the grip is slightly thinner, no new contact).
  `review/props/grip_sheet.png` (Standing, mid-Attack): same grip.

## Result (staged, not installed)

`export/mm6_kni.glb` (= `mm6_kni_d80r74.glb`): LODs 6,281 / 3,129 / 1,105 / 344 (installed 8,403 / 5,172 / 2,110 /
697), shadow LODs rebuilt, variants on every primitive, eight influences, 8 clips unchanged.
`export/mm6_kni_sword.glb` (= `mm6_kni_sword_a35.glb`): 989 / 451 / 180.
LOD0 with the sword 10,388 -> 7,270 (-30 %).
Review: `review/faces/k8.png` + `k8_clay.png` (rows installed, pick, both at Attack frame 30), `review/faces/k7_tasset.png`
(tasset after the weld fix), `review/faces/k2_hands.png`, `review/props/sword_compare.png` (rows installed, g35
transferred normals, **a35**, k35 blade kept), `review/props/grip_sheet.png`, `review/ladder_sheet.png`.
Viewer `review/viewer/` (body only, installed vs pick per variant; `check_viewer.mjs` 48 switches, no console errors).

Install after review: `tools/install_model.py level_generation/creatures/mm6_kni_reduce_claude/export/mm6_kni.glb --world mm6`
and the same for `mm6_kni_sword.glb`, then the `mm6_knight_plate_actor_model_tiers_follow_sprite_scales` regression and
a ledger row. Rollback sources: `work/mm6_kni_source_pre_reduce.glb`, `work/mm6_kni_sword_source_pre_reduce.glb`.

## Round 2: original helmet, symmetry, retexture (2026-10-14)

User on the reduced pick: "DEFINITELY needs retexture for more saturated armor ... he looks completely bleached out ...
the shoulderpad skull details are important to stand out, head armor is important to match original, overall symmetry
needs to be preserved, cleaner lines". The v1 masters (`../mm6_kni_codex/`) had replaced the original skull-mask
helmet with a T-visor great helm and asked for "restrained silver edges and muted blue accents".

- **HD masters v2** (`references_hd/`, Codex, brief `CODEX_BRIEF.md`): the original skull-mask helmet with crest,
  upward horns and violet ram-horn spirals, black chrome with bright edges, saturated violet, readable pauldron
  skulls, symmetric; the banded cuirass of v1 kept so the views fit the mesh (run 1 painted the sprites' muscle
  cuirass; one targeted correction). Plus a four-view helmet turnaround.
- **Symmetry** (`scripts/symmetrize.py`): the knight's left half mirrored onto the right with mirrored weights, both
  gauntlets kept (the right one is the fitted sword fist). 6,281 -> 6,700 tris.
- **Helmet** (`requests/helmet_model_v1.json`, Meshy 7.1 multi-image, 30 credits): reduced texture-aware to 2,500
  (`scripts/helmet_reduce.py`), fitted rigid on B_Head (`scripts/graft_helmet.py`, uniform scale 1.15x the old
  helmet's depth: a box fit squashed the ram horns to half width), replacing the old helmet, visor, bolts and horns
  (938 faces). Its own Meshy texture is the helmet set (1K). The v1 hair plume (it arched over the head and rose above
  the new horns) is squashed into a cap behind the helmet and follows the head from 1.50-1.58 m up.
- **Body retexture** (`scripts/uv_upload.py`, fresh smart UVs at 94 %, helmet small in the upload corner;
  `requests/body_texture_v1.json`, 10 credits). Meshy credits this round 40; project total 70 of 100.
- **Compose** (`scripts/compose.py`): AO grade, native shading by height on the chrome (0.5), chrome contrast by a
  power curve onto the sprites' chrome median (body chrome median 0.030 -> 0.017 linear; a full rank map turned broad
  light-grey plates into near-white), regions trim (violet hue) and chrome on both sets, ramps from the aligned native
  pixels (`scripts/native_pixels.py`: trim gain 1.0, chrome gain 1.3 at chroma 0.6, since the sprites' blue reflections
  plus the engine's sky reflection gave a navy cast). MR: R specular mask (armour 1, hair 0.25), G roughness clamped
  0.22-0.5, B 0; material metallicFactor 0, specular on.
- **Runtime** (`scripts/build_rt.sh`): export -> `swap_multi.py` (installed clips/skin kept, helmet primitive added) ->
  `apply_textures.py` -> region_variants (body + helmet tier materials) -> LODs -> variants -> prune -> viewer.
  `export/mm6_kni_rt8.glb`: LODs 8,262 / 4,121 / 1,497 / 800 (body 5,762 + helmet 2,500).
- Checks: in-game captures per tier (`review/ingame/rt8_close.png`, temporary install, original restored), clay clip
  sheets (`review/sym/clips_sheet.png`, `review/sym/hair2_sheet.png`), viewer 48 switches without errors.
  Known: in Hit and Fidget the inherited hair shell still shows beside/over the helmet for a moment.
- Pipeline fixes found on the way: `viewer_variants.py` resized RGBA masks with premultiplied alpha (masks keep A = 0,
  so a 1K mask on a 2K base baked no tiers in the viewer); now per channel.

Install after review: `tools/install_model.py .../export/mm6_kni_rt8.glb --world mm6 --name mm6_kni.glb` and
`export/mm6_kni_sword.glb` (round 1 sword, 989 tris), then the knight regression and a ledger row.

Viewer also shows the unreduced original body (`../mm6_kni_codex/work/round2/baseline_mm6_kni.glb`, 12,815 tris,
the appearance the user accepted before Codex rounds 2-3) as `kni_*_u12k` next to installed and rt8.

## Round 3: reduction from the unreduced original (2026-10-14)

User, after comparing in the viewer: "unreduced original has OK mesh. can you perform the tris reducing on it instead?"
Source `../mm6_kni_codex/work/round2/baseline_mm6_kni.glb` (12,815, Codex round 1 textures and maps). Round-1 work
files for the 8,403 source are kept in `work/round1_8403/`. `make_groups.py` now takes the two largest
hand-dominated components as gauntlets (here the helmet is the largest piece); `build_pick.sh` takes `SRC=`.

- Calibration: Codex's installed 8,403 against this source is p99 4.3 / max 20.9 mm, inside the gate; what differs
  is its rebake (texture, normal map: dark slivers in the gauntlets, a red band on the fauld top, faceted gem).
  Texture-aware decimation here keeps the original UVs and maps.
- Ladder (helmet / gauntlets / plume / rest): 0.5/0.5/0.5/0.6 with rest 0.6 passes at 7,897; one drift-lock round
  (`keep_u`), then the chest gem and both knee cops kept exactly (`keep_v`, faceted otherwise). Lower helmet,
  gauntlet and plume ratios fail (max 33.5 mm, Death).
- **Pick `u7r65`:** `export/mm6_kni_u7r65.glb`, LODs 8,335 / 4,161 / 1,479 / 468, p99 5.46 / max 25.0 mm, IoU 0.989,
  SSIM 0.991, drift > 40 on 5 faces (11 cm2). Sheets `review/faces/u2_clay.png`, `u2_atk.png` (rows original,
  installed, pick). Viewer: original, installed, pick, rt8 per tier (96 switches, no errors).
- Not yet carried over: the round 2 helmet, symmetry and retexture (built on the round-1 cut).

### Master colour check before the round 3 retexture

User: "check the ORIGINAL master restored images if they align with the ones to be submitted to the meshy? I remember
the armor being really dark, and the coloured areas much more saturated." `scripts/master_check.py` (chrome luminance
and trim saturation/value per view against the restored x2 standing frames and native palette 760): the v2 masters
were silver steel, chrome median 0.17-0.26 vs 0.11-0.15, violet value 0.40-0.53 vs 0.27-0.30 (the round 2 Meshy
retexture used them, compose.py darkened the result afterwards). `scripts/grade_masters.py` grades the masters onto
the sprites (chrome luminance by rank, trim hue/saturation/value): `references_hd/graded/`, chrome 0.124 / p90 0.36,
trim saturation 0.44, value 0.29. Sheets `review/retex/master_check_v2.png` (v2 masters) and `master_check_graded.png`.

### Round 3 retexture on the new cut (`rt10`)

User: "do what you think best here". Round 2 work files backed up in `work/round2_rt8/`.
- `symmetrize.py` on `export/mm6_kni_u7r65.glb` (8,335 -> 8,620), `graft_helmet.py` (FIT=1.15) with the Meshy helmet
  reduced to 1,800 (`work/helmet_1800.glb`; 1,500 faceted the ram horns, review renders in the scratchpad), 1,250
  old helmet faces removed: 9,170 = body 7,370 + helmet 1,800. Fresh UVs (`review/retex/uv_upload_u7.png`).
- Meshy `body_texture_v2` (`requests/body_texture_v2.json`, graded masters, 10 credits; project 50 of its 70,
  mm6:kni 80 of 100): black chrome with blue-violet trim (`review/retex/body_texture_v2_sheet.png`).
- `rt9` (compose unchanged, `MESHY_BODY=body_texture_v2`): the darker trim luminance picked darker native trim colours,
  muted in game (`review/ingame/rt9_close.png`). **`rt10`**: `TRIM_GAIN=1.4 TRIM_CHROMA=1.2`
  (`review/ingame/rt10_close.png`, rows rt8 / rt10): vivid violet / red / ivory on black chrome.
- `export/mm6_kni_rt10.glb`: LODs 9,170 / 4,575 / 1,792 / 898. Viewer 120 switches, no errors. Grip gate with the
  round 1 sword: contact as installed, nearest 1.6 mm from the axis (installed 0.8), as in round 1.
- Rebuild: `MESHY_BODY=body_texture_v2 TRIM_GAIN=1.4 TRIM_CHROMA=1.2 python3 scripts/compose.py && bash scripts/build_rt.sh rt10`.

Install after review: `tools/install_model.py .../export/mm6_kni_rt10.glb --world mm6 --name mm6_kni.glb` and
`export/mm6_kni_sword.glb`, then the knight regression and a ledger row.

### Retexture of the new cut as it is (`ro1`)

User: "i thought you would use the model for head/body I said 'ok' and just retexture that?" (rt10 had replaced the
helmet, mirrored the body and changed the hair). rt10 work files are in `work/round3_rt10/`.
- Masters: the Codex v1 masters (`../mm6_kni_codex/references_hd/`, T-visor helm, banded cuirass: they match this mesh)
  graded onto the sprites with `scripts/grade_masters.py references_hd/graded_v1 ../mm6_kni_codex/references_hd`
  (chrome 0.17-0.20 -> 0.124, trim hue +24 deg to 257, saturation 0.30 -> 0.43; `review/retex/master_check_v1*.png`).
- `scripts/orig_uv_prep.py export/mm6_kni_u7r65.glb`: work/uv.blend and the upload with the cut's own UVs (58 %
  coverage, 0.6 % overlap). Meshy `body_texture_v3` (`requests/body_texture_v3.json`, original UVs, 10 credits;
  project 60 of its 70, mm6:kni 90 of 100).
- `MESHY_BODY=body_texture_v3 HELMET=0 Z_TOP=1.9 TRIM_GAIN=1.4 TRIM_CHROMA=1.2 python3 scripts/compose.py` (body-only
  mode), `bash scripts/build_orig.sh ro1`: `export/mm6_kni_ro1.glb`, LODs 8,335 / 4,161 / 1,479 / 468, geometry,
  skin and clips of the cut unchanged.
- Review: `review/ingame/ro1_close.png` (rows installed / ro1), `review/retex/ro1_vs_native.png`; viewer 144
  switches, no errors.

Install after review: `tools/install_model.py .../export/mm6_kni_ro1.glb --world mm6 --name mm6_kni.glb` and
`export/mm6_kni_sword.glb`, then the knight regression and a ledger row.

### Level feet (`ro2`)

User: "fix the feet, not being idle on the ground flat". The installed clips hold both soles rolled about 9 deg
(5.8 deg pitch + roll) in Standing, Fidget and Attack (bind pose flat within 0.5 deg); Hit up to 43 deg.
`scripts/flatten_feet.py export/mm6_kni_ro1.glb export/mm6_kni_ro2.glb Standing:full,Fidget:full,Attack:full,Hit:roll`:
foot rotations levelled about the ankle while planted (full: roll and pitch; roll: Hit keeps its toe pivot), B_Pelvis
lowered so the planted sole keeps its original height. Now 0.0 deg in Standing/Fidget/Attack (0.8 max), roll at most
2.2 deg in Hit; Walking/Running/Death untouched. `review/faces/feet_front_ro.png` (columns ro1 / ro2, rows Standing,
Fidget, Attack; `scripts/feet_front.py`).
Install `export/mm6_kni_ro2.glb` (supersedes ro1) with `--name mm6_kni.glb`, then the sword, regression and ledger row.

## Installed (2026-10-14)

User: "accepted". `export/mm6_kni_ro2.glb` -> `assets_source/worlds/mm6/models/mm6_kni.glb` (sha256 92c8ca3e...) and
`export/mm6_kni_sword.glb` -> `mm6_kni_sword.glb` (0c4c3bff...) with `tools/install_model.py`. Regression
`mm6_knight_plate_actor_model_tiers_follow_sprite_scales` passes (`review/checks/regression_ro2.log`). Ledger row added.
