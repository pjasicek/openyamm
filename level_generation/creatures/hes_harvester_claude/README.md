# The Harvester (Hesper boss 10104): rigged actor — Claude project

Round 3, "Claude A" of [CREATURE_BUILDS](../../../design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md): the Scour's
boss on the Great Pit's floor ([THE_SCOUR](../../../design/kreegan_world/zone2/THE_SCOUR.md), "Set piece: the
Harvester (M8)"; `harvester.lua`). A Kreegan-grafted Ancient mining machine: a drill on a hinged boom, crawler tracks,
bucket conveyors on both flanks, two heat vents behind the drill housing, a gooseneck slag sprayer at the rear, two
core drums with white-gold slots. The MM8 Demolisher (Juggernaut C) is only its stat and scale base (×3).

**Status (2026-10-23): built, staged, checked in the viewer and a desktop smoke run; the integrator accepted the shape
and clips and asked for a finish pass (below, done). In-game acceptance is the integrator's (openyamm-30); user
acceptance not recorded.**

[Review sheet](review/harvester_review.png) (concept, viewer frames, in game, the dig's vents) ·
[viewer shots](review/shots/viewer_sheet.png) · [Eevee poses](review/poses/) · [LODs](review/lods/lods_sheet.png) ·
[in game](review/ingame/run4/run4_sheet.png) · [HD masters](references_hd/selected_views_review.png) ·
viewer `http://127.0.0.1:8912/level_generation/creatures/hes_harvester_claude/review/viewer/`

## Concept

No sheet existed. Brief [`CODEX_BRIEF_HARVESTER.md`](../../../design/kreegan_world/concepts/monsters/CODEX_BRIEF_HARVESTER.md)
(the Great Pit concept z2_06's Harvester, the Sentinels' materials); two candidates by Codex image generation
(`codex exec`). The user had the integrator pick: **candidate 2** (crawler tracks, boom hinge hub, gooseneck sprayer
on a turning ring, bucket chain; the plates either side of the drill are the armoured front), saved as
`boss_harvester.png`; record `generation_runs_harvester.json` (approval block). Integrator's notes kept: the
white-gold core slot readable, the flank vents as separate glow regions with an open state for the dig, the
sprayer's glowing nozzle.

## Deliverables

| File | What |
|---|---|
| `export/hes_harvester.glb` | runtime actor: skinned mesh `Harvester`, materials `HS_Harvester` (2048 base, 1024 normal / ORM) and `HS_Glow_Harvester` (128x128 swatches as its emissive texture over a dark base, strength 1.25: blooms; the hull material emits orange through a 1024 seam mask), LODs **10 965 / 5 472 / 2 681 / 1 160** triangles + shadow LODs tucked inside, 8 clips, socket `Socket_Nozzle` |
| `export/hes_harvester_lod0.glb`, `_authored_lods.glb`, `.blend`, `_info.json` | LOD0 with rig and clips, LOD1..3 on the same rig, the editable master, measurements |
| `integration/actors.yml` | the staged binding `hes_harvester` (scale 100, cast/ranged = Spray from the nozzle, `dig` role) |
| `references_hd/` | Codex HD masters (00..04; 02_back redrawn in run 3 from `meshy_geometry_back.png` to match the model), briefs, runs |
| `meshy/`, `requests/` | the two Meshy jobs; `texturing/` the retexture upload and its four binary-alpha views; `textures/` the composed maps |

## Pipeline (`TOK=<lease> scripts/build_runtime.sh` rebuilds everything from the Meshy returns)

1. HD masters from the concept (Codex, `references_hd/CODEX_BRIEF.md`), `00_three_quarter_meshy.png` = 00 with binary
   alpha. Meshy Smart Topology (`meshy-t2`, 15 000, untextured) from it: 14.6k triangles in 275 pieces.
2. `parts.py`: orient (drill to -y, tracks at z = 0, 9.8 m long), split by component into body, drill (6 rings),
   boom (housing rings), sprayer (neck + nozzle) and 12 buckets; **Meshy mirrored the single rear sprayer into a
   second, lower nozzle: deleted** (components 46, 68); buckets moved (at most 16 cm) to an even 0.756 m spacing.
3. `prepare_uv.py`: planar dissolve + collapse (body 0.72) to 10.9k, smooth shading with sharp edges over 38°,
   **xatlas** charts and packing (`work/xatlas_venv`, `scripts/xatlas_uv.py`): Blender's Smart UV shattered the
   faceted shells into thousands of islands (36 % coverage); xatlas 47 %. The uploaded file is kept (xatlas packs a
   little differently each run; later runs write `work/harvester_neutral_rebuild.glb`). **Note:** one rebuild
   before this guard overwrote `texturing/harvester_neutral_upload.glb`, so it no longer has the uploaded hash; only
   the retexture's own mesh is used from step 4 on, so nothing depends on it.
4. Meshy retexture (`meshy-7`, 2K PBR, original UVs, views 01/03/02/04) → `adopt_retexture.py` (its mesh, parts by
   nearest face) → `dump_tris.py` → `compose.py` (the finish below, dilation, glTF normal, metal binarised,
   roughness ≥ 0.45 on ceramic; the glow swatches as their own 128 maps: no free square in the xatlas gutters; the
   orange seam mask).
5. `build_actor.py`: the added glow pieces, rig, clips, authored LODs (welded, small pieces dropped, collapsed;
   the glow pieces protected by a zero-weight group); then `prepare_actor_glb.py`, `link_lods.py`,
   `shrink_shadow_lods.py`, `claude_shared/emission.py` (the hull's seams), `set_emissive.py`, `check_key_times.py`,
   `floor_check.py`, `check_winding.py`.
6. Review: `render_review.py` (Eevee clip frames on a ground plane), `lod_views.py`, the viewer (`review/viewer/`,
   its `review.js` focus table refitted for a 10 m machine).

## Rig and clips (30 fps; every vertex rigid on one bone)

| Bone | Carries / motion |
|---|---|
| `B_Root` | ground centre, not animated |
| `B_Body` | hull, tracks, fins, drums, hoods: rumble, the lunge, the hit jolt, the death sag |
| `B_Boom` | hinge (0, -2.83, 1.20) between the gold hubs: the drill housing rings, tilt down 26° in the dig |
| `B_Drill` | the drill cone on its axis: spins |
| `B_Sprayer` | the gooseneck's foot (-0.43, 3.33, 2.05): swivels outboard (right flank) to spray; droops in death |
| `B_Vent_L/R` | the vent louvre plates: slide 0.6 m forward into the frames in the dig |
| `B_Bucket_R0..5`, `_L0..5` | the conveyor buckets: one step rearward per Walking cycle, the front one rising, the rear one sinking |
| `Socket_Nozzle` | the spray's release point (non-deforming) |

Standing 4 s (rumble, drill turning over, sprayer sweep), Walking 2 s (stride 2.8 m: speed 140 × 2 s), Attack 1.5 s
(drill lunge, impact 0.6 s), Spray 1.5 s (ranged and cast, release 0.6 s), **Dig 8 s** (0–1.2 s boom down so the drill
tip goes 0.38 m into the floor, vents light at 0.5–1.5 s, grind, vents dark at 6.5–7.5 s, boom up by 8 s), Hit 0.5 s,
Death 3 s (drill spins down, boom slumps 20°, hull sags and rolls, sprayer droops, vents half lit), Dead 1 s.
The hull rocks on its contact patch: every pose lifts or lowers `B_Body` so the underside's lowest vertex stays at its
rest height. Gates: key times PASS (480 samplers); 0 inverted closed parts; `floor_check.py` PASS (the hull's lowest
point within 2 cm of the floor in every frame of every clip; the dig's drill goes below on purpose).

## Finish (integrator review, 2026-10-23: "dirty and camouflaged")

Meshy painted the ivory with brown rust blotches, flagged the rust as metal and painted the cables brown. `compose.py`
classes each piece of the retexture mesh (connected by shared positions): a piece with at least 18 % light,
low-saturation texels is a **plate**, repainted warm cream (0.93, 0.85, 0.67) keeping only its fine detail (luminance
over a 3-texel blur) and a soft large-scale shade; all its "metal" is rust and goes ivory too (the plates have no crisp
trim to keep). The drill, boom and tracks are **steel** (0.21, 0.20, 0.21) by relative brightness; a piece mostly
metal is **gold** (one aged-gold ramp by luminance: buckets, rings, pivots); everything else is **resin**, the sheet's
dark violet-black (0.15, 0.085, 0.19) by relative brightness, its metal spots counted as grime. 250 pieces: 53 plates,
45 steel, 56 gold. No retexture needed (the integrator allowed one within the cap).

## Glow

- `HS_Glow_Harvester` (emissive texture = the swatches, base colour = them × 0.25 so the lit base does not wash the
  orange out; strength 1.25): the nozzle throat (orange disc), the two core-drum slots (white-gold strips laid onto
  the drums by ray casts; one per side, since Meshy made a drum on each flank), the vent louvres (eight hot orange-red
  bars between thin dark slats; hidden 0.6 m back inside each hood at rest, so the vents are dark except in the dig).
  The frames have a solid block 0.2 m behind them, so the concept's swinging hatches had no room: the louvres slide.
  Named `HS_Glow_…` because `emission.py` matches material names by prefix.
- The hull (`HS_Harvester`): orange seams, factor (1, 0.42, 0.1) through `textures/harvester_seam_mask.png`: resin
  texels within 12 cm of a plate on the upper hull (the plates overlap the cables, so a narrower band hid under them),
  broken into segments by a smooth 3D pattern so only some joints glow. `emission.py` clamps each channel at 1, so its
  strength stays 1 to keep the orange.

## Meshy spending (lease `hesper:harvester`, cap 60)

| Job | Kind | Credits |
|---|---|---|
| `harvester_st_v1` | Smart Topology, 15 000 | 5 |
| `harvester_retexture_v1` | retexture 2K PBR | 10 |
| **total** | backup account | **15** |

No paid animation (machine clips are procedural; nothing to ingest into `anim_library`).

## Staging and checks

- `hesper_stage/monsters.yml`: models entry `hes_harvester.glb`; row 10104 bound to `hes_harvester` (height 540 →
  360, radius 300 → 400: half width 2.2 m, half length 4.9 m). hes_out2 stores the old height on its placed actor,
  so the Harvester draws at 1.5× until the map is rebuilt (the "Actor sizes" audit, FIX_PROMPTS.md; the integrator
  ruled not to rebuild the Scour for it). The stand-in descriptor in `hesper_out2/actors.yml` and its
  `hes_harvester_standin.glb` model entry are left as they were (the Scour builder's).
- After the finish pass (final export): `stage.py` (1 GLB written), `rebuild_all.sh --scenarios-only` **73/73 PASS**
  (incl. `hesper_out2/scour_harvester`); viewer `check` 8/8 clips, no console errors; a minimised desktop run on the
  stage (hes_out2, `review/ingame/run4/`) draws it on the pit floor by the hopper tower, no "Actor model load failed".
  The dig, vents and spray in a fight are the integrator's in-game check after the out2 rebuild.

## Differences from the concept / open points

- Two core drums (one per flank) where the concept has one central drum; both slots glow.
- The sprayer stands on the rear right (Meshy's placement), not on the centre line; it swings to the right flank.
- The tracks do not scroll: `openyamm_uv_scroll` does work on skinned materials, but it runs all the time (also
  while it stands and digs), and the treads' texels sit in many xatlas charts, so a scroll would need its own tread
  material with a tiling strip UV; road wheels are part of the hull mesh.
- LOD3 (1 160) is ragged up close and shows a speck of the hidden louvre glow; it draws only when the machine is
  small on screen.
- Far LODs are authored here (as `hes_turrets_claude`), not by `lod_repair_claude/scripts/repair.py`, which works on
  installed models in `assets_source`.
