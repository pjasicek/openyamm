# Hesper Drones: Seeker / Hunter / Reaver — Claude project

Hesper's flying Kreegan-controlled survey drones (monsters 10050 **Seeker Drone** A, 10051 **Hunter Drone** B,
10052 **Reaver Drone** C ×1.1; `design/kreegan_world/data/make_monster_tables.py`, `MONSTERS.md`), from the approved
concept sheet `design/kreegan_world/concepts/monsters/fam_drones.png` (brief `CODEX_BRIEF_ZONE1_FAMILIES.md` §1).
Quadruped playbook route for a floating rigid machine (flyer floor rule from `mm6_bh_claude/`, rigid bones and
muzzle socket like `hes_turrets_claude/`). **Exported, not installed** (the Hesper stage integrates it).
Meshy: **15 of 60 credits** (Smart Topology 5, retexture 10). User artistic acceptance is not recorded.

[Viewer](review/viewer/) (`http://127.0.0.1:8912/level_generation/creatures/hes_drone_claude/review/viewer/`) ·
[tiers](review/tiers_contact_sheet.png) · [clip close-ups](review/clip_closeups.png) · [clip sheet](review/clip_sheet.png)
(workbench, every tier's gear shown) · [floor check](review/floor_check.json) ·
[HD masters](references_hd/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/hes_drone.glb` | runtime body: skinned mesh `HDR` (LODs **5,252** / 2,732 / 915 / 239 triangles + shadow LODs tucked inside), unlit glow material, mesh node `HDR_Thrust` (48-triangle alpha-blended thrust cone), skins `hdr_a/b/c`, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget; sockets `Socket_Muzzle`, `Socket_Muzzle2` |
| `export/hes_drone_twin_emitter.glb`, `_twin_emitter_glow.glb` | tier B gear on nodes `GearEmitter` / `GearEmitterGlow` (252 + 36 triangles at LOD0, own LODs) |
| `export/hes_drone_shield_ring.glb`, `_shield_ring_glow.glb` | tier C gear on nodes `GearRing` / `GearRingGlow` (320 + 20 triangles) |
| `export/hes_drone_lod0.glb`, `work/anim_v1.blend` | portable LOD0 with all gear joined; editable master |
| `textures/` | shared set: `hdr_basecolor_2k.png` (AO-graded), `hdr_normal_1k.png`, `hdr_metal_rough_1k.png` (R AO, G roughness, B 0), `hdr_region_mask.png`, `hdr_ramps.json`, `hdr_material_classes.png`, `hdr_thrust.png`, `hdr_glowmask.png` |
| `integration/actors.yml` | staged bindings for the three descriptors (`hes_seeker_drone`, `hes_hunter_drone`, `hes_reaver_drone`) |

Install later (Hesper stage, not `assets_dev`): the five GLBs with `tools/install_model.py ... --world hesper`, then the
`integration/actors.yml` entries.

## Tiers (one body, region mask + ramps; gear as attachments)

| Skin | Monster | Casing (R) | Resin/chitin (G) | Glow (B) | Trim (A) | Gear |
|---|---|---|---|---|---|---|
| hdr_a | 10050 Seeker Drone, scale 100 | bone-white ceramic | violet | orange | gold | — |
| hdr_b | 10051 Hunter Drone, scale 100 | darker scorched ivory | black | hotter orange-red | darker bronze | twin emitter (second barrel on the left flank beside the lens) |
| hdr_c | 10052 Reaver Drone, scale 110 | blackened | deep violet | orange-white | bright gold | shield emitter ring (gold belt with glowing cells round the middle) |

Ramps are designed from the concept's tier views (3 sRGB stops per region, `compose_hdr.py` `PAL`), mapped over each
region's luminance range. Bone ribs and tendon claws are repainted ivory and the tendon cables near-black, outside every
region (the concept keeps them on all tiers). No head set: the creature is small and the lens is a separate procedural
dome (radial glow painted in a reserved UV strip), so one atlas suffices. Glow (lens dome, emitter disc, ring cells) is a
separate **unlit** material `Glow_*` sharing the atlas and the mask, so its tier colour follows the glow ramp; the thrust
cone is its own mesh node with an unlit blended material `Thrust_*` (glow ramp per tier). All materials: specular 0,
metallic 0; glow and thrust without edge darkening. Material classes (`hdr_material_classes.png`): 11 glazed ceramic
(casing) and other, 4 resin/chitin and cables, 6 glow lens, 9 gold, 5 bone.

## Model, rig, clips

- HD masters: Codex from the concept (5 views + `gear.png`, 1536×1024). The primary's tendons came back as four looped
  cables; accepted because the rig replaces them.
- Meshy Smart Topology (15k, 127 pieces). `clean.py`: Meshy's looped tendon cables deleted, scaled to 0.80 m nose to
  tail, lens assembly kept at 75 % and the rest collapse-decimated (before UVs, so the retexture paints the reduced
  mesh), Meshy's soft lens face replaced by a clean 16-sided turned dome, three procedural 6-sided tendons with bone
  claws added. `uv_export.py`: Smart UV + small-island merge + angle-based unwrap, a strip v < 0.125 reserved for
  procedural parts. `gear.py`: B's barrel (12-sided, gold collars, glowing disc) and C's belt fitted per angle to the
  casing (behind the lens dome at the front), the thrust cone, `Socket_Muzzle2`.
- Rig (`rig.py`): `Body` (root, casing centre), `Lens` (dome: recoil and iris scale), `Socket_Muzzle`, `Thrust` (cone
  pulse by scale), `Tendon<k>_1..3` (arc-length blended weights, 0 unweighted vertices), gear bones. Every other vertex
  rigid on `Body`.
- Clips (`anim.py`, 24 fps): Standing 2.0 s, Walking 1.0 s, Running 0.75 s (hover bob, nose-down lean 0/8/15°, tendons
  trailing 0/16/30° with lagging sway, thrust pulse 3/5/8 Hz by scale), Attack 0.75 s (**impact 0.292 s**: recoil kick,
  lens punches in), Hit 0.5 s, Death 1.5 s (shudder, thrust flickers out, lens iris closes to 30 %, falls nose first,
  hits the floor at 0.875 s, bounce, rests tilted; tendons lie on the floor), Dead (held), Fidget 1.5 s (±28° scan turn).
- **Floor rule (flier)**: hover offset 3.3 cm measured over every living frame, so the lowest living point (tendon
  claws in Running) meets the floor; Standing floats 2.1–4.1 cm above it. The Death eases it out: casing on the floor,
  every vertex ≥ −0.06 cm, Dead 0.0 cm (`review/floor_check.json`, `scripts/floor_check.py` via `floor_audit.ModelFloor`).
- Checks: `check_winding.py` 0 inverted closed parts on all five GLBs; `run_creature_review.py check` 24/24 switches,
  no console errors. Texel density about 620 texels/m at 2K (4.4 m² of surface: many resin tubes). Not checked in game
  (no install in this task).

## Engine needs (not done: no engine work)

- **Creature glow/bloom**: creatures do not bloom yet (`MODEL_RENDERING.md`); the unlit lens, emitter, ring cells and
  thrust read as bright paint. No emissive textures on skinned actors, so the vent pulse is a scale pulse only.
- **Death sparks**: no spark-burst `death_effect` (only disintegration, explosion = fireball burst, burn). A short
  electric spark effect at dying start (and maybe a smoke wisp on the corpse) would match "sparks out".
- **Reaver shield**: the 600 Light personal shield shell (proposed Hesper monster columns) is an engine effect.
- **Twin emitter fire**: B's bolt leaves between both muzzles (`glow: [muzzle, muzzle2]`, no release); alternating
  muzzles per shot would need a release-socket cycle.
- Hesper monster rows and actor bindings in the stage (as for the turrets, guards and villagers).
- Attachments per descriptor already exist (`attachments:` with node + inherited skin); none needed there.

## Doubtful / for review

- Meshy's geometry is lumpy: the top carries paired side spurs and tangled resin loops rather than one clean central
  rib row, and the tail is a round cap (Meshy symmetrised the lens to the back). At 0.8 m and swarm distances it reads,
  but close up it is busier than the concept.
- UVs: many small islands remain on the decimated tubes (522 islands); seams are padded, but close-ups may show seam
  speckles. Ceramic vs gold is a hue/saturation heuristic (Meshy painted the plates tan like its gold); gold kept on
  the lens collars only.
- The viewer uses three.js lighting and baked tier colours; engine colours will differ slightly.
- Body LOD0 is 5,252 triangles; a further cut is possible if a swarm of 6–8 proves heavy.

## Replay

`TOK=<lease>`: `scripts/step.sh inspect_raw.py`, `clean.py`, `uv_export.py`, Meshy `requests/retexture_v1.json`,
`rig.py`, `gear.py`, `dump_uv3d.py`, `bake_ao.py`; `python3 scripts/components.py`, `compose_hdr.py`, `tier_bake.py`;
`scripts/step.sh anim.py`; `scripts/build_runtime.sh`; viewer: `scripts/step.sh viewer_export.py hdr_a|b|c`,
`fix_materials.py` on each, `update_viewer_manifest.py`; `python3 scripts/floor_check.py export/hes_drone.glb`.
