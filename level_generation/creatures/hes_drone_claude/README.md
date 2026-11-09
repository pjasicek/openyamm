# Hesper Drones: Seeker / Hunter / Reaver — Claude project

> **Reduced (2026-10-22):** `../hes_drone_reduce_claude/` (default route of `RETOPOLOGY_PLAYBOOK.md`, no
> retexture): body 4,396 -> 3,846 (LODs 1,923 / 1,129 / 589); lens, collar, glow, ribs, tubes, cables, masses and vent
> drum exact, hard-edge normals from this export; gear attachments unchanged. Exported, not installed; this project's
> exports are untouched and remain the rollback source. Ledger: `../REDUCTION_LEDGER.md`.

Hesper's flying Kreegan-controlled survey drones (monsters 10050 **Seeker Drone** A, 10051 **Hunter Drone** B,
10052 **Reaver Drone** C ×1.1; `design/kreegan_world/data/make_monster_tables.py`, `MONSTERS.md`), from the approved
concept sheet `design/kreegan_world/concepts/monsters/fam_drones.png` (brief `CODEX_BRIEF_ZONE1_FAMILIES.md` §1).
Quadruped playbook route for a floating rigid machine (flyer floor rule from `mm6_bh_claude/`, rigid bones and
muzzle socket like `hes_turrets_claude/`). **Exported, not installed** (the Hesper stage integrates it).
Meshy: **15 of 60 credits** (Smart Topology 5, retexture 10; both used only by the archived v1). User artistic
acceptance is not recorded.

**v2 (current, coordinator decision 2026-10-22): a hand-built body.** The Meshy shell (v1: tangled loops, paired side
spurs, a copy of the lens on the back) is replaced by a clean hard-surface build in Blender (`scripts/build_body.py`,
in the style of the turrets' `build_hard_surface.py`), textured from our own Hesper materials (`scripts/compose_v2.py`),
no new Meshy spend. Rig, cables, clips, tiers, attachments and bindings are kept. The v1 exports, textures, review
images and master are archived in `v1_meshy/`. [Before / after](review/before_after_tiers.png).

**Smoothing pass (2026-10-22, after the user's turret review: "very obvious sharp polygon edges")**: casing, collar
and tail lathed with 32 sides (were 24); smooth normals over every curved piece, hard edges only at real breaks
(a profile corner over 50°, a material change, the collar lips, the vent drum's rim steps and nozzle disc, every
plate's gold border against its top), where the vertices are split so the UV islands break there too; the resin
tubes 6 sides × 10 rings (were 7 × 12) to pay for it; the bone ribs reshaped; the tail tip's star removed.
[Before / after close-ups](review/before_after_smoothing.png) (casing three-quarter, lens, tail, ribs; the before is
the 24-side build rebuilt in a scratch copy with the same scripts and no hard-edge splits).

[Viewer](review/viewer/) (`http://127.0.0.1:8912/level_generation/creatures/hes_drone_claude/review/viewer/`) ·
[tiers](review/tiers_contact_sheet.png) · [clip close-ups](review/clip_closeups.png) · [clip sheet](review/clip_sheet.png)
(workbench, every tier's gear shown) · [floor check](review/floor_check.json) ·
[HD masters](references_hd/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/hes_drone.glb` | runtime body: skinned mesh `HDR` (LODs **4,396** / 2,250 / 776 / 248 triangles + shadow LODs tucked inside), unlit glow material, mesh node `HDR_Thrust` (48-triangle alpha-blended thrust cone), skins `hdr_a/b/c`, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget; sockets `Socket_Muzzle`, `Socket_Muzzle2` |
| `export/hes_drone_twin_emitter.glb`, `_twin_emitter_glow.glb` | tier B gear on nodes `GearEmitter` / `GearEmitterGlow` (336 + 48 triangles at LOD0, own LODs; on the clean left flank beside the lens) |
| `export/hes_drone_shield_ring.glb`, `_shield_ring_glow.glb` | tier C gear on nodes `GearRing` / `GearRingGlow` (384 + 20 triangles) |
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
region's luminance range. Bone ribs are repainted ivory and the trailing cables near-black, outside every
region (the concept keeps them on all tiers). No head set: the creature is small and the lens is a separate procedural
dome (radial glow painted in a reserved UV strip), so one atlas suffices. Glow (lens dome, emitter disc, ring cells) is a
separate **unlit** material `Glow_*` sharing the atlas and the mask, so its tier colour follows the glow ramp; the thrust
cone is its own mesh node with an unlit blended material `Thrust_*` (glow ramp per tier). All materials: specular 0,
metallic 0; glow and thrust without edge darkening. Material classes (`hdr_material_classes.png`): 11 glazed ceramic
(casing) and other, 4 resin/chitin and cables, 6 glow lens, 9 gold, 5 bone.

## Model, rig, clips

- **v2 body** (`build_body.py`, 4,396 triangles with the cables): a rounded lozenge casing lathed about the long axis
  (32 sides, 0.94 as wide as tall) with five raised gold-edged ceramic plates; the lens as a rounded gold front ring,
  a dark segmented collar, a rounded gold rear ring and the orange dome; a pointed ceramic tail cap (no lens shape at
  the back); a vent drum under the belly (dark band, 12 glowing slots, gold rim, glowing nozzle); the Kreegan
  overgrowth only on the right flank (-X) and the back: seven thick resin tubes (6 sides) swept over the casing and three chitin
  masses; ONE row of seven curved bone ribs on the top centre line (flared root sunk into the casing, a blade section
  0.6 as wide as long with a keeled leading edge, hooking back harder towards the tip); two bone hooks under the tail; three short trailing cables (10 cm, 6 sides, a third of
  the old tendons) from the rear underside behind the vent drum, hanging back 46° from vertical at the root and 72° at
  the end, each closed by a small gold plug (no claws: the drone flies; 2026-10-22, user: "why does it have legs?").
  Every face's winding follows an outward hint of its piece. UVs: each lathe, tube, plate, rib and mass is one island
  (TileUV in metres, packed uniformly), the strip v < 0.125 reserved as before. Smooth normals over each piece; split
  vertices (hard edge + UV island border) at profile corners over `HARD_DEG` 50°, material changes and plate lips.
- **v2 textures** (`compose_v2.py`, no Meshy): `hoterm` ceramic (its gold band cut out) with panel seams, gold lips
  and rivets; `hcgold` on every gold part (real gold trim now that the casing is separate); `hoaresin` on the tubes
  and as resin skin over the overgrowth zone (planar across the axis over the tail's last 2 cm, so no star at the pole), `hochitin` on the masses (their orange counts as glow); procedural lens,
  vent glow, dark metal collar, bone ribs and black ringed cables; AO-graded; a normal map from the painted height
  (glTF +Y up, kept by `prepare_actor_glb.py`). Ramps: the same tier palette, mapped by luminance quantile for casing,
  resin and trim (the resin texture is dark-skewed), linear for the glow.
- v1 (archived, `v1_meshy/`): HD masters (Codex, 5 views + `gear.png`) -> Meshy Smart Topology -> `clean.py`,
  `uv_export.py` -> Meshy retexture -> `compose_hdr.py`. The masters stay the design reference.
- Rig (`rig.py`): `Body` (root, casing centre), `Lens` (dome: recoil and iris scale), `Socket_Muzzle`, `Thrust` (cone
  pulse by scale), `Tendon<k>_1..3` (arc-length blended weights, 0 unweighted vertices), gear bones. Every other vertex
  rigid on `Body`.
- Clips (`anim.py`, 24 fps): Standing 2.0 s, Walking 1.0 s, Running 0.75 s (hover bob, nose-down lean 0/8/15°, cables
  streaming a further 0/22/38° back with lagging sway, thrust pulse 3/5/8 Hz by scale), Attack 0.75 s (**impact 0.292 s**: recoil kick,
  lens punches in), Hit 0.5 s, Death 1.5 s (shudder, thrust flickers out, lens iris closes to 30 %, falls nose first,
  hits the floor at 0.875 s, bounce, rests tilted; the cables lie flat on the floor), Dead (held), Fidget 1.5 s (±28° scan turn).
- **Floor rule (flier, as `mm6_bh_claude/`)**: the hover offset (8.9 cm) is measured over every living frame on every
  visible mesh, as `floor_audit` counts them. The cables trail above the vent drum's bottom, so the lowest point is the
  thrust glow's tip at its longest pulse (Standing), which meets the floor. The casing and vents, the lowest solid
  parts, float 7.0–10.2 cm above the floor in Standing (7.0–10.6 over all living clips) and the cable ends 8.0–10.0 cm
  at their lowest. The Death eases it out: casing on the floor, cables flat, Death and Dead 0.0 cm
  (`review/floor_check.json`, `scripts/floor_check.py` via `floor_audit.ModelFloor`; per-part lows in
  `work/anim_info.json`; side views in `review/floor_side_views.png`).
- Checks (v2 after the smoothing pass): `check_winding.py` 0 inverted closed parts on all five GLBs;
  `scripts/check_key_times.py` (copied from `hes_guard_reduce_claude/`) PASS on the runtime, LOD0 and viewer GLBs;
  floor rule (living min 0.0 cm = thrust tip, casing ≥ 7.0 cm, Death/Dead 0.0 cm); `run_creature_review.py check`
  24/24 switches, no console errors. Not checked in game (no install in this task).

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

- v2 is a simpler, cleaner shape than the concept painting: the overgrowth is seven tubes, three masses and a resin
  skin texture rather than the concept's dense braid; the ribs are simple curved blades.
- Silhouettes of the small swept pieces (6-sided tubes, cables, ribs) still show their sides at very close range; the
  LOD0 budget went to the casing, collar and tail.
- The viewer uses three.js lighting and baked tier colours; engine colours will differ slightly.
- Many casing pieces are open shells joined edge to edge (collar, casing, tail); `check_winding.py` only judges closed
  parts, so the open ones were checked visually in the culled viewer.

## Replay

v2, credit-free: `TOK=<lease> scripts/rebuild_v2.sh` (body, rig, gear, AO, textures, clips, runtime GLBs, floor check,
viewer GLBs and manifest); then `run_creature_review.py check` / `shots`, `scripts/crop_shots.py`, `scripts/sheet.py`,
`scripts/check_key_times.py export/hes_drone.glb`. `build_body.py` takes env `SIDES` (32) and `HARD_DEG` (50).
v1 (archived): `inspect_raw.py`, `clean.py`, `uv_export.py`, Meshy `requests/retexture_v1.json`, `rig.py` with
`HDR_SRC=uv_v1.blend`, `compose_hdr.py`.
