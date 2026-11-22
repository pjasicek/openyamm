# Codex brief: the World of Xeen completion certificate (a new painting in the originals' layout)

Scope: image generation only. Write ONLY into `level_generation/ui/xeen_certificate_20261121/raw/`. Do not edit, move
or delete any other file; do not run builds. Use your built-in image generation tool.

What it is: the background of the victory certificate a player receives in OpenYAMM (an engine that plays the Might
and Magic VI-IX worlds and the World of Xeen) when the World of Xeen's story ends: Sheltem is gone, the two faces of
the flat world of Xeen are one world, and Prince Roland weds Queen Kalindra. World of Xeen had no certificate page, so
this is a NEW painting made to sit beside the original Might and Magic VI and VII certificates (`refs/6winbg.png`,
`refs/7winbg.png`) as a third of the same family. The game prints the headline, the party, the ending text, the time
and the score over it, and places a small OpenYAMM mark.

## Inputs (attached, in this order)
1. `guide.png`: the layout. Its coloured lines are instructions, not art.
2. `refs/6winbg.png`, 3. `refs/7winbg.png`: the style to match exactly (paper, sepia ink, faded illustration, the
   gold knotwork border with its corner and side medallions, the engraved title lettering, the bottom subtitle plaque).
4. `refs/eg270001.png`, 5. `refs/eg280001.png`: World of Xeen's ending pictures of the flat square world floating in
   the stars (the subject of the illustration). 6. `refs/eg140001.png`: the wedding of Roland and Kalindra (subject
   reference for small distant figures only).

## Format
1536 x 1024 landscape, unresized. The certificate fills exactly the middle 1365 x 1024 (the beige area of the guide);
the bars left and right (85 and 86 px) stay flat mid grey (128, 128, 128).

## Composition (follow the guide)
- BORDER: the gold interlaced knotwork border of the MM6/MM7 certificates along all four edges (between the outer brown
  line and the inner thin line of the guide), with the same kind of knot medallions in the corners and the middles of
  the sides; continuous, clean interlace.
- TITLE (upper green box): engraved gold-sepia lettering exactly "Might and Magic" in the style of 6winbg's title
  (the small "and" between the two words as there). No numeral, no other words.
- SUBTITLE PLAQUE (lower green box): a long engraved plaque like 6winbg's, reading exactly "WORLD OF XEEN" in small
  capitals like "THE MANDATE OF HEAVEN".
- ILLUSTRATION: very faded sepia ink and wash across the whole parchment inside the border, like the dragon and riders
  of 6winbg: the flat square world of Xeen seen at a three-quarter angle, floating among faint stars and clouds, both
  of its faces joined into one land under a single sun, mountains, a lake and towers small on it; at the lower right,
  small and distant, a castle balcony or cloud terrace with a bride and groom and a few guests raising their arms.
  Inside the red text zone the illustration must stay very pale and low contrast (the faintest parts of 6winbg), so
  that dark text printed over it reads perfectly; it may be stronger near the border.
- MARK (blue circle): plain parchment, nothing drawn there.
- No other text, letters, numbers, signatures, logos or watermarks anywhere (only the two lines above).

## Deliverables
`raw/xeen_cert_a.png` and `raw/xeen_cert_b.png` (1536 x 1024, unresized), two candidates differing in the illustration,
not in the layout. Write `raw/xeen_cert_generation.json` (prompt, inputs with sha256, outputs, notes). At most one
corrective regeneration per candidate.

## Checks per image
Grey bars flat; the border continuous and inside the guide's band; the title reads exactly "Might and Magic" and the
plaque exactly "WORLD OF XEEN"; the text zone pale; the mark spot plain; the colours the sepia, ivory and gold of the
references (no blue, no purple).
