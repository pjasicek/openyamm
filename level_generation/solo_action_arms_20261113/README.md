# First-person arms: better textures, race skins and our own arms (2026-11-13/14)

The solo mode's first-person arms are Oblivion's hand and forearm meshes, a private stand-in
(reference/oblivion_poc/, never shipped). This project checks two routes to better arms and builds a skin for every
playable race. Everything Oblivion-derived stays under `reference/oblivion_poc/` (git-ignored); this folder holds only
our own scripts, notes and Meshy receipts.

## Measured problem

`texture_quality.py` on the Oblivion arms (`arms_full.glb`):

| Texture | Size | Atlas use | Equivalent | Density p50 (texels per arm size) | Spread |
|---|---|---|---|---|---|
| Hands (both share one mirrored set) | 512 x 256 | 80 % | 458 px | 2,246 | 2.02 |
| Forearms (a corner of the body texture) | 512 x 256 | 24 % | 253 px | 561 | 1.85 |

The forearms, which fill the lower screen in every pose, have a quarter of the hands' density. That is the blur.

## Route A: Oblivion's arm mesh, new UVs, 4K paint (private)

Scripts in `reference/oblivion_poc/hd/scripts/`:

1. `unwrap_arms.py` (Blender): joins hands and forearms in their bind pose and unwraps them as one atlas with
   `claude_shared/uv_atlas.py` (PartUV charts, sparrow packing, hands 1.4x denser). Result: 24 charts, about 82 %
   of a 4096 square used, density spread 1.14, stretch p90 1.11, no fragments.
2. `rebuild_arms.py`: writes the new UVs into the animated GLB without Blender (per triangle corner, vertices split
   at the new seams, every other attribute copied), so skeleton, weights and the 147 clips stay byte-identical. The
   face order is checked against Blender's (edge-length ratio spread 1.00007).
3. Meshy retexture of the joined mesh on our UVs (`enable_original_uv: true`, 4K, text prompt): 10 credits a paint.
4. `gutter_fill.py`, then `skin_detail.py`: a tiled procedural pore and grain normal detail (whiteout blend), with
   the albedo 7 % darker in the pores. One density everywhere lets one tile size work on hands and forearms.
5. `race_ramp.py`: race skins from one paint by three-stop colour ramps read off the MM8 portraits and paperdoll
   hands (CLAUDE_CREATURE_TEXTURES.md's one-paint-plus-ramps rule), keeping 20 % of the paint's own colour so nails
   and veins stay readable.
6. `build_races.sh` writes `reference/oblivion_poc/glb/arms_hd_<race>.glb` (+ text keys) for human, elf, dwarf,
   vampire, dark elf, goblin, undead (ramps of the human paint) and troll, minotaur, zombie (their own paints, then
   ramped onto the MM8 palette).

Density after: one 4K set for all four parts; hand density about 5x and forearm about 15x the original (linear).
Meshy's 4K paint is soft (even tone, knuckle colour, nails; no pores), so the fine detail is the normal map's.

In the game (`preview/arms_hd/ingame_zoom_original_vs_human.jpg`) the HD human shows knuckle wrinkles, pores and veins
where the original is smooth plastic; the silhouette is Oblivion's low-poly mesh either way. Blender's studio render
shows albedo only, so it understates the gain (no normal maps).

The ramps first used the paint's full luminance stretch, which turned faint painted creases into dark marks on the
fingers; they now keep 60 % of that contrast (`CONTRAST` in race_ramp.py), and the human paint goes through a mild
human ramp too.

## Route B: our own creature arms on the first-person skeleton (shippable path)

Our humanoid creature rigs use biped names (`B_L_Forearm`, `B_L_Finger01` ...), one to one with the first-person
skeleton's (`Bip01 L Forearm` ...). `scripts/graft_arms.py` cuts a model's forearms and hands, carries each joint's
geometry from our bind frame to the first-person joint's (frames from the bone direction and the hand's index-to-little
line, one global scale from the forearm length) and binds it to the first-person skin, so the existing clips drive it.
No paint or rig work is needed for a first look; every race with one of our models gets its own shapes (the lich's bone
hands, the minotaur's dark fists, the goblin's green ones).

Tried on 12 models (`reference/oblivion_poc/preview/arms_own/`): mm6 monk, barbarian, native, minotaur, goblin,
dwarf, lich, knight; mm7 minotaur headsman; mm8 initiate monk, dwarf, lich, vampire. All follow the clips; fists close.
Gaps at first-person distance: 450-3,600 triangles for both arms (Oblivion: 3,460), so fingers read faceted; the hands
get a small share of a whole-body 2K atlas; sleeves, bracers and straps partly survive the cut.

`scripts/smooth_unwrap.py` (Blender) is the fix recipe: one Catmull-Clark level (weights interpolated), new even UVs
(uv_atlas), then the same Meshy 4K paint and detail pass as route A, then `graft_arms.py` again to re-bind by name
(`--uv-from` copies an earlier unwrap when only positions changed, so a paid paint stays valid).

Lessons from the prototype (mm8 vampire, `reference/oblivion_poc/glb/arms_own_human.glb`):
- Oblivion's `ForearmTwist` sits at the elbow, ours 60 % down the forearm: twist-weighted geometry must ride the
  forearm's mapping or the forearm is pulled to the elbow (fixed in graft_arms.py).
- First-person arms run on past the elbow towards the eye; ours stop at the elbow. `--upper` keeps the upper arm,
  carried rigidly with the forearm and bound to it.
- Ours are slimmer than Oblivion's: `--girth 1.25` thickens forearm and upper arm across their axis.
- One subdivision level takes the vampire's arms from 2,387 to 15,066 triangles; fingers stop reading faceted.
- In the game (`preview/arms_own/ingame_three_routes.jpg`, `fists_zoom_A_vs_B.jpg`) the grafted arms follow every
  clip but the fist does not close: our NPC fingers are shorter and rolled differently from Oblivion's finger bones,
  so a per-joint frame mapping leaves the palm half open; the cut also leaves seams on the forearm and the hands read
  small. Grafting third-person arms is a rig and clip proof and a quick race preview, not the shippable arm.

## Recommendation

1. **Now (private prototype):** use route A's `arms_hd_<race>.glb`. It is a clear gain in the game (knuckle
   wrinkles, pores, veins; every race distinct) at 40 credits for all ten races, and it keeps Oblivion's
   well-fitted hands and clips. Needs the small engine hook below to pick the race.
2. **For shipping:** a dedicated first-person arm pair of our own, modelled in the first-person skeleton's bind pose
   (fingers on the finger bones, forearm running past the elbow), not a graft. Route: HD master images of the arms
   in that pose (Codex), Meshy model with Smart Topology (about 5-30 credits), weights from the first-person
   skeleton (the humanoid playbook's arm and hand gate, finger weights by connectivity as in mm6_gob2_claude), then
   this project's UV, 4K paint and detail pass (10 credits a race paint, or one paint plus ramps). Oblivion's clips
   keep driving it through the shared bone names until we make our own clips.
3. **Race shapes** a texture cannot give (troll and vampire claws, the minotaur's thick hands, the lich's bones)
   come from that arm with per-race variants, or from our creature models' hands grafted onto it once its bind pose
   is ours.

## Race skins

| Race | Source | Note |
|---|---|---|
| Human | Meshy paint (human prompt) | |
| Elf, Dwarf, Vampire, Dark Elf, Goblin, Undead | ramps of the human paint | colour only |
| Troll | Meshy paint (warty grey-green), ramped | no claws: needs a shape change |
| Minotaur | Meshy paint (fur), ramped | fur is painted on human hands: thick fingers and hoof-like nails need a mesh |
| Zombie | Meshy paint (rot), ramped | |
| Dragon | n/a | the dragon fork's forelegs |

What a texture cannot do: claws (troll, vampire, goblin), the minotaur's thick hands, the undead's bones (route B's
lich graft has them), dwarf and minotaur proportions. Those come from route B's per-race meshes.

## Engine hook (not built)

The arms are one GLB per `[debug] view_model_path`. For race skins the presentation needs: pick
`<stem>_<race>.glb` beside the configured path when it exists (race id from the active member, names: human, vampire,
darkelf, minotaur, troll, undead, elf, goblin, dwarf, zombie), falling back to the configured file. One branch in
`GameApplication::renderFirstPersonViewModel` before `ensureLoaded`; `FirstPersonViewModel` already reloads on a
path change.

## Credits

| Job | Project | Credits |
|---|---|---|
| arms_human_v1 (retexture 4K) | reference/oblivion_poc/hd | 10 |
| arms_troll_v1 | reference/oblivion_poc/hd | 10 |
| arms_minotaur_v1 | reference/oblivion_poc/hd | 10 |
| arms_zombie_v1 | reference/oblivion_poc/hd | 10 |
| own_human_v1 (route B, before the twist fix) | level_generation/solo_action_arms_20261113 | 10 |
| own_human_v2 (route B, upper arm and girth) | level_generation/solo_action_arms_20261113 | 10 |

Total 60 of the 100 allowed (workspaces released).

## Captures and how to redo them

- Blender (studio light, from Camera01 at the engine's 60 degrees): `reference/oblivion_poc/hd/scripts/arms_render.py`;
  sheets in `reference/oblivion_poc/preview/arms_hd/` (`sheet_human_v1.jpg`, `races_blender_sheet.jpg`) and
  `preview/arms_own/` (`candidates_sheet.jpg`, `own_sheet.jpg`, `routeA_vs_B.jpg`).
- In the game (`viewmodel pose` at the mockup scene, solo run): `reference/oblivion_poc/hd/scripts/race_tour.sh <glb>
  <out>` for one GLB, `capture_all.sh` for every race; results and `races_ingame_sheet.jpg` in
  `preview/arms_hd/ingame/`. They need a display (the virtual one: `WAYLAND_DISPLAY=oyheadless`, the default of
  `ARMS_WAYLAND`) and `--ruleset mmerge:solo`: the arms are drawn only in a solo run.
