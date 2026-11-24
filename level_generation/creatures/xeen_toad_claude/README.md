# Xeen Giant Toad (Claude quadruped project, 2026-11-20)

Xeen's **Toads** family (`source/monsters.yml` `toads`, rows 11450-11452): Giant Toad A (L5), Bog Toad B (L8), Swamp
Toad C (L11), X1 Toad Meadow and X3. Clouds of Xeen image 13 (`raw/dark/xeen.mon` row 13, `sprites/xeen/013.mon`,
`013.att`): a broad warty brown toad, front view only, an idle with a blink, a tongue attack (a thick turquoise tongue
shot at the viewer) and a leap. Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md),
[HD masters](../CLAUDE_HD_MASTER_REFERENCES.md), [creature textures](../CLAUDE_CREATURE_TEXTURES.md) and the
[texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md). Meshy: **15 of 40 credits** (Smart Topology 5,
retexture 10). Installed in the Xeen world and seen in game (2026-11-20, spawned in XD-21 with `build-xeen`: all three tiers draw
with their skins; `level_generation/creatures/xeen_tiers_claude/check_tour_xd21.yml`).

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_toad.glb` (sha256 `0fb89757…`, D-126 tongue 2026-11-24; D-118 repair `2652afbd…`; before `3c859135…`) | installed source; runtime copy in `assets_dev/worlds/xeen/models/` |
| `export/xeen_toad_final.glb` | the same file: `export/xeen_toad.glb` + far LODs from `lod_repair_claude` (step r25_12, `verify_far_only` OK) |
| `work/anim_v1.blend` | the keyed UV master (rig `Toad_Rig` with `Jaw`, meshes `Toad` (slot 1 `Mouth`), `Tongue`) |
| `work/anim_repair.blend` | the D-118 repair of `work/anim_base.blend` (`scripts/repair_toad.py`), which the clips are keyed on |
| `textures/` | `toad_basecolor_graded.png` (2K), `toad_normal_1k`, `toad_mr_1k` (R AO, G roughness, B 0), `toad_region_mask.png` (R = hide), `toad_ramps.json`, `toad_material_classes.png` (1 skin, 6 eye), `toad_tongue.png` (512 x 1024, `scripts/paint_tongue.py`) and `toad_tongue_material_classes.png` (7) |
| `integration/actors.yml` | the bindings merged into `assets_dev/worlds/xeen/models/actors.yml` |
| `review/` | `repair_gates.json` (and `repair_gates_anim_v1_before.json`), `viewer/` (three.js review page), `shots/`, `clips_side.png`, `clips_front.png`, `clips_quarter.png` (clay clip sheets), `tiers_abc.png`, `stress_*.png`, `texture_quality.json` |

Mesh: Smart Topology 15,310 triangles, collapse-decimated after weighting with head, hands and toes protected to
**9,491**; LODs 9,491 / 4,744 / 2,372 / 1,185 (shadow LODs tucked 5-12 mm inside). Ten pieces (body, two hind legs,
two forearms, two upper-arm lobes, two eye domes, a brow gland strip) plus the tongue (240 triangles, own material).

## Rig and clips (scripts/)

`prep.py` (scale to a 0.85 m sitting height, 1.95 x 1.91 m), `slices.py` (joints from per-piece slices),
`rig_toad.py` (Body, Chest, Head, Throat; UpperArm/ForeArm/Hand and Thigh/Shin/Foot/Toes per side; Tongue1-4;
heat weights, eye pieces rigid on Head, a smooth throat weight, the tongue a tapered tube on its own chain),
`stress.py`, `uv_toad.py` (reduction, `uv_atlas.unwrap`, upload), `anim_toad.py` (30 fps, every frame floor-checked:
the core lifted out of the floor, planted or swinging hands and feet raised until they clear it).

| Clip | Length | What |
|---|---|---|
| Standing | 2.0 s loop | breathing, throat pulses twice |
| Walking | 0.8 s loop | short hops, 1.30 m per cycle (`stride_length` 1.30) |
| Running | 0.73 s loop | long hops, 2.40 m per cycle (`run_stride_length` 2.40) |
| Attack | 1.0 s | a low rear, a small throat puff, the jaw opens onto the mouth cavity, the tongue shoots 1.17 m at the party: **impact 0.42 s**, snaps back |
| Hit | 0.5 s | jolt back and down |
| Death | 1.4 s | convulsive leap, flips onto its back, legs twitch and sag; tongue and throat kept in |
| Dead | held | on its back |
| Fidget | 2.0 s | throat puffs, head turns, a short tongue flick |

Floor audit (`claude_shared/floor/floor_audit.py --world xeen --match 'Xeen Toad A'`): standing -0.4..0, walk
-0.9..+0.2, living -1.7, corpse 0.24 world units: ok.

## Textures and tiers

Meshy `retexture_v1` (meshy-7, 4K, PBR) on the `uv_atlas` layout (PartUV charts, seam pass, sparrow): atlas **72.4 %**,
density p10/p50/p90 790/849/1217 (spread 1.54 with the head and throat 1.6x denser by design), 62 islands, fragments
0.6 %, stretch p90 1.19. Colour downsampled once to 2K, graded gently (`--fine 1.0 --local 0.3 --ao-strength 0.5
--contrast 1.06 --saturation 1.15`), `gutter_fill.py` last on every map.

One region (the hide); the eyeballs (the dark blobs of the two eye pieces) stay out of it. Xeen has a single toad
palette, so only A is native; B and C are design choices (recolours of the graded skin, ramps fitted by
`region_variants.fit_ramps`, mean error 1.6-2.4 levels):

| Skin | Monster | Colour |
|---|---|---|
| `toad_a` | Giant Toad (11450) | native tan to reddish brown |
| `toad_b` | Bog Toad (11451) | olive moss green-brown (hue 72) |
| `toad_c` | Swamp Toad (11452) | dark slate green with a teal cast (hue 158) |

## Binding

Scale 120 world units per model metre (sitting 102 units tall, 230 long; the Xeen sprite stands at 58 % of the Xeen
witch's height), B/C `scale_reference: Xeen Toad A`; `yaw_offset -pi/2`; `cast: Attack` (no spell);
`upper_body_root: Chest`; look on `Head` (30/20 degrees); `events.attack_melee.impact 0.42`.

## Known limits

- The mouth opens only where Attack keys the `Jaw` (up to 9 degrees); the cavity is the painted lip crease on its own
  material, so a wide gape would show its shallow depth.
- The hind legs are a nearly closed fold (hip to ankle 0.31 m, thigh and shin 0.77 / 0.75 m), so the hops extend them
  only a little (toes leave at 42 % of the cycle, heel lift 18 degrees): a toad's long kick is not drawn.
- The tongue is a 240-triangle tube with ten sides, so its silhouette and end cap stay faceted up close (D-126 repainted
  it; the geometry is unchanged).
- The floor audit takes A only: B and C (`scale_reference`) stop `floor_audit.py` with a KeyError (the tool's lookup
  of sprite scales by descriptor; not a model fault).

## Log

### 2026-11-24, D-118 repair (F57, X1 p22 "this looks strange"; agent `xeen-toad-repair`, no Meshy)

Faults (`devdocs/xeen/reviews/PLAYER_FEEDBACK_20261124.md` F57): mid-attack the lips parted onto black slits and the
reared head filled the view; the hop takeoffs threw the thigh lobes up over the back, torn; a turquoise peg stood out
of the dead toad's throat. Repair in scripts, mesh, UV layout and paint unchanged:

- `scripts/repair_toad.py` (new; `anim_base.blend` -> `anim_repair.blend`):
  - hind legs: the heat weights gave each fused thigh/shin lobe mostly to Foot (0.39) and Toes (0.35), so the heel lift
    swung the whole lobe. New weights on the two hind-leg pieces: Toes in front of the toe base, Foot on the sole
    fading out over 30 cm behind it (a hard seam there tore), the lobe Thigh with a share of Shin by distance, 8
    smoothing passes;
  - mouth: the lip line found from the paint (the painted crease is one clean band, z 0.675 at the snout to 0.59 at
    the corners; `work/lip.json` from `lip_detect.py` had followed the brow and eye creases at the sides, z to 0.76);
    the 79 dark crease faces within 2.5 cm of it go to material slot 1 `Mouth` (`textures/toad_mouth.png`, a 16x64
    gradient, dark at the lip edge to red-brown on the line; one colour for every tier, no ramps) with their own UVs;
    a `Jaw` bone (child of Head, hinge between the mouth corners) takes the lower lip and the lower crease wall
    (Chest and Head shares within 3-10 cm of the line move to Jaw below it, Chest to Head above it; Throat keeps its
    puff). Deviation from D-118's wording "fixed to Head and Throat": the Throat bone's puff scale would push the lower
    lip about by up to 12 cm, so the lower lip rides on Jaw, Head's child;
- `scripts/anim_toad.py`: Attack rears less (pitch 3-4 and head 4-5 degrees, were 6-8 and 10-12), throat puff 0.5-0.6
  (was 0.9-1.0), heel 3-6 (was 6-20), the jaw opens 2 -> 9 degrees around the strike; the hind-leg IK pole lies in the
  leg's rest plane (the old offset pole let the nearly closed fold spin); the hops lift the heel 18 degrees (was 55),
  the toes leave at 0.42 of the cycle (was 0.52) and the flight trail shrinks smoothly relative to the body; in the
  keyed clips the hind toes follow 60 % of the body's lunge or jolt; Death keeps the tongue in and the throat unpuffed,
  the shin flail halved;
- `scripts/export_glb.py`: the `Mouth` material on slot 1 (slots replaced in place);
- `scripts/repair_gates.py` (new), per clip, every frame: floor, the hind legs over the back, edge stretch on the
  legs, the tongue outside the body. `review/repair_gates.json` (all eight PASS) against
  `review/repair_gates_anim_v1_before.json` (all eight FAIL): Walking over the back +11.3 -> -8.5 cm, leg edge stretch
  27.1 -> 4.1 cm; Running 44.7 -> 4.6 cm; Death stretch 25.3 -> 5.8 cm; the tongue 25.7 -> 4.0 cm out in Death and Dead
  (the resting tongue sits 3.5 cm deep in the lip crease);
- `scripts/repair_views.py` (new; close-up review renders), `scripts/make_viewer.py` (new; `review/viewer/`, checked
  with `tools/run_creature_review.py check`: 8 clips, no console errors; `review/shots/`).

Runtime: `build_runtime.sh` (LODs 9,491 / 4,744, winding 0), far LODs from `lod_repair_claude` (`repair.py --source
export/xeen_toad.glb --world xeen`, r25_12 accepted, 2,369 / 1,182, `verify_far_only` OK; the far copies carry
`Mouth_LOD2`/`Mouth_LOD3`; the first try failed on zero-area mouth UVs, now spread along the mouth), winding 0,
installed with `tools/install_model.py --world xeen --name xeen_toad.glb`. Floor audit A: stand -0.1..0, walk
-0.8..+0.2, living -0.9, corpse 0.24: ok. Clip sheets `review/clips_{side,front,quarter}.png` (before:
`output/xeen_fb/p3_toad/before/`). In game (X1 at the pin, `output/xeen_fb/p3_toad/ingame/`): the attack opens onto a
red-brown mouth with the tongue strike, no slits; the death flips it onto its back with no peg. Before/after:
`output/xeen_fb/p3_toad/before_after.jpg`.

### 2026-11-24, D-126 the tongue (agent `xeen-toad-tongue`, no Meshy)

The strike showed a large flat teal disc over the face: the old map was a 256 px two-colour gradient, and the
cylinder unwrap (u by `atan2` around a fixed height) squeezed the tip's end cap, the part seen head-on, into one texel
row with one u at the tip, and ran one face per ring backwards across the whole map at the u seam.
- `scripts/tongue_uv.py` (new; also called by `uv_toad.py`): the tube (rings 0-21, root to the widest bulb ring) on
  u = side / 10 with its own seam column, v 0-0.75 by arc length; the end cap (ring 21 to the tip) as an azimuthal
  equidistant disc around the tip at 700 px/m; the root 10-gon as a small disc. Applied to `work/anim_base.blend`,
  `anim_repair.blend` and `anim_v1.blend` (mesh, weights and clips unchanged; backups in
  `output/xeen_fb/p3_toad/tongue/backup/`); dumps `work/tongue_uv3d.npz`.
- `scripts/paint_tongue.py` (new; run by `build_runtime.sh`): `textures/toad_tongue.png` 512 x 1024, procedural from
  the native attack frames: their 16-step turquoise ramp (28,68,76 to 188,248,252), mid turquoise base (native steps
  4-6), darker teal mottling and veins, pale lengthwise wet streaks on the top and flanks, a pale crescent on the cap's
  upper rim, a darker, more saturated tip and a shadowed root; painted from each texel's rest 3D position, so tube,
  cap and rim are seamless; nearest-texel gutter fill. Mean sRGB 54,130,135, the tip 24,101,112.
  `textures/toad_tongue_material_classes.png`: class 7 (mouth interior) on every island texel.
- `scripts/export_glb.py`: `Tongue` roughness 0.35 (was 0.3); `build_runtime.sh`: `--extra Tongue
  openyamm_specular=0.5` (class 7's specular). One tongue for all three tiers, outside the region mask and ramps, like
  `Mouth`. `compose_toad.py` no longer writes the tongue.
- Runtime: `build_runtime.sh` (body maps byte-identical, LODs 9,491 / 4,744, winding 0); far LODs again from
  `lod_repair_claude` (r25_12 accepted, same scores, `verify_far_only` OK; the tongue has no far LODs), winding 0,
  installed with `tools/install_model.py --world xeen --name xeen_toad.glb`; Android textures cooked
  (`cook_models.py --profile android --only worlds/xeen/models/xeen_toad.glb`, verify 0 problems; this also cooked
  the D-118 maps, which had none).
- Checks: viewer shots of the strike head-on, side and three-quarter (`review/shots/ta_*.png`); in game at X1 p22
  (`output/xeen_fb/p3_toad/tongue/ingame/`). Before/after: `output/xeen_fb/p3_toad/tongue_before_after.jpg`.
