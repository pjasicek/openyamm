# Xeen Sprites: Killer Sprite model (tiers Medusa Sprite / Killer Sprite / Sprite Queen), 2026-11-20

Lane S sub-agent build (identity `xeen:sprite`, budget 60 credits). Design: the Clouds **Killer Sprite** (Xeen image
22): a slender blue fey woman, long pale teal hair, a short ragged magenta dress, bare feet, four translucent blue
wings. The Darkside Medusa Sprite (image 53: orange skin, snake locks, bat wings) is a different design; tier A only
nods to its green palette, and a bat-winged Medusa model can follow as its own project.

**Installed** as `worlds/xeen/models/xeen_sprite.glb` (`tools/install_model.py --world xeen`). The binding is **not**
written (the lane parent owns `actors.yml`): the ready-to-paste block is [integration/actors.yml](integration/actors.yml).
No in-game run was made (no monster rows bound yet).

| Item | Value |
|---|---|
| Export | `export/xeen_sprite.glb` (sha256 `11a57cb9...d39d2a0`, 10.1 MB) = `assets_source/worlds/xeen/models/xeen_sprite.glb`; cooked runtime copy `assets_dev/worlds/xeen/models/xeen_sprite.glb` (`18141e92...87b1bd`) |
| Masters | `references_hd/` 00-04 body (no wings) and 05 the four wings alone, Codex (two runs, medium effort), gated against `native/` |
| Mesh | Meshy Smart Topology 15k of `00_three_quarter.png` (v1), stray strands, wisps and lash strips dropped; procedural pinky per hand (Smart Topology gave a thumb and three fingers twice); reduced after weighting to 8,740 triangles (skin 5,200, hair 1,698, legs 1,500, eyes 342) + wing cards 612 |
| Rig | 52 `B_*` bones on the humanoid set's source frames (dru1/natm route): Meshy auto-rig joints, ring wrists/ankles, Meshy elbows on the ring centreline, mesh-measured hands, fingers by connectivity, twist bones; 4 rigid wing bones on `B_Spine2`; palm and chest sockets |
| Wings | flat cards cut from the HD wing master (48 px cells, alpha = membrane translucency 0.42-0.92 with an opaque rim), own mesh `Wings` and material `Wing_A..C` (alpha BLEND, double-sided, no edge darkening, no shadow), rooted behind the hair at shoulder-blade height, span 1.45 model m |
| LODs | 8,740 / 4,370 / 2,185 / 1,090 (LOD1 `build_actor_lods.py`, LOD2/3 the `repair.py` ladder, step r25_12 accepted: LOD2 2.5 % / 6.0, LOD3 4.3 % / 8.2), shadow LODs tucked; wings have no LODs (612 triangles) |
| Textures | body 2K colour (4K Meshy paint downsampled once, gentle grade), 1K normal, 1K ORM (R baked AO, G roughness, B 0), 1K region mask (R skin, G hair, B dress), class map `textures/sprite_material_classes.png`; wings 1K RGBA + 1K mask (R membrane); gutter fill last |
| Meshy credits | **25 of 60**: Smart Topology v1 5, auto-rig 5 (joint estimate + weights), Smart Topology v2 5 (second draw for the four-digit hands; also four digits, unused), retexture 4K 10 |

## Tiers (one shared texture set, region mask + ramps; `textures/sprite_ramps.json`)

| Variant | Tier | Skin | Hair | Dress | Wings |
|---|---|---|---|---|---|
| `sprite_a` | Medusa Sprite | olive green (104,132,62) | dark green (40,78,42) | green (54,126,50) | pale green (128,196,120) |
| `sprite_b` | Killer Sprite | native blue (the paint) | pale teal (the paint) | magenta (the paint) | blue with indigo eye spot (the paint) |
| `sprite_c` | Sprite Queen | pale violet (182,152,216) | gold-white (238,224,172) | deep purple (74,26,104) | lilac (196,166,236) |
| `sprite_d` | Gorgon Sprite (Xeen Dark Sprite A, 11534; D-23) | bronze (#b0642c) | black | green | violet (Darkside image 53) |
| `sprite_e` | Elder Gorgon Sprite (Dark Sprite B, 11535) | deep copper (#94422a) | black | dark wine | ember orange |


`sprite_d` and `sprite_e` were added in lane S session 3 by the tier route (`../xeen_tiers_claude/xeen_tiers.py` with
`spec_sprites.json`, `by_material` for the wing ramps): the installed `assets_source/worlds/xeen/models/xeen_sprite.glb`
is now `../xeen_tiers_claude/export/xeen_sprite.glb` (this project's `export/xeen_sprite.glb` plus two variants). A
rebuild of this project must rerun that step before installing.

sRGB mid-tones; each texel keeps its luminance relative to its region's median (`compose_sprite.py`), ramps fitted by
`region_variants.fit_ramps`. Tier B fit error (8-bit, mean/p95): skin 1.9/5.6, hair 3.9/12.3, dress 1.8/6.0, wings
4.1/20.7 (the indigo spot and the pale membrane share luminances). Specular 0, metallic 0 on body and wings.

## Scale and floor

Built at adult proportions (1.70 m rest). Hovering (knees bent, toes pointed) the body spans 0.03-1.69 m, so the
binding's **scale 66** gives a 1.1 m sprite (about 110 world units; wing tips about 117). Flyer rule: every loop's
lowest point over the loop meets the floor (wing tips included); one-shot actions keep Standing's height and rise only
where they would cut the floor; the death keeps its lowest point on the floor and the corpse lies on it (all 0.0 cm,
`scripts/floor_probe.py` with the floor audit's posing on the installed GLB). No `z_offset`. The floor audit itself
needs the binding: run `floor_audit.py --world xeen --match 'Xeen *Sprite*'` after pasting it.

## Clips (30 fps keys; `scripts/flyer_clips.py`, `wing_flap_floor.py`)

| Clip | Length | Source and authoring |
|---|---|---|
| Standing | 3.6 s loop | Mixamo Floating (seam 0); legs kept at 40 % round their mean, then a dangling pose (knees 38/22 deg, toes pointed 35 deg); wings 6.1 Hz |
| Walking | 3.6 s loop | Standing leaned 14 deg, neck/head turned back, thighs trailing; wings 6.4 Hz |
| Running | 3.6 s loop | Standing leaned 26 deg; wings 7.5 Hz (the engine plays it above 158 units/s) |
| Attack | 1.633 s | Mixamo Mutant Swiping frames 15-64 (upper body; hovering legs, 35 % of the travel, 10 % of the crouch): right claw raised, slashed down and forward; **impact 0.733 s** (peak fingertip speed 14 m/s, fingertips furthest forward) |
| Cast | 1.6 s | Mixamo Standing 2H Magic Attack 01 frames 20-68: both hands overhead, then pushed forward together; **release 0.900 s** (palms 0.55 m forward); glow between `Socket_Palm_Left/Right`, spare `Socket_Chest` |
| Hit | 0.5 s | humanoid set Unarmed GetHit F1 on the hovering legs |
| Death | 3.167 s | Mixamo Standing Death Forward 01 (turned, travel x0.4): staggers, knees, falls face down; legs leave the hover pose over 0.2-0.7 s; wing beat dies out over 0.35-1.0 s and the wings fold shut (78 deg) |
| Dead | 1 s | Death's last pose |
| Fidget | 1.967 s | Mixamo Taunt Gesture on the hovering legs (left arm 12 deg out over the hip) |

One-shot clips ease from and back to Standing frame 0 (0.2 / 0.3 s). Wings: each turns about the spine's up axis
through its root, 20 +- 18 deg behind the back plane, lower wings 0.15 cycle behind; at 30 fps keys one beat is about
five keys.

## Gates (final rig `work/rig_v5.blend`, textured master `work/rig_v6.blend`)

- G3: frame error 0.0 deg; hand frames from the mesh knuckle line (`hand_frame_check.py`).
- G4 arm stretch p99 <= 2.0 except the cast's raised/forward arms (frames 20-27: 2.13-2.23, the off-shoulder band
  at the armpit; 14 diffusion passes did not lower it). Accepted deviation, as the druidess's 2.3.
- G5 hand stretch <= 2.32x (limit ~4.5x).
- G6 contacts: none in any clip after two arm offsets (Fidget left arm 12 deg over frames 10-44, Death right arm 16
  deg over 46-66; before: 2.1 cm into the hover thigh, 3.2 cm into the torso).
- Floor: above. Winding: 0 inverted closed parts. LOD ladder: accepted (`lodrepair/work/xeen_sprite/result.json`,
  `verify_far_only.py`: only the far levels differ).
- Texture quality (body, `texture_quality.py`): atlas 66.2 %, density p50 1,501 (non-head bones 1,466-1,478; head
  islands x2 by design, so overall spread 2.1), fragments 0.0 %, stretch p90 1.2; Meshy paint 4K on that layout.
- Viewer: `node ../claude_shared/check_viewer.mjs <url>/level_generation/creatures/xeen_sprite_claude/review/viewer/`
  switched 27 (3 tiers x 9 clips), no console errors. (`tools/run_creature_review.py check` timed out loading the
  10 MB tier GLBs from its own server; the direct check passes.)
- Renders: `review/party_sheet.png` (party eye height, tier B, Standing/Attack/Cast/Death), `review/tiers_sheet.png`
  (A/B/C: party, three-quarter, face, back), `review/close_hands.png`, `review/tier_targets*.png`.

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_sprite_claude
# one-off: examine_parts.py (st_v1_parts), meshy_joints.py, source_rest.py, proportions.py source, prep_wings.py
TOK=$TOK scripts/rebuild.sh                      # STAGE=rig | anim | all; gates printed at the end
# textures (once, on the locked layout): uv_sprite.py -> requests/retexture_v1.json -> dump_uv3d.py, bake_ao_sprite.py
TOK=$TOK SYNC=1 scripts/build_runtime.sh [--install]   # compose, gutter fill, export, LODs, tiers, far LODs, winding
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
```

`build_wings.py` rebuilds the cards in place (used on `rig_v6.blend` after the span change); `sync_actions.py` copies
re-gated clips into the textured master without touching its UVs. The LOD tools are a project copy of
`lod_repair_claude/scripts` in `lodrepair/` (outputs stay in this project; its Blender render runs through
`tools/run_creature_blender.sh`).

## Known limits

- The pinky is a procedural tapered tube rooted in the palm edge (no knuckle bend at rest); it curls with its finger
  chain like the others. Close up it reads slightly thinner and straighter than the other fingers.
- Tier A/C wing eye spots read dark grey-green / grey-violet (the ramp's darkest stops); tier B keeps the native blue.
- The hair is one shell weighted head -> neck -> chest -> Spine1 by height (no secondary motion).
- Wings are flat cards without shadows (alpha blended); they have no LODs.
- Running and Walking are leaned versions of the 3.6 s hover loop, not separate flight cycles.
