# Variants: MM9 Wyrde family (wyrd_young row 265 Morgan, wyrd_mature row 264 Verdandi) — owner wyrde-agent

Project `level_generation/creatures/mm9_wyrde_claude/`, lease `mm9:wyrde` claimed 2026-11-02 10:50 UTC.

- 10:50 lease claimed. `meshcmp.py wyrd_young:wyrd_mature`: head/torso/arms/legs p90 0.0 cm, max 0.0: identical mesh (558 faces, MM9 human
  female skeleton, 73 joints, bind identical to PeasantF1's). Skins: same design and gold trims/jewellery; differ in face + hair (Morgan young
  blonde, Verdandi ~60 brown hair with braids, earrings), mantle (blue plain vs green damask), gown (plum vs brown, Verdandi with a belt cord).
  Plan: one Meshy body painted from Morgan's clothes; Verdandi = tier (mantle/gown ramps, damask + cord channels projected from MM9's skin),
  own 1K head colour per tier.
- Rows: 264 and 265 only (wyrd_old row 263 out of scope). MONSTERS ScriptName basemelee.scr, clip library PeasantFemale. DAT objects:
  hallofthegods `WyrdeoftheKnowing0` (264), `WyrdeoftheKnown1` (class WyrdeoftheUnknown, 265), no ScriptName; WG_NPC334.scr only toggles
  their visibility in the win cutscene; no script plays an animation on them. (darkpassageway `WyrdeoftheUnknown0` is class WyrdeoftheKnown =
  Igrid, row 263, NPC338.scr, no animation.) The `Wyrd*stat` props are statues (PropAnim `statue`, sculpt skins, scale 9): not actors, not in
  scope. Clips carried: MM9 roles only (Standing stand1, Walking Walk, Running run, Fidget Fidget4, Hit Wince1, Death Die1, Dead, Cower).
- 11:05 Codex HD master run 1 (three-quarter) started.
- Credits: 0 / 60.
- 11:30 HD masters gated (Codex run 1 three-quarter, run 2 four views; `references_hd/`, sheet `review/masters_vs_mm9.png`).
  Smart Topology 5 cr (backup 3085 before). One fused shell (head, hair, hood, cowl, mantle, gown, sleeves with closed cuff caps);
  split by crease-cost Dijkstra (`seg_wy.py`) + a straight hood/cowl cut behind the face (`assemble_wy.py`); sleeves pulled onto MM9's
  arm, MPFB hands with forearm stubs through the cuff caps; sphere eyeballs, socket rims relaxed, ears pressed in.
- 12:00 UVs (`uv_wy.py`: body 62.0 %, head 55.2 %). Body retexture 4K 10 cr (backup 3080 before). Rig on MM9's 73-joint female skeleton
  + MPFB fingers; PeasantFemale clips (MM9 roles only: no script plays any clip on these rows).
- 12:20 Codex head turnarounds (Morgan, Verdandi). Head retextures 4K: Morgan 10 cr (backup 3070 before), Verdandi 10 cr (3060 before).
  Credits so far 35 / 60.
- 12:40 Tiers: one body paint (Morgan's clothes), ramps R mantle / G gown / B Verdandi damask (MM9's own pattern, planar) / A Verdandi cord;
  per-tier head colour (face, hair, hood quantile-matched to MM9's mantle). See-through r1: hood interior beside the jaw 177 px, cowl in
  the fall 272 px -> linings of the faces seen from behind (`visible_backfaces.py` + `linings_wy.py`), LOD0 14,498.
- 13:00-13:40 Face pre-screen against MM9 (`review/sheet_faces_vs_mm9.png`, `review/sheet_r4_face.png`): fixed cheek seam lines (gutters),
  Morgan's brown under-hood hair -> blonde, nose underside smudge -> skin + soft nostrils, throat green wedge/red band -> skin, a painted
  forehead pearl -> skin, eyelids painted on the rigid eyeball spheres; hands one clean skin. See-through r5: every zone <= 7 px in every
  clip except Death torso 26 px (r1: 177 / 272 / 63). LOD0 14,931.
- 13:45 Installed `assets_source/worlds/mm9/models/mm9_wyrde.glb`; bound `MM9 264 Wyrde of the Knowing (Verdandi)` (wy_mature) and
  `MM9 265 Wyrde of the Unknown (Morgan)` (wy_young) under the flock; rows 264/265 in `mm9_npc_actor_rows.tsv` (fallbacks 380/384); tables
  regenerated (9264, 9265). `mm9_actor_models_build_every_binding` PASS (204 on 90 models). Floor audit ok. Viewer check 0 errors.
  Credits 35 / 60 (backup 3085 at start). Map placement not switched (orchestrator). README has the details and open points.
- 14:10 Regression: binding PASS; suite 190 passed / 3 failed (out05 known + two map-load failures caused by another session's 13:44 edit of worlds/mm9/modifiers.yml, 'taunt_seconds' unknown to the build). Lease released.
- 15:20 Review pass (orchestrator, 0 credits; lease re-claimed): forehead pearl gone (head colour; normal flat; not in body/ramps), noses clean
  skin + soft nostrils (paint, flat normal, 2 mm geometry relax), eyelids lowered in geometry (9 / 5 deg) + per-tier lid paint (Verdandi
  squint), Morgan's scalp blonde with strands, lips one shape (Morgan soft rose, Verdandi natural), Verdandi's damask non-mirrored brick
  repeat, true profiles + low 3/4 vs MM9 (chins fine). Sheet `review/sheet_faces_before_after_r5.png`. See-through r6 as r5 (<= 7 px, Death
  torso 26), arm/hand 0 frames > 1 cm, jitter 0, binding PASS (214 on 92), floor ok, reinstalled r9 (sha e2173398438a). Lease released.
- 16:30 Mouth pass (orchestrator, 0 credits; lease re-claimed): lips not proud and one piece (the pout was Meshy's 1.9 cm paint); old lip
  area -> skin, thin one-colour lips on a 5.2 cm slit curve (Morgan calm, Verdandi corners +3.5 mm, soft smile lines), mouth cavity painted
  muted rose (a geometry relax of the mouth opened the cavity: dropped), normals relaxed at mouth and nose underside (pale fold / dark V),
  nose underside relax 4 mm. Sheet `review/sheet_faces_before_after_r14.png`. See-through r7 as before, arm/hand 0, jitter 0, binding PASS
  (214 on 92), floor ok, viewer 0 errors, reinstalled r14 (sha 8275fd6e7f31). Lease released.
- 17:30 Face form pass (user notes on r14; 0 credits; lease re-claimed): cause = my r9-r14 nose relax, normal relax, flattened head normal
  and flat nose/thin-line mouth paint; Meshy's geometry has a proper nose and modelled lips. Undone (Meshy nose geometry, NRELAX 0, Meshy
  head normal, Meshy nose and mouth paint), paint only toned (nostril darks lifted, lips one rose per tier). No sculpt, no Codex repaint, no
  Meshy job needed. Sheet `review/sheet_faces_r14_vs_r16.png`. See-through r8 as before, arm/hand 0, jitter 0, binding PASS (214 on 92),
  floor ok, viewer 0 errors, reinstalled r16 (sha f56f8f2407e6). Lease released.
