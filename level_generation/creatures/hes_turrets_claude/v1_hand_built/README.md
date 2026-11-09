> **Archived v1 (2026-10-22): replaced by the v2 Meshy turrets (../README.md).** This folder keeps the v1 exports,
> scripts, review, integration and the two v1 mounts (`mounts/`) for rollback: copy `export/*.glb` back to `../export/`,
> `mounts/*.glb` to `level_generation/props/hesper_decorations/work/hard_surface/`, `integration/actors.yml` to
> `../integration/`, restore the mount entries of `build_hard_surface.py` MODELS and the stage heights 185/214, re-stage.

# Hesper Landfall wall turrets: rigged actor models — Claude project

Landfall's two friendly wall turrets (monsters 10065 **Ward Turret**, 10066 **Gate Bastion**;
`design/kreegan_world/data/make_monster_tables.py`; concepts `design/kreegan_world/concepts/monsters/ward_turret.png`,
`gate_bastion.png`) as actors that can turn to a target and shoot (user, 2026-10-22: "they should also be like
eventually able to rotate to target + shoot"). Hard-surface, rigid, credit-free: built from the same primitives as
the placed decorations. Not in `assets_dev`: the Hesper stage (`hesper_stage/monsters.yml`, `decorations.yml`) uses
these exports and the mounts; re-stage with `python3 level_generation/projects/hesper_stage/stage.py` after a rebuild.

[v1 review sheet](review/turrets_sheet.png) (rest, head +60° yaw with the barrel +15°, the ring close up, the Attack's
shot frame, Dead; one row per turret)

## Deliverables

| File | What |
|---|---|
| `level_generation/props/hesper_decorations/work/hard_surface/hes_ward_turret_mount.glb`, `hes_gate_bastion_mount.glb` | the mounts: the pedestal and wall plate up to and with the gold turning ring (320 / 192 triangles), same materials; decorations to place under the actors |
| `export/hes_ward_turret_actor.glb` | runtime actor: one rigid skinned mesh `WardTurret` (head, neck, lens, pennant, barrel), LODs 816 / 432 / 280 / 144 triangles (authored) + shadow LODs tucked inside, clips Standing, Attack, Hit, Death, Dead, socket `Socket_Muzzle` |
| `export/hes_gate_bastion_actor.glb` | runtime actor `GateBastion` (head, shoulders, patch plate, three lenses, twin barrels), LODs 1480 / 712 / 376 / 196, the same clips, sockets `Socket_Muzzle_L` (+x, the turret's left) and `Socket_Muzzle_R` |
| `export/*_actor_lod0.glb`, `export/*_actor.blend` | the LOD0 export and the editable master (textures packed) |
| `integration/actors.yml` | staged bindings (descriptors = the monster rows' Picture names), with the combat-target `look` on `B_Barrel` |

Bones (every vertex 100 % on one bone, nothing stretches): `B_Root` at the ring's top centre (0, 0, 0.77 m), not
animated: the engine turns the whole actor to its facing, so the actor's yaw is the turret's traverse; `B_Head`
(child, same pivot) carries the housing; `B_Barrel` (the barrels' axis point in the housing: ward 1.41 m, bastion
1.60 m) pitches the barrels and slides them back for the recoil; the sockets at the emitter tips are non-deforming
children of `B_Barrel`. The neck sits 5 mm into the ring, so no gap opens at any yaw.

## Shading and LODs (user review 2026-10-22: "very obvious sharp polygon edges")

The round parts were flat-shaded 10–14-sided `cylinder`s. They are now `lathe`/`round_cylinder` solids of revolution
(`build_hard_surface.py`): 24 sides around the head drum and its bands, 16–20 on the neck, 16 on barrels, cooling
rings and emitters, 12 on the lenses, 24 on the Ward's pedestal, 32 on the turning ring. Normals are smooth around
the circumference. Edges are hard only at real breaks: the flat caps, and the drum meeting its tapered end cones
(the profile turns by more than 30°). UVs are at the shared density (one native texel per world unit), wrapped by arc
length with the wrap seam on the underside (the back for upright parts), and the caps are planar. The flat parts keep
flat shading: the Bastion's octagonal plinth, the shoulders, plates, hatch and hex bolts. The whole-turret
decorations `hes_ward_turret` / `hes_gate_bastion` share `turret()` and changed the same way (1136 / 1672
triangles). Every other model of the builder is unchanged. Before/after close-ups:
`scripts/render_closeup.py -- <actor lod0> <mount> <heavy 0|1> <prefix>`.

LODs are **authored**, not decimated: `tools/build_actor_lods.py` turned the thin rings and bands into spikes. The
actor build calls `turret(heavy, part, lod)` once per level with the side counts of `TURRET_SIDES` (LOD1 about
10–14 sides, LOD2 6–10 sides, LOD3 6–8 sides without bands, rings or lenses; the Bastion drops its fins at LOD2 and
its shoulder trims at LOD3). `scripts/link_lods.py` links `export/<name>_authored_lods.glb` into the runtime GLB as
`openyamm_lods` and adds the merged shadow meshes. It reuses `build_actor_lods.py`'s helpers and leaves LOD0, the rig,
the clips and the images unchanged.

## Clips (30 fps, all from t = 0)

| Clip | Length | What |
|---|---|---|
| Standing | 6 s | a slow scan: head yaw ±25° (sine), barrel ±2° at twice the rate; loops |
| Attack | 0.5 s | still until the shot at frame 5 (**impact 0.167 s**): the barrels kick 7 cm back and 4° up, recover by 0.5 s |
| Hit | 0.4 s | a shudder: head yaw +4/−3/+2/−1°, a little roll |
| Death | 1.2 s | a twitch up, then the barrels slump 20° down, the head turns 8° and rolls 5°, a small bounce |
| Dead | held | the Death's last pose |

Walking, run and fidget play Standing (stationary). The sensor lenses do not pulse: the builder's glow is a constant
emissive factor and the clips animate bones only.

## Rebuild

```sh
blender --background --factory-startup --python level_generation/props/hesper_decorations/scripts/build_hard_surface.py \
    -- hes_ward_turret_mount hes_gate_bastion_mount           # the mounts (the builder's MODELS)
TOK=<lease> level_generation/creatures/hes_turrets_claude/scripts/build_runtime.sh   # actors: build (LOD0 + authored
                                                     # LODs), prepare, link LODs, shadow LODs, extras (edge darkening 0)
tools/run_creature_blender.sh --token <lease> level_generation/creatures/hes_turrets_claude/scripts/render_review.py \
    hes_ward_turret_actor level_generation/props/hesper_decorations/work/hard_surface/hes_ward_turret_mount.glb
python3 level_generation/creatures/hes_turrets_claude/scripts/review_sheet.py
```

`build_hard_surface.py`'s `turret(heavy, part, lod)` builds the whole turret (`all`, the decoration), the `mount`,
the `head` or the `barrel` (at `lod` 0..3), and returns the pivots; the actor build imports it
(its own build loop runs only as `__main__`). Checks: `check_winding.py` 0 inverted closed parts on both mounts,
both whole turrets, both actors and both authored-LOD files.

## Staging (later, with the Hesper actors)

Install the two actor GLBs into the stage's `worlds/hesper/models/` and add `integration/actors.yml` there; add the
two mounts to `hesper_stage/decorations.yml` (radius as the whole turrets: 70 / 100); in `hesper_out1/build_out1.py`
place the mount decoration where the whole turret stands now and a Stationary 10065 / 10066 actor at the same
position, facing outward.

## Engine work still needed

Done (2026-10-22, engine tactics: `devdocs/ACTOR_SCRIPTING_INVESTIGATION.md`, Tactics; data in
`level_generation/projects/hesper_stage/monsters.yml` `tactics` and `integration/actors.yml` `look`):

- **Aim at the current target:** `look: {target: combat, nodes: [B_Barrel], max_yaw_degrees: 8, max_pitch_degrees: 45,
  min_pitch_degrees: -20, hold_clip: Attack}`: `B_Barrel` pitches toward the target the turret engages (any distance,
  eased like the head look), with a little yaw lead, and rests without one. While it tracks, Attack's first frame
  replaces the Standing scan (the scan swung the guns ±25° off the target between shots); the scan plays when idle.
  `B_Head` is not fine-yawed: the whole actor traverses.
- **Traverse:** the AI turns the whole actor to its target at 120°/s (Ward) or 75°/s (Bastion), fires only within 5°,
  keeps tracking between shots, and with no target turns back to its placement facing (outward) at the same rate.
- **The Hesper monster rows and actor bindings in the stage** (`hesper_stage/monsters.yml`).

Still needed:

- **Hesperian vs Kreegan relation:** a Hesperian monster group hostile to every Kreegan group and friendly to the party
  (the monster relations table), so the turrets and the guards fire on drones and raiders and never on the party.
  Today they only fight the party after it strikes one of them.
- **Shields:** the Light (Ward Turret 800) and Standard (Gate Bastion 2 200) personal shields of the proposed Hesper
  monster columns (`design/kreegan_world/data/monster_hesper.txt`), drawn as the concepts' thin blue-white shell.
- A turret struck by the party snaps to face it once (the world's hostility switch), then traverses.

No Meshy credits.

## Viewer

`review/viewer/` (serve the repository over http, port 8912): both turrets, each actor LOD0 with its mount added
as a static mesh at the shared origin (`scripts/viewer_glb.py`; review copies, not runtime files); every clip.
`tools/run_creature_review.py --project level_generation/creatures/hes_turrets_claude check`: 10/10 switches.
