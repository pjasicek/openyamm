# MM9 Dragon King (mm9_dragonking) — 3D boss model, 2026-10-30

The final boss of the Dragon's Lair (`dragonstadium.odm`, map 9079): MM9 monster 212 "Dragon King" (OpenYAMM 9212,
descriptor `MM9 212 Dragon King`, one skin GREENDRAGONLT), from `mm9/extracted/MODELS/MODELS/DRAGON.abc` (113 joints,
1,334 triangles, 15 clips, 6 sockets). Built on the MM9 rig-reuse route of `../mm9_dfly_claude/` and
`../mm9_lobber_claude/`: a new HD Meshy mesh posed to the MM9 bind pose and weighted to the ORIGINAL MM9 skeleton, the
MM9 clips played resampled, MM9 clip events as action times. Progress, hashes and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_dragonking.glb` (installed; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml` block "MM9 Dragon King", scale 100 (= MM9 size: about 1,820 units standing, wings to 2,350) |
| Triangles LOD0/1/2/3 | **12,675 / 6,336 / 2,257 / 735** since the 2026-10-30 head/jaw rework (LOD0: body material 7,433; head material 5,242 = head, horns, frills, eyes, 21 teeth 4,105 + mouth cavity 1,137); was 11,350 / 5,665 / 2,021 / 655; smooth-shaded |
| Skeleton | the MM9 one, 113 joints, names unchanged, + `Socket_Mouth` on `Xjawbase` (the node of MM9's own `RangeAttack` socket) |
| Textures | no tiers. Body (`DragonKing`): 2K base colour (graded), 1K normal, 1K metal-rough. Head (`DragonKing_Head`, since 2026-10-30): 2K base colour (graded; Meshy head retexture + Codex mouth swatches), 1K normal, 1K metal-rough; each with its material class map (specular per texel) |
| Meshy credits | **55 / 60** (Smart Topology 5, retexture v1 10, retexture v2 10, head retexture v1 10, texture pass body 10 and head 10; backup account; limit raised from 40 for the texture pass) |

## Texture quality pass (2026-10-30) - current maps

`../claude_shared/TEXTURE_QUALITY_PASS.md`, `../claude_shared/MM9_TEXTURE_PASS_BRIEF.md`. The user approved the model and
clips; mesh, rig, weights, clips, sockets, smooth shading, the mouth cavity and the flat fly lift are kept. UVs and texture
maps changed. **20 Meshy credits** (body 10, head 10, backup account). The head set missed the targets (atlas 30.6 %,
fragments 12.9 %), so it was redone too. Scripts: `scripts/texpass/`.

| `texture_quality.py`, LOD0 | Body before | Body after | Head before | Head after |
|---|---|---|---|---|
| Atlas use (2K) | 35.9 % | **55.9 %** | 30.6 % | **50.9 %** (mouth strip included) |
| Equivalent fully used square | 1,227 px | **1,531 px** | 1,134 px | **1,462 px** |
| Density p10 / p50 / p90 | 1,103 / 1,132 / 1,156 | **1,369 / 1,416 / 1,454** (+25 %) | 623 / 711 / 748 | **896 / 935 / 978** (+31 %) |
| Spread p90/p10 | 1.05 | 1.06 | 1.20 | 1.09 |
| Islands / surface on fragments | 284 / 3.3 % | 175 / **1.2 %** | 610 / 12.9 % | 257 / **4.2 %** |
| Stretch p90 | 1.05 | 1.18 | 1.48 | 1.19 |
| Meshy source | 2K | 4K | 2K | 4K |

Body density is about 51 texels per unit, head about 197. Two targets are missed: the head atlas (50.9 % against 55 %) and
its fragments (4.2 % against 3 %, 12.9 % before). By UV area about a third of the fragments is the 21 teeth, cut into 113
small islands (1.6 %), and the eyes (0.1 %); the rest is skin (3.0 %, 66 islands). Merging harder (merge_below 40) made it worse
(5.3 %), and the paid layout was not changed for it.

- **Body UVs** (`scripts/texpass/uv_body.py`, `work/head_v1.blend` -> `work/texpass/uv_final.blend`): `uv_atlas.py` on the
  body faces alone. Head, teeth, eyes and cavity stay in the upload so Meshy sees the whole dragon, with UVMap collapsed to
  one point (no atlas spent, as the Winged Mutant). The seven quads of the mouth rebuild were triangulated (export did so
  anyway); no vertex moved.
- **Head UVs** (`scripts/texpass/uv_head.py`, merge_below 24): `uv_atlas.py` on the head faces without the mouth, packed
  into the whole band under the mouth strip (v 0..0.8; new `height_share` option), not the old 0.8 square that left the right
  fifth of the set empty. The upload carries these exact UVs, so the head needs no rescale.
- **Mouth strip**: its UVs did not change, so all four head maps keep the approved strip byte for byte above v 0.803
  (`compose_head.py`, `pin_tone.py --strip`). Nothing there was rebuilt.
- **Packing**: xatlas's fast packer is not monotonic. Ten brute-force steps found nothing in 27 minutes (51.8 %), a 0.1 % fine
  sweep reached 55.9 % in about 5 minutes (new `fine=` option, `steps=0`). Chart variants (max_cost 4, merge 24, roundness 1)
  gave 53.0-55.6 % on the body; the head took merge 24 (42.5 % against 41.0 % before the strip).
- **Retextures**: `requests/retexture_texpass.json` and `head_retexture_texpass.json`, same masters and head references,
  `meshy-7`, 4K, our UVs. Both returns report the upload's layout (55.9 %, 42.4 %). Meshy's roughness comes back at 2K.
- **Maps** (`compose_body.py`, `compose_head.py`): colour padded at 4K and downsampled once to 2K, normal and
  metal-rough to 1K, AO re-baked on both new layouts. Grade gentle (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast
  1.06 --saturation 1.15`).
- **Classes**: body classes from the new paint's own colours and rig groups, the rules of `compose_dragon.py` with a 9-texel
  smoothing because the new scale net is much finer. A first try carried the old mask over; replaced before install
  (bat lesson, 2026-10-14). Head classes from geometry tags as before.
- **Drift and pin** (`pin_tone.py`). The fresh paint came back darker and grainier: body skin 76/90/13 against the approved
  87/95/19, membrane 27/32/9 against 34/37/15, eyes 86/79/24 against 143/134/6, and skin fine detail 1.8x the approved. Per
  class the new colour takes blur(approved - new) over 14 texels, and detail finer than 12 texels is scaled to 1.5x
  the approved on skin (x0.85) and 1.3x on membrane (x0.91). Result: skin 86/95/18, membrane 33/37/15, head skin
  54/59/7 against 53/59/7, luminance sd skin 54 against 52, membrane 29 against 31. The first pin (sigma 24, membrane only)
  left the neck back lighter than approved; a tighter skin grain of 1.2x washed the belly out.
- The neck seam is as approved: both sets are pinned to their approved colours.

**Checks.** Winding 0 inverted; installed (`tools/install_model.py --world mm9`, source = export); viewer
`r4_dragonking_texpass_20261030`, `run_creature_review.py check` 12 clips, 0 console errors; flat-shading 0.04 on both
materials; `detached_parts_audit.py` output identical to the approved GLB (1 part, 0.0127 in one Death frame, as before);
`glb_diff.py` (`work/texpass/glb_diff.txt`): all clips same keys and durations, every vertex matched at rest, largest
posed difference 1.8 mm (0.18 world units); the likely cause, not traced, is skin-weight rounding at the merged UV seams. LOD0 vertices 12,128 ->
10,829 (fewer UV seams). LOD2 2,258 -> 2,257 triangles. `floor_audit.py --world mm9`: Dragon King ok (stand -0.1..0, corpse 0.0). Regression `--world mm9
--headless-run-regression-suite actors`: `mm9_actor_models_build_every_binding` PASS (66
descriptors on 32 models, 0 failed), and the MM6-MM8 model case too (647 on 185). The rest of the suite was cut off by a 280 s
limit on this run. Yrsa's `Hit sinks to -5.4` in the floor audit belongs to that project, not to this pass.

Accepted from review-viewer shots, `review/texpass_before_after_sheet.png`: 14 identical cameras, full body, wings, chest,
belly, feet, head and the open mouth (Hit 0.4 s; the Fidget 0.75 s head leaves the viewer's framing). One skin, so one tier.
Before state: `work/before_texpass/`. Numbers: `work/texpass/` (`uv_final_*.json`, `pin_*.json`, `quality.json`).

## Smooth shading fix (2026-10-30)

The installed model was fully flat-shaded: every LOD0 triangle's vertex normals equalled its face normal, with 5.6
vertices per unique position (33,793 vertices for 11,350 triangles), so every triangle showed (the look the user
rejected on another model: "I can see the rectangles composing the model").

- **Cause.** `scripts/fit_dragon.py` builds `Body` as a new mesh (`bpy.data.meshes.new` + `bm.to_mesh`), and Blender
  makes a new mesh's faces flat. No later step (rig, reduce, UV, xatlas, mouth, export) smoothed them
  (`scripts/probe_smooth.py`: 0 smooth faces in every work blend), so the glTF export wrote face normals and split
  every vertex per face. The xatlas layout was not the cause (its UV seams split vertices only along chart edges).
- **Fix** (`scripts/build_export.py`, before the clips): `shade_smooth()`, then hard edges only at real creases
  (dihedral angle above 60°: horn and claw ridges, spike tips, membrane rims) and around the mouth-patch lip faces
  (`mouth_uv.py`; they are a UV seam already and open into the mouth when the jaw drops): 1,621 of 17,414 edges. Other
  UV seams stay smooth. UVs, textures, weights and clips are unchanged (clip report identical).
- **Normal map.** Meshy's tangent-space map is a detail map, not a bake against the flat normals: per-triangle mean
  |xy| 0.03 against a flat-to-smooth tilt of 0.20, correlation −0.05 / ±0.02 (x / y). It reads the same on the smooth
  normals (no re-bake).
- **Result.** Flat fraction LOD0 1.00 → 0.04 (the 4 % are faces closed in by crease edges: teeth, spike tips), LOD1–3
  0.99 → 0.02–0.10; vertices per position 5.6 → 1.7; LOD0 vertices 33,793 → 10,404. Triangles unchanged: **11,350 /
  5,665 / 2,021 / 655**. Meshy credits: **0** (total still 25 / 40).
- Before/after close-ups (head ¾, head profile, body; textured and clay): `review/shading_fix_20261030.png`
  (`scripts/shading_closeups.py`). Previous runtime GLB kept as `work/mm9_dragonking_flat_before_20261030.glb`.
- Checks: winding 0 inverted closed parts; installed (`tools/install_model.py --world mm9`); viewer refreshed
  (`r2_dragonking_smooth_20261030`), `tools/run_creature_review.py ... check` 12 clips switched, 0 console errors;
  `floor_audit.py --world mm9` 49/49 ok (Dragon King stand −0.1..0, corpse 0.0).

## Head set, real mouth and fly bob (2026-10-30, user review)

User: "needs own head texture, jaw (fidget frame 36), otherwise fine (just check the 'head bob' when flying, the wings
pushing the body 'up' when they go below z<0)" (41.png: blurry, blotchy head; 42.png: the red lip curtain). Sheet
`review/headjaw_rework_20261030.png`:
- 41.png's framing;
- Fidget frame 36 at 48 fps (0.75 s) in 42.png's framing;
- the other mouth-open extremes before and after, side and into the mouth;
- clay shading;
- the fly-loop head-height plot (also `review/fly_head_height_20261030.png`).
Head-set preview: `review/head_set_preview.png`. Scripts: `scripts/jaw/`. Previous runtime GLB:
`work/mm9_dragonking_before_rework_20261030.glb`.

**Jaw: cause.** Meshy modelled a short open mouth: a side slot about 0.15 tall from the snout tip back to y -4.1, with
the teeth in it, a shallow palate and floor and a small pocket to -3.77. The rest of the snout is one closed shell. MM9
hinges the jaw at y -3.1. The old split (`reweight_mouth.py`) used a plane fitted to the MM9 mouth that ran about 0.3
above the real slot, through the eyes. So the upper lip, all upper teeth (every tooth was weighted to `Xjaw`) and half
of each eye moved with the jaw. The 139 "lip" faces across the plane stretched into the red curtain over a hollow head
(edges up to 58x).

**Jaw: fix.** `scripts/jaw/mouth_rebuild.py`, on `work/uv_v2f.blend`, replaces `reweight_mouth.py` and `mouth_uv.py`:
- **Mouth line.** Measured from Meshy's slot with side rays (centre z = 15.822 + 0.187 y, 18 stations), continued from
  the Meshy corner (y -4.10) to a new corner at y -3.40, 0.3 in front of the MM9 hinge. Meshy's loose tongue is removed.
- **Cavity cutter.** Built station by station (24 stations):
  - palate vault: up to 0.36 deep, at least 0.06 under the outer skin (ray-clamped per vertex);
  - floor with sulci and a raised tongue: at least 0.05 over the jaw's underside;
  - slit at the skin: Meshy's slot minus 0.04 in front of the corner, narrowing to 0.022 at the new corner;
  - throat: inside the head, turning down to y -2.85.
  An exact Boolean difference (hole tolerant) cuts the shell in front of y -2.3. The cutter's faces become the cavity:
  palate 607 and floor 529 triangles, with their own UVs in the head set's top strip (isotropic, 0.18 UV per unit). Eight
  Meshy interior faces left inside the cutter became cavity tissue.
- **Weights.**
  - Shell vertices in front of y -3.52 split by connectivity: snout-top flood 706, chin flood 379, 0 shared.
  - The cheek corner blends over a 0.15 band.
  - Cavity: palate to the skull, floor to the jaw (nearest MM9 label of that side). Over the last 0.45 before the
    corner this blends into a ring rule (floor bottom 0, palate top 1) that runs through the throat. The jaw share fades
    out toward the hinge, because points behind the pivot would rise into the palate.
  - Eyes are rigid to the skull. Each tooth is rigid to the jaw whose gum holds its root deeper (11 upper, 10 lower).
- **Teeth gate** at bind, the most closed pose (every clip starts at jaw 0). Height fields are cast from inside the
  mouth gap: 0 of 21 teeth in the opposite jaw, 20 roots inside their gum (one root at the lower lip edge), no tooth
  moved.

**Jaw: mouth-open clips** (jaw against bind, `scripts/jaw/jaw_angles.py`): Death 44.5 deg (1.17 s), Cast 41 (1.0 s),
AttackRanged 33, Land 33, Fidget 31.5 (0.87 s), Hit 29, Taunt 29.

**Jaw: stretch.**
- Cavity (`scripts/jaw/mouth_stretch.py`, every frame):
  - texel stretch sqrt(area): p99 1.47 (Fidget) to 1.83 (Death), max 3.3 at the new corners;
  - edge length: p99 2.1 to 3.2 (the corner and throat sides lengthen along the opening).
- Whole model (`scripts/gates.py`, `review/gates_20261030.json`): edge p99 at most 2.08 in every clip. Only 7 edges
  stretch over 10x: the 0.02 corner-slit edges, at most 0.41 long posed. Before, 84 edges stretched over 10x, up to 2.9
  long.

**Head set.**
- **Head faces** (`scripts/jaw/head_split_dk.py`): 5,246 triangles, with their own material `DragonKing_Head` and
  `HeadUV` (Smart UV, then x0.8 into the lower-left; the cavity in the top strip). They are:
  - faces with a mean weight of at least 0.5 in the `Xheadpiv` subtree, above a level neck cut at z 14.45 (the throat
    follows the jaw's bottom fins far down the neck);
  - every loose part on the head (eyes, teeth, side frill);
  - the cavity.
- **Codex head turnaround** (`references_head/`, one run through `claude_shared/codex_slot.sh`): front,
  three-quarter, profile and back views, plus palate and floor swatches. Our textured renders were the shape and camera
  authority. Gate: the silhouettes overlay, except two of the four tall head spikes (Codex paints two horns plus the
  crest; Meshy painted all four as horns).
- **Meshy head retexture** (`requests/head_retexture_v1.json`): upload of 4,105 triangles without the cavity,
  `enable_original_uv`, 2K, **10 credits**, backup account.
- **Compose** (`scripts/jaw/compose_head_dk.py`):
  - the retexture is resampled into the 0.8 square and graded like the body (`grade_basecolor.py`, with a head AO
    baked through HeadUV by `scripts/jaw/bake_ao_head.py`);
  - the skin is matched to the body across the neck (texel bands above and below the cut): luminance gain 0.84 plus
    half the remaining colour cast;
  - the cavity strip comes from the Codex swatches, warped per UV column so the gum bands sit on the lip edges, with a
    normal from the swatch relief and roughness 0.35;
  - classes (skin, tooth, eye, mouth) come from the geometry tags.
- **Body maps** are unchanged; their old head islands and mouth patch are now unused.
- **2K head base colour** instead of the playbook's 1K: at 1K the head would hold 242k texels, fewer than the 271k it
  had in the 2K body atlas, so it would be no sharper. The head base colour matches the body's 2K; its normal and
  metal-rough stay 1K.

**Shading.** The smooth shading of the morning fix is kept. `build_export.py` smooths, with hard edges above 60 deg
and now along the cavity rim instead of the old lip faces. Flat fraction 0.04 on both materials (`flatcheck.py`); the
4 % are faces closed in by crease edges (spike and claw tips, teeth).

**Fly bob: cause.** The floor pass used per-key `--raise Walking/Running`, which lifts the root at every key by the
depth of the lowest point. In the fly loop that point is a wing tip at the bottom of the stroke, 2.26 to 2.30 below the
floor. So the root jumped 2.49 for about 0.25 s per beat: a head range of 2.61, against MM9's own 0.63.

**Fly bob: fix.** `--raise-uniform`, a new backward-compatible option of `claude_shared/floor/floor_fix.py`, applies
one lift for the whole loop: the depth of its lowest point over the loop (Walking +2.485, Running +2.524). The body
follows MM9's own vertical motion, and the wing tips touch the floor only at that one extreme.
- Head range is now 0.626 / 0.625 (MM9: 0.626 / 0.625), root range 0, loop seams 0.
- The 0.25 s blend from Standing is unchanged.
- Ground clips (Standing, attacks, Cast, Hit, Fidget, Taunt) keep their feet on the floor: the root is fixed at 8.317
  (MM9's 8.545 minus the 0.229 foot-contact correction), with per-key raises of at most 0.053 (about 5 world units).

## Clips and the MM9 three-attack design

MM9's `dragon.scr` has a fireball (`rAttack1`, far targets), a flame-thrower breath (`Rattack2`/`Rattack3`, targets
within 230), a wing attack that pushes (`WingAttack`) and a hand attack whose clip the model lacks. Its MONSTERS.txt row
lists attack 1 `DragonFireBolt`, a redundant attack 2 and the authored third attack `DragonBreath2`;
`devdocs/mm9/MM9_MONSTER_LEGACY_SPRITE_MAPPING.md` folds the breath into OpenYAMM attack 2 (two direct attacks), and the
monster row casts Incinerate (90 %) and Dark Grasp (10 %). The engine plays one clip per role (both attacks carry a
missile, so both play `attack_ranged`; spells play `cast`):

| Role | Clip (30 fps) | MM9 source | Event (impact) |
|---|---|---|---|
| standing | Standing 2.0 s loop | stand | — |
| walking / run | Walking 1.4 s / Running 1.07 s loop | fly (Running ×1.31, whole frames) | — |
| fidget | Fidget 1.8 s | fidget1 | — |
| attack_melee | AttackMelee 1.0 s | WingAttack | 0.533 s: the wing clap (peak forward sweep; MM9's `WingAttack` event at 0 starts the push) |
| attack_ranged (attack 1 fire bolt, attack 2 breath bolt) | AttackRanged 1.0 s | rAttack1 | 0.417 s `RangeAttack`, glow + release at `Socket_Mouth` |
| cast (Incinerate, Dark Grasp) | Cast 2.0 s | Rattack3 (the breath) | 0.833 s `BreathAttack` (breath ends 1.333 s), glow + release at `Socket_Mouth` |
| hit | Hit 0.9 s | wince1 | — |
| dying / dead | Death 3.5 s, Dead 1.0 s | die1 (corpse wings eased onto the floor), last pose | — |
| script `taunt`, `land` | Taunt 2.2 s, Land 5.8 s | taunt, land (fly-in from 71 units up) | for a boss script |

The breath is the cast because the cast is the action seen most (spell use 90 %) and Incinerate is a fire breath in
look; the MM9 fire-bolt spit serves both missile attacks. MM9's `HeadFollow` is the binding's `look` over
XneckB / Bip01 Head / XneckD (50° yaw, 35° pitch). Unused MM9 clips: gdsetup01, fidget2, spitacross, Rattack2 (same
motion as Rattack3), wince2. MM9 `Velocity` death events (a slide) are not reproduced (clips are in place).

## Route

0. **HD masters** (`references_hd/`, Codex, two runs through `claude_shared/codex_slot.sh`): renders of the MM9 model
   with GREENDRAGONLT (`mm9_views_tier1.png` five views, `mm9_head_tier1.png` head close-up, `mm9_top_tier1.png`,
   the skin ×4). Brief `CODEX_BRIEF.md`, records `generation_runs.json`, `selected_views_review.png`. Masters in the MM9
   bind pose (upright, wings raised and swept back), 1024×1536. Gate: 00 accepted; 04 slightly oblique (accepted).
1. **Meshy** Smart Topology 15k from `00_three_quarter.png` (`requests/smart_topology_v1.json`): 15,938 faces; good
   body, but the wings spread sideways (MM9 sweeps them back) and two long sliver webs joined the right wing claws to
   the head frill.
2. **Fit** (`scripts/fit_dragon.py`): global similarity ICP on the non-wing points; the sliver webs deleted (long
   faces between head and wrist), small holes filled; each wing started from a landmark frame (shoulder, highest
   point = wrist, farthest point = tip) refined by chamfer against the MM9 wing surface (about 59° turn, scale 0.92);
   then articulated similarity ICP over the 113-bone hierarchy (coarse to fine, joint-continuity pairs, a turn limit
   against the parent of 50° / 25° for toes and fingers); weights in Meshy space (nearest posed MM9 vertex, the head
   box never taking wing labels), and inverse skinning back to the MM9 bind pose (blend of per-bone inverse images).
   Overlays `work/ov1_sheet.png` (bind), `work/rig1_sheet.png` (MM9 clips on the fitted mesh).
3. **Weights** (`scripts/rig_dragon.py`): bone groups (forelegs, hind legs, wings, tail, core) from the Meshy-space
   labels, nearest MM9 bind vertex of the same group, wing membranes the barycentric blend of the MM9 wing triangle
   under them, diffusion with jaw labels held; small pieces rigid; 4 influences.
4. **Reduce** (`scripts/reduce_body.py 0.8 0.6 0.7 0.65`: body, pieces, head, wings): 15,971 → 11,355, no visible
   change at close range (`work/red_sheet.png`).
5. **UV**: Blender Smart UV shattered the mesh (25 % coverage, retexture v1 on it is superseded); xatlas
   (`scripts/xatlas_uv.py` with `../hes_harvester_claude/work/xatlas_venv`, `scripts/xatlas_io.py`), head islands ×2,
   re-packed: 43 % coverage, head 3.8× the body's texel density. **Retexture v2** from 01/03/02/04 on that layout.
6. **Feet and mouth**: `scripts/floor_feet.py` rests the hooked hind claw tips on the floor in the bind pose;
   `scripts/reweight_mouth.py` splits upper/lower jaw by the MM9 mouth plane through the hinge (diffusion had dragged
   the lips into a stretched green bucket when MM9 drops the jaw ~50°); `scripts/mouth_uv.py` maps the 139 lip faces
   that open into the mouth onto a painted red mouth patch (top-left corner of the atlas, compose step).
7. **Clips** (`scripts/clips_mm9.py` DRAGON table, run by `scripts/build_export.py`): MM9 key poses as PCHIP curves at
   30 fps, loop seams closed (stand 0.08° before), Dead = last Death pose; the corpse's wings turn up to 45° about the
   body axis between 1.2 s and 1.95 s (our membranes are larger than MM9's).
8. **Textures** (`scripts/compose_dragon.py`): padded 2K base + mouth patch, graded (`grade_basecolor.py`, AO
   `bake_ao.py` reach 0.6), 1K normal, 1K metal-rough (R AO, G roughness), material classes (skin, membrane,
   claw/horn, eye, mouth) for `claude_shared/material_classes_to_orm.py`.
9. **Runtime** (`scripts/build_runtime.sh`): prepare → LODs → shadow shrink (margins 0.02-0.06 units) → material
   classes → floor (two passes) → winding (0 inverted) → `tools/install_model.py --world mm9`; binding by
   `scripts/bind_actor.py` under the shared `mm9_actors_yml.lock` (temp file + `os.replace`).

## Budget (LOD0 11,350 triangles)

Above the 15k ceiling's usual creature range (rigid ~5k, clothed humanoids 5-8k) because: the boss stands about 1,820
units tall (four times a human) and fills the screen in its own arena; the silhouette carries two large membranes with
three finger spars and scalloped edges each, four clawed feet (three digits each), two long horns, a crest and spiked
side frills, and a dorsal spike row down the tail. The reduction stopped where the head, claws and wing edges still
held at close range (`work/red_sheet.png`); LODs halve from there (5,665 / 2,021 / 655).

## Floor

Flier in the table (`canFly`), but MM9 stands, attacks, casts and dies on the ground; only travel is airborne. Pass 1
`--hover -0.2289` (MM9's stand pose leaves our Meshy toes 0.23 above the floor), pass 2 tail strips lifted
(`--lift-joints ... --lift-only 'Xtail*'`), `--ground-loop Standing`, `--raise` on every other ground clip (lifts only keys
that dip under the floor), `--raise-uniform` on the fly loop (Walking, Running: one lift of 2.49 / 2.52 for the whole
loop; see the 2026-10-30 section), `--ground-death`: the
corpse rests on its bulky side (moved up 1.25 units onto the floor). `floor_audit.py --world mm9`: ok.

## Rebuild

```sh
T=<lease token>; B="tools/run_creature_blender.sh --token $T"; P=level_generation/creatures/mm9_dragonking_claude
V=level_generation/props/mm9_isleofashes_claude/work/venv/bin/python; X=level_generation/creatures/hes_harvester_claude/work/xatlas_venv/bin/python
$V tools/mm9_import_discovery/convert_abc_model.py mm9/extracted/MODELS/MODELS/DRAGON.abc $P/source/tier1 --id dragon \
  --texture 0=mm9/extracted/SKINS/SKINS/GREENDRAGONLT.dtx --scale 0.0256
$B $P/scripts/mm9_rig_source.py $P/source/tier1/dragon.glb $P/work/mm9_dragon_src.blend 0 8.5455
$B $P/scripts/fit_dragon.py $P/work/mm9_dragon_src.blend $P/meshy/body_smart_v1/model_urls_glb.glb $P/work/fit_v1.blend $P/work/fit_v1.json
$B $P/scripts/rig_dragon.py $P/work/fit_v1.blend $P/work/rig_v1.blend $P/work/rig_v1.json
$B $P/scripts/reduce_body.py $P/work/rig_v1.blend $P/work/reduced_v1.blend $P/work/reduced_v1.json 0.8 0.6 0.7 0.65
$B $P/scripts/uv_export.py $P/work/reduced_v1.blend dragon $P/work/uv_v1.blend $P/texturing/dragonking_body_upload.glb
$B $P/scripts/xatlas_io.py export $P/work/uv_v1.blend $P/work/xatlas_in.npz
$X -I $P/scripts/xatlas_uv.py $P/work/xatlas_in.npz $P/work/xatlas_uv.npz
$B $P/scripts/xatlas_io.py apply $P/work/uv_v1.blend $P/work/xatlas_uv.npz $P/work/uv_v2.blend $P/texturing/dragonking_body_upload_v2.glb
# (retexture_v2 was made on this upload; xatlas packs a little differently per run: keep work/xatlas_uv.npz)
$B $P/scripts/floor_feet.py $P/work/uv_v2.blend $P/work/uv_v2f.blend
$B $P/scripts/reweight_mouth.py $P/work/uv_v2f.blend $P/work/uv_v3.blend $P/work/reweight_mouth.json
$B $P/scripts/mouth_uv.py $P/work/uv_v3.blend $P/work/uv_v3m.blend $P/textures/dragonking_mouth_patch.json
$B $P/scripts/dump_uv3d.py $P/work/uv_v3m.blend $P/work/uv3d_body_v3.npz Body
$B $P/scripts/bake_ao.py $P/work/uv_v3m.blend Body $PWD/$P/textures/dragonking_ao_2k.png 0.6 2048
python3 $P/scripts/compose_dragon.py && python3 $P/../claude_shared/grade_basecolor.py --ao $P/textures/dragonking_ao_2k.png $P/textures/dragonking_basecolor.png
# (uv_v3/uv_v3m and compose_dragon only feed the body maps; the mesh is rebuilt from uv_v2f below, 2026-10-30)
$B $P/scripts/jaw/mouth_rebuild.py $PWD/$P/work/uv_v2f.blend $PWD/$P/work/uv_v4m.blend $PWD/$P/work/jaw/mouth_rebuild.json
$B $P/scripts/jaw/head_split_dk.py $PWD/$P/work/uv_v4m.blend $PWD/$P/work/head_v1.blend $PWD/$P/texturing/dragonking_head_upload.glb $PWD/$P/work/head_v1.json
python3 tools/creature_meshy.py --project $P --token $T submit --job head_retexture_v1 --kind retexture --request requests/head_retexture_v1.json --credits 10   # then poll / download
$B $P/scripts/jaw/dump_head_uv.py $PWD/$P/work/head_v1.blend $PWD/$P/work/head_uv_v1.npz
$B $P/scripts/jaw/bake_ao_head.py $PWD/$P/work/head_v1.blend Body $PWD/$P/textures/dragonking_head_ao_2k.png 0.6 2048
python3 $P/scripts/jaw/compose_head_dk.py
$B $P/scripts/build_export.py $PWD/$P/work/head_v1.blend $PWD/$P/work/anim_v2.blend $PWD/$P/export/mm9_dragonking_lod0.glb $PWD/$P/work/clips_v2.json
python3 tools/creature_workspace.py run --project $P --token $T -- $P/scripts/build_runtime.sh --install
flock -x level_generation/creatures/claude_shared/locks/mm9_actors_yml.lock python3 $P/scripts/bind_actor.py
python3 $P/scripts/make_viewer_manifest.py r3_dragonking_headjaw_20261030 "dragonking=Dragon King (GREENDRAGONLT)=$P/export/mm9_dragonking.glb"
```

The block above is the history up to the head/jaw rework. Current maps and master, after `head_v1.blend` (never re-run
the two UV scripts: the paid paints belong to their exact layouts; `work/texpass/uv_final.blend` is the master):

```sh
W=$PWD/$P/work/texpass
$B $P/scripts/dump_uv3d.py $W/uv_final.blend $W/uv3d_body.npz Body
$B $P/scripts/jaw/dump_head_uv.py $W/uv_final.blend $W/head_uv.npz
$B $P/scripts/texpass/dump_pairs.py $W/uv_final.blend $W/old_uv.npz $W
$B $P/scripts/bake_ao.py $W/uv_final.blend Body $PWD/$P/textures/dragonking_ao_2k.png 0.6 2048
$B $P/scripts/jaw/bake_ao_head.py $W/uv_final.blend Body $PWD/$P/textures/dragonking_head_ao_2k.png 0.6 2048
python3 $P/scripts/texpass/compose_body.py
python3 level_generation/creatures/claude_shared/grade_basecolor.py --ao $P/textures/dragonking_ao_2k.png --fine 1.0 --local 0.3 \
  --ao-strength 0.5 --contrast 1.06 --saturation 1.15 $P/textures/dragonking_basecolor.png
cp $P/textures/dragonking_basecolor_graded.png $W/body_graded_gentle.png
python3 $P/scripts/texpass/compose_head.py
cp $P/textures/dragonking_head_basecolor_ungraded_graded.png $W/head_graded_gentle.png
A=$P/work/before_texpass/textures
python3 $P/scripts/texpass/pin_tone.py $W/body_graded_gentle.png $A/dragonking_basecolor_graded.png $W/pairs_body.npz \
  $P/textures/dragonking_material_classes.png $P/textures/dragonking_basecolor_graded.png --sigma 14 --grain 1=1.5 3=1.3
python3 $P/scripts/texpass/pin_tone.py $W/head_graded_gentle.png $A/dragonking_head_basecolor.png $W/pairs_head.npz \
  $P/textures/dragonking_head_material_classes.png $P/textures/dragonking_head_basecolor.png --sigma 14 --grain 1=1.25 \
  --strip 0.803 --strip-image $A/dragonking_head_basecolor.png
TOKEN=$T $P/scripts/texpass/rebuild.sh <viewer revision> --install
```

## Checks (2026-10-30)

- Head/jaw/fly rework (2026-10-30, later the same day): winding 0 inverted closed parts; installed
  (`tools/install_model.py --world mm9`); viewer `r3_dragonking_headjaw_20261030`, `run_creature_review.py ... check`
  12 clips switched, 0 console errors; `floor_audit.py --world mm9` 49/49 ok; regression `--world mm9
  --headless-run-regression-suite actors`: `mm9_actor_models_build_every_binding` 49 descriptors on 20 models, 0 failed
  (every case of the suite PASS); `scripts/gates.py` -> `review/gates_20261030.json` (seams 0). Numbers in the
  2026-10-30 section above.

- Viewer `review/viewer/` (http://127.0.0.1:8912/level_generation/creatures/mm9_dragonking_claude/review/viewer/):
  `tools/run_creature_review.py ... check` 12 clips, 0 console errors; shots `review/shots/`,
  `review/viewer_shots_sheet.png`; playback `review/playback/` (every clip at 1× and 0.5×).
- Gates (`scripts/gates.py`, 30 Hz, `review/gates.json`): loop seams 0 (Standing, Walking, Running); edge ratio
  p1 / p99 per clip 0.59-0.79 / 1.30-2.50. Every edge stretched over 5× (163-201 per pose, max 58×) is a lip face
  at the mouth line: the red mouth curtain that opens when MM9 drops the jaw, by design.
- Floor audit `floor_audit.py --world mm9`: 49/49 ok (Dragon King: flier, stand −0.1..0, walk up to 539 in flight,
  corpse 0.0). Regression `mm9_actor_models_build_every_binding` (`--world mm9`): 49 descriptors on 20 models, 0 failed.
  Winding: 0 inverted closed parts.
- In game (Dragon's Lair `dragonstadium.odm`, `tools/run_game.sh` minimized, private `--user-data`
  `work/ingame_userdata/` whose `settings.ini` is restored from `work/ingame_settings_template.ini` before each run by
  `scripts/run_ingame.sh`, which also waits for any other game to exit): `review/ingame_sheet.png` (k01-k03 a friendly
  Dragon King standing on the lair floor, k04-k07 its death fall and corpse, k08-k25 a hostile one flying at the party
  and releasing fire from the mouth), `review/ingame_hostile_sheet.png` (from under the start arch).

## Deviations and open points

- **Ground boss as a flier.** MM9 keeps the dragon on the ground (it flies only in `land`); the OpenYAMM table makes
  it `Fly Y`, so the engine flies it at the party, and its attacks and casts (MM9 ground poses) play in the air.
  Travel uses the MM9 fly loop. A boss script could keep it grounded and use the `land`/`taunt` script clips.
- Breath = cast, fire-bolt spit = both missile attacks (one clip per engine role); `Rattack2` (same motion as
  Rattack3) and MM9's high-target choice are not reproduced.
- The wings are Meshy's, laid onto the MM9 wing by a landmark + chamfer turn: slightly larger and set about 15°
  higher than MM9's (wrist 4 units higher in bind). In the corpse they are eased up to 45° and the bulky body rests
  on its side 1.25 units above MM9's thin one.
- Mouth (since 2026-10-30): a real cavity (palate, floor with tongue, gums, throat) cut into Meshy's snout; the mouth
  corner moved from Meshy's y -4.10 to -3.40, 0.3 in front of the MM9 hinge (its 0.02 slit stretches up to 18x at 44 deg).
- Two texture sets (body, head), no tiers (one MM9 skin), so no region mask or ramps; specular per texel from the
  material classes. Head base colour 2K, not 1K (see the 2026-10-30 section).
- Texture pass: head atlas 50.9 % (target 55 %) and head fragments 4.2 % (target 3 %), see that section.
- Fly loop: one constant lift (+2.49 Walking, +2.52 Running = 249 / 252 world units) for the whole loop, MM9's own
  0.63 head motion on top; the transition from standing blends over 0.25 s (`blend_seconds`).
- **Grounded boss (user decision 2026-10-30, boss script later):** Walking and Running are MM9's FLY loop (DRAGON.abc
  has no ground walk), so a grounded Dragon King that moves would beat its wings with the body horizontal about 250
  world units above the floor. The ground clips (Standing, Fidget, attacks, Cast, Hit, Taunt, Death) stand on the floor
  with no baked hover. A boss script that keeps it grounded should keep it in place (turning on Standing), or a ground
  walk would have to be authored; Land starts 71 units (7,100 world units) up.
- Retexture v1 (10 credits) was superseded by v2 on a better UV layout.
- User artistic acceptance: accepted "dragon king - ok" (2026-10-30, after the head/jaw rework).
