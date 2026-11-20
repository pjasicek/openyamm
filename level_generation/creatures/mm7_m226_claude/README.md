# MM7 Leather Fighter (m226): Robber / Raider / Bandit — Claude rig-first project

MM7 batch A, model 2 ([batch file](../mm7_batches/BATCH_A.md)). Same route and scripts as
[`mm7_m222_claude`](../mm7_m222_claude/README.md) (humanoid playbook default; natm scripts with bar1's sword timing),
with its own mesh, rig, weights, textures and weapon (the native bodies differ: m222 is a woman, m226 a man).
**Installed 2026-10-20 (reduced exports).**

[Review viewer](review/viewer/index.html) · [viewer shots](review/shots/) · [grip](review/grip_palm.png)

**Accepted, reduced and installed (2026-10-20):** installed 2026-10-20 from [`../mm7_batches/BATCH_A_stage/`](../mm7_batches/BATCH_A_stage/README.md). **Reduced (user: "reduce tris"):** the exports to install are now the ones in [`../mm7_m226_reduce_claude/`](../mm7_m226_reduce_claude/README.md) (body LOD0 10,455 -> 8,233, falchion unchanged; same UVs, textures, tiers and clips; install commands there). This project's `export/` is their source and rollback.

## Deliverables

| File | What |
|---|---|
| `export/mm7_m226.glb` | runtime body: LODs 11,185 / 5,574 / 1,955 / 612 triangles (LOD0 incl. the 730-triangle falchion before the split), shadow LODs, 3 tier variants (`m226_a/b/c`), head material merged, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget |
| `export/mm7_m226_sword.glb` | falchion attachment on node `Sword` (730 / 364 / 130 / 42 triangles) |
| `export/mm7_m226_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export and editable master |
| `textures/`, `integration/actors.yml` | texture sets, region mask, `m226_ramps.json`, class maps; staged binding |

Install later (user decision):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m226_claude/export/mm7_m226.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m226_claude/export/mm7_m226_sword.glb --world mm7
```

then append `integration/actors.yml` to `assets_dev/worlds/mm7/models/actors.yml` (`Fighter Leather A/B/C`, scale
99.0 = `m226sa0` 187 px × dsft 0.9 = 168.3 units over 1.70 m; walk stride 1.639 m, run stride 1.8 m; impact 0.983 s;
look 60°/35°; falchion on `Sword`). Speeds 200/220/240: A and B walk (A at ~1.23x the clip), C (240 > 2.4 × 99 = 238)
runs.

## Model

- HD masters `references_hd/` (primary v2, four views, `falchion.png`); head turnaround `references_head/`.
- Smart Topology 15k (14,555 triangles, 101 parts, nothing removed): body/arms/boots, head and both hands as separate
  shells, shoulder yoke, hair, ponytail, face strands, eyes, back scabbard, dagger and sheath, belt and straps, 81 small
  studs, spikes and buckles. Reduced after weighting to 10,455 (skin 5,900 with head and hands protected; the fittings
  decimated together) — about 4 % over the ~10k guideline (deviation; reducing further would invalidate the textures).
- Rig: source-frame rig; elbows at t 0.48 on both arms (Meshy 0.45/0.45, ring line fits 0.45/0.51, source 0.50);
  fingers by connectivity on the hand shells (pieces 3/4); hand frames within 25° except the thumbs (32°/30°).
- Weights (`weights_fix.py`): skin = Meshy + shoulder fade + jaw free; hair/strands/eyes rigid head; yoke copies the
  skin (arm share ≤ 0.35, smoothed); ponytail head → neck → chest by height; belt/straps copy without arm weight;
  scabbard rigid chest; dagger rigid pelvis; fittings rigid on the dominant bone under them. Finger web smoothing keeps
  only adjacent fingers (`finger_weights.py`).
- Falchion (`make_falchion.py`): broad-side outline and texture from `references_hd/falchion.png`, convex edge on +X
  (the reference's left side, mirrored), notched spine, 1.2 cm grip (= the solved fist), 1.0 m; blade roll 90°.

## Clips

As m222 (MM7 human fighters share the native action design): Standing Mixamo Standard Idle; **Walking Mixamo Walk**
(1.639 m stride; constant 1.7 cm floor lift); Running Standard Run + run fit; Attack Sword And Shield Slash (2)
planted + 20 % legs, stepped feet, 0.3 s lead, blow 0.983 s (native attack 1.0 s); Hit set Unarmed get-hit F1;
Death Falling Back Death (travel halved); Fidget Sword And Shield Power Up planted. The empty left hand keeps 50 % of
the source finger curl (`apply_grip.py LEFT_CURL=0.5`).

## Gates (2026-10-20)

- G4 arm stretch p99 ≤ 1.84, max 2.92 (attack recovery). G5 right ≤ 1.73x, left ≤ 3.9x (after the web fix and the
  half curl; 6.9x before).
- G6: no blade/forearm/hand inside the skin except the Death right hand 5 cm while it wraps the raised thigh during
  the fall (source motion, a few frames) and ≤ 1.1 cm brushes. The grip: the index finger sits ~3.7 mm into the 1.2 cm
  handle (not visible; render `review/grip_*.png`).
- Soles: grounded within −1.6…+1.6 cm (walk after the lift −1.5…+1.5).
- Blade: convex edge leads at the impact (+0.94); edge-leading share attack 0.70, walk 0.95, fidget 0.76, hit 0.96.
- Viewer: 24/24 tier/clip switches, no console errors. In game: not checked (nothing installed).

## Textures and tiers

`compose_m226.py`: body/head 1K sets (body retexture with Meshy UVs copied back exactly; head retexture on our head
UVs); skin repainted to one albedo; AO graded; ORM per class. One recolour region **R = green cloth** (jerkin,
collar, laced thigh panel): the palette entries that differ between the tiers and are green in palette 52; ramps per
tier from the native stand/walk/attack pixels: A 52 green, B 228 blue, C 229 red.

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

Feet (review 2026-10-20, "slightly angled on the boot edge"): the project's `foot_level.py` also levels the sole's roll
about the heel–toe line on grounded frames (the clips had rolled the boots onto their outer edges; the rest pose is
flat) and moves the pelvis by the change of the lowest sole point, so floor contact is unchanged; the run gets
`Running:rollonly`. Soles and gates re-measured after the rebuild (`review/gates_final.txt`). Walk and run take one constant roll per foot in the foot's own frame and one constant pelvis shift (review 2026-10-20: the per-frame roll switched on and off as the feet landed and lifted, a visible ankle twitch; foot rotation per frame is back to the source's). Hit, Attack, Fidget, Death and Standing: the roll is weighted by flatness (planted and level lengthwise), capped at 20 deg and smoothed over the clip (batch C's rule, mm7_m218_claude; peer report 2026-10-20: the groundedness-only roll snapped a stepping foot in Hit up to 22 deg and a lifting foot in Death up to 65 deg per frame); every clip's foot turn per frame is now within 2 deg of the source's. Walk bob (review 2026-10-20, "uneven head bob"): `walk_bob.py` after `clip_timing.py` smooths the walk's pelvis height over the loop (both steps alike, ankles kept reachable) and re-solves the legs to the same ankle paths and foot rotations; the retarget's floor rule had left a zigzag and up to 3.7 cm frame jumps.

## Replay

As m222: `TOKEN=<lease> ELBOW_T=0.48 STAGE=rig scripts/rebuild.sh`, then `STAGE=anim DEATH_UNTIL=12 R_HANDLE=0.012
LEAD=0.3 LEFT_CURL=0.5 scripts/rebuild.sh` (twice on a fresh project: the first pass writes the grip the sword
clearance uses); `make_falchion.py` (python3, then Blender); texture chain; `compose_m226.py`;
`scripts/build_runtime.sh`; `viewer_tiers.py`; `update_viewer_manifest.py`.

## Known limits / for user review

- LOD0 body 10,455 triangles (~4 % over the guideline).
- Death: the sword hand passes into the raised thigh for a few frames; the attack's overhead swing is fast (source).
- The viewer shows the steel blade dark (environment reflections on a low-roughness steel material).
