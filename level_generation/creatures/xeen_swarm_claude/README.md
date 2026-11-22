# Xeen swarms: Insect Swarm, Stingers and the Doom Bug (Claude project, 2026-11-20)

Xeen's **Swarms** family (`source/monsters.yml` `swarms`, picture `Xeen Swarm`): Doom Bug A (L2), Insect Swarm B (L4),
Stingers C (L6); Vertigo, Joe's Warehouse, Witch Tower. The Xeen art splits in two:
- Insect Swarm and Stingers share Clouds image 23 (`sprites/xeen/023.mon`, `.att`): a cloud of rust-brown flying
  stinging insects with grey wings.
- The Doom Bug is Clouds image 2 (`sprites/xeen/002.mon`): one giant teal cricket with purple eyes and brown
  antennae, not a swarm.

## Decision: a mesh swarm, not particles

The engine draws actors as models or sprites; there is no particle-bodied actor, and a particle cloud would need engine
work (lane A1) for hit, death and corpse handling. A swarm of a few rigged insects on their own bones works with every
existing actor system (picking, hit reaction, death, corpse, tiers, LODs) and costs one Meshy model. So the swarm is
**seven copies of one Stinger** (`references_hd/`, Meshy `wasp_smart_topology_v1` and `wasp_retexture_v1`), each on
bone `W<i>` with four wing bones, flying procedural closed paths. The Doom Bug is its own model (below).

## Swarm (installed)

| Item | Value |
|---|---|
| Installed | `assets_source/worlds/xeen/models/xeen_swarm.glb` (runtime copy in `assets_dev`) = `export/xeen_swarm_final.glb` |
| Meshes | `Swarm` (7 x 995 triangles, opaque) and `SwarmWings` (882 triangles, blended, alpha 0.55); LODs 6,944 / 3,317 / 3,125 / 2,083 (far chain `lod_repair_claude` step r45_30: the thin legs fail the stronger collapses) |
| Skins | `swarm_b` Insect Swarm (native rust orange-brown), `swarm_c` Stingers (dark crimson; Xeen draws both with one palette, so C is a design choice) |
| Region | R = the orange-brown hairy body (hue 8-50 degrees); legs, eyes, stinger and wings keep their paint. Ramp fit 8-9 levels mean |
| Texture | one Stinger: 4K Meshy paint on its `uv_atlas` layout (81 % use for the single insect), 2K colour, gentle grade, gutter fill; the seven copies share the UVs |
| Scale | 100 (each Stinger 0.72 m wingspan; the cloud about 1.4 m wide, 0.2-1.5 m high) |
| Clips (30 fps) | `Fly` 2.0 s loop (standing, walking, running), `Attack` 1.0 s (the insects dart at the party one after another, abdomens down: **impact 0.45 s**), `Hit` 0.5 s (scatter), `Death` 1.6 s (they drop one by one onto their backs), `Dead`, `Fidget` 2.0 s (a quarter swirl) |
| Floor | flyer rule: the lowest living point meets the floor (lift 0.18 m baked); `floor_fix.py --raise Death` lifted 2 keys; audit ok |

Scripts: `pieces.py`, `wasp_single.py` (reduce, unwrap, upload), `swarm_build.py` (copies and bones), `swarm_anim.py`,
`bake_ao_wasp.py`, `compose_wasp.py`, `tier_ramps.py`, `export_glb.py`, `build_runtime.sh`.

## Doom Bug

| Item | Value |
|---|---|
| Installed | `assets_source/worlds/xeen/models/xeen_doombug.glb` (far LODs from `lod_repair_claude`) |
| Mesh | Meshy `bug_smart_topology_v1`, 53 chitin pieces, decimated after rigging to 9,413 triangles; LODs 9,413 / 4,706 / far chain |
| Rig | `bug_rig.py`: a bone per piece over the pieces' contact tree with anatomical corrections, rigid weights; the left middle leg came back as a femur only, so its tibia, tarsus and claws are the right middle leg's mirrored copies |
| Texture | `bug_retexture_v1` 4K on the `uv_atlas` layout: atlas 79.1 %, spread 1.47, fragments 1.0 %, stretch p90 1.14; one skin `bug_a` (region R = the teal chitin, a ramp that reproduces the paint, fit 3.2 levels) so later recolours are numbers only |
| Scale | 130 (1.5 m long -> 195 units; the Xeen sprite is about the toad's size) |
| Clips (30 fps) | Standing 2.0 s, Walking 0.8 s tripod (0.70 m/cycle; the jumping legs only shuffle), Running 0.5 s (0.80 m/cycle), Attack 0.9 s rear and lunge-bite (**impact 0.42 s**), Hit 0.5 s, Death 1.5 s (rears, flips onto its back, legs curl up), Dead, Fidget 2.0 s (head turn, a front leg cleans an antenna) |

Scripts: `bug_rig.py` (`tree` argument: the piece tree only), `anim_bug.py`, `clip_sheet_bug.py`, `bake_ao_bug.py`,
`compose_bug.py`, `tier_ramps_bug.py`, `export_bug.py`, `build_runtime_bug.sh`. Meshy for the whole project: wasp 5 + 10,
cricket 5 + 10 = **30 of 40 credits**.

## Known limits

- Hornets (Hell Hornet, Hornet Swarm, Hornet Queen, D3) are "as Swarms": they can take more skins of this model;
  the Xeen Hell Hornet sprite (Darkside image 20) is a single big teal beetle-wasp, so a hornet model may be wanted.
- Seen in game only as spawned actors in XD-21 (2026-11-20, `build-xeen`); the Doom Bug not yet; not accepted by the user.
