# Solo-mode Dragon: first-person forelegs (2026-11-13/14)

The Dragon's view model for the solo action mode ([devdocs/solo_action/DRAGON.md](../../devdocs/solo_action/DRAGON.md)):
two clawed forelegs of our own (Codex masters, a Meshy mesh), rigged and animated here in Blender, exported in the
node and clip contract of `game/render/FirstPersonViewModel`. Installed on 2026-11-14 as
`assets_dev/engine/view_model/dragon_forelegs.glb` (with its text keys), which a dragon in a solo run draws
([DRAGON.md](../../devdocs/solo_action/DRAGON.md) "Built in the engine").

## Pipeline

1. **Masters (step 0).** `references_hd/`: Codex HD masters of one right foreleg (shoulder cut to talons; four digits,
   wrist spur, charcoal scales with red seams, gold scute strip, ivory talons) from the MM8 Dragon's native views
   (`references/native_views.png`) and its accepted whole-body masters (`mm8_m492_claude/references_hd`).
   `CODEX_BRIEF.md`, `generation_runs.json`, `selected_views_review.png`. The side views 03/04 are imperfect (Codex
   stopped at its correction limit); the retexture uses front, left, back and the three-quarter primary.
2. **Mesh.** Meshy Smart Topology from `00_three_quarter.png` (`requests/smart_topology_v1.json`): 6,664 triangles,
   `meshy/smart_topology_v1/`.
3. **UVs.** `scripts/prep_upload.py` (the shared `uv_atlas.py`, TEXTURE_QUALITY_PASS) into
   `texturing/foreleg_upload_*.glb`; reports beside them. Deviation: the selected layout (`v2a`, PartUV threshold
   1.08) uses 58 % of the atlas, below the 65 % minimum. A threshold of 1.0 reached 73.8 %, but in 500 charts with
   twice the visible seam length, which a view model seen up close shows more than 13 % more texel density; the
   default threshold gave 40.5 % (6 charts), xatlas 50.1 %.
4. **Texture.** Meshy retexture at 4K with the original UVs from the masters (`requests/retexture_v1.json`: front,
   left, back and the three-quarter primary), then `scripts/texture_pass.py` (one downsample to 2K for colour, normal
   and ORM, the nearest-texel gutter fill last, a textured foreleg GLB in `texturing/foreleg_textured.glb`).
5. **Rig and clips.** `scripts/build_forelegs.py` finds the landmarks in the mesh (shoulder cut, elbow, wrist and
   knuckle slices, the three forward talons by k-means), builds one armature with both legs (the left mirrored),
   weights by distance to the bone segments (digits only near their own column), keys every clip with IK targets and
   bakes them. Exports `dragon_forelegs.glb` (clips `claws<action>`) and `dragon_forelegs_h2h.glb` (the same motion
   under `handtohand<action>` and `casttarget`, for the arms' unarmed kit), each with its `.textkeys.json`. With
   `--install <dir>` it copies `dragon_forelegs.glb` and its text keys there; the engine's copy is made with
   `blender -b --python scripts/build_forelegs.py -- --mesh texturing/foreleg_textured.glb --out export --install
   ../../assets_dev/engine/view_model` (from this folder; the rebuild is byte-identical to the export).
6. **Check.** `scripts/render_claws.py` renders the exported GLB from its Camera01 at the view model's 60° vertical
   field of view; `scripts/compose_claws.py` mirrors each frame (the engine mirrors X) and composites it over the HUD
   study's New Sorpigal scene (`renders/forelegs_*`).

**Skin fix (2026-11-14).** In the game the outer digit of each leg ended at idle in a flat cut with streaked texture.
The cause was the weights, not the mesh (it is closed: the open-edge check finds no open edge) nor the near plane: a
hard switch at the knuckle plane gave the side digits, far from the hand bone, only their digit bones below it, and
the hand above it a 28 % share of the forearm; the idle's curl stretched edges there 20 times (0.5 units to 10). The
weights now go by zone with smooth bands across the wrist (`WRIST_BAND`, 26 % of the leg) and the knuckles
(`KNUCKLE_BAND`, 10 %). The build gates every baked clip (`mesh_gates`, every other frame): no on-screen edge grown by
more than 0.75 units and 1.6 times its rest length, and no open edge in the eye's view; a failure stops the export.
Now the largest on-screen growth is 0.5 units, nothing over the limit. Checked in the game, every clip held:
`tours/claws_legs_oute3.yml` and `claws_legs_6d05.yml` into `renders/engine/legs_oute3/` and `legs_6d05/`.

## Node and clip contract

- Nodes: `Camera01` (the eye; animated for the bite lunge and the breath kick), `Weapon` (required by the loader; an
  empty under the right hand), `ClawTipR`/`ClawTipL` (talon tips for the slash direction), `Mouth` (the breath's start,
  10 forward and 16 below the eye).
- Space: the private Oblivion arms' as Blender imports them, including their `ZupToYup` root: up +Z, the eye looking
  along **+Y**, screen right +X. The arms' bind pose looks like -Y forward; that is the rest pose, not the eye's
  direction. The first build used -Y and drew nothing in game: everything sat behind the eye.
- Timing: keys start at frame 0, so a clip's times start at 0. Import a GLB into Blender at 30 fps before checking it;
  the default 24 fps skews every frame.
- Clips (30 fps), text keys in Oblivion's format:

| Clip | Length | Keys | Motion |
|---|---|---|---|
| `clawsidle` | 3.0 s | — | both forelegs low in the lower corners, talons forward, breathing |
| `claws{forward,backward,left,right}` | 1.0 s | — | walk bob, legs alternating |
| `clawsfast…` | 0.7 s | — | run bob |
| `clawsattackright` | 0.667 s | Hit 0.20, a:L 0.433 | right foreleg winds up top right, rakes diagonally across the centre, follows through low left |
| `clawsattackleft` | 0.667 s | Hit 0.20, a:R 0.433 | mirrored |
| `clawsequip` | 0.8 s | — | forelegs rise into view |
| `clawsblockidle` | 1.3 s | — | Scales guard: forelegs crossed before the face, talons up |
| `clawsblockhit` | 0.3 s | — | the guard jolts back |
| `clawsbreath` | 0.9 s | Hit 0.40 | forelegs drop out of view (inhale, the eye rises), release at Hit with a forward kick, return |
| `clawsbite` | 0.6 s | Hit 0.25 | forelegs part to the edges, the eye lunges forward and down |

The attack timings are Oblivion's hand-to-hand numbers (Hit 0.20, chain 0.433, length 0.667); no Oblivion data is used.

## Paid jobs (Meshy, budget 200 of the night's 300)

| Job | Task id | Credits | Purpose |
|---|---|---|---|
| smart_topology_v1 | 01a1d720-2766-7763-82e2-1489d2e9a9a9 | 5 | foreleg mesh from `00_three_quarter.png` |
| retexture_v1 | 01a1d740-72bf-7109-8f02-eaded5ad85a6 | 10 | 4K paint on the v2a UVs from the masters |

Total: 15 credits.

## Checks

- Blender, true time from Camera01: `renders/forelegs_v4_sheet.jpg` (idle, the right swipe at 0.06/0.10/0.15/0.20
  (Hit)/0.30, the left swipe at its Hit, the guard, the breath's inhale, the bite).
- In game, on a MAW solo run with the unarmed kit (before the install): `renders/ingame/` and `renders/ingame_sheet.jpg`.
- In the engine (installed, the `claws` set; 2026-11-14): `tours/claws_engine_oute3.yml`, `claws_engine_6d05.yml`,
  `claws_engine_live_slow.yml`, `claws_engine_breath_slow.yml` into `renders/engine/`; overview
  `renders/engine_sheet.jpg`. A MAW solo dragon: `testparty apply early solo_dragon` in the debug console. The tour
  `tours/claws_ingame.yml` holds poses and two live swipes that kill a goblin. Its header has the command; desktop runs
  use the normal launcher, or the headless monitor with `WAYLAND_DISPLAY=oyheadless SDL_VIDEODRIVER=wayland DISPLAY=`
  and `--visible`.

## Open

- The wind-up shows the palm, talons up, at the top right. A wrist turned outward would read more like a claw drawn
  back.
- The gold scute strip on the upper arm is wide (Codex's master); it shows at the lower edge in swipes and the guard.
- There is no jaw mesh for the bite: only the eye lunges.
- One tint: the player dragon's colour ramps (region mask + ramps per CLAUDE_CREATURE_TEXTURES) are not made.
- The engine changes in DRAGON.md are made (2026-11-14); a jaw piece and the colour ramps remain.
