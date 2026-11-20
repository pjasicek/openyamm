# Hesper Landfall wall turrets: rigged actor models — Claude project

Landfall's two friendly wall turrets (monsters 10065 **Ward Turret**, 10066 **Gate Bastion**;
`design/kreegan_world/data/make_monster_tables.py`; concepts `design/kreegan_world/concepts/monsters/ward_turret.png`,
`gate_bastion.png`, brief `CODEX_BRIEF_WARD_TURRETS.md`) as actors that turn to a target and shoot, each on a static
mount decoration. Not in `assets_dev`: the Hesper stage (`hesper_stage/monsters.yml`, `decorations.yml`) uses these
exports and the mounts; re-stage with `python3 level_generation/projects/hesper_stage/stage.py` after a rebuild.

**v2 (2026-10-22, current): Meshy models built to the concepts.** The user's review of v1 (test image 76: "our Ward
Turret is a plain drum on a pillar ... the outline the mesh of the concept looks really different, might make sense to
give it to meshy?") replaced the hand-built primitives with the quadruped-playbook Meshy route for a rigid machine:
Codex HD masters from the concepts, Meshy Smart Topology, Meshy retexture from the four masters, our split into rigid
parts on the v1 bone layout, emission, authored LODs, new Meshy pedestals as the mounts. **Meshy: 30 of 60 credits**
(table below). The v1 round is archived for rollback in [`v1_hand_built/`](v1_hand_built/README.md). User acceptance
is not recorded.

[Concept vs model](review/concept_vs_model.png) (per turret: concept main / v2 from the concept's side, concept side /
v2 side, concept back / v2 back, then v1) · [review sheet](review/turrets_sheet.png) (rest, aim up, aim down, the
Attack's shot frame, Dead, head close-up) · [LODs](review/lods_sheet.png) · [in game](review/ingame_v2.png) (hes_out1,
the East Gate's Bastions and the wall's Wards, stage world) · [HD masters](references_hd/ward_turret/selected_views_review.png),
[Bastion masters](references_hd/gate_bastion/selected_views_review.png) ·
viewer `http://127.0.0.1:8912/level_generation/creatures/hes_turrets_claude/review/viewer/`

## Concept vs model


| | Concept (`ward_turret.png`) | v1 hand-built |
|---|---|---|
| Silhouette | one sweeping S-curve: tapered pedestal, an angled yoke arm rising backwards, an egg-shaped head flowing forward into a long thick barrel | stacked primitives: drum pedestal on a square plate, straight neck, a horizontal drum head with cone ends, a thin rod barrel |
| Pedestal | squat tapered block (wider at the foot, about as wide as the turret is tall) of pale grey-green prefab panels with darker ribbed seam strips, brass rivets, a yellow-black hazard hatch at the front; a square base plate with four hex bolts on corner blocks; a heavy riveted gold ring and a dark turntable | a white cylinder with a vent grille and a small hazard square; bolts flush on the plate; the gold ring is a plain disc |
| Head | sleek curved ceramic housing panelled with gold trim strips, pivoting on a gold elbow hub at the top of the yoke arm; black cables loop from the head to the turntable | drum on a straight gold neck; no arm, hub or cables |
| Barrel | about as long as the head and a third of its height thick: ceramic shroud, an exposed glowing blue-white energy coil, a front sleeve, a glowing emitter at the muzzle | a thin rod (a fifth of the head's height) with gold rings and a pale cyan cap |
| Energy | bright blue-white: the big side lens, the coil and the emitter glow | flat pale cyan caps; a small lens; nothing reads as light |
| Pennant | red cloth with a gold circle-and-line glyph on a gold pole sticking out at the rear left, hanging free | a flat red plate on the drum's back face |
| Colours | ivory ceramic, warm brushed gold, pale grey-green pedestal, black cables, blue-white light, red cloth | white everywhere, gold bands only |

| | Concept (`gate_bastion.png`) | v1 hand-built |
|---|---|---|
| Silhouette | a broad domed beetle-shaped head with two tall curved shoulder fins, over-under twin barrels raking forward, a cable column, a two-step octagonal plinth | a drum with two box shoulders, two side-by-side thin rods, a cylinder neck |
| Barrels | thick ceramic shrouds with gold collars, a section of dark stacked cooling fins around glowing blue tubes, heavy muzzle blocks with glowing emitters | thin rods with gold rings, pale caps |
| Lenses | a row of three round blue lenses in a gold bar under the barrels | three cyan slivers |
| Housing | panelled ivory ceramic with gold bands and rivets, a grey-green settler patch plate on the left, a rear hatch | plain drum, a flat patch plate |
| Column | short gold neck inside thick black cable conduits running into the ring | plain gold cylinder |
| Pedestal | grey-green prefab octagon in two steps, brass corner blocks, a louvred vent, a red banner with a gold glyph at the front | white octagon, a red square |

### v2 against the concept (what is still different)

- **Ward Turret:** the S-curve outline is the concept's: tapered pedestal, angled yoke arm with gold elbow hubs, the
  curved gun housing flowing into a long barrel, cables looping to the turntable, red pennant with the gold glyph on a
  pole at the rear left, hazard hatch on the pedestal front (painted: the retexture left the plate plain; it sits
  left of centre, where Meshy put the plate). Differences: Meshy made the housing symmetric with a lens pod on EACH
  side (the concept shows one lens, on the left); the barrel's front is a ring of rods (a gatling-like bundle) rather
  than a sleeve over an exposed coil, so the coil is a glowing core added inside the rods; the pedestal is a round
  panelled cone on the square plate (the concept's reads squarer); a few thin housing plates have ragged edges up
  close. Scale: 1.58 m tall in all, plate 1.4 m (it must fit the 2 m wall-walk; the brief's 1.8 m with the concept's
  squat proportions would need a 1.9 m plate).
- **Gate Bastion:** domed housing with the two curved shoulder fins, the grey-green patch plate on the left, the
  rear port, over-under twin barrels with dark cooling fins and glowing grooves, three lenses, cable column, gold
  turning ring, two-step plinth with the red banner at the front and louvred vents. Differences: Meshy put the twin
  barrels on the turret's right (0.78 m off the yaw axis) rather than centred (the concept's three-quarter view allows
  both readings; the front and back masters were redrawn to match the model before the retexture); the plinth is
  closer to a hexagon than an octagon. Scale: 2.10 m tall, plinth 2.95 x 2.66 m (on the 4.2 m gate towers).
- **Colours:** ivory ceramic, warm gold trim (metallic 0.85 as the hard-surface builder's gold), pale grey-green
  prefab pedestals, black cables, red cloth, blue-white energy on its own emissive material (below).

## Deliverables

| File | What |
|---|---|
| `export/hes_ward_turret_actor.glb` | runtime actor: skinned mesh `WardTurret`, materials `HS_WardTurret` (2048x1024 base, 1024x512 normal / ORM) and `HS_WardTurret_Energy` (emissive), LODs **5 587 / 2 792 / 1 387 / 656** triangles + shadow LODs tucked inside, clips Standing, Attack, Hit, Death, Dead, socket `Socket_Muzzle` |
| `export/hes_gate_bastion_actor.glb` | runtime actor `GateBastion`, `HS_GateBastion` + `HS_GateBastion_Energy`, LODs **6 167 / 3 082 / 1 534 / 726**, the same clips, sockets `Socket_Muzzle_Upper`, `Socket_Muzzle_Lower` |
| `level_generation/props/hesper_decorations/work/hard_surface/hes_ward_turret_mount.glb`, `hes_gate_bastion_mount.glb` | the mounts (Meshy pedestals up to and with the gold turning ring): **1 341 / 1 560** triangles, own 1024x512 maps, front (hatch / banner) at -y like the actor; decorations under the actors |
| `export/*_actor_lod0.glb`, `export/*_actor_authored_lods.glb`, `export/*_actor.blend` | LOD0 with rig and clips, LOD1..3 on the same rig, the editable master |
| `integration/actors.yml` | staged bindings (descriptors = the monster rows' Picture names), with the combat-target `look` on `B_Barrel` |
| `references_hd/<turret>/` | Codex HD masters (`00`..`04`, briefs, runs), the concept crops; `meshy/`, `requests/` the Meshy jobs; `textures/` the composed maps |

## Pipeline (`scripts/`, all reproducible from the Meshy returns: `TOK=<lease> scripts/build_runtime.sh`)

1. **HD masters** (Codex, `references_hd/<turret>/CODEX_BRIEF.md`): from the concept sheet and its crops, five
   1536x1024 masters per turret, rest pose with the barrels level, no shield. The Bastion's `01_front`/`02_back` were
   regenerated once (run 3) from grey renders of the Meshy model, because run 2 had centred the barrels.
   `00_three_quarter_meshy.png` = the primary with its soft alpha halo thresholded (Meshy input).
2. **Meshy Smart Topology** (`meshy-t2`, 9 000 / 12 000 triangles, untextured) from `00`.
3. `parts.py`: orient (barrels to -y, base at z = 0, yaw axis = the pedestal's centre), scale (Ward 1.58 m, Bastion
   2.10 m), split by connected component into parts (indices fixed for the raw files; `components.py` renders them
   labelled), turn the Ward's mount -45 degrees (its plate came square to the three-quarter camera), cut the
   Bastion's barrels inside the dome. `part_views.py` checks the split and the pitch clearances.
4. `prepare_uv.py`: planar dissolve + collapse to the budget per part, smooth shading with sharp edges over 38 degrees
   (the curved housings shade smoothly, hard edges only at real breaks), Smart UV with the turning parts in the top
   half of the atlas and the mount in the bottom half; the neutral upload for the retexture.
5. **Meshy retexture** (`meshy-7`, 2K PBR, original UVs, the four masters front/left/back/right).
6. `adopt_retexture.py`: the retexture's own mesh from here on (it kept every position but moved some UVs by up to
   8-25 texels and welded seams, and its maps are painted on its UVs); parts transferred by nearest face (exact).
7. `compose.py`: crops the atlas into actor (top) and mount (bottom) maps; paints the Ward's hazard hatch, the
   Bastion's glowing fin grooves and an energy swatch; metallic binarised (gold 0.85), roughness at least 0.45 on
   ceramic; normal map converted to glTF +y up (measured).
8. `build_actor_v2.py`: exports the mount decoration; energy geometry and material; rig, weights, clips; LODs
   (each welded, small pieces dropped, collapsed: 50 / 25 / 12 %; an unwelded collapse tore the seam-split plates into
   spikes); then `prepare_actor_glb.py`, `link_lods.py` + `shrink_shadow_lods.py` (shadow LODs), `set_extras.py`
   (edge darkening 0, as the undarkened mount), `set_emissive.py`.
9. Review: `render_review_v2.py` (Eevee, energy glowing), `concept_sheet.py`, `review_sheet.py`, `lod_views.py`,
   `viewer_glb.py` (viewer copies: actor LOD0 + mount).

## Bones, pivots and clips

Every vertex is rigid on one bone except the Ward's two cable loops (blended `B_Head` to `B_Barrel` over the 0.3 m
below the pivot, so they bend when the gun pitches).

| Bone | Ward Turret | Gate Bastion |
|---|---|---|
| `B_Root` (ring top, 0.599 / 1.023 m; not animated: the engine turns the actor) | the turntable | (no geometry) |
| `B_Head` (same pivot, child) | the yoke arm and elbow hubs (the Standing scan swings everything above) | column, cables, dome, shoulders, patch plate, lenses |
| `B_Barrel` (pitch pivot, bone along -y as v1; the `look` node) | the elbow hubs' axis (0, 0.16, 0.92): the whole gun housing, lens pods, pennant, barrel shroud | (-0.72, -0.25, 1.76) between the barrels where they enter the dome: the twin barrels |
| `B_Recoil` (Ward only, child of `B_Barrel`) | the barrel's rod bundle, collars, coil and muzzle (slides back) | — |
| sockets (non-deforming) | `Socket_Muzzle` at the muzzle, on `B_Recoil` | `Socket_Muzzle_Upper` / `_Lower` at the two muzzles |

Clips (30 fps, as v1, re-keyed to these pivots): Standing 6 s (scan, `B_Head` yaw +-25 degrees, barrel +-2), Attack 0.5 s
(shot at frame 5 = **0.167 s**: the Ward's barrel slides 7 cm back on `B_Recoil` with the housing kicking 4 degrees up;
the Bastion's barrels slide back 7 cm and kick 4 degrees), Hit 0.4 s, Death 1.2 s (the gun slumps 20 degrees, head turns
8 and rolls 5), Dead held. **Aim limits** (`look` in `integration/actors.yml`): Ward -35..+30 degrees (beyond +30 the
housing's rear and the pennant dip into the pedestal), Bastion -35..+35 (v1: -20..+45; the turrets stand on 6.4 m
walls and 9 m towers, so aiming down matters most). The pennant pitches with the housing (no cloth motion).

## Behaviour: idle scan, acquiring, tracking (2026-10-23)

The user's review: the idle "movement" turned one way, reset to the start and did it again (the Standing clip's ±25°
head scan looping by reset). The models are unchanged; the behaviour is now engine tactics
(`devdocs/ACTOR_SCRIPTING_INVESTIGATION.md`, Tactics: `scan`, `lead_seconds`; data in `hesper_stage/monsters.yml`):

- **Idle:** the whole actor turns (the mount stays): an eased ping-pong sweep around its placement facing, random
  turnaround headings, the odd stop part-way, short random pauses, slight barrel pitch changes, each turret on its own
  sequence and start delay. Ward ±55° at 16°/s peak, pauses 0.8–2.6 s, pitch ±5°; Bastion ±40° at 10°/s, 1.2–3.5 s,
  ±3°; D0's Old Starport Turret ±70° at 12°/s. While it scans (and while it aims) Attack's first frame holds, so the
  Standing clip's scan no longer plays (it remains for a binding without the tactics).
- **Acquiring:** a target it senses is tracked at the traverse rate (120°/s Ward, 75°/s Bastion), easing onto it, also
  before a friendly turret engages (a drone beyond its promotion range); no instant turn on being hit or turned
  hostile. The barrel pitches onto the target.
- **Combat:** it keeps tracking between shots, 0.25 s ahead of a moving target (facing, barrel and shot), fires only
  within 5°, the recoil plays on the barrel over the held aim; the target is the nearest each AI step (native), so it
  retargets when one dies or leaves range or sight.
- **Lost target:** holds the last aim (facing and barrel) for 3.5 s (Bastion 4 s), then eases back into the sweep.

Captures (`review/scan/`, minimised desktop run on the stage, hes_out1, the wall-walk Ward north of the East Gate,
`tour.yml`): [idle 20 s](review/scan/idle_strip.jpg) (drones approaching from the north are picked up around 15 s),
[a drone spawned east](review/scan/drone_strip.jpg) (tracking, shots), [hold and return](review/scan/after_strip.jpg);
[yaw trace](review/scan/yaw_trace.png) from the headless `yaw_trace_scenario.yml` (run from
`output/hesper_stage/scenario_run`).

## Energy (emission)

The lenses, emitters, the Ward's coil and the Bastion's fin grooves use their own material `HS_<Mesh>_Energy`
(base colour = the shared atlas): Meshy's lens and emitter glass faces are mapped onto a painted blue-white disc in the
atlas; added geometry: the Ward's coil core inside the rod bundle and a recessed muzzle disc, the Bastion's two muzzle
discs and three lens discs (each a strip-capped disc, no high-valence fan); the Bastion's fin-band faces (grooves
painted blue, fins dark). `set_emissive.py` gives the material `emissiveFactor` [0.70, 0.85, 1.0] (and edge
darkening 0). **The emissive texture is authored but not written**: `tools/cook_models.py` rejects `emissiveTexture`
("the engine does not sample") and the stage failed with it, so the exports carry the factor only (a flat blue-white
glow over the energy faces). When the engine samples emissive textures on actors (another agent is adding emissive and
bloom for skinned actors), rebuild with `EMISSIVE_TEXTURE=1 TOK=<lease> scripts/build_runtime.sh`: the texture is
then the material's own base colour, so the glow follows the painted energy (cores white, rims blue, fins dark).

## Meshy spending (lease `hesper:lowfolk_turrets`, limit 60)

| Job | Kind | Credits |
|---|---|---|
| `ward_turret_st_v1` | Smart Topology, 9 000 | 5 |
| `gate_bastion_st_v1` | Smart Topology, 12 000 | 5 |
| `ward_turret_retexture_v1` | retexture 2K PBR | 10 |
| `gate_bastion_retexture_v1` | retexture 2K PBR | 10 |
| **total** | | **30** |

Hesper total so far (all `hes_*_claude` projects and the decorations workspace): about 400 of 1 000.

## Checks

- `check_winding.py`: 0 inverted closed parts on both actors, both authored-LOD files and both mounts.
- `scripts/check_key_times.py` (copied from `hes_guard_reduce_claude/`): PASS on the runtime, LOD0 and viewer GLBs.
- `tools/run_creature_review.py --project level_generation/creatures/hes_turrets_claude check`: 10/10 switches, no
  console errors.
- Re-staged (`stage.py`): 4 GLBs written; `hesper_out1/landfall_defenders.yml` passes on the stage world (headless).
- In game (minimised desktop run on the stage, `review/ingame_v2.png`): both turrets load and draw on the gate towers
  and the wall; the energy reads as pale blue paint only (no actor bloom yet).

## Staging changes

- `hesper_stage/monsters.yml`: 10065 height 185 -> 160 (radius 60), 10066 height 214 -> 210, radius 90 -> 120.
- `hesper_stage/decorations.yml`: `hes_gate_bastion_mount` radius 100 -> 140 (the plinth is 2.95 m wide).
- `hesper_decorations/scripts/build_hard_surface.py`: the two mount entries left MODELS (a builder run would have
  overwritten the Meshy mounts); `turret(heavy, 'mount')` still builds the v1 mount. The whole static v1 turret
  decorations `hes_ward_turret` / `hes_gate_bastion` are unchanged (bound, not placed).

## Doubts / for review

- Up close the Meshy housings show ragged thin-plate edges and small UV-island bleed; at the turrets' distance (on
  walls and towers) they read clean, and LOD1 takes over below 550 projected pixels.
- The Ward's symmetric twin lens pods and the gatling-like muzzle are Meshy's reading of the concept, not the concept.
- The Bastion's barrels sit 0.78 m right of the yaw axis: the turret faces its target exactly, so the bolt (released
  between the two muzzle glows, as before) starts off the centre line.
- The Ward's hazard hatch is painted where Meshy's plate is, a little left of the pedestal front's centre.
- The pennant pitches rigidly with the gun; at +30 degrees it tilts with it.
- Shields (Light 800 / Standard 2 200) and the Hesperian-versus-Kreegan relation are still engine work (as in v1's notes,
  `v1_hand_built/README.md`, "Engine work still needed").
