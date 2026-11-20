#!/bin/bash
# Targeted retry of the vignette (attempt 4): an edit of raw/fleet_foot_3.png (sparse hatching and calligraphic runes
# fixed) that gives the caption Fly's stroke weight and size and the haze Fly's darkness.
cd "$(dirname "$0")/../../../.."
D=level_generation/ui/mm9_fleet_foot_20261109
codex exec "Follow the brief in $D/CODEX_BRIEF.md (vignette rules, Output section) for list position 1 of $D/art.json, \
as a retry: existing masters and records stay, save this attempt as raw/fleet_foot_4.png, append its record to \
raw/runs_fleet_foot.json, and write the master as masters/fleet_foot_v4.png (same master rules). One image generation. \
The attached images are, in order: (A) raw/fleet_foot_3.png, the attempt to edit; (B) refs/refs_fly_caption.png, the \
original Fly picture (left) and its lower-left quarter enlarged three times (right); (C) refs/refs_air_vignettes.png, \
the brief's input 1. Edit image A, keeping the two running boots, their pose, leather, cuffs, buckles, wings, wind \
streaks, curls and dust exactly, and keeping the haze made of separate pen strokes with true transparency between \
them. Two corrections, judged against B at the same picture size: \
(1) The rune caption is too thin, too small and too faint. Redraw it at the same place (bottom left) with the weight \
of Fly's caption in B: the large glyph a bold teal-green pen stroke, about one sixth of the picture's height, its \
stroke about as thick as a fifth of its height, with a dark outline and a lighter highlight along it, a simple hooked \
or looped shape; to its right two rows of five small glyphs, each about one eighteenth of the picture's height, drawn \
with bold strokes about a quarter as thick as the glyph is tall, filled with bright red-orange ink and outlined in \
dark brown, like Fly's small glyphs. New invented shapes made of hooks, bars and bent strokes; none may look like a \
digit, a Latin letter or a familiar symbol. \
(2) The hatching haze is far paler than Fly's. Make it as dark and dense as the haze behind Fly's wings in B: \
dark brown-black diagonal hatch strokes packed closely right behind the boots and the wind, then thinning to sparse \
strokes and to nothing at the outer edge; still individual strokes with transparency between them, not a filled \
panel. True alpha background, no parchment, no frame." \
    -C "$PWD" -s workspace-write --add-dir ~/.codex/generated_images -o "$D/raw/batch_retry4_last_message.md" \
    -i "$D/raw/fleet_foot_3.png" -i "$D/refs/refs_fly_caption.png" -i "$D/refs/refs_air_vignettes.png" \
    < /dev/null > "$D/raw/batch_retry4_run.log" 2>&1
ls "$D/masters"
