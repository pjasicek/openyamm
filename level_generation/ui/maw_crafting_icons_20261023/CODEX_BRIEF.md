# Codex brief: MAW crafting item icons

## Scope

- Image generation with your built-in image generation tool, plus Python (PIL) only to crop, resize and check your
  own outputs.
- Write only into `level_generation/ui/maw_crafting_icons_20261023/`. Do not change existing masters or records.
- No builds, no code changes, no other files touched.

## Inputs

**Attached image 1** (`refs_mm_icons.png`): existing Might and Magic inventory icons: ten valuable gems (Zircon,
Iolite, Citrine, Amber, Amethyst, Topaz, Emerald, Sapphire, Ruby, Diamond) and a potion bottle. **Match this icon
style**: a realistic painted object, lit softly from the top left, rich but not glossy, crisp edges, no outline, no
background, no shadow on the ground. The new gems must look like members of the same set yet be distinguishable
from these ten and from each other at a small size.

## What to make

`items.json` lists 30 crafting items of a fantasy role-playing game: `id`, `file`, `name`, `inv_cells` (inventory
width × height in cells), `master_box_px` and `description`. The prompt names the list positions to do in this run;
do those, one image generation each.

- **The object's shape follows its cells:** a 1 × 1 item is compact, a 1 × 2 item tall and narrow, a 2 × 2 item
  compact and square, a 2 × 3 item tall. Fill most of the box.
- **Gems 1-10** are loose cut or natural gems, each its own colour and cut. **Gems 11-20** are their "Ascended"
  forms: the same gem as the matching plain one (same colour and character), larger and flawless, in a fine gold
  filigree cradle, with a stronger inner light. A player must see at a glance which plain gem an ascended one belongs
  to, and that it is the finer one.
- The other ten are unique magical artefacts; each needs a clear silhouette at a small size.
- **No text, letters, numbers or logos.** Runes are abstract cut shapes.

## Output

- Ask the image tool for a **transparent background** and keep its alpha.
- Crop to the object with about 8 px of transparent margin, then scale (keeping the aspect ratio, high-quality
  resampling) to fit inside `master_box_px`. Do not pad to the box.
- Save `masters/<file>` (RGBA PNG); every raw generation as `raw/<file stem>_<n>.png`.
- Records: write `raw/runs_<file stem>.json` (a JSON list), one record per generated image: `id`, `file` (the raw
  path, `raw/…`), `prompt`, `selected`, `reason`.
- Check each result: the shape follows the cells, no text, a transparent background with clean edges. Retry at most
  once with one targeted correction if a check fails.
- Skip any item whose master already exists, so a rerun resumes.
