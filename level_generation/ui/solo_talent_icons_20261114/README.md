# Solo talent icons (MAW talent tree v2), 2026-11-14

Status: **approved by the user (2026-11-14)** and installed (`assets_dev/engine/icons_x2/talent_<id>.png`, `talents.yml`).

Icons of their own for the 19 talents and 2 keystones of the MAW solo run's talent tree v2
(`assets_dev/engine/data_tables/talents.yml`, design `devdocs/solo_action/TALENT_TREE_V2_BUILD.md`), replacing the
borrowed item and spell icons. Status: **installed** (see [Install](#install)). Viewer: [viewer.html](viewer.html)
(self-contained; every icon by tree at 40 and 128 px with its effect).

## Where they are drawn

- The solo action bar (`game/ui/GameplaySoloHud.cpp`, `drawItemIcon`) beside spell and item icons.
- The Talents page (`game/ui/GameplaySoloTalentsPage.cpp`, `drawIcon`): fitted into a box filled with IconBack
  (#151b1c) on the dark obsidian page, about 40 px.

Both load `icon_item` through `GameplayUiRuntime::ensureItemIconTextureLoaded`, which reads the PNG from the
`engine x2` icon package (`assets_dev/engine/icons_x2/`) with the item-icon decode (near-magenta and near-cyan texels
keyed out; the export nudges any such texel, there were none).

## Style and subjects

- Style input: [refs_spell_icons.png](refs_spell_icons.png), twelve of the game's spellbook icons (the lit `sb??NNa`
  art that `GameplayObsidianPainter::spellIcon` draws via the spellbook layout's hover asset): meteor, winged boots,
  wings, helm, crossed swords, fist, clover, frost star, eye, falling stars, medal, turtle.
- [CODEX_BRIEF.md](CODEX_BRIEF.md): one painted subject per icon, transparent background, strong silhouette at
  32-40 px, no text; tree colour identity (Arms steel and blood red, Archery wood, feather and green, Arcana violet
  and blue light, Any tree and keystones gold and bone; keystones grander, with a stronger gold glow).
- [icons.json](icons.json), written by `scripts/make_icons_json.py` (subjects and palettes live there; ids, names,
  trees and effect texts come from talents.yml).

| Tree | Talent | Subject |
| --- | --- | --- |
| Arms | Weapon Training | upright longsword, red grip, crimson glow |
| Arms | Cleave | double-bitted axe inside a full crimson-white crescent slash |
| Arms | Sweeping Blows | curved sword whose red arc sweeps through three helmeted heads |
| Arms | Onslaught | crossed bloodied hand axes under three rising red chevrons |
| Arms | Charge | bull-horned great helm rushing right, red speed streaks |
| Arms | Shield Wall | three overlapping red round shields |
| Archery | Marksman | drawn recurve bow with nocked arrow |
| Archery | Multishot | fan of five green-fletched arrows |
| Archery | Piercing Arrows | arrow passing through two wooden target discs |
| Archery | Power Shot (2026-11-16, replaced Pinning Shot) | one arrow wrapped in a golden-green burst and a shock ring, motion streaks behind |
| Archery | Steady Aim | straw target, arrow in the bullseye |
| Archery | Quickfoot | single leather boot with one green wing |
| Arcana | Attunement | open spellbook with a violet sigil rising |
| Arcana | Blink | violet portal ring, a streak of light leaping out |
| Arcana | Spell Surge | staff head crystal bursting with lightning |
| Arcana | Resolve | violet force dome, flame, ice and lightning glancing off |
| Arcana | Overload | crackling orb splitting into four linked orbs |
| Arcana | Binding Circle | glowing double rune ring with chains of light rising |
| Any | Bloodthirst | ivory fang dripping a crimson blood drop |
| Any | Conditioning (2026-11-16) | seven-pointed old gold star, a gem of a different colour on each point |
| Any | Spell Suppression (2026-11-16) | gold gauntlet crushing an orange-violet spell orb into fading sparks |
| Any | Manathirst (2026-11-16) | Bloodthirst's ivory fang dripping a glowing sapphire-blue mana drop |
| Keystone | Cheat Death | cracked bone skull, a gold spark of life bursting out |
| Keystone | Unbroken | whole stone heart bound in crossed gold bands |

## How they were made

- `scripts/run_batch.sh`: four parallel `codex exec` workers (built-in image generation; `-i refs_spell_icons.png`,
  `-C` repo, `-s workspace-write`, `--add-dir ~/.codex/generated_images`), positions 1-5, 6-10, 11-15 and 16-21 of
  icons.json, about seven minutes wall time. Each worker crops its picks to `masters/<id>.png` (512 x 512 RGBA) and
  records every generation in `raw/runs_<id>.json` (prompt, selected, reason); raw images are `raw/<id>_<n>.png`,
  run logs `raw/batch_<tag>_run.log` and `_last_message.md`, the workers' own check sheets `raw/check*.png`.
- Retries (25 generations for 21 icons):
  - by the workers' own 40/32 px checks: Sweeping Blows (dark targets merged into the trails), Binding Circle (the
    rising light read as flames, not chains), Unbroken (fissures made the heart look cracked);
  - by review (batch e, run alone with `run_batch.sh e "3" "<correction>"`): Sweeping Blows again, since the
    worker's pick (`raw/sweeping_blows_2.png`, its master kept as `raw/sweeping_blows_master_round1.png`) was a thin
    horizontal strip that shrank to a line at 40 px; `raw/sweeping_blows_3.png` is square, with three helmeted
    heads along the arc.
- `scripts/build_previews.py`: exports `runtime_x2/talent_<id>.png` (128 x 128 RGBA, subject fitted to 124 px on its
  longer side, 0644), the previews and viewer.html:
  - `previews/contact_40px.png`, `previews/contact_128px.png`: by tree, each on an IconBack tile on the page colour;
  - `previews/beside_spells_40px_x2.png`: the twelve reference spell icons, then all talent icons at 40 px,
    magnified 2x.

Review notes: every icon reads at 40 px and each tree's colour reads as a row. The set is cleaner, more saturated and
glossier than the grittier MM6-MM8 spellbook paintings; it sits well beside them on the bar but is not
indistinguishable from them. Cleave is the least distinct at 40 px (a red disc with an axe), but its silhouette
differs from the other Arms icons.

2026-11-16: Conditioning and Spell Suppression added (`run_batch.sh f "17"` and `g "18"`, one generation each, no
retry; 29,940 and 32,631 Codex tokens) and installed the same way. Weapon Training, Marksman and Attunement left the
table that day; their masters and runtime copies stay here, unused.

Manathirst added the same day (`run_batch.sh h "19"`, one generation, no retry; 29,147 Codex tokens) and installed
the same way.

Spend: no paid API calls. Codex subscription only: 25 image generations and about 220,000 Codex tokens (batches
a 45,952, b 41,533, c 49,277, d 50,073, e 32,802).

## Rerun

From the repository root:

```
python3 level_generation/ui/solo_talent_icons_20261114/scripts/make_icons_json.py   # after talents.yml changes
level_generation/ui/solo_talent_icons_20261114/scripts/run_batch.sh                  # skips existing masters
python3 level_generation/ui/solo_talent_icons_20261114/scripts/build_previews.py
```

To redo one icon, move its master to `raw/` and run `run_batch.sh <tag> "<position>" "<correction>"`.

## Install

- `runtime_x2/talent_<id>.png` copied (0644) to `assets_dev/engine/icons_x2/` (what the item-icon loader reads) and,
  as the source copy, to `assets_source/engine/icons_x2/`.
- `talents.yml`: each entry's `icon_item`/`icon_spell` line became `icon_item: talent_<id>` (keystones too).
- Not cooked to `.oytex`: `tools/cook_ui_textures.py` cooks only `obsidian_*` sources, the item-icon load
  (`GameplayHudBitmapTransparencyMode::ItemIcon`) never looks for a cooked file (`GameplayHudCommon::loadHudTexture`
  tries `loadCookedHudImage` only in `HudColorKey` mode), and `tools/package_runtime_assets.py` treats only
  `obsidian_*`/`faces_*` `.oytex` in `icons_x2` as cooked HUD art. A cooked install would need all three changed.
- Not checked in a game run: the check is static (the placeholders `item004` and `lshield2` resolve from the same
  folder through the same loader).
