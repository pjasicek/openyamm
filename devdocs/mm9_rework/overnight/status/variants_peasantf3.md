# Variant peasantf3 (owner variants-c), 2026-11-02

- 10:20 lease claimed (mm9:peasantf3). Reading brief and the body project; comparing MM9 meshes.
- 10:45 MM9 comparison: PeasantF3.abc = PeasantF1.abc bind and skeleton (identical binds); clips are the shared PeasantFemale library.
  Differences: long veil down the back (Ponytail12, +20 cm), two braids (xpony chains), skins: F3a blonde in a blue dress, F3b dark-haired
  prisoner in a torn brown dress; both a low neckline. Rows 35 Prisoner (F3b, no DAT placement), 40 Shopkeeper (F3a, ShopkeeperHuman2FemaleA x8).
- Baseline: F1 rebuilt in a copy of its project = byte-identical to the installed mm9_peasantf1.glb.
- Veil (with lining and rim) and braids built (`scripts/add_parts_pf3.py`, +3.0k triangles), head set re-laid (`uv_pf3.py`, body UVs
  copied from F1 verbatim). Uploads ready. Codex HD masters (body 4 + head 4, skin A) running.
- 12:xx Meshy 20 credits (body + head retexture 4K, backup 3175 -> 3155). Faces: Codex repaint by landmarks (A blonde, B dark-haired).
  Gates: arm/hand 0 frames > 1 cm, jitter 0, robe 0, sleeve poke 0, bone length 0, winding 0, flat 0.00/0.01, floor ok.
  Installed `mm9_peasantf3.glb`, bound `MM9 40 Shopkeeper` (pf3_a) and `MM9 35 Prisoner` (pf3_b), tables regenerated, binding PASS.
  F1 files unchanged (sha256 proof in README). See-through gate running.
- FINAL r5: braids shortened to 82 % (bust contacts), installed, binding PASS 198/86, viewer r5 check 0 errors. 20 credits.
  F1 sha256 + project files unchanged. Open: headwear gate 1.2-2.7 cm braid ends on the bust in motion, veil 1.3-3.0 cm in head turns;
  see-through up the hollow dress for the corpse from its feet (F1 construction); LOD0 17.5k (>15k); tier B is a ramp (no dirt/tears).
  Lease released.
- 12:01 second pass started (orchestrator: cheek plates, chin block, under-jaw block, veil ledge, LOD0 < 15k, braid/veil contacts).
- PASS 2 (r16, 0 credits): ear-plate patches, chin crease/block, under-chin block, veil ledge fixed (skin_harmonize_pf3.py,
  chin_smooth_pf3.py, chin/neck normal relax, hood tucked under the veil); LOD0 17,494 -> 14,978 (grid_reduce_pf3.py on veil/braids,
  F1 skirt lining 60 %); braids <= 1.9 cm, veil <= 1.6 cm except Talk/Conv1/Cower 2.9. Gates all 0 (arm, jitter, robe, poke),
  binding PASS 201/88, reinstalled, viewer r16 0 errors. F1 and Hag unchanged (sha256).
- FINAL pass 2 = r17 (braids thickened to 12.5 mm). Reinstalled (sha 967f547d), binding PASS 204/90, viewer r17 0 errors, all gates 0.
  Lease released.
- 13:46 pass 3 started (user: chin/jaw profile, nose patch, veil teeth, temple blotches).
- PASS 3 (r21, 0 credits, user "check the profile"): chin 12 mm forward / 4 mm down + under-chin/neck corner carved, pass-2 chin smoothing and
  chin/neck normal relax removed, part seams held by position (nape seam had opened 4.6 mm); nose tip rounded and its dark paint cleaned;
  veil front edge one line (hood_edge_pf3.py); temple blotches to skin. Gates r21: arm 0, jitter 0, robe 0, poke 0, winding 0, flat 0.00/0.01,
  detached = 2 legs (as F1), braids <= 1.9 cm, veil <= 1.6 except Talk/Conv1/Cower 2.9; see-through unchanged (corpse up the skirt).
  Installed sha 5c6071d5, binding PASS 214/92, viewer r21 0 errors, floor ok. F1 unchanged (sha256), Hag untouched. Sheet:
  level_generation/creatures/mm9_peasantf3_claude/review/pass3/profile_sheet.png. Lease released.
- 14:38 pass 4: white zigzag on the cheek in profile.
- PASS 4 (r34, 0 credits; resumed after two reboots, memory cap from VARIANTS_BRIEF used): cheek "<" streak fixed. Cause: the 4-vertex
  hole beside each cheek that F1's tweak_pf1.py closes by collapsing its rim (folded wedges catch side light); F1 has the same. Fix:
  rim reopened on a small ring + 2-triangle cap on one skin texel; coincident vertices kept together. Gates 0, binding PASS 216/93,
  installed sha 8c7de192 (= export), viewer r34 0 errors. F1/Yrsa/Hag unchanged. Sheet review/pass4/profile_sheet.png. Lease released.
- 15:42 pass 5 started: fresh head paint per tier (user: eyes/nose/lip marks).
- PASS 5 (p5r14, 20 Meshy credits: two head retextures; backup now 2755, floor 1740): fresh head paint per tier on the current head
  mesh/UVs from Codex HD head masters. Viewer marks traced with viewer-only test GLBs: dark wedges under the eyes = eyeball sphere normals
  facing down (eyeballs now take the surrounding face's normal); lower-lip glint = 293 collapsed slivers spanning UV islands (own
  single-texel rows); lip parting = mouth normals biased forward; midline/nose seam specks and gutters repainted. Gates as pass 4 (headwear
  braids <= 1.9 cm), binding PASS 224/98, floor 35/40 ok, viewer 0 errors, installed sha 4c8f6d61 (= export). F1/Yrsa/Hag unchanged.
  Sheets review/pass5/viewer_ba_{a,b}_{head,body}.png, final_front_zoom.png. Remaining: pixel ticks on the nose ridge, faint mouth-corner
  arcs, white veil tick between ear and braid in 3/4 (pre-existing). Lease released.
