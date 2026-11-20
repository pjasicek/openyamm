#!/bin/bash
# Targeted retry of the vignette (attempt 3): an edit of raw/fleet_foot_2.png that keeps the subject and fixes the
# two style faults of attempts 1-2 (an opaque dark backdrop instead of sparse hatching; thorny, blobby runes).
cd "$(dirname "$0")/../../../.."
D=level_generation/ui/mm9_fleet_foot_20261109
codex exec "Follow the brief in $D/CODEX_BRIEF.md (vignette rules, Output section) for list position 1 of $D/art.json, \
as a retry: the existing master and records stay, save this attempt as raw/fleet_foot_3.png, append its record to \
raw/runs_fleet_foot.json, and write the master as masters/fleet_foot_v3.png (same master rules). One image generation. \
The attached images are, in order: (A) raw/fleet_foot_2.png, the attempt to edit; (B) the brief's input 1, \
refs/refs_air_vignettes.png. Edit image A, keeping the two running boots, their pose, leather, cuffs and buckles, the \
white ankle wings, the wind streaks and curls and the dust exactly. Fix two faults against the originals of image B: \
(1) The background haze: A has a solid, nearly opaque dark grey-blue backdrop behind the whole picture. Replace it with \
the haze of the originals in B (behind Fly's wings and the Jump boots): loose, sparse diagonal charcoal-brown pen \
hatching strokes with true transparency between the strokes, densest close behind the boots and fading to nothing \
outward; most of the area away from the boots is fully transparent. The pale wind streaks keep a thin darker edge so \
they still read on light parchment. No filled shape, no dark panel. (2) The rune caption at the bottom left: redraw it \
in the calligraphic style of B's captions: the large glyph a smooth single pen-stroke teal-green shape with a highlight \
and a dark outline, simple hooked and looped like Fly's large glyph, NOT thorny, spiky or ornamental; to its right two \
short rows of four or five small glyphs drawn as thin simple pen shapes of two or three strokes each (hooks, bars, \
small loops) in red-orange ink with dark outlines, slender like B's small glyphs, NOT fat or blobby. Invented shapes, \
no real letters, digits or familiar symbols. Keep the caption at the same place and size. True alpha background, no \
parchment, no frame." \
    -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images -o "$D/raw/batch_retry3_last_message.md" \
    -i "$D/raw/fleet_foot_2.png" -i "$D/refs/refs_air_vignettes.png" < /dev/null > "$D/raw/batch_retry3_run.log" 2>&1
ls "$D/masters"
