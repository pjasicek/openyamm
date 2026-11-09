# MM7 3D batch M: reuse MM8 models with MM7 colours

Ten MM7 creatures drawn from the same 3D renders as MM8 creatures that already have installed models. They need no
new model: each gets an MM7 copy of the MM8 model with MM7 colour tiers. One Claude session does all ten, one after
another, with no Meshy spending (0 credits). Other sessions work on the other batches at the same time; each touches
only its own projects. The full batch list is in [README.md](README.md).

## The ten creatures

| # | Creature | MM7 native project | MM8 source model | Your project | MM7 monster ids | Expected match | Status |
|---|---|---|---|---|---|---|---|
| 1 | Air Elemental | `mm7_m508` | `mm8_m508.glb` | `mm7_m508_claude` | 232 Tempest, 233 Cyclone, 234 Air Elemental | same art (checked) | installed 2026-10-21 (binds `mm8_m508.glb`) |
| 2 | Fire Elemental | `mm7_m202` | `mm8_m496.glb` | `mm7_m202_claude` | 238 Warden of Fire, 239 Guardian of Flame, 240 Fire Elemental | same art (checked) | installed 2026-10-21 (binds `mm8_m496.glb`) |
| 3 | Water Elemental | `mm7_m210` | `mm8_m500.glb` | `mm7_m210_claude` | 244 Sprite, 245 Sylph, 246 Water Elemental | same art; tier C uses palette 503 (checked) | installed 2026-10-21 (`mm7_m210.glb`) |
| 4 | Light Elemental | `mm7_m206` | `mm8_m528.glb` (Will o' Wisp) | `mm7_m206_claude` | 241 Lesser, 242, 243 Greater Light Elemental | same art (checked) | installed 2026-10-21 (binds `mm8_m528.glb`) |
| 5 | Troll | `mm7_m461` | `mm8_m480.glb` (Troll peasant) + `mm8_m480_club.glb` | `mm7_m461_claude` | 448 Swamp Troll, 449 River Troll, 450 Mountain Troll | same render at 1/1.515 raster, other colours (checked) | installed 2026-10-21 (`mm7_m461.glb` + `mm7_m461_club.glb`) |
| 6 | Ultra Dragon | `mm7_7m480` | `mm8_m492.glb` | `mm7_7m480_claude` | 460, 461, 462 Mega-Dragon | same art (checked) | installed 2026-10-21 (binds `mm8_m492.glb`) |
| 7 | Dragon | `mm7_m182` | `mm8_m492.glb` | `mm7_m182_claude` | 223 Green Dragon, 224 Blue Dragon, 225 Red Dragon | different render (checked): new model | installed 2026-10-21 (`mm7_m182.glb` v3b: MM6 cdr1 body/rig/clips + MM7 head, 75 credits; see mm7_m182_claude/README.md) |
| 8 | Gog | `mm7_m250` | `mm8_m612.glb` | `mm7_m250_claude` | 274 Gogling, 275 Gog, 276 Magog | same art, same palettes (checked) | installed 2026-10-21 (binds `mm8_m612.glb`) |
| 9 | Wyvern | `mm7_m434` | `mm8_m560.glb` | `mm7_m434_claude` | 424 Wyvern, 425 Horned Wyvern, 426 Ancient Wyvern | same body, other colours (checked) | installed 2026-10-21 (`mm7_m434.glb`) |
| 10 | Minotaur | `mm7_m286` | `mm8_m484.glb` + `mm8_m484_axe.glb` | `mm7_m286_claude` | 301 Minotaur, 302 Minotaur Headsman, 303 Minotaur Lord | different render (checked): new model | installed 2026-10-21 (`mm7_m286.glb` + `mm7_m286_axe.glb`, v2c reduced: body 8,481, axe 772 tris; 60 credits; see mm7_m286_claude/README.md) |

Native projects live under `level_generation/creatures/`, MM8 source models under
`assets_source/worlds/mm8/models/`; read from both, do not change them. "Expected match" comes from a visual
comparison only: the identity check below decides. Dragon and Ultra Dragon both use the MM8 Dragon body; give each
its own export and tiers.

Keep the **Status** column of this table up to date (`not started`, `in progress: <stage>`, `exported`, `blocked:
<reason>`). It is the resume point for this batch if the session is restarted.

## Method

Follow the worked example `level_generation/creatures/mm7_m390_claude/` (MM7 Roc on the MM8 Thunderbird body; read
its README first). Copy its scripts into your project and adapt them; do not edit that project. For each creature:

1. **Identity check.** Compare the MM7 native frames with the MM8 source family's bitmaps (`data/Data/sprites.lod/`,
   like `scripts/identity_check.py`): matching frame names, alpha overlap, palettes and frame scale per tier. Record
   the result in `review/identity_check.json` and the README.
2. **Decide.** If the shapes match (same art, or the same render in other colours), reuse the MM8 model. If they do
   not, stop for that creature: mark it `blocked: not the same body`, describe the difference under **Open issues**
   and go on to the next one. Do not start a new Meshy model in this batch.
3. **MM7 colours.** Build the three MM7 tiers as colour variants of the MM8 model: the MM8 region mask plus per-tier
   ramps fitted to the MM7 standing frames (like `scripts/tier_ramps.py`), following
   `level_generation/creatures/CLAUDE_CREATURE_TEXTURES.md`. Change only the glTF JSON (variants, materials, ramps):
   geometry, skin, clips, LODs and images stay byte-identical to the installed MM8 source in
   `assets_source/worlds/mm8/models/`. If the MM8 region mask cannot carry the MM7 colours (a region MM7 colours
   differently), add a mask channel in your project and say so in the README.
4. **Export** `export/mm7_<stem>.glb` (and the attachment GLB, renamed, where the source has one). Check it in the
   project viewer (all three tiers, every clip) and run `level_generation/decorations/mm8_3d/animated/scripts/check_winding.py`.
5. **Size.** Compare the MM7 descriptor heights and frame scales with the MM8 ones and note where the clips could
   leave the MM7 collision box (as the Roc README does).
6. **README.** Decision, identity numbers, ramps and fit error, checks, and the install command and `actors.yml`
   binding for later, plus the alternative of adding the MM7 variants to the shared MM8 model (that changes an
   installed MM8 asset, so it is the user's call).

## Do not install: keep everything in the projects

**Installed 2026-10-21 at the user's request** ("ok good install"): the seven MM7 GLBs (Water, Troll + club,
Wyvern, Dragon, Minotaur + axe) with `tools/install_model.py --world mm7`, and the 30 bindings from each project's
`review/actors_binding.yml` appended to `assets_dev/worlds/mm7/models/actors.yml` (Air, Fire, Light, Ultra Dragon and
Gog bind the installed MM8 GLBs). The rules below applied while the batch was in production.

The user will decide later when these go into the game. Until then:

- Do not run `tools/install_model.py`, and do not write anything under `assets_dev/` or `assets_source/`.
- Do not edit `actors.yml`, model manifests, monster tables or any other runtime binding or table.
- Do not change shared tools, playbooks or skills, or another project (including the installed MM8 models and their
  projects). If one needs a fix, note it under **Open issues** below.
- Each model stops at accepted project exports in the project's export folder. The project README lists the exact
  `tools/install_model.py ...` command(s) and the `actors.yml` binding you would add, ready to apply later.
- Check visually with `python3 tools/run_creature_review.py --project level_generation/creatures/<project>` (the
  project viewer), including the playbook's gates on every clip.
- An in-game check is optional and only in a private asset root under `output/`, launched with
  `./tools/run_game.sh --isolated <name> --world mm7 ... --assets <that root>`. If that root uses hard links, delete
  the link and write a new file before changing anything, so the real `assets_dev/` is never modified. Note in the
  project README how it was checked.

## When the batch is done

Report per model: export paths, gate results, Meshy spend, and anything left for the user to review. Collect
problems that need the user's decision here:

## Open issues

Batch result (2026-10-20): eight exported with 0 Meshy credits; Dragon and Minotaur were blocked as different bodies
and are now in new-model production. Exports equal the installed MM8 GLBs except in
glTF JSON (binary chunks asserted identical); each project README has the identity numbers, ramps, checks, size notes,
the install command and a ready `review/actors_binding.yml`.

1. **Dragon (`mm7_m182_claude`): not the same body; new model in production (user, 2026-10-20).** The MM7 Dragon is its own render (best-match alpha IoU
   0.50 against every MM8 `m492` frame, 0.54 height-normalised; same-render families here score 0.95–1.0): slimmer body,
   long thin tail, small crest instead of the horn crown, other wings, yellow belly plate. The user chose a new model (Meshy, 100-credit budget) in this
   project; the batch's no-install rule still applies.
2. **Minotaur (`mm7_m286_claude`): not the same body; new model in production (user, 2026-10-20).** Other outfit (fur loincloth and wrist bands, no harness
   or chainmail), other double axe and other poses (IoU 0.52 against `m484`, 0.47 against the MM8 Minotaur Peasant
   `m488`). New model as for the Dragon.
3. **Expected match corrections (done).** The Expected match column now carries the identity result. Gog is "same art,
   same palettes" (613/614/615 are the files MM8 uses); the Troll is the MM8 Troll Peasant render re-rasterised at
   1/1.515 and drawn at frame scale 2.5, so its model scale is 192.77, not a frame-scale ratio to an MM8 descriptor.
4. **Reuse instead of copies (decided 2026-10-20).** Air, Fire, Light, Ultra Dragon and Gog bind the installed MM8 GLBs
   directly (`mm8_m508/m496/m528/m492/m612.glb`; Ultra Dragon `skin: m492`, Gog `gog_a/b/c`): the game merges every
   mounted world's `actors.yml` and resolves `worlds/mm8/models/` from any world, so about 51 MB of copies are not
   installed and no MM8 asset changes. Their `review/actors_binding.yml` files say so; the exports stay as fallbacks.
   Water, Troll and Wyvern install their own GLBs (adding variants to the MM8 models would change installed assets).
5. **MM7 data quirks seen while sizing (recorded, no change).** MM7 collision heights are far below the drawn size for
   the Gog (47/48/95 for a 143–285 unit body), the Air Elemental (85) and the unused Ultra Dragon (190 for a ~900 unit
   dragon); the MM7 sprites have the same mismatch, so the tables are left alone. The Ultra Dragon's frame groups
   `7m499*` are missing from the sprite frame tables, so its binding uses explicit scales. The Light Elemental's
   `mm8:fx/wisp_stars` resolves in every world (`engine/effects/library.yml` includes it); nothing to copy.
6. **Viewer tooling (recorded, no change).** The Roc viewer template (`mm7_m390_claude/review/viewer/review.js`) has
   camera focuses fixed to the Roc's size and a leftover `mm6:natm` id; it works for the Roc, and the batch-M viewers
   patch their own copy (`scripts/viewer.py`) to frame the posed body, so the finished Roc project is left as accepted.
