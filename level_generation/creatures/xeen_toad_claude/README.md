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
| `assets_source/worlds/xeen/models/xeen_toad.glb` (sha256 `3c859135…`) | installed source; runtime copy in `assets_dev/worlds/xeen/models/` |
| `export/xeen_toad_final.glb` | the same file: `export/xeen_toad.glb` + far LODs from `lod_repair_claude` (step r25_12, `verify_far_only` OK) |
| `work/anim_v1.blend` | the keyed UV master (rig `Toad_Rig`, meshes `Toad`, `Tongue`) |
| `textures/` | `toad_basecolor_graded.png` (2K), `toad_normal_1k`, `toad_mr_1k` (R AO, G roughness, B 0), `toad_region_mask.png` (R = hide), `toad_ramps.json`, `toad_material_classes.png` (1 skin, 6 eye), `toad_tongue.png` |
| `integration/actors.yml` | the bindings merged into `assets_dev/worlds/xeen/models/actors.yml` |
| `review/` | `clips_side.png`, `clips_front.png`, `clips_quarter.png` (clay clip sheets), `tiers_abc.png`, `stress_*.png`, `texture_quality.json` |

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
| Attack | 1.0 s | rears the head, throat puffs, the tongue shoots 1.17 m at the party: **impact 0.42 s**, snaps back |
| Hit | 0.5 s | jolt back and down |
| Death | 1.4 s | convulsive leap, flips onto its back, legs twitch and sag |
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

- The mouth is closed geometry: the tongue grows out of the lip seam (as the Xeen frames draw it) instead of a
  jaw opening.
- In the takeoff of a hop the folded thigh lobe rises over the back for a few frames (heat weights over the fused
  thigh/shin lobe). Acceptable at game distance; a voxel-proxy weight solve would separate them.
- The tongue texture is a small procedural turquoise map (stretch p90 17 on its cylinder unwrap; not visible).
- Seen in game only as spawned actors in XD-21 (no X1/X3 placement yet); not accepted by the user.
