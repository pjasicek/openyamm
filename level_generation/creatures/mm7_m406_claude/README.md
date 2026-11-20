# MM7 Swordsman (m406): Swordsman / Guard / Adventurer — Claude rig-first project

MM7 batch A, model 4 ([batch file](../mm7_batches/BATCH_A.md)). Same route and scripts as the batch's fighters
([`mm7_m230_claude`](../mm7_m230_claude/README.md)); the native body is not the Plate Fighter's (open spiked helmet
over a mail coif, bearded face, bare upper arms), so it has its own mesh, rig, weights and textures. **Installed 2026-10-20 (reduced exports).**

[Review viewer](review/viewer/index.html) · [viewer shots](review/shots/) · [grip](review/grip_palm.png)

**Accepted, reduced and installed (2026-10-20):** installed 2026-10-20 from [`../mm7_batches/BATCH_A_stage/`](../mm7_batches/BATCH_A_stage/README.md). **Reduced (user: "reduce tris"):** the exports to install are now the ones in [`../mm7_m406_reduce_claude/`](../mm7_m406_reduce_claude/README.md) (body LOD0 10,294 -> 8,072, sword unchanged; same UVs, textures, tiers and clips; install commands there). This project's `export/` is their source and rollback.

## Deliverables

| File | What |
|---|---|
| `export/mm7_m406.glb` | runtime body: LODs 10,748 / 5,372 / 1,932 / 639 triangles (LOD0 incl. the 454-triangle longsword before the split), shadow LODs, 3 tier variants (`m406_a/b/c`), head material merged, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget |
| `export/mm7_m406_sword.glb` | longsword attachment on node `Sword` (454 / 226 / 80 / 25 triangles) |
| `export/mm7_m406_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export and editable master |
| `textures/`, `integration/actors.yml` | texture sets, region mask, `m406_ramps.json`, class maps; staged binding |

Install later (user decision):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m406_claude/export/mm7_m406.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m406_claude/export/mm7_m406_sword.glb --world mm7
```

then append `integration/actors.yml` (`Swordsman A/B/C`, scale 119.0 = `m406sa0` 184 px × dsft 1.1 = 202.4 units over
1.70 m; walk stride 1.715 m, run stride 1.8 m; impact 0.983 s; look 60°/35°; longsword on `Sword`). Speeds 220/250/280
are all below the run threshold (2.4 × 119 = 285.6): every tier walks, A at ~1.08x the clip.

## Model

- HD masters `references_hd/` (primary v2, four views, `longsword.png`); head turnaround `references_head/`.
- Smart Topology 15k (16,124 triangles, 16 parts, nothing removed): legs with plate and knee cops, torso with the
  tabard as one shell, head, spiked helmet, separate hands and arms, mail coif, eyes, buckle, knee-cop studs. Reduced
  after weighting to 10,294 (head and hands protected) — about 3 % over the ~10k guideline.
- Rig: source-frame rig; Meshy elbows and wrists (`ELBOW_FROM=meshy WRIST_FROM=meshy`: ring wrists 1.9 cm perimeter,
  line-fit elbows on the vambrace bulge); fingers by connectivity on the gauntlets with two m406 fixes in
  `fit_fingers.py`: the gauntlet's dorsal plate and a cuff flap split off as extra pieces, so the digits are the five
  long pieces and the thumb the one nearest the carried source thumb tip.
- Weights (`weights_fix.py`): skin = Meshy + shoulder fade + jaw free; the tabard flaps of the torso shell blend into
  the pelvis → thigh strip rule below the belt (left/right mix per vertex), no arm weight on the lower torso; helmet
  and eyes rigid head; coif copies the skin without arm/clavicle weight; buckle and studs rigid on the dominant bone.
- Longsword (`make_sword.py`): straight diamond blade, blue-gem guard, 1.3 cm grip, 1.05 m; roll 90°.

## Clips

As the other fighters: Standing Standard Idle; Walking Mixamo Walk (1.715 m; 1.4 cm floor lift); Running Standard Run
+ run fit; Attack Sword And Shield Slash (2) planted + 20 % legs, 0.3 s lead, blow 0.983 s; Hit set Unarmed get-hit
F1; Death Falling Back Death (travel halved); Fidget Sword And Shield Power Up planted. Left fingers keep 50 % of the
source curl. `arm_clear.py` (walk L ≤ 2°, attack L ≤ 6°, death R ≤ 24°), then `sword_clear.py` (death up to 75°).
Grip solve with the finger spread limited to ±25° (`SPREAD_MAX`; the mis-fitted middle finger spread −60° and tore
the web 8x) and 6 web smoothing passes.

## Gates (2026-10-20)

- G4 arm stretch p99 ≤ 1.97, max 2.82. G5 left ≤ 2.09x; **right 5.69x on one web edge between the index and middle
  fingers inside the fixed fist** (hidden by the fingers and the handle; above the ~4.5x guideline — deviation).
- G6: walk clean; attack ≤ 1.7 cm (rest-pose overlap of the gauntlet cuffs, constant 1.3–1.7 cm in every clip);
  **Death: the blade 5.7 cm into the body around frame 33 while lying** (the smoothed hand turn leaves a residual).
- Soles: −2.0…+1.6 cm. Blade (double-edged): attack 0.73, walk 0.92, fidget 0.68, hit 0.94.
- Viewer: 24/24 tier/clip switches, no console errors. In game: not checked (nothing installed).

## Textures and tiers

`compose_m406.py`: body/head 1K sets (Meshy UVs copied back exactly; head retexture on our head UVs: face, beard, coif,
helmet and the tabard top); skin (head and bare arms) repainted to one albedo shared by both sets; AO; ORM per class.
One recolour region **R = the tabard's coloured half and chevron ground**: the saturated blue entries of the manifest's
tabard indices 168–209 (the bluish-white half excluded; first pass made every ramp near-white). The native sprites are
drawn in palette 74 (tier B): A 70 green, B 74 blue, C 409 red.

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

Feet (review 2026-10-20, "slightly angled on the boot edge"): the project's `foot_level.py` also levels the sole's roll
about the heel–toe line on grounded frames (the clips had rolled the boots onto their outer edges; the rest pose is
flat) and moves the pelvis by the change of the lowest sole point, so floor contact is unchanged; the run gets
`Running:rollonly`. Soles and gates re-measured after the rebuild (`review/gates_final.txt`). Walk and run take one constant roll per foot in the foot's own frame and one constant pelvis shift (review 2026-10-20: the per-frame roll switched on and off as the feet landed and lifted, a visible ankle twitch; foot rotation per frame is back to the source's). Hit, Attack, Fidget, Death and Standing: the roll is weighted by flatness (planted and level lengthwise), capped at 20 deg and smoothed over the clip (batch C's rule, mm7_m218_claude; peer report 2026-10-20: the groundedness-only roll snapped a stepping foot in Hit up to 22 deg and a lifting foot in Death up to 65 deg per frame); every clip's foot turn per frame is now within 2 deg of the source's. Walk bob (review 2026-10-20, "uneven head bob"): `walk_bob.py` after `clip_timing.py` smooths the walk's pelvis height over the loop (both steps alike, ankles kept reachable) and re-solves the legs to the same ankle paths and foot rotations; the retarget's floor rule had left a zigzag and up to 3.7 cm frame jumps.

## Replay

`TOKEN=<lease> STAGE=rig WRIST_FROM=meshy ELBOW_FROM=meshy scripts/rebuild.sh`, then `STAGE=anim DEATH_UNTIL=12
R_HANDLE=0.013 LEAD=0.3 LEFT_CURL=0.5 SPREAD_MAX=25 SMOOTH_PASSES=6 DEATH_MAX_TURN=75 scripts/rebuild.sh` (twice on a
fresh project); `make_sword.py` (python3, then Blender); texture chain; `compose_m406.py`; `scripts/build_runtime.sh`;
`viewer_tiers.py`; `update_viewer_manifest.py`.

## Known limits / for user review

- Right fist: one stretched web edge; the thumb does not close over the handle.
- Death: the blade presses into the lying body for a few frames.
- LOD0 body 10,294 triangles (~3 % over the guideline). Gold knee cops read saturated yellow in the viewer.
