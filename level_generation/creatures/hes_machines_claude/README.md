# Hesper colony and Lattice machines — Claude project (Round 3, Claude C)

Scope: the "Claude C" row of [CREATURE_BUILDS.md](../../../design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md#round-3-claude-sessions-self-contained-2026-10-23):
10054 Old Starport Turret, 10140 Test Emplacement, 10142 Capacitor Column, 10143 Throne Conduit.

**Status (2026-10-23):** all four rows are built, checked and **staged**. 10054, 10142 and 10143 were **accepted by
the integrator** (P3.md: no retexture, the conduit's LOD deviation and the soft turret head accepted; the D12/D16
height rebuilds, D16's cell placement and D0's mount swap went to a dungeon session). **10140 Test Emplacement** was
added afterwards from `hes_ion_cannon_codex`'s export (no Meshy). Meshy: **55 of 60 credits**. The concept picks are
the user's (below).

[Viewer](http://127.0.0.1:8912/level_generation/creatures/hes_machines_claude/review/viewer/) (all three, all clips) ·
[viewer shots](review/viewer_shots.png) · [PBR stills](review/pbr/) · [in game](review/ingame/sheet.png) ·
[true scale in D12](review/ingame/d12_spawn/01-spawned_conduit_vs_staged.png) /
[in D16](review/ingame/d16_spawn/01-spawned_cell.png) · [scenarios](review/scenarios_20261023.log)

## Concepts (user-approved picks, 2026-10-23)

Brief: [`CODEX_BRIEF_COLONY_LATTICE_MACHINES.md`](../../../design/kreegan_world/concepts/monsters/CODEX_BRIEF_COLONY_LATTICE_MACHINES.md);
two Codex candidates each, the user picked in the session:

| Row | Sheet | Pick |
|---|---|---|
| 10054 | [`starport_turret.png`](../../../design/kreegan_world/concepts/monsters/starport_turret.png) | candidate 1: boxy hooded head on a fork yoke, faded colony livery, no pennant |
| 10142 | [`capacitor_column.png`](../../../design/kreegan_world/concepts/monsters/capacitor_column.png) | candidate 2: three stacked violet drum cells in gold clamps (the column's own skin) |
| 10143 | [`throne_conduit.png`](../../../design/kreegan_world/concepts/monsters/throne_conduit.png) | candidate 1: one continuous violet core, bone-and-gold crown, resin roots, cables off one side |
| 10140 | none: the approved `ion_cannon.png` at a quarter scale on a plinth (MONSTERS art row) | — |

Records: `generation_runs_<stem>.json` beside each sheet.

## Deliverables (`export/`)

| File | What | LOD triangles (0/1/2/3) |
|---|---|---|
| `hes_starport_turret.glb` | 10054 actor: `StarportTurret`, `HS_StarportTurret` (2048x1024 base, 1024x512 normal/ORM) + `HS_StarportTurret_Energy` (blue-white `emissiveFactor`), clips Standing / Attack / Hit / Death / Dead, `Socket_Muzzle` | 4 528 / 2 263 / 1 353 / 710 |
| `hes_starport_turret_mount.glb` | its own pedestal as a decoration (unskinned, 1 475 triangles with the inner core, own 1024x512 maps). **Not bound or placed**: D0 places `hes_ward_turret_mount`, whose ring is at the same 0.599 m, so the head sits correctly on it | — |
| `hes_capacitor_column.glb` | 10142 actor: `CapacitorCell`, 2K base / 1K maps, `_Energy` (violet-white factor) and `_Dark` (the off state) | 5 529 / 2 762 / 1 346 / 661 |
| `hes_throne_conduit.glb` | 10143 actor: `ThroneConduit`, the same material set | 6 006 / 3 003 / 2 389 / 1 493 |
| `*_lod0.glb`, `*.blend`, `*_info.json` | LOD0 with rig and clips, the editable master, build facts | |

Bindings: `integration/actors.yml` (descriptors `hes_starport_turret`, `hes_capacitor_column`, `hes_throne_conduit`;
scale 100, models in metres, floor at z = 0, front glTF +z, yaw offset as the Ward Turret's).

## Rigs, clips, glow and the off state

- **Old Starport Turret** (the Ward Turret's route): `B_Root` turntable at the ring top (0.599 m), `B_Head` the fork
  yoke and hub trunnions, `B_Barrel` the housing, lens pods and barrel (pitch pivot (0, 0.10, 0.97) between the hubs;
  the `look` node), `B_Recoil` the front sleeves and muzzle (slides 7 cm), `Socket_Muzzle`. Clips at 30 fps: Standing
  6 s (scan), Attack 0.5 s (shot at frame 5 = 0.167 s), Hit 0.4 s, Death 1.2 s (the gun slumps 15°), Dead.
  Energy: a lens disc on each pod (Meshy built a lens pod on both flanks; the concept has one on the left), the muzzle
  disc and the barrel's exposed coil section, on `HS_StarportTurret_Energy` (blue-white, the Ward's colour). The
  stage's scan/traverse tactics for 10054 are unchanged.
- **Look gate** (`scripts/look_gate.py`, `review/look_gate.json`): the barrel group pitched −40…+40° against the
  yoke/turntable and the pedestal: the pedestal is hit from +35°; contact with the yoke never exceeds the rest pose.
  Binding: pitch −30…+25°, barrel yaw 0 (the whole actor traverses).
- **Capacitor cell and Throne Conduit**: one rigid body on `B_Root`; the glowing faces (`B_Glow`, material `_Energy`,
  violet-white `emissiveFactor` [0.62, 0.42, 1.0], bloom) and a copy of them 3 mm inside (`B_Dark`, material `_Dark`,
  the same atlas at `baseColorFactor` [0.22, 0.2, 0.26]) are switched by bone scale (1 / 0.001, constant keys): lit in
  Standing (6 s), flickering out for two frames in Hit (0.4 s, with a shudder), flickering and going out in Death
  (1.2 s), dark in Dead. That is the design's off state: a shorted column's cell, a cut conduit. (A column shorted by
  its terminal hides its cell actor: D16's events.) Attack clips map to Standing (no attack).
- No emissive textures (rule 4): factor-only glow on the `_Energy` materials.

## Pipeline (`scripts/`; `TOK=<lease> LOD_REPAIR_PYTHON=<venv> scripts/build_runtime.sh [name...]`)

1. HD masters (Codex, `references_hd/CODEX_BRIEF.md`, two runs per machine): five unresized views each; the
   primaries' soft alpha halo thresholded into `00_three_quarter_meshy.png` (Meshy input).
2. Meshy Smart Topology (`meshy-t2`, 10 000 / 9 000 / 9 000 triangles, untextured).
3. `parts.py` (orient, scale to 1.6 / 3.0 / 6.0 m, centre on the yaw axis; the turret split into mount / turntable /
   yoke / housing+barrel / front sleeves by component; its pedestal turned 45° so a face looks forward),
   `prepare_uv.py` (planar dissolve + collapse to 55-70 %, sharp edges over 38°, Smart UV; the turret's moving parts
   in the atlas's top half, the mount in the bottom half).
4. Meshy retexture (`meshy-7`, 2K PBR, original UVs, front/left/back/right masters), `adopt_retexture.py` (the
   returned mesh, parts by nearest face: exact), `dump_tris.py`.
5. `compose.py`: runtime maps; metal only where Meshy says metal **and** the colour is gold/bronze (Meshy marked 79-86 %
   of these machines metal, ceramic and resin included, and they rendered dark); roughness floors; normal maps to
   glTF; the turret's energy swatch; the cell's glowing faces by violet colour (`work/<name>_energy.json`).
6. `build_machine.py` (rig, clips, glow/dark copies, the turret's pedestal core), `prepare_actor_glb`,
   `build_actor_lods`, `shrink_shadow_lods.py`, `set_glow.py`, far LODs by the `lod_repair_claude` route
   (`lodrep/`: the Ashrunner project's copy, plus an `LOD_LADDER` override), `check_key_times.py`.
7. Review: `render_review.py` (Eevee), `viewer_glb.py` (viewer copies), `look_gate.py`, `glb_views.py`.

**The conduit** needed a second retexture: Smart UV cut its thin cables into 1 792 islands and the first retexture
painted them as a gold/navy mosaic with a copper core. `UV_VERSION=v2` unwraps it with xatlas
(`scripts/xatlas_uv.py`, 652 charts: whole cable strips and plates) and adopts `throne_conduit_retexture_v2`, which
came back coherent (ivory plates, black resin cables, gold bands). Its core still came back copper, so
`mark_energy.py` picks the core tube and crown node by geometry and `compose.py` repaints them violet-white.

## Checks

- `check_winding.py`: 0 inverted closed parts on all three actors and the mount.
- `check_key_times.py`: PASS on every runtime and LOD0 GLB.
- Far LODs (`work/lodrep_<name>/result.json`): turret 30/16 % and cell 25/12 % pass the switch gate. **Conduit:
  deviation** — LOD2 outline 7.6 % against the 6 % gate (colour 20.8 within its limit 23.5; LOD3 passes) at the
  ladder's last step (40/25 %); a larger LOD2 equals LOD1 (50 %), so the gate is not reachable without rebuilding
  LOD1 as well. Its thin cables thin out at the LOD2 switch size.
- Viewer: `run_creature_review.py check`: 15/15 model and clip switches, no console errors; shots in `review/shots/`.
- Stage: `stage.py` cooked the three GLBs; `rebuild_all.sh --scenarios-only`: **73 passed, 0 failed**
  (`review/scenarios_20261023.log`).
- Desktop smoke runs (minimised, stage world; `review/ingame/`): D0 (Firing Range, Hangar Control), D16 (Power Core)
  and D12 (Throne): every row loads and draws, no "Actor model load failed".

## For the integrator / map builders

- **D12's conduits and D16's cells draw at a quarter / half of their size** until those maps are rebuilt: the engine
  scales an actor model by the placed actor's stored body height over the monster's height
  (`WorldFxSystem.cpp`), and both maps were built when these rows were 160 high (the Ward stand-in). The rows are now
  600 (conduit) and 300 (cell) high; re-running `hesper_d12` and `hesper_d16` builds fixes it
  (true-scale spawns: `review/ingame/d12_spawn/`, `d16_spawn/`). D0's turrets keep 160 and are right.
- **D16's cells stand beside their columns**, not in a gap in the column's face (D16 section 7); a map matter.
- The conduit's floor cables trail off its left (model +x); the placement's facing decides where they go. Whether a
  non-attacking stationary actor with a traverse rate turns toward the party (and swings its cables) is not verified.
- `export/hes_starport_turret_mount.glb` (the colony pedestal) can replace D0's `hes_ward_turret_mount` decorations;
  binding and placement are the D0 builder's.

## Known limitations

- The turret's moving parts got only about 13 % of their half of the atlas (the packing left most of it empty), so
  the head's texture is softer than the pedestal's up close. Fixing it means a new UV layout and a new retexture
  (10 credits; 5 remain under the cap).
- Meshy built a lens pod on both flanks of the turret; both lenses glow.
- The cell's ceramic plates came back tan-gold rather than ivory.

## Meshy (lease `hesper:colony_lattice_machines`, cap 60; backup account)

| Job | Kind | Credits |
|---|---|---|
| `starport_turret_st_v1`, `capacitor_column_st_v1`, `throne_conduit_st_v1` | Smart Topology | 3 × 5 |
| `starport_turret_retexture_v1`, `capacitor_column_retexture_v1`, `throne_conduit_retexture_v1` | retexture 2K PBR | 3 × 10 |
| `throne_conduit_retexture_v2` | retexture 2K PBR (xatlas layout) | 10 |
| **total** | | **55** |

Receipts and task ids: `creature_3d_progress.json`.

## 10140 Test Emplacement (`scripts/build_emplacement.py`)

The approved great ion cannon, reused as the work package asks (no new Meshy job): its rest-state export
`hes_ion_cannon_codex/export/hes_great_cannon.glb` (snapshot `work/emplacement/great_cannon_source.glb`, SHA-256
`86936db620847ecfedcfe34a6906e71020ff92897fe807e209e02ae17a8c5a1d`), whole: its "bastion" is a round turntable base.

- **Scale 0.12:** the 50 m head becomes 6 m (THE_CROWN.md's build table: "barrel 600" on a plinth of radius 300; the
  MONSTERS art row says "a quarter scale", which predates the 5 000-unit head). 2.96 m tall, base 3.8 m across.
  Row height 300, radius 190.
- **Rig:** `B_Root` base and yoke (by welded component: base below 5 m, head above 8.4 m at the source scale),
  `B_Barrel` the head, pitching about the yoke arms' tops; `Socket_Muzzle` at the muzzle crown.
  `review/look_gate_emplacement.json`: the head clears the yoke from 0 to +30°; below 0 it digs into the yoke arms
  (Meshy's head and arms interpenetrate at rest), so the look is −5…+25° and the death slump −4°.
- **Glow:** the cannon's zones (breech core, pods, four rings, muzzle crown) as three bone-switched layers: dim
  (`HS_TestEmplacement_Energy`, the cannon's resting violet [0.24, 0.08, 0.46]), dark (3 mm inside, Death/Dead) and
  hot (3 mm outside, `HS_TestEmplacement_Hot`, [0.9, 0.62, 1.0] × emissive strength 3) in four groups. Attack 1.0 s
  is the great cannon's wind-up in its order — breech (frame 6), pods (12), rings (18), muzzle crown (23) — the shot at
  frame 24 (0.8 s, `release: muzzle`), then out. Hit flickers the zones; Death goes dark.
- LODs 9 982 / 4 981 / 2 326 / 1 097 (LOD0 is the cannon's 7 916 plus the glow copies; far LODs pass at 25/12 %).
  Winding 0 inverted; key times PASS; viewer 20/20 with the other three
  ([shots](review/viewer_shots_emplacement.png), [PBR](review/pbr/test_emplacement_sheet.png)).
- Staged (row 10140: height 300, radius 190; tactics unchanged). Scenarios after it: **75 passed, 1 failed**
  (`review/scenarios_20261023_emplacement.log`: `hesper_d15/d15_main_path` step 87, a Drudge Hulk in front of an
  interaction; D15 places none of these rows). A first sweep was cut short by a concurrent engine rebuild and an edit
  of `rebuild_all.sh`. Desktop smoke run of `hes_out4` (G7 yards, `review/ingame/out4/`): loads and draws, no
  "Actor model load failed".
- **For the Crown builder:** the placed actor stores the old height 160, so until `hesper_out4` is rebuilt it draws
  at 160/300 of its size (as D12/D16). The muzzle socket is in the model; the map's lock beam and blast wall are the
  map's.
