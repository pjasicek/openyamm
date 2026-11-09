# Codex brief: MM9 Fleet Foot art (spellbook picture and HUD indicator pieces)

## Scope

- Image generation with your built-in image generation tool, plus Python (PIL) only to crop, resize and check your
  own outputs.
- Write only into `level_generation/ui/mm9_fleet_foot_20261109/` (`raw/` and `masters/`). Do not change existing
  masters or records. No builds, no code changes, no other files touched.

## What this is

In the MM9 world the Air spell in Fly's place is Fleet Foot, a run-speed charm: winged boots. Two pieces of game art
need it: a spell picture ("vignette") on the parchment spellbook page next to the original Air pictures, and an
animated HUD indicator (a boot whose wing flaps) next to the HD Fly indicator. The indicator is assembled from a
separate boot and wing by a script, so you paint those as two separate pictures.

`art.json` lists the pieces: `kind`, `file`, `subject`. The prompt names the list positions to do in this run; do
those, one image generation each.

## Inputs (attached images)

Run for the vignette:

1. `refs/refs_air_vignettes.png`: four original Air spell pictures on parchment, each as a pair: left the
   **highlighted** state (full colour), right the **normal** state (sepia). Top left Fly (two white wings), top right a
   sword and shield, bottom left Feather Fall, bottom right Jump (a standing pair of winged boots, front view). Style
   authority.
2. `refs/refs_mm9_fleetfoot.png`: MM9's own Fleet Foot spell picture (a different, older style): the subject only.

Run for the HUD pieces:

3. `refs/refs_hud.png`: top row, MM9's eight native Fleet Foot HUD frames enlarged (36 px each): a brown leather boot,
   toe to the right, with a dark wing at the ankle that flaps. Bottom row, the engine's HD Fly indicator frames (a
   winged sandal): style authority for the HD icon painting.
4. `refs/refs_mm9_fleetfoot.png`: as input 2, for the boot's leather and cuff.

## Vignette (kind `vignette`)

Paint the **highlighted (full colour) state** only; the sepia state is derived later from it.

- Style of reference 1: a detailed hand-drawn and hand-coloured illustration with ink hatching, like a page of an old
  grimoire; dramatic diagonal composition; around it a soft dark hatched charcoal haze that fades to nothing (as behind
  the Fly wings). Colour is concentrated on the magic (the rushing wind, the white wings); the leather stays a natural
  warm brown like the Jump boots. Not glossy, not 3D-rendered, not cartoon.
- It must not repeat Jump's picture (a standing pair seen from the front): the boots are seen from the side, running.
- **Rune caption at the bottom left**, laid out exactly like Fly's (reference 1, top left): one large glyph in
  **teal-green** ink at the far left, and to its right two short rows of four or five small glyphs in **red-orange ink
  with dark outlines**. The glyphs are invented abstract shapes resembling the reference glyphs (hooks, bars, loops),
  new ones, not copies of Fly's. **No real letters, words or numbers.** The large glyph is about a sixth of the
  picture's height, the small glyphs about a twentieth.
- **Transparent background** (true alpha); no parchment, no frame, no border. The haze is semi-transparent dark
  hatching, not a filled rectangle.
- Square composition (the result fills a 300 x 298 slot like Fly's), the subject in the upper and right part, the
  caption bottom left.
- Prompt base: "Hand-drawn and hand-coloured grimoire illustration of a spell for a classic fantasy RPG spellbook page,
  in the exact style of the attached reference vignettes (input 1, left of each pair): ink hatching, aged painterly
  colour, soft dark hatched haze fading out behind the subject, a rune caption at the bottom left (one large teal-green
  glyph, two short rows of small red-orange glyphs with dark outlines), transparent background, no parchment, no
  frame, no real text. Subject: " + `subject`.

## HUD boot (kind `hud_boot`)

- One tall brown leather boot, **strict side view, toe pointing right, heel at the left, shaft upright**, the shape
  of the boot in the native frames (input 3, top row): a narrow shaft about half as wide as the foot is long, the boot
  about 1.3 times as tall as the foot is long, a slightly flared top, a long foot with a gently pointed toe, a low heel.
  A thin dark leather strap with a small metal ring around the ankle, where the wings attach. **No wings**, no
  sparkles, no ground shadow.
- Painted like the HD Fly sandal (input 3, bottom row): warm saturated leather from light tan to dark chestnut, crisp
  dark brown outline, soft painterly shading with a few highlights, readable at 128 px. Not photo-real, not flat
  vector.
- Transparent background (true alpha), nothing else in the picture.

## HUD wing (kind `hud_wing`)

- One single dark bird wing, spread open, seen from its outer side and lying flat in the picture plane: the **root
  (shoulder) at the lower left**, the leading edge running straight to the **tip at the upper right**, the long flight
  feathers fanning along the lower edge. An elongated, pointed wing about three times as long as it is wide.
- Colours of the native wing (input 3, top row): charcoal-black feathers with cool steel-grey highlights and a faint
  blue sheen on the coverts. Painted like the HD Fly wings (input 3, bottom row): crisp dark outline, individual
  feathers readable at 128 px, soft painterly shading.
- Transparent background (true alpha), nothing else (no boot, no second wing).

## Output

- Save every raw generation as `raw/<file stem>_<n>.png`.
- Masters (RGBA PNG): crop to the visible content with about 12 px transparent margin, scale so the longer side is
  768 px (vignette) or 512 px (boot, wing): `masters/<file>`.
- Records: `raw/runs_<file stem>.json` (a JSON list), one record per generated image: `file` (the raw path),
  `prompt`, `selected`, `reason`.
- Check each result against its kind's rules (subject, view and orientation, rune caption on the vignette, no real
  letters, true transparent background, the reference style). Retry at most once with one targeted correction if a
  check fails.
- Skip any entry whose master already exists, so a rerun resumes.
