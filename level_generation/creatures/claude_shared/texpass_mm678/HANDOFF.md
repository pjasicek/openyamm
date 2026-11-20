# MM6–MM8 texture quality pass: handoff (2026-11-01)

The user wants the [texture quality pass](../TEXTURE_QUALITY_PASS.md) (the MM9 Magreeb recipe: new UVs from
`uv_atlas.py`, Meshy paint at 4K downsampled once, gentle grade, ramps kept) run over the worst-textured installed
MM6–MM8 monsters. Three were done as a trial on 2026-10-31. This file is the queue, the cost picture and what the trial
taught; read it, the recipe and the three trial READMEs before starting.

> **`uv_atlas.unwrap()` defaults changed on 2026-11-12** ([UV study](../../uv_research_20261111/REPORT.md),
> [recipe section 0](../TEXTURE_QUALITY_PASS.md#0-default-pipeline-since-2026-11-12-uv-study)): PartUV charts from a
> skin-weight tree, a seam pass and sparrow packing (about 70 % atlas instead of 48-60 %). Finished projects' scripts
> (`mm6_demon_texpass_claude/scripts`, `mm7_m258_texpass_claude/scripts`, rebuild projects' `uv_*.py`) call `unwrap()`
> and now get the new route. **To reproduce an old layout, call
> `unwrap(..., charts='xatlas', packer='xatlas', seam_rounds=0)`** (plus `weld=0, correct_aspect=True` on a mesh with
> split vertices or a non-square image on its material); do not edit those scripts. New passes use the defaults and
> need `claude_shared/partuv_venv` and `claude_shared/sparrow_venv` (setup in the recipe); without them `unwrap()`
> falls back to xatlas by itself and lists it in the report's `fallbacks`. Redo only models with atlas < 50 %,
> fragments > 5 % or stretch p90 > 1.5, worst first, and re-fill gutters last with `gutter_fill.py`.

## State

| Creature | Project (README section "Texture quality pass") | Atlas before -> after | Credits | State |
|---|---|---|---|---|
| Bone Dragon `mm8_m616` | `../../mm8_m616_claude/` | 7.2 -> 49.0 % | 10 | installed |
| Water Elemental `mm8_m500` + MM7 `mm7_m210` | `../../mm8_m500_claude/` (MM7 pointer in `mm7_m210_claude`) | 30.6 -> 53.4 % | 20 | installed, both worlds; eyes corrected 2026-11-01 (r4) |
| Troll Peasant `mm8_m480` + MM7 Troll `mm7_m461` | `../../mm8_m480_texpass_claude/` | 18.9 -> 56.4 % | 20 | installed 2026-11-01, both worlds |
| Peasant Elf Female `mm7_m322` (9 skins) | `../../mm7_m322_texpass_claude/` | 42.9 -> 58.0 % | 20 | installed 2026-11-01; face patches fixed (hair mask off lips/ears, one skin tone, seam levelling); close-up fixes r2 (mouth, strap, cleavage) and eyes r3 (one procedural disc per eyeball, 2.68x) |
| Mage `mm7_m274` (Sorcerer / Wizard / Archmage) | `../../mm7_m274_texpass_claude/` | 49.9 -> 59.6 % (2080x1024 -> 2048²) | 20 | installed 2026-11-01; scalp hair in the beard region (ginger / dark grey / white), one skin tone, seams healed; close-up fixes reinstalled 2026-11-01 (small lower lip, beard over the chin patch, procedural eyes in own 64-px patches); moustache geometry removed in every LOD (5-edge opening filled), flat painted moustache installed, bare-skin variant viewer only |
| Peasant Human2 Male `mm7_m362` (9 skins) | `../../mm7_m362_texpass_claude/` | 41.6 -> 60.5 % (2080x1024 -> 2048²) | 20 | installed 2026-11-01; cause: beard mask was a 0.7 box over chin and lips; now no beard on any skin (user), one skin tone on the mesh (neck seam dE 2.1), procedural eyes, mouth, nostrils; undershirt in the chest opening, leather tie bars |
| Peasant Human1 Female `mm7_m342` (9 skins) | `../../mm7_m342_texpass_claude/` | 26.8 -> 55.9 % (2080x1024 -> 2048²) | 20 | installed 2026-11-01; one skin tone (3D vertex field, seams blended), earring gold off the hair; r2 same day: procedural eyes on one disc chart each (x3.3), dark lid/lip/mouth shading, soft nostrils, white stockings, idle clips' skirt balloon removed (arms +6°, hand push off the robe chains) |
| Peasant Human2 Female `mm7_m372` (6 skins) | `../../mm7_m372_texpass_claude/` | 48.9 -> 53.0 % (2080x1024 -> 2048²) | 40 | installed 2026-11-01; second layout and paint so the face keeps its density (head front x3.5: 2,308 texels/m), one skin tone in 3D (neck split 232 -> 199 levelled to 190 -> 187, skin seams p95 36.9 -> 15.0), hood beads kept green, procedural eyes (x2.1, largest free square), ramps unchanged; face follow-up reinstalled same day: muted rose lips, smooth dark-rose slit (mouth opening filled), small nostril shadows, upper lid over the iris top, mesh: 16 cm spike fan removed and cheek hole filled (LOD0/LOD1); round 3 reinstalled same day: idle-clip robe bulge fixed as m342 (arms 6°, no hand push; skirt 0.443 -> 0.383 m at 0.85 m), eyeball lid parts shade like the lids (normal map), soft nose underside, one-gradient slit, matte lips |

**After every install, run `mm6_mm7_mm8_actor_models_build_every_binding`.** The Troll's first MM8 install lost a
cooked texture, most likely to another agent's concurrent full cook; reinstalling restored it.

**User review 2026-11-01:** Troll clearly better; Bone Dragon OK. Water Elemental: the 4K head paint had drawn thin,
off-centre slit pupils; r4 carries the approved eye paint over (installed both worlds, see its README "Eye correction").
For later creatures: compare eyes against the approved paint and the HD head views before install; a head paint can
move pupils even when the rest of the face reads well.

**MM7 batch, user review 2026-11-01:** the user asked for passes on the MM7 models from a player screenshot (Mage
`m274`, peasants `m322`, `m342`, `m362`, `m372`). After close-up review rounds the user accepted all five: Mage (moustache
geometry removed, flat painted moustache), Human2 Male (no beard on any skin, undershirt in the chest opening), Human1
Female (face, idle-clip skirt balloon), Elf Female (eyes r3), Human2 Female ("good enough" after round 3; eye-hole rims
and the jagged lip slit are mesh, not fixed). Leases released.

**Lessons from the MM7 batch** (apply to every later humanoid pass, before install):
- Review faces at close range (eyes, nose, mouth; front and 3/4) in every skin; the user does.
- Paint eyeballs procedurally in eye-local coordinates, one chart per eyeball, as dense as free space allows
  (`mm7_m342_texpass_claude` is the reference). Meshy paint on small eyeball triangles reads as shards.
- Paint the mouth interior and inward lip faces as one dark gradient; lips matte, never the eyes' glossy material.
- Check region masks on the face: beard/hair channels must not cover lips, chin or ears.
- Check idle clips for skirt or robe balloons from the cloth simulation pushing around hanging hands (m342, m372 fix:
  arms out 6°, no hand push on the skirt chains).
- Do not invent facial hair from sprite readings without asking (`m362` has none, per the user).

**Open (not requested):** Jog/Walk skirt stretch and knee poke-through on `m342` and `m372`; brows that ignore the hair
colour on `m342`/`m362`; the sibling peasants Human1 Male `m352` and Elf Male `m332` probably share the face issues.
Not done on any pass: an in-game run, the Android cook.

## Queue

`ranking_20261031.csv` here: `texture_quality.py` on every LOD0 base-colour set of every bound MM6–MM8 model
(227 sets on 185 models; LOD2/3 materials, effect sheets and tiny held items excluded by hand). Group rule, per model,
worst set: **A** = atlas < 25 %, or fragments >= 30 %, or equivalent < 600 px, or stretch p90 >= 4; **B** = atlas
< 35 % or fragments >= 20 %. The user agreed with doing A, then B; the rest (about 90, mostly humanoids at 40–65 %)
is not worth the review risk.

**Group A** (46 left, worst first): Fire Elemental `mm8_m496`, Dragonfly `mm7_m186`, Air Elemental `mm8_m508`,
Bat `mm7_m158`, Roc `mm7_m390`, Thunderbird `mm8_m552`, Merchant `mm6_mer1`, Lich `mm6_lch`, Thief `mm6_thf`,
Gorgon `mm8_m564`, LizardArch `mm6_lzd`, Crystal Dragon `mm8_m548`, Hydra `mm7_m266`, Phoenix `mm8_m572`,
Ogre Peasant `mm8_m436`, Drake `mm6_drg1`, Beholder `mm7_m166`, Cockatrice `mm6_ckt`, Ratman `mm8_ratman`,
Troll `mm8_m476`, Dragon `mm8_m492`, Wyvern `mm7_m434` = `mm8_m560` (one GLB layout), Triton `mm8_m576`,
Genie `mm6_djn`, Robot `mm7_m386`, Gargoyle `mm6_gar`, Dragon `mm7_m182`, Sea Serpent `mm6_seas`, Behemoth `mm7_m162`,
Skeleton `mm6_ske`, Demon Queen `mm6_qfi`, Wasp Warrior `mm8_m556`, Efreeti `mm8_m536`, DemonFly `mm6_wdm`,
Druidess `mm6_dru1`, Genie `mm7_m238`, BGoblin `mm6_gob2`, Lizardman Peasant `mm8_lizardman_peasant`,
Centaur `mm8_centaur`, Malevolent Boulder `mm8_m588`, zcat `mm7_7m500`, Ghost `mm7_m242`, Raven Man `mm8_m584`,
PeasantM4 `mm6_natm`, plus the two below that need a different fix.

**Not a retexture first:** Demon `mm6_demon` claws use a whole 2K texture at 3.2 % (repack or shrink; its body set at
33 % / 30 % fragments is a normal candidate). Nobleman `mm6_nobl` (stretch p90 8.25) and zReactor `mm6_rea`
(7.9): find out what is broken in their UVs before deciding.

**Group B** (36): PeasantF3 `mm6_mfp`, Medusa `mm6_med`, Manticore `mm7_m278`, Rat `mm7_m382`, peasant `mm7_m342`,
Eye `mm6_bh`, Ogre Mage `mm8_m540`, Crystal Walker `mm8_m596`, Necromancer `mm8_m472`, Elf Spearman `mm7_m218`,
Ether Knight `mm8_m604`, Juggernaut `mm8_m608`, Griffin `mm7_m258`, Ogre Warrior `mm8_m440`, Thunder Lizard
`mm8_m516`, Ghost `mm6_gst`, Dragon `mm6_cdr1`, Dire Wolf `mm8_wolf`, Treant `mm7_m479`, Couatl `mm8_m408`, PeasantM3
`mm6_mep`, Bedraggled `mm8_m620`, FighterChain `mm6_figc`, Cobra `mm6_cob`, peasant dwarf `mm7_m302`, Werewolf
`mm6_wwf`, Lich `mm7_m270`, Wyrm `mm6_wyrm`, Skeleton Archer `mm8_m628`, Minotaur `mm8_m484`, Serpentmen `mm8_m524`,
Hydra `mm6_hyd`, Goblin `mm7_m246`, PeasantF4 `mm6_natf`, Skeleton Warrior `mm7_m398`, Cleric Moon `mm7_m170`.

Shared layouts across worlds: check each MM7 project's README for a `build_glb.py` that builds it from an MM8 GLB
(the Troll and Water Elemental did); then do the MM8 source and rebuild the MM7 copy with its own palettes.
Do not start a model another agent is reworking (check `output/creature_3d_locks/` and recent READMEs).

## Cost

Meshy balance on 2026-11-01 (`tools/creature_meshy.py balance`): primary 2, **backup 3,860** (monthly credits,
reset 2026-11-30; they do not carry over). One 4K retexture is 10 credits; a creature with a face gets a second
head-only paint (Troll, Water Elemental: 20). Estimate: group A about 700–1,000, group B about 500–750, so about
1,200–1,750 for both. The Hesper decorations workspace has a 1,000-credit claim on the same budget. The user said
credits are not the constraint; report the count per creature anyway. Time is: 40–60 minutes of agent wall time per
creature, three agents in parallel worked without conflicts.

## What the trial settled

- **Start from the installed GLB** (`assets_source/worlds/<w>/models/`), never an old project export: installed files
  carry reductions, far-LOD repairs, head-bob reshaping and the 2026-10-31 gait clips (Walk2/Jog/Run/Sprint). Change
  only UVs, images and region ramps. Diff nodes, skin, inverse binds, every clip sampler, materials, variants, LOD lists
  and per-corner position/normal/joint/weight before install (`mm8_m480_texpass_claude/scripts/glb_diff.py`,
  `mm8_m500_claude/scripts/texpass_diff.py`).
- **A separate `<model>_texpass_claude` project with its own lease** (the Troll's route) keeps production projects free
  for other agents; editing in the production project (Bone Dragon, Water Elemental) also worked when nobody else
  held it. The Troll's `scripts/` is the most reusable set: `dump_lod0.py`, `uv_texpass.py`, `resample_approved.py`,
  `bake_ao.py`, `compose.py`, `apply_layout.py`, `glb_diff.py`, `lod1_check.py`, `tier_tone.py`,
  `merge_install.sh`, viewer and sheet scripts.
- **LODs:** LOD1 gets UVs projected per chart from the new LOD0 (check colour against LOD0 at the same surface points).
  LOD2/3: superseded 2026-11-12 by the [LOD playbook](../../LOD_PLAYBOOK.md) §7. The refill below (`apply.py` ->
  `transfer()` without `param_uv`) is the nearest-point mode, and `repair.py` must run on the installed GLB, not on
  `originals/`. Old rule: LOD2/3 keep their repaired geometry and UVs; refill only their maps with
  `../../lod_repair_claude/scripts/transfer_textures.py` at the installed 512/256 px.
- **One 2048 atlas, head denser (`head_factor` 1.8), plus a head-only 4K retexture** from the close head views on the
  same UVs, crossfaded into the body paint at the neck. That beat a separate 1K head set on face detail and needs no new
  materials or bindings. Do not edit `actors.yml`; keep material and variant names.
- **Atlas 55 % is often out of reach** on thin or spiky bodies (Bone Dragon 49 % after five layouts, Water Elemental
  53.4 % after three packers). Try the fast packer sweep before brute force; accept about 48–55 % with fragments
  under about 5 %. (Old route; the 2026-11-12 defaults reached 70-75 % on the UV study subjects, none of them thin or spiky.)
- **Drift seen and fixed:** the 4K paint invented a black crackle network on the Bone Dragon's bone (filled from the
  surrounding bone, then brightness and contrast pinned to the approved paint at the same surface points); membranes
  came back bluish (corrected); the Water Elemental's regions came back with more contrast (a per-region contrast
  factor fitted into the ramps: scales 0.825, ventral 0.942, fins 0.726). Holding every region to the approved mask
  turned new white edge paint cyan; hold only the regions that need it.
- Older projects may lack the review viewer's `index.html`/`review.js`: copy them from
  `mm8_m480_texpass_claude/review/viewer/` (or the Magreeb project) and set the creature's camera presets.
- Per creature, report: `texture_quality.py` before/after, credits, sheet paths (identical cameras, every tier, both
  worlds for shared layouts), winding, flat shading, detached parts, floor audit, the creature's and the
  `mm6_mm7_mm8_actor_models_build_every_binding` regressions, viewer `check`, and what drifted. Back up the before
  state in `work/before_texpass/` and add a dated README section.

## Re-measuring

```sh
ls assets_source/worlds/mm{6,7,8}/models/*.glb | xargs -P 16 -I{} sh -c \
  'python3 level_generation/creatures/claude_shared/texture_quality.py {} --json <out>/$(basename {} .glb).json'
```

Ignore LOD2/3 materials (`_LOD2`, `_LOD3`), effect sheets (fringes, wind, bursts, wisp, fish school, ooze) and held
items; take descriptor names from each world's `models/actors.yml`.

## Generic toolkit (texpass-2, 2026-11-11)

The audit-fix texpass stream used a config-driven copy of the Troll scripts. Copy `scripts/` from the latest
texpass-2 project (`../../mm7_m258_texpass_claude/scripts/`) and write a `texpass.json`; the
[Dragonfly README](../../mm7_m186_texpass_claude/README.md) explains the route.
- `new_project.sh <world> <stem>` claims the lease, backs up the GLB and `actors.yml` entries, and adds the ledger
  row.
- The pass runs `dump.py` → `uv.py` (Blender) → `resample.py` → `bake_ao.py` (Blender) → `compose.py` → `apply.py`
  → `viewer.py` → `shots.py` → `finish.sh --install`.

Options added on the way, with the README that explains each:

| Option | What it does | README |
|---|---|---|
| `merge_sets` | merges several image sets into one atlas | Hydra m266, DemonFly wdm |
| `layout_prims` | lays out only some primitives | ADragon m182 head |
| `head_uv_split` | head from a 2080×1024 body \| head atlas | Ogre m436 |
| `head_parts` | head from a grafted head primitive | DemonFly wdm |
| `keep_approved_regions`, `keep_approved_grow` | keeps the approved colour on mask regions (eyes and pupils) | Gorgon m564, ADragon |
| `keep_approved_near` | keeps the approved colour near bind-pose points, for eyeballs without a region | Genie m238, Ogre Mage m540 |
| `head_sigma`, `head_detail` | gentler faces | Genie, Manticore m278 |
| `detail_limit` | damps patches the paint invents | Bat m158 nose |
| `normal_carry.py` | moves the approved normal map per chart | ADragon, Genie |

`claude_shared/uv_atlas.py` now reverts charts that SLIM collapsed to a point (Bat m158). The lesson that recurs: on
smooth-skinned or patterned faces and hides, a fresh 4K paint can bring its own pattern (scales, crackle). Read the
face and hide close-ups and pull the compose towards the approved paint when the look changes.
