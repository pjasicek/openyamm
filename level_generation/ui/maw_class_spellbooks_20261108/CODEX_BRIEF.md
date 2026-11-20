# Codex brief: MAW class spellbook art (mockup study)

## Scope

- Image generation with your built-in image generation tool, plus Python (PIL) only to crop, resize and check your
  own outputs.
- Write only into `level_generation/ui/maw_class_spellbooks_20261108/` (`raw/` and `masters/`). Do not change
  existing masters or records. No builds, no code changes, no other files touched.

## What this is

The game's spellbook is an old parchment book. Each school has a page with a round engraved medallion at the top left
(a scene with the school's name on a banner) and hand-drawn spell pictures ("vignettes") scattered over the pages,
each with a small caption of invented magical runes. A school is chosen with a round tab on the book's edge. Two MAW
classes get schools of their own: the Death Knight (Frost, Blood, Unholy) and the Assassin (Combat, Subtlety, Poisons,
Assassination). You paint their art so it sits with the original pages.

`art.json` lists the pieces: `kind` (vignette, medallion or tab), `file`, `subject` (what to paint), and for tabs
`colours`. The prompt names the list positions to do in this run; do those, one image generation each.

## Inputs (attached images, in this order)

1. `refs/refs_vignettes.png`: eight original vignettes on parchment, each as a pair: left the **highlighted** state
   (full colour), right the **normal** state (sepia). Style authority for vignettes.
2. `refs/refs_medallions.png`: the twelve original school medallions. Style authority for medallions.
3. `refs/refs_tabs.png`: the original school tabs, each as a pair: left the line-drawn idle state, right the painted
   selected state. Style authority for tabs.

## Vignettes

Paint the **highlighted (full colour) state** only; the sepia state is derived later from it.

- Style of reference 1: a detailed hand-drawn and hand-coloured illustration with ink hatching, like a page of an old
  grimoire; one subject, dramatic diagonal composition; around it a soft dark hatched charcoal haze that fades to
  nothing (as behind the hand and the lightning in the reference). Colour is concentrated on the magic (ice, blood,
  necrotic glow, fire, poison); metal and bone stay in muted natural tones. Not glossy, not 3D-rendered, not cartoon.
- Add a **rune caption** beside the subject, as every reference has: one large glyph in dark green ink and two or
  three short rows of small glyphs in dark red-brown ink, all invented abstract shapes resembling the reference
  glyphs. **No real letters, words or numbers.** Place it in the empty corner the composition leaves (side or below).
- **Transparent background** (true alpha); no parchment, no frame, no border. The haze is semi-transparent dark
  hatching, not a filled rectangle.
- About as wide as tall, or wider (reference vignettes are 1.0-1.6 times as wide as tall).
- Prompt base: "Hand-drawn and hand-coloured grimoire illustration of a spell for a classic fantasy RPG spellbook page,
  in the exact style of the attached reference vignettes (input 1, left of each pair): ink hatching, aged painterly
  colour, soft dark hatched haze fading out behind the subject, a small caption of invented rune glyphs (one large
  dark green glyph, small dark red-brown glyphs), transparent background, no parchment, no frame, no real text.
  Subject: " + `subject`.

## Medallions

- Paint only the **round scene inside the medallion**, in the style of reference 2: a sepia monochrome engraving
  (warm browns from cream to near black), detailed, illustrative, like an old book plate. **No ring, no knotwork
  border, no banner, no text**: those are added from the original page.
- The scene fills a circle that touches all four edges of a square canvas; keep the important shapes inside the
  central 80 % of the circle (the rim gets covered). Outside the circle may be plain cream.
- Prompt base: "A circular sepia engraving for a fantasy spellbook school medallion, in the exact style of the
  attached medallion scenes (input 2): monochrome warm brown ink and wash, fine engraving lines, old book plate look.
  The scene fills a circle touching the square canvas edges. No border ring, no banner, no lettering. Scene: " +
  `subject`.

## Tabs

- One image with **two discs side by side** on a transparent background, the same emblem in both:
  left, the idle state: a simple dark brown line drawing of the emblem with a thin circular outline on a transparent
  inside, like the left tabs of reference 3; right, the selected state: the emblem painted in rich colour inside a
  round coin with a thin dark rim, like the right tabs of reference 3, in the colours given.
- The emblem must read at 40 px: one bold simple shape, few details.
- Prompt base: "Two round spellbook school tab emblems side by side on a transparent background, in the exact style of
  the attached tabs (input 3). Left: a simple dark brown ink line drawing of the emblem inside a thin circle,
  transparent inside. Right: the same emblem painted in rich colour inside a round coin with a thin dark rim. Bold
  simple emblem readable at 40 pixels, no text. Emblem: " + `subject` + ". Colours of the painted coin: " +
  `colours`.

## Output

- Save every raw generation as `raw/<file stem>_<n>.png`.
- Masters (RGBA PNG):
  - vignette: crop to the visible content with about 12 px transparent margin, scale so the longer side is 768 px:
    `masters/<file>`.
  - medallion: scale to 768 x 768: `masters/<file>`.
  - tab: split at the gap between the two discs, crop each to its disc with 4 px margin, pad to square and scale to
    256 x 256: `masters/<stem>_d.png` (left, line drawing) and `masters/<stem>_u.png` (right, painted).
- Records: `raw/runs_<file stem>.json` (a JSON list), one record per generated image: `file` (the raw path),
  `prompt`, `selected`, `reason`.
- Check each result against its kind's rules (one subject, rune caption present on vignettes, no real letters,
  transparent background where asked, the reference style). Retry at most once with one targeted correction if a
  check fails.
- Skip any entry whose master already exists, so a rerun resumes.
