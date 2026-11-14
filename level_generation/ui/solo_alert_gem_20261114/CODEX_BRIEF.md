# Codex brief: solo alert gem

## Scope

- Image generation with your built-in image generation tool, plus Python (PIL, numpy) only to crop, resize and check
  your own outputs.
- Write only into `level_generation/ui/solo_alert_gem_20261114/`. No builds, no code changes, no other files touched.

## Inputs

**Attached image 1** (`refs.png`):
- Top row, left: Might and Magic IX's four "compass gems" (blue, green, yellow, red), 35 pixels in the original,
  enlarged. A round domed cabochon jewel in a thin bronze bezel; a bright highlight top left, a ring of small sparkles
  inside the lower rim, a darker centre. **This is the design to remake in high definition.**
- Top row, right: our HUD's minimap rim: a thin, soft brass ring.
- Bottom row: our HUD's "Obsidian" style: painted, lit softly from the top left, crisp edges; dark blue-black
  obsidian with faint veining, polished pale-gold/brass rims (the diamonds), and a dark plate with a fine brass edge.

## What to make

One image: **a single round alert gem**, green, in the Obsidian style.

- The jewel: MM9's domed cabochon remade at high definition: deep emerald green, glassy and translucent, a darker
  centre, a soft inner glow toward the lower rim, a crisp white specular highlight top left, a few fine sparkles
  along the lower inner edge. Rich but not neon.
- The setting: a **polished brass bezel** of the same colour and lighting as the minimap rim and the diamonds'
  rims (pale warm gold-brass), about 9 % of the gem's diameter thick, with a thin dark obsidian collar outside it
  so it reads on any background. Plain and round: no prongs, no points, no ornaments, no text.
- Seen straight on, perfectly round and centred. No background, no cast shadow, no outline.

## Output

- Ask the image tool for a **transparent background** and keep its alpha. Generate 2 candidates.
- For each: crop to the gem with 4 % transparent margin, make it square, resize (high-quality) to 256 x 256, save
  `raw/gem_green_<n>.png` (the full raw generation as `raw/gem_green_<n>_full.png`).
- Pick the better one (round, centred, clean alpha edge, reads clearly at 32 x 32: check a 32 px downscale) and save
  it as `masters/gem_green.png`.
- Write `raw/runs.json`: one record per candidate: `file`, `prompt`, `selected`, `reason`.
