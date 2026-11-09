# Codex brief: Statistics menu icon

## Scope

- Image generation with your built-in image generation tool, plus Python (PIL) only to crop, resize, remove a
  background and check your own outputs.
- Write only into `level_generation/ui/playthrough_stats_20261107/icon/`. No builds, no code changes, no other files.

## Input

**Attached image 1** (`refs_menu_icons.png`): the four existing icon-only menu buttons of the gameplay top bar, left
to right: Journal (black leather book with quill and ink pot), Party (three bronze busts), Rest (canvas tent with a
crescent moon), Options (bronze gear). They sit at about 22 px on a dark green-black obsidian bar. **Match this
style exactly**: one painted object, warm antique bronze/brass with dark leather or ivory accents, soft light from the
upper left, rich but not glossy, crisp edges, no outline, no frame, no background, no ground shadow.

## What to make

A fifth button that opens the party's **playthrough statistics** (time played, monsters slain, deaths, experience,
gold). Make three candidates, one image generation each, each a different subject:

1. `candidate_a.png`: an open brass-capped parchment scroll (both rollers visible, sheet partly unrolled) whose sheet
   carries a few abstract dark tally strokes in groups (four strokes crossed by a fifth). No letters or numbers.
2. `candidate_b.png`: a bronze astrolabe / measuring dial with one pointer, seen slightly from the front, with a ring
   hanger at the top. Its silhouette must not read as the Options gear: smooth round rim, no teeth.
3. `candidate_c.png`: a small bronze laurel-free trophy goblet (chalice) with a single crossed sword and quill behind
   it, read as "deeds recorded". Keep it to one strong silhouette.

Common prompt to use as the base of every generation, then the subject:
"Create a SINGLE simple transparent menu icon for the Carved Obsidian fantasy RPG UI, a member of the attached set of
four icons (book with quill, three bronze busts, tent, gear). One immediately recognizable object, one strong clean
silhouette, smooth hand-painted shading, lightly worn antique bronze and brass, ivory parchment and dark leather where
appropriate. Broad simple shapes, minimal surface detail, readable at 22 screen pixels on dark green-black stone. Soft
even highlights from upper left. Center the COMPLETE object in a square canvas, occupying about 80% of its longest
dimension. TRUE transparent alpha background. No lettering, numbers, labels, border, backing plaque, medallion,
scene, glow or floor shadow. No photorealistic microtexture, no cartoon emoji, no pixel art."

## Output

- Save each generation untouched to `raw/`, then a cleaned 1024 x 1024 RGBA master to `masters/<candidate>.png` with a
  true transparent background (remove any baked checkerboard or flat backdrop; keep soft antialiased edges).
- Then write `masters/check_sheet.png`: the three candidates beside the four reference icons, at 22 px and 44 px,
  on `#161e18`, so the set can be compared.
- Finish with one short line per candidate: whether it reads at 22 px and how it differs from the gear and the book.
