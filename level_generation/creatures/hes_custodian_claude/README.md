# The Custodian (Hesper boss 10100, D1 Drone Control): Claude project

Round 3, Claude B of `design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md` (2026-10-23). The design: MONSTERS.md
row 10100 ("BRobot C (MM8 Terminator Unit), x1.8, maintenance arms with cutting discs, cracked colony livery") and
`design/kreegan_world/zone1/dungeons/D1_STARPORT_TERMINAL.md` ("The Custodian": an old Ancient maintenance mech
the Kreegans took over; slow telegraphed sweeps, a disc shot at range, a Light shield; staggers when it breaks).
**Staged** on the Hesper stage (`hesper_stage/monsters.yml` row 10100, `integration/actors.yml`); D1 has not placed
its monsters yet, so the row waits for the dungeon. Not installed in `assets_dev`. User acceptance: the concept
(candidate 1) only; the model awaits the integrator's in-game acceptance.

[Concept](../../../design/kreegan_world/concepts/monsters/boss_custodian.png) ·
[HD masters](references_hd/selected_views_review.png) · [viewer shots](review/viewer_shots.png) ·
[clips, clay](review/clips_clay_v3.png) · [glow parts](review/glow2_sheet.png) · [Meshy return, textured](review/tex1_sheet.png) ·
[in game, D1](review/ingame/d01_smoke_sheet.jpg) ·
viewer `http://127.0.0.1:8912/level_generation/creatures/hes_custodian_claude/review/viewer/`

## Concept

`design/kreegan_world/concepts/monsters/CODEX_BRIEF_CUSTODIAN.md`; two Codex candidates
(`boss_custodian.png` = candidate 1, `boss_custodian_candidate_2.png`), `generation_runs_custodian.json`. The
user picked candidate 1: the Terminator Unit's hovering sphere (two V-notched rings, one eye between them, the sensor
head on a post, a vent ring underneath) in Landfall's colony livery (bone-white ceramic and gold, deep blue panels, a
red field with the gold ring-and-stem sigil), cracked and missing a panel, an amber "gone wrong" eye, and two
three-segment maintenance arms ending in saw discs. No Kreegan resin.

## Deliverables

| File | What |
|---|---|
| `export/hes_custodian.glb` | runtime actor: skinned mesh `Custodian`, materials `Cust` (2048 base, 1024 normal / ORM), `Cust_Glow` (eye and vents, orange-red `emissiveFactor` [1.0, 0.15, 0.02] over a dark red-orange base, pulse 0.2 / 2 s, bloom), `Cust_Lens` (sensor lens, blue-white); LODs **7,287 / 3,652 / 2,184 / 1,159** triangles + shadow LODs (LOD2/3 by `lodrep/`, own 512 / 256 px textures); 9 clips; sockets `Socket_Eye`, `Socket_Disc_L/R` |
| `export/hes_custodian_lod0.glb` | LOD0 with rig and clips (before prepare/LODs) |
| `integration/actors.yml` | staged binding (descriptor `hes_custodian`, scale 100, events, look, clips) |
| `work/anim.blend` | editable master (rig, clips, materials); `work/build.blend` before the rig |

Scale: metres, the sphere 2.4 m across, 3.30 m to the sensor's top, 3.6 m across the arms at rest; the Terminator
Unit body (BRobot C, collision height 228) at x1.8 is about 410 units, so the model is a little smaller than the
literal factor, sized by the concept's proportions. Stage row: height 330, radius 150, reference `BRobot C`.

## Pipeline (`scripts/`; `TOK=<lease> LOD_REPAIR_PYTHON=<venv> scripts/build_runtime.sh` replays everything after the Meshy jobs)

1. **HD masters** (Codex, `references_hd/CODEX_BRIEF.md`): from the approved concept and its crops; `00` (run 1, one
   correction), `01`-`04` (run 2). The masters' soft dark alpha halo is thresholded for Meshy (`*_meshy.png`).
2. **Meshy Smart Topology** (`custodian_st_v1`, `meshy-t2`, 12 000) from `00`: 12,202 triangles in 68 clean
   components (two hemisphere shells, rings, vents, sensor, every arm segment, hub and disc separate).
3. `parts.py`: components to parts by index (`review/arm_labels.png`): Body (shells, rings, belt, vents, inner cables,
   arm mounts, sensor post), Sensor (head), Shoulder_L/R (hub, upper-arm rods and pistons), Elbow_L/R (elbow hubs,
   forearm, disc housing), Disc_L/R (disc and hub); the two long cables of each arm are weighted along the
   shoulder-elbow-hub line. Metres, sphere centre on the vertical axis, floor at the disc rims.
4. `prepare_uv.py` (from the turrets'): planar dissolve + collapse per part (body x0.45, arms x0.7) -> 6,865
   triangles; smooth shading, sharp over 38 degrees; Smart UV 66 degrees, the sphere at 1.4x texel density, packed
   with rotation (38 % of the atlas; a first try that merged small islands made huge distorted islands, `review/uv1_sheet.png`).
5. **Meshy retexture** (`custodian_retexture_v1`, `meshy-7`, 2K PBR, original UVs, the four masters).
6. `adopt.py`: the retexture's own mesh, parts and weights copied by nearest face/vertex (0 mm).
7. `compose.py`: base 2048, normal 1024 (flipped to glTF), ORM 1024. Meshy marked 96 % of the cream ceramic metallic;
   metal now comes from the colour (gold trim: yellow hues saturated over ~0.5; the discs' grey steel), 28 % of
   texels. Finds the nine vents Meshy painted under the sphere (`textures/cust_glow.json`).
8. `build.py`: glow geometry the retexture lacks: the eye lens (a dome in the gap between the rings at the front;
   the gap opens into the hollow sphere), a disc over each painted vent, the sensor lens; materials.
9. `rig_anim.py`: rig and clips (below), with floor rules per frame (the body lifted out of the floor, an arm under
   the floor raised sideways about its shoulder, in Death/Dead the corpse and both arms laid on the floor).
10. `export.py` -> `tools/prepare_actor_glb.py` -> `tools/build_actor_lods.py` -> `shrink_shadow_lods.py` ->
    `lodrep/repair_glb.py` (the lod_repair_claude route: first ladder step passing, r30_16) -> `claude_shared/emission.py`
    (colours at strength 1: the tool clamps colour x strength per channel, a 1.6 strength turned the amber yellow).

## Rig and clips (24 fps)

Root (floor) > Body (sphere centre) > Sensor, Shoulder_L/R > Elbow_L/R > Disc_L/R; sockets Socket_Eye (2 cm in front of
the lens), Socket_Disc_L/R (disc hubs, on the elbows). Every part rigid on one bone except the cables.

| Clip | s | What | lowest point (m) |
|---|---:|---|---|
| Standing | 3.0 | hover bob, sensor scan +-28 degrees, discs turning (2 turns) | 0.00 .. 0.11 |
| Walking | 1.0 | glides leaning 6 degrees forward, bob; stride 1.5 m (speed 150) | 0.00 .. 0.14 |
| Attack | 1.58 | the sweep: arms out and discs flat while the body winds back 60 degrees (0-0.42), then a full turn (the discs pass the front at the **0.5 s impact**), settle | 0.00 .. 0.67 |
| Shoot | 1.0 | leans back, the eye charges, recoil at the **0.5 s** release from Socket_Eye | 0.00 .. 0.01 |
| Hit | 0.5 | jolt back, arms fling up | 0.00 .. 0.12 |
| Death | 2.0 | shudder, the hover cuts out: drops, rolls forward-left, the arms fall onto the floor | 0.00 .. 0.04 |
| Dead | 1.0 | the corpse: vents and both arms on the floor | 0.00 |
| Fidget | 2.5 | sensor looks round, left disc raised and revved | 0.00 .. 0.11 |
| SweepTelegraphed | 3.0 | the design's 2 s wind-up sweep (impact 2.0 s); **not bound** (for a later TelegraphedSweep2s behaviour) | 0.00 .. 0.69 |

The native attack the game times the actions by (BRobot C, `rob3ata`, contact frame 4 of a 0.75 s action) acts at
about 0.5 s, so the bound Attack winds up for 0.5 s; the D1 design's two-second wind-up needs the
`TelegraphedSweep2s` behaviour (monster_hesper.txt flag; not in the engine yet). Until then the wind-up glows on both
discs (`attack_melee` glow, orange) as the telegraph.

## Checks

- Winding 0 inverted closed parts; key times PASS (324 samplers); LOD repair gate pass at r30_16.
- Floor: every clip's lowest point printed per frame above (0 mm at worst under the floor).
- Viewer `run_creature_review.py check`: 9/9 clips, no console errors; [shots](review/viewer_shots.png).
- Staged: `stage.py` ok; `rebuild_all.sh --scenarios-only` (results in the report); desktop smoke run on D1 with
  `actor spawn` (below).

## Meshy (lease `hesper:custodian`, cap 60 for Claude B's row: this model only)

| Job | Kind | Credits |
|---|---|---|
| `custodian_st_v1` | Smart Topology 12 000, from `00_three_quarter_meshy.png` | 5 |
| `custodian_retexture_v1` | retexture 2K PBR, the four masters | 10 |
| **total** | backup account (`tools/creature_meshy.py` fell back to it) | **15** |

## Doubtful / for review

- The belt gap between the rings opens into the hollow sphere; at the sides it shows as a dark slit.
- The eye is lower than the body centre (the gap Meshy modelled sits at z 1.45-1.65 of the 1.84 m centre).
- Size: 3.3 m against the literal x1.8 of BRobot C (about 4.1 m); scale the binding if the integrator wants the
  literal factor (Drone Control's ceiling is 640 units above its floor, D1 plan).
- No death explosion (`death_effect`): the corpse stays, as the boss drops Aster shard 1 where it falls.
- The light shield, the stagger on shield break and the telegraphed sweep are data/engine (shields.yml,
  monster_hesper.txt), not part of the model.

## Integrator review (2026-10-23)

Accepted (size 3.3 m kept; SweepTelegraphed stays unbound until `TelegraphedSweep2s`, ENGINE.md priority 2). Polish
done: the eye read pale yellow; the glow material's base is now a dark red-orange (0.30, 0.05, 0.01; a bright amber
base lit on top of the emission had washed it out) and its emission orange-red [1.0, 0.15, 0.02], eye and vents
alike. Rebuilt (gates unchanged), restaged, scenarios pass, viewer 9/9; D1 run `review/ingame/d01_fix_sheet.jpg`.
